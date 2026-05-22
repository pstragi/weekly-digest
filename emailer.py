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

_ACCENT = "#1A5C4A"
_LIME = "#9ECF3A"

_BADGE_MUST_READ = (
    f'<span style="background:{_ACCENT};color:#fff;padding:2px 10px;'
    "border-radius:4px;font-size:10px;font-weight:700;"
    'letter-spacing:1px;text-transform:uppercase;">🔥 MUST READ</span>'
)
_BADGE_TOP_PICK = (
    f'<span style="background:{_ACCENT};color:{_LIME};padding:2px 10px;'
    "border-radius:4px;font-size:10px;font-weight:700;"
    'letter-spacing:1px;text-transform:uppercase;">⭐ TOP PICK</span>'
)

_MONO = "font-family:'DM Mono',monospace;"


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
    return f'<span style="{_MONO}font-size:10px;color:#A0968A;">{label}</span>'


def _article_card(art: dict, summary_data: dict) -> str:
    badge = _importance_badge(art.get("importance", 5))
    time_label = _published_label(art.get("published_dt"))
    summary = summary_data.get("summary", art.get("excerpt", ""))
    takeaway = summary_data.get("takeaway", "")
    lang = art.get("language", "en").upper()

    badge_html = f"{badge} " if badge else ""

    takeaway_html = ""
    if takeaway:
        takeaway_html = f"""
      <div style="display:flex;align-items:flex-start;gap:10px;margin-top:12px;">
        <div style="width:3px;background:{_LIME};border-radius:2px;flex-shrink:0;align-self:stretch;min-height:32px;"></div>
        <p style="font-size:12px;color:#3D3530;line-height:1.6;margin:0;font-weight:500;">{takeaway}</p>
      </div>"""

    return f"""
    <div style="margin-bottom:20px;padding:20px;background:#fff;border-radius:12px;border:1px solid #E2E8E4;">
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:10px;flex-wrap:wrap;">
        {badge_html}<span style="{_MONO}font-size:10px;color:#A0968A;">{art['source'].upper()}</span>
        <span style="{_MONO}font-size:10px;color:#C8BFB4;">/</span>
        {time_label}
        <span style="{_MONO}font-size:9px;border:1px solid #D8D0C6;color:#A0968A;padding:1px 5px;border-radius:3px;letter-spacing:1px;">{lang}</span>
      </div>
      <a href="{art['url']}"
         style="font-size:17px;font-weight:700;color:#0D0D0D;text-decoration:none;
                line-height:1.3;display:block;margin-bottom:10px;letter-spacing:-0.2px;">{art['title']}</a>
      <p style="font-size:13px;color:#6A6460;line-height:1.7;margin:0;font-weight:300;">{summary}</p>
      {takeaway_html}
    </div>"""


def _category_section(
    category: str, info: dict, articles: list[dict], summaries: dict, section_num: int
) -> str:
    cards = "".join(
        _article_card(art, summaries.get(art["id"], {})) for art in articles
    )
    num = str(section_num).zfill(2)
    label = category.replace("_", " ")
    return f"""
    <div style="margin-bottom:40px;">
      <div style="display:flex;align-items:center;gap:16px;margin-bottom:24px;
                  padding-bottom:16px;border-bottom:3px solid {_ACCENT};">
        <span style="{_MONO}font-size:11px;color:#B0A89C;letter-spacing:1px;">{num}</span>
        <span style="font-size:18px;font-weight:700;color:#0D0D0D;letter-spacing:-0.3px;">{info['emoji']} {label}</span>
      </div>
      {cards}
    </div>"""


def build_html(articles_by_category: dict, summaries: dict) -> str:
    from config import INTERESTS

    CET = pytz.timezone("Europe/Warsaw")
    today = datetime.now(CET).strftime("%A, %B %-d, %Y")
    date_short = datetime.now(CET).strftime("%d-%m-%Y")
    total = sum(len(v) for v in articles_by_category.values())

    sections = "".join(
        _category_section(cat, INTERESTS[cat], articles_by_category[cat], summaries, i + 1)
        for i, cat in enumerate(cat for cat in INTERESTS if cat in articles_by_category)
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>News Digest — {today}</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
</head>
<body style="margin:0;padding:0;background:#EEF0EB;
             font-family:'Plus Jakarta Sans',-apple-system,BlinkMacSystemFont,sans-serif;">
<div style="max-width:680px;margin:0 auto;padding:28px 16px 40px;">

  <!-- Header -->
  <div style="background:linear-gradient(135deg,#0A2E24 0%,#0D4A3A 25%,#1A6B50 55%,#5FA84A 80%,#9ECF3A 100%);
              border-radius:18px;padding:40px 44px 44px;position:relative;overflow:hidden;">
    <div style="position:absolute;top:0;left:0;right:0;bottom:0;opacity:0.07;
                background:repeating-linear-gradient(90deg,#fff 0px,#fff 1px,transparent 1px,transparent 40px);
                pointer-events:none;"></div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:32px;">
      <span style="{_MONO}font-size:11px;color:rgba(255,255,255,0.5);letter-spacing:1px;">NEWS DIGEST</span>
      <span style="{_MONO}font-size:11px;color:rgba(255,255,255,0.5);letter-spacing:1px;">{total} STORIES</span>
      <span style="{_MONO}font-size:11px;color:rgba(255,255,255,0.5);letter-spacing:1px;">{date_short}</span>
    </div>
    <div style="line-height:1.0;margin-bottom:28px;">
      <div style="font-size:56px;font-weight:300;color:rgba(255,255,255,0.55);letter-spacing:-2px;line-height:1;">YOUR</div>
      <div style="font-size:56px;font-weight:700;color:#fff;letter-spacing:-2px;line-height:1;">NEWS</div>
      <div style="font-size:56px;font-weight:700;color:#9ECF3A;letter-spacing:-2px;line-height:1;">DIGEST ✦</div>
    </div>
    <div style="border-top:1px solid rgba(255,255,255,0.15);padding-top:20px;">
      <div style="font-size:13px;color:rgba(255,255,255,0.5);font-weight:300;">{today}</div>
    </div>
  </div>

  <!-- Body -->
  <div style="background:#F8F7F2;border-radius:18px;padding:36px 40px 44px;margin-top:8px;">
    {sections}

    <!-- Footer -->
    <div style="border-top:1px solid #E5E2DA;padding-top:20px;
                display:flex;justify-content:space-between;align-items:center;">
      <span style="{_MONO}font-size:10px;color:#C0B8B0;letter-spacing:0.5px;">Curated by Claude AI</span>
      <span style="{_MONO}font-size:10px;color:#C0B8B0;letter-spacing:0.5px;">Mon &amp; Thu · 07:00 CET</span>
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
