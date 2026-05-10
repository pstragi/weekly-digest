import logging
import re
import ssl
import time
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
from typing import Optional

import certifi
import feedparser
import requests
import trafilatura
from bs4 import BeautifulSoup

# Fix macOS Python SSL certificate issue (Python.org installer doesn't bundle certs)
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
REQUEST_TIMEOUT = 15
FULL_TEXT_MAX_CHARS = 8000


class _HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(self._parts)


def _strip_html(html: str) -> str:
    s = _HTMLStripper()
    s.feed(html)
    return re.sub(r"\s+", " ", s.get_text()).strip()


def _parse_published_time(entry) -> Optional[datetime]:
    for attr in ("published_parsed", "updated_parsed", "created_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def fetch_rss(source: dict, lookback_hours: int) -> list[dict]:
    """Fetch and parse articles from a single RSS source."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    articles = []

    try:
        feed = feedparser.parse(source["rss"], request_headers=HEADERS)

        if feed.bozo and not feed.entries:
            log.warning(
                f"[{source['name']}] RSS parse issue: {getattr(feed, 'bozo_exception', 'unknown')}"
            )
            return []

        for entry in feed.entries:
            published = _parse_published_time(entry)

            # Respect lookback window; allow undated entries through
            if published and published < cutoff:
                continue

            title = entry.get("title", "").strip()
            url = entry.get("link", "").strip()
            if not title or not url:
                continue

            # Extract excerpt from summary or content
            raw_excerpt = ""
            if hasattr(entry, "summary") and entry.summary:
                raw_excerpt = entry.summary
            elif hasattr(entry, "content") and entry.content:
                raw_excerpt = entry.content[0].get("value", "")

            excerpt = _strip_html(raw_excerpt)[:500] if raw_excerpt else ""

            articles.append(
                {
                    "id": f"{source['name']}::{url}",
                    "title": title,
                    "url": url,
                    "excerpt": excerpt,
                    "source": source["name"],
                    "language": source["language"],
                    "published_iso": published.isoformat() if published else None,
                    "published_dt": published,
                    "authority": source["authority"],
                    "is_popular_feed": source.get("is_popular_feed", False),
                    "full_text": None,
                }
            )

        log.info(f"  [{source['name']}] {len(articles)} articles in window")

    except Exception as exc:
        log.warning(f"  [{source['name']}] fetch failed: {exc}")

    return articles


def fetch_full_text(url: str) -> Optional[str]:
    """Extract clean article body text from a URL."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, verify=certifi.where())
        resp.raise_for_status()

        # Prefer trafilatura — best-in-class article extractor
        text = trafilatura.extract(
            resp.text,
            include_comments=False,
            include_tables=False,
            no_fallback=False,
            favor_precision=True,
        )
        if text and len(text) > 200:
            return text[:FULL_TEXT_MAX_CHARS]

        # Fallback: BeautifulSoup body extraction
        soup = BeautifulSoup(resp.text, "lxml")
        for tag in soup(["nav", "footer", "aside", "script", "style", "header"]):
            tag.decompose()
        main = (
            soup.find("article")
            or soup.find("main")
            or soup.find(class_=re.compile(r"content|article|post", re.I))
            or soup.find("body")
        )
        if main:
            raw = re.sub(r"\s+", " ", main.get_text(separator=" ", strip=True))
            if len(raw) > 200:
                return raw[:FULL_TEXT_MAX_CHARS]

    except Exception as exc:
        log.debug(f"  full text fetch failed for {url}: {exc}")

    return None


def fetch_all_articles(lookback_hours: int = 36) -> list[dict]:
    """Fetch articles from all configured sources, deduplicated by URL."""
    from config import SOURCES

    all_articles: list[dict] = []

    for source in SOURCES:
        articles = fetch_rss(source, lookback_hours)
        all_articles.extend(articles)
        time.sleep(0.4)  # polite inter-request delay

    # Deduplicate by URL
    seen: set[str] = set()
    unique: list[dict] = []
    for a in all_articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)

    log.info(f"Total: {len(unique)} unique articles from {len(SOURCES)} sources")

    from config import DEBUG_MAX_ARTICLES
    if DEBUG_MAX_ARTICLES is not None:
        unique = unique[:DEBUG_MAX_ARTICLES]
        log.info(f"DEBUG_MAX_ARTICLES={DEBUG_MAX_ARTICLES}: trimmed to {len(unique)} articles")

    return unique
