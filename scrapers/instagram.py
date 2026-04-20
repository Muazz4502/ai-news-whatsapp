import logging
import time
from datetime import datetime, timezone, timedelta

import requests

from config import HOURS_LOOKBACK

logger = logging.getLogger(__name__)

# Instagram creators to track: {display_name: username}
INSTAGRAM_CREATORS = {
    # Indian Creators
    "Vaibhav Sisinty":  "vaibhavsisinty",
    "Varun Mayya":      "thevarunmayya",
    "Tiff In Tech":     "tiffintech",
    "Sundas Khalid":    "sundaskhalidd",
    # International Creators
    "Allie K Miller":   "alliekmiller",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "X-IG-App-ID": "936619743392459",
}


def _fetch_profile_posts(username: str) -> list[dict]:
    """Fetch recent posts from an Instagram public profile."""
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()

    data = resp.json()
    user = data.get("data", {}).get("user", {})
    media = user.get("edge_owner_to_timeline_media", {})
    return media.get("edges", [])


def fetch_instagram_posts() -> list[dict]:
    """
    Fetch recent posts from tracked Instagram creators.
    Returns list of dicts: {title, url, source, score, published_at}
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_LOOKBACK)
    results = []

    for creator_name, username in INSTAGRAM_CREATORS.items():
        try:
            edges = _fetch_profile_posts(username)
            count = 0

            for edge in edges:
                node = edge.get("node", {})
                timestamp = node.get("taken_at_timestamp", 0)
                published = datetime.fromtimestamp(timestamp, tz=timezone.utc)

                if published < cutoff:
                    continue

                # Extract caption text
                caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
                caption = ""
                if caption_edges:
                    caption = caption_edges[0].get("node", {}).get("text", "")
                # Use first line of caption as title
                title = caption.split("\n")[0].strip() if caption else "New post"
                shortcode = node.get("shortcode", "")
                url = f"https://www.instagram.com/p/{shortcode}/" if shortcode else f"https://www.instagram.com/{username}/"

                results.append({
                    "title": title,
                    "url": url,
                    "source": f"Instagram / {creator_name}",
                    "score": 5,  # Base score for tracked creators
                    "published_at": published,
                })
                count += 1

            if count:
                logger.info(f"Instagram {creator_name}: fetched {count} new posts.")

            # Brief pause between profiles to avoid rate limiting
            time.sleep(1)

        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 429:
                logger.warning(f"Instagram rate limit for {creator_name}. Skipping remaining.")
                break
            logger.error(f"Instagram HTTP error for {creator_name}: {e}")
        except Exception as e:
            logger.error(f"Instagram error for {creator_name}: {e}")
            time.sleep(1)

    logger.info(f"Instagram total: {len(results)} posts from creators.")
    return results
