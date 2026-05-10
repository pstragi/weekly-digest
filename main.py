#!/usr/bin/env python3
"""
News Digest Agent
-----------------
Bi-weekly: Monday (covers Thu–Sun, 96 h) and Thursday (covers Mon–Wed, 72 h).

Usage:
  python main.py                 # run once, send email
  python main.py --dry-run       # run once, save HTML preview instead of emailing
  python main.py --schedule      # start bi-weekly schedule (Mon & Thu at 07:00 CET)
"""
import argparse
import logging
import sys
from datetime import datetime, timedelta

import pytz

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("digest.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# Monday digest covers Thu–Sun (4 days); Thursday digest covers Mon–Wed (3 days).
_LOOKBACK_BY_WEEKDAY = {0: 96, 3: 72}  # 0=Monday, 3=Thursday


def _lookback_hours_for_today() -> int:
    """Return the right lookback window for today's weekday (defaults to config value)."""
    from config import LOOKBACK_HOURS
    return _LOOKBACK_BY_WEEKDAY.get(datetime.now().weekday(), LOOKBACK_HOURS)


def run(dry_run: bool = False, lookback_hours: int | None = None) -> None:
    from scraper import fetch_all_articles
    from scorer import score_and_select_articles
    from emailer import send_digest
    from config import LOOKBACK_HOURS

    hours = lookback_hours if lookback_hours is not None else LOOKBACK_HOURS

    log.info("=" * 55)
    log.info(f"News Digest — starting run (lookback={hours}h)")
    log.info("=" * 55)

    log.info("Step 1/3 — Fetching articles from all sources…")
    articles = fetch_all_articles(lookback_hours=hours)
    log.info(f"  → {len(articles)} unique articles retrieved")

    if not articles:
        log.warning("No articles found — aborting.")
        return

    log.info("Step 2/3 — Scoring and selecting articles…")
    selected = score_and_select_articles(articles)
    total = sum(len(v) for v in selected.values())
    log.info(f"  → {total} articles selected across {len(selected)} categories")

    if not selected:
        log.warning("No articles passed scoring — aborting.")
        return

    log.info("Step 3/3 — Generating summaries and sending digest…")
    send_digest(selected, dry_run=dry_run)

    log.info("✓ Done.")


def run_scheduled() -> None:
    from apscheduler.schedulers.blocking import BlockingScheduler

    CET = pytz.timezone("Europe/Warsaw")
    scheduler = BlockingScheduler(timezone=CET)

    # Monday 07:00 — covers Thu–Sun (96 h)
    scheduler.add_job(
        lambda: run(lookback_hours=96),
        trigger="cron",
        day_of_week="mon",
        hour=7,
        minute=0,
        timezone=CET,
        id="monday_digest",
    )
    # Thursday 07:00 — covers Mon–Wed (72 h)
    scheduler.add_job(
        lambda: run(lookback_hours=72),
        trigger="cron",
        day_of_week="thu",
        hour=7,
        minute=0,
        timezone=CET,
        id="thursday_digest",
    )

    now = datetime.now(CET)
    # Find next Monday or Thursday at 07:00
    candidates = []
    for days_ahead in range(1, 8):
        candidate = (now + timedelta(days=days_ahead)).replace(
            hour=7, minute=0, second=0, microsecond=0
        )
        if candidate.weekday() in (0, 3):
            candidates.append(candidate)
            break

    next_label = candidates[0].strftime("%A %Y-%m-%d 07:00 CET") if candidates else "next Mon/Thu"
    log.info(f"Scheduler started — next digest at {next_label}")
    log.info("Press Ctrl+C to stop.")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        log.info("Scheduler stopped.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bi-weekly News Digest Agent powered by Claude"
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Start bi-weekly schedule (Monday & Thursday at 07:00 CET)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run once but save HTML to digest_preview.html instead of sending email",
    )
    parser.add_argument(
        "--lookback",
        type=int,
        default=None,
        metavar="HOURS",
        help="Override lookback window (default: auto from weekday, or config LOOKBACK_HOURS)",
    )
    args = parser.parse_args()

    if args.schedule:
        run_scheduled()
    else:
        hours = args.lookback if args.lookback is not None else _lookback_hours_for_today()
        run(dry_run=args.dry_run, lookback_hours=hours)


if __name__ == "__main__":
    main()
