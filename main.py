import logging
import threading
import time

import schedule

from config import DAILY_SEND_TIME, TOP_ITEMS_COUNT
from database import initialize as db_init, mark_seen, purge_old_entries
from scrapers.twitter import fetch_tweets
from scrapers.rss_feeds import fetch_rss_items
from scrapers.hackernews import fetch_hn_stories
from scrapers.youtube import fetch_youtube_videos
from scrapers.instagram import fetch_instagram_posts
from processor import process_all
from notifier import send_whatsapp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("ai_news_bot.log"),
    ],
)
logger = logging.getLogger(__name__)


def run_daily_job():
    """Full pipeline: scrape all sources -> process -> deliver -> mark seen."""
    logger.info("=== Starting daily AI news job ===")

    all_items: list[dict] = []
    scrapers = [
        ("Twitter/X",    fetch_tweets),
        ("RSS Feeds",    fetch_rss_items),
        ("Hacker News",  fetch_hn_stories),
        ("YouTube",      fetch_youtube_videos),
        ("Instagram",    fetch_instagram_posts),
    ]

    for name, fn in scrapers:
        try:
            items = fn()
            logger.info(f"{name}: {len(items)} items collected.")
            all_items.extend(items)
        except Exception as e:
            logger.error(f"{name} scraper failed: {e}")

    logger.info(f"Total items before processing: {len(all_items)}")

    message, selected = process_all(all_items, top_n=TOP_ITEMS_COUNT)

    success = send_whatsapp(message)

    if success and selected:
        for item in selected:
            mark_seen(item["url"], item["title"], item["source"])
        logger.info(f"Marked {len(selected)} articles as seen.")
    elif not selected:
        logger.info("No new items to deliver.")
    else:
        logger.warning("Delivery failed — articles NOT marked as seen (will retry tomorrow).")

    purge_old_entries(days=30)
    logger.info("=== Daily job complete ===")


def _scheduler_loop():
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    logger.info("AI News WhatsApp Bot starting...")

    db_init()

    schedule.every().day.at(DAILY_SEND_TIME).do(run_daily_job)
    logger.info(f"Scheduled daily digest at {DAILY_SEND_TIME}.")

    # Run immediately on first launch so you get a digest right away.
    # Comment out the line below if you want schedule-only mode.
    run_daily_job()

    scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True)
    scheduler_thread.start()

    logger.info("Bot running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully.")
