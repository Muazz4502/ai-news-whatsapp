import calendar
import logging
import time
from datetime import datetime, timezone, timedelta

import feedparser

from config import HOURS_LOOKBACK

logger = logging.getLogger(__name__)

# YouTube channels: (display_name, channel_id)
# RSS feed URL: https://www.youtube.com/feeds/videos.xml?channel_id=<ID>
YOUTUBE_CREATORS = {
    # Indian Creators
    "Vaibhav Sisinty":  "UClXAalunTPaX1YV185DWUeg",
    "Varun Mayya":      "UCsQoiOrh7jzKmE8NBofhTnQ",
    "Krish Naik":       "UCjWY5hREA6FFYrthD0rZNIw",
    "Tiff In Tech":     "UCSILOZMPDRzMbKf_hQ7uGMg",
    "Sundas Khalid":    "UCteRPiisgIoHtMgqHegpWAQ",
    # International Creators
    "Andrej Karpathy":  "UCXUPKJO5MZQN11PqgIvyuvQ",
    "Two Minute Papers": "UCbfYPyITQ-7l4upoX8nvctg",
    "Matt Wolfe":       "UChpleBmo18P08aKCIgti38g",
    "AI Explained":     "UCNJ1Ymd5yFuUPtn21xtRbbw",
    "Allie K Miller":   "UCTVXt1spq1Vm4K-SyhS5KAQ",
    "3Blue1Brown":      "UCYO_jab_esuFRV4b17AJtAw",
}


def _parse_date(entry) -> datetime | None:
    for field in ("published_parsed", "updated_parsed"):
        t = getattr(entry, field, None)
        if t:
            return datetime.fromtimestamp(calendar.timegm(t), tz=timezone.utc)
    return None


def fetch_youtube_videos() -> list[dict]:
    """
    Fetch recent videos from tracked YouTube creators via RSS.
    Returns list of dicts: {title, url, source, score, published_at}
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_LOOKBACK)
    results = []

    for creator_name, channel_id in YOUTUBE_CREATORS.items():
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        try:
            feed = feedparser.parse(feed_url)
            if feed.bozo:
                logger.warning(f"YouTube RSS warning for {creator_name}: {feed.bozo_exception}")

            count = 0
            for entry in feed.entries:
                published = _parse_date(entry)
                if published and published < cutoff:
                    continue

                link = getattr(entry, "link", None)
                title = getattr(entry, "title", "No title").strip()
                if not link:
                    continue

                results.append({
                    "title": title,
                    "url": link,
                    "source": f"YouTube / {creator_name}",
                    "score": 5,  # Base score for tracked creators
                    "published_at": published,
                })
                count += 1

            if count:
                logger.info(f"YouTube {creator_name}: fetched {count} new videos.")

        except Exception as e:
            logger.error(f"YouTube error for {creator_name}: {e}")
            time.sleep(0.5)

    logger.info(f"YouTube total: {len(results)} videos from creators.")
    return results
