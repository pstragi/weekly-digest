import json
import logging
import re
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import anthropic
import pytz

log = logging.getLogger(__name__)

SUMMARY_SYSTEM_PROMPT = """\
You are a sharp, concise editor writing for a smart professional reader.

For each article write:
1. "summary": 2–3 sentences that capture the key insight or finding and WHY it matters.
   Be specific — include numbers, names, or data if they are in the content.
   Do NOT start with "This article..." or "The author says...". Get straight to the point.
2. "takeaway": one punchy sentence — the single most actionable or surprising point.

LANGUAGE RULE: Write the summary and takeaway in the SAME LANGUAGE as the article.
- If the article language field is "pl", write in Polish.
- If the article language field is "en", write in English.
Do NOT translate articles.

Return ONLY valid JSON array. No markdown, no extra text.
Format: [{"id": "...", "summary": "...", "takeaway": "..."}]
"""


def _parse_json(raw: str) -> list:
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    log.error("Could not parse summaries JSON")
    return []


def generate_summaries(
    articles_by_category: dict, client: anthropic.Anthropic
) -> dict[str, dict]:
    """Generate 2–3 sentence summaries + takeaways for all selected articles."""
    to_summarize = []
    for category, articles in articles_by_category.items():
        for art in articles:
            content = art.get("full_text") or art.get("excerpt") or art["title"]
            to_summarize.append(
                {
                    "id": art["id"],
                    "title": art["title"],
                    "source": art["source"],
                    "language": art.get("language", "en"),
                    "category": category,
                    "content": content[:4000],
                }
            )

    if not to_summarize:
        return {}

    prompt = (
        f"Summarize each of these {len(to_summarize)} articles.\n\n"
        f"Articles:\n{json.dumps(to_summarize, ensure_ascii=False, indent=2)}"
    )

    log.info(f"Generating summaries for {len(to_summarize)} articles…")

    _summary_schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "id":       {"type": "string"},
                "summary":  {"type": "string"},
                "takeaway": {"type": "string"},
            },
            "required": ["id", "summary", "takeaway"],
            "additionalProperties": False,
        },
    }

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=8000,
        system=SUMMARY_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
        output_config={"format": {"type": "json_schema", "schema": _summary_schema}},
    )

    raw = next(
        (b.text for b in response.content if b.type == "text"), ""
    ).strip()
    results = _parse_json(raw)
    return {item["id"]: item for item in results}


# ── HTML helpers ──────────────────────────────────────────────────────────────

_BADGE_MUST_READ = (
    '<span style="background:#c53030;color:#fff;padding:2px 8px;'
    "border-radius:10px;font-size:11px;font-weight:700;"
    'letter-spacing:0.3px;">🔥 MUST READ</span>'
)
_BADGE_TOP_PICK = (
    '<span style="background:#c05621;color:#fff;padding:2px 8px;'
    "border-radius:10px;font-size:11px;font-weight:700;"
    'letter-spacing:0.3px;">⭐ TOP PICK</span>'
)


def _importance_badge(importance: float) -> str:
    if importance >= 8.0:
        return _BADGE_MUST_READ
    if importance >= 6.5:
        return _BADGE_TOP_PICK
    return ""


def _published_label(published_dt: Optional[datetime]) -> str:
    if not published_dt:
        return ""
    now_utc = datetime.now(pytz.utc)
    age_h = (now_utc - published_dt).total_seconds() / 3600
    if age_h < 1:
        mins = int(age_h * 60)
        label = f"{mins}m ago"
    elif age_h < 24:
        label = f"{int(age_h)}h ago"
    else:
        label = published_dt.strftime("%b %d")
    return (
        f'<span style="color:#718096;font-size:12px;margin-left:6px;">{label}</span>'
    )


def _article_card(art: dict, summary_data: dict) -> str:
    badge = _importance_badge(art.get("importance", 5))
    time_label = _published_label(art.get("published_dt"))
    summary = summary_data.get("summary", art.get("excerpt", ""))
    takeaway = summary_data.get("takeaway", "")

    takeaway_html = ""
    if takeaway:
        takeaway_html = (
            '<p style="color:#2d3748;font-size:13px;margin:8px 0 0;'
            "padding:8px 12px;background:#ebf8ff;border-radius:6px;"
            'line-height:1.5;">'
            f"<strong>💡 Takeaway:</strong> {takeaway}</p>"
        )

    return f"""
    <div style="border-left:3px solid #4299e1;padding:12px 16px;margin:14px 0;
                background:#f7fafc;border-radius:0 8px 8px 0;">
      <div style="margin-bottom:6px;display:flex;align-items:center;flex-wrap:wrap;gap:4px;">
        {badge}
        <span style="color:#718096;font-size:12px;">{art['source']}</span>
        {time_label}
      </div>
      <a href="{art['url']}"
         style="color:#1a202c;font-size:15px;font-weight:700;text-decoration:none;
                line-height:1.4;display:block;">{art['title']}</a>
      <p style="color:#4a5568;font-size:14px;line-height:1.65;margin:8px 0 0;">
        {summary}
      </p>
      {takeaway_html}
    </div>"""


def _category_section(category: str, info: dict, articles: list[dict], summaries: dict) -> str:
    cards = "".join(
        _article_card(art, summaries.get(art["id"], {})) for art in articles
    )
    return f"""
    <div style="margin:28px 0 20px;">
      <h2 style="color:#1a202c;font-size:17px;font-weight:800;margin:0 0 2px;
                 padding-bottom:10px;border-bottom:2px solid #e2e8f0;">
        {info['emoji']} {category.replace('_', ' ')}
      </h2>
      {cards}
    </div>"""


def build_html(articles_by_category: dict, summaries: dict) -> str:
    from config import INTERESTS

    CET = pytz.timezone("Europe/Warsaw")
    today = datetime.now(CET).strftime("%A, %B %-d, %Y")
    total = sum(len(v) for v in articles_by_category.values())
    cats = len(articles_by_category)

    sections = "".join(
        _category_section(cat, INTERESTS[cat], articles_by_category[cat], summaries)
        for cat in INTERESTS
        if cat in articles_by_category
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Daily Digest — {today}</title>
</head>
<body style="margin:0;padding:0;background:#edf2f7;
             font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,
             'Helvetica Neue',Arial,sans-serif;">
  <div style="max-width:680px;margin:0 auto;padding:24px 16px;">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#1a202c 0%,#2d3748 100%);
                padding:28px 32px;border-radius:12px 12px 0 0;">
      <div style="color:#718096;font-size:11px;font-weight:700;letter-spacing:1.2px;
                  text-transform:uppercase;">Your News Digest</div>
      <h1 style="color:#fff;font-size:22px;font-weight:800;margin:6px 0 0;
                 letter-spacing:-0.3px;">{today}</h1>
      <p style="color:#718096;font-size:13px;margin:8px 0 0;">
        {total} hand-picked stories across {cats} topics
      </p>
    </div>

    <!-- Body -->
    <div style="background:#fff;padding:24px 32px;border-radius:0 0 12px 12px;
                box-shadow:0 4px 12px rgba(0,0,0,0.06);">
      {sections}

      <!-- Footer -->
      <div style="border-top:1px solid #e2e8f0;margin-top:28px;padding-top:16px;">
        <p style="color:#a0aec0;font-size:12px;text-align:center;margin:0;
                  line-height:1.6;">
          Curated by Claude AI · Delivered Monday &amp; Thursday at 7:00 AM CET
        </p>
      </div>
    </div>

  </div>
</body>
</html>"""


# ── Send ──────────────────────────────────────────────────────────────────────

def send_digest(
    articles_by_category: dict,
    dry_run: bool = False,
    dry_run_path: str = "digest_preview.html",
) -> None:
    """Generate summaries, build HTML email, and send (or save for dry-run)."""
    from config import (
        ANTHROPIC_API_KEY,
        SMTP_SERVER,
        SMTP_PORT,
        SMTP_USER,
        SMTP_PASSWORD,
        RECIPIENT_EMAIL,
        SENDER_NAME,
    )

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    summaries = generate_summaries(articles_by_category, client)
    html_body = build_html(articles_by_category, summaries)

    if dry_run:
        with open(dry_run_path, "w", encoding="utf-8") as f:
            f.write(html_body)
        log.info(f"Dry-run: HTML saved to {dry_run_path} — open in a browser to preview.")
        return

    CET = pytz.timezone("Europe/Warsaw")
    today = datetime.now(CET).strftime("%A, %B %-d")
    subject = f"📰 Your Daily Digest — {today}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{SENDER_NAME} <{SMTP_USER}>"
    msg["To"] = RECIPIENT_EMAIL
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    log.info(f"Sending digest to {RECIPIENT_EMAIL}…")
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, RECIPIENT_EMAIL, msg.as_string())

    log.info("Email sent successfully!")
