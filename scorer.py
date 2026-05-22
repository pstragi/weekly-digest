import json
import logging
import re
from datetime import datetime, timezone
from typing import Optional

import anthropic

log = logging.getLogger(__name__)

SCORING_SYSTEM_PROMPT = """\
You are a senior news editor curating a personalized daily digest for one reader.

The reader's six interest categories:

MARKETING — Digital marketing, advertising, brand strategy, content marketing, SEO,
  social media, growth hacking, PR, martech, influencer marketing, performance marketing.

TECHNOLOGY — AI and machine learning breakthroughs, startups and funding, software,
  cybersecurity, digital transformation, automation, tech industry news.

SCIENCE — Scientific discoveries and research, biology, physics, climate science,
  space, medicine, genetics, neuroscience. Must be research/discovery-driven.

SOCIAL_SCIENCES — Psychology, sociology, human behavior, cognitive science, mental
  health trends, social phenomena, culture, relationships, behavioral economics.

SPORT — Sports news and results, football, tennis, athletics, championships,
  sports science, fitness with a sports angle.

WELLBEING — Health optimization, nutrition science, self-development, mindfulness,
  productivity, sleep science, stress management, personal growth, longevity.

CRYPTO — Cryptocurrency markets, Bitcoin, Ethereum, DeFi, NFTs, blockchain technology,
  Web3, crypto regulation, exchange news, tokenomics, on-chain analytics, trading trends,
  stablecoins, Layer 2 networks. Must be specifically about crypto/blockchain — do NOT
  assign tech articles that merely mention blockchain to this category.

SCORING RULES:
- category: the single best-matching category from the list above (semantic match, not keywords)
- relevance (0–10): how strongly the article fits that category
  * 9–10: the article is deeply and clearly about this topic
  * 6–8: strong match, clearly relevant
  * 3–5: loosely related
  * 0–2: doesn't fit — use 0 if the article fits NO category (politics, celebrity gossip, etc.)
- importance (0–10): how significant / worth reading is this article?
  * 9–10: breaking news, major industry change, groundbreaking research, widespread impact
  * 7–8: significant trend, important research finding, major company move
  * 5–6: useful insight, interesting development, notable update
  * 3–4: general news, minor update, regional story without wider impact
  * 1–2: opinion/listicle/promotional/press release content

Return ONLY a valid JSON array. No markdown, no explanation, no trailing text.
Format: [{"id": "...", "category": "...", "relevance": 0.0, "importance": 0.0}]
"""


def _parse_json(raw: str) -> list:
    """Parse JSON from Claude's response with markdown-stripping fallback."""
    text = raw.strip()

    # Strip opening ```json or ``` and closing ```
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        pass

    # Last resort: find the first [...] block in the text
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    log.error("Could not parse Claude's JSON response")
    return []


def _compute_recency_score(published_dt: Optional[datetime]) -> float:
    if not published_dt:
        return 5.0
    age_h = (datetime.now(timezone.utc) - published_dt).total_seconds() / 3600
    if age_h < 24:
        return 10.0
    if age_h < 48:
        return 5.0
    if age_h < 120:  # up to 5 days
        return 3.0
    return 1.0


_SCORE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "id":         {"type": "string"},
            "category":   {"type": "string"},
            "relevance":  {"type": "number"},
            "importance": {"type": "number"},
        },
        "required": ["id", "category", "relevance", "importance"],
        "additionalProperties": False,
    },
}


def _score_chunk(client: anthropic.Anthropic, articles: list[dict]) -> list[dict]:
    """Ask Claude to score one batch of articles (≤80 items)."""
    # Use short numeric IDs in the Claude call to minimise response tokens,
    # then map back to the real article IDs afterwards.
    index_to_id = {str(i): a["id"] for i, a in enumerate(articles)}

    payload = json.dumps(
        [
            {
                "id": str(i),
                "title": a["title"],
                "excerpt": (a.get("excerpt") or "")[:300],
                "source": a["source"],
            }
            for i, a in enumerate(articles)
        ],
        ensure_ascii=False,
        indent=2,
    )

    prompt = (
        f"Score these {len(articles)} articles. "
        "For each one assign: category, relevance (0-10), importance (0-10).\n\n"
        f"Articles:\n{payload}"
    )

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=SCORING_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
        output_config={"format": {"type": "json_schema", "schema": _SCORE_SCHEMA}},
    )

    raw = next(
        (b.text for b in response.content if b.type == "text"), ""
    ).strip()
    result = _parse_json(raw)
    if not result:
        log.error(f"Full raw response:\n{raw}")
        return []

    # Restore real article IDs
    for item in result:
        item["id"] = index_to_id.get(str(item["id"]), item["id"])
    return result


def score_and_select_articles(articles: list[dict]) -> dict[str, list[dict]]:
    """
    Score all articles with Claude, compute final scores, and return the
    top MAX_ARTICLES_PER_CATEGORY articles per interest category.
    Also fetches full text for the selected articles.
    """
    from config import ANTHROPIC_API_KEY, INTERESTS, MAX_ARTICLES_PER_CATEGORY
    from scraper import fetch_full_text

    if not articles:
        log.warning("No articles to score.")
        return {}

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Batch scoring (chunks of 80 to stay within token limits)
    all_scores: list[dict] = []
    chunk_size = 80
    for i in range(0, len(articles), chunk_size):
        chunk = articles[i : i + chunk_size]
        log.info(
            f"  Scoring batch {i // chunk_size + 1} "
            f"({len(chunk)} articles)…"
        )
        all_scores.extend(_score_chunk(client, chunk))

    article_map = {a["id"]: a for a in articles}

    # Compute final weighted scores
    scored: list[dict] = []
    for item in all_scores:
        article_id = item.get("id", "")
        article = article_map.get(article_id)
        if not article:
            continue

        category: str = item.get("category", "TECHNOLOGY")
        relevance: float = max(0.0, min(10.0, float(item.get("relevance", 0))))
        importance: float = max(0.0, min(10.0, float(item.get("importance", 0))))

        if relevance < 1.0:  # article is off-topic — skip
            continue

        recency = _compute_recency_score(article.get("published_dt"))
        authority = float(article["authority"].get(category, 5))
        popularity_multiplier = 1.1 if article.get("is_popular_feed") else 1.0

        final_score = popularity_multiplier * (
            0.35 * relevance
            + 0.35 * importance
            + 0.20 * recency
            + 0.10 * authority
        )

        scored.append(
            {
                **article,
                "category": category,
                "relevance": relevance,
                "importance": importance,
                "recency": recency,
                "final_score": final_score,
            }
        )

    # Select top N per category: 2 English + 1 Polish, with fallback if unavailable
    selected: dict[str, list[dict]] = {}

    for category in INTERESTS:
        candidates = sorted(
            [a for a in scored if a["category"] == category],
            key=lambda x: x["final_score"],
            reverse=True,
        )

        en = [a for a in candidates if a.get("language") == "en"]
        pl = [a for a in candidates if a.get("language") == "pl"]
        top = en[:2] + pl[:1]

        # Fill remaining slots if a language had fewer articles than target
        if len(top) < MAX_ARTICLES_PER_CATEGORY:
            used = {a["id"] for a in top}
            for a in candidates:
                if len(top) >= MAX_ARTICLES_PER_CATEGORY:
                    break
                if a["id"] not in used:
                    top.append(a)

        if not top:
            log.info(f"  {category}: no articles found")
            continue

        log.info(f"  {category}: {len(top)} articles selected — fetching full text…")
        for art in top:
            art["full_text"] = fetch_full_text(art["url"])

        selected[category] = top

    return selected
