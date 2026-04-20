import logging
import time
from datetime import datetime, timezone, timedelta

import requests

from config import HOURS_LOOKBACK

logger = logging.getLogger(__name__)

HN_ALGOLIA_URL = "https://hn.algolia.com/api/v1/search"


def fetch_hn_stories() -> list[dict]:
    """
    Query the Hacker News Algolia API for recent AI stories.
    Returns list of dicts: {title, url, source, score, published_at}
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_LOOKBACK)
    cutoff_ts = int(cutoff.timestamp())

    params = {
        "query": "artificial intelligence machine learning LLM OpenAI Anthropic",
        "tags": "story",
        "numericFilters": f"created_at_i>{cutoff_ts},points>1",
        "hitsPerPage": 30,
    }

    backoff = 1
    for attempt in range(4):
        try:
            resp = requests.get(HN_ALGOLIA_URL, params=params, timeout=10)
            if resp.status_code == 429:
                logger.warning(f"HackerNews rate limit. Backing off {backoff}s.")
                time.sleep(backoff)
                backoff = min(backoff * 2, 32)
                continue
            resp.raise_for_status()
            data = resp.json()

            results = []
            for hit in data.get("hits", []):
                url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit['objectID']}"
                results.append({
                    "title": hit.get("title", "").strip(),
                    "url": url,
                    "source": "Hacker News",
                    "score": hit.get("points", 0) + hit.get("num_comments", 0),
                    "published_at": datetime.fromtimestamp(
                        hit["created_at_i"], tz=timezone.utc
                    ),
                })

            logger.info(f"HackerNews: fetched {len(results)} stories.")
            return results

        except requests.RequestException as e:
            logger.error(f"HackerNews API error: {e}")
            time.sleep(backoff)
            backoff = min(backoff * 2, 32)

    logger.error("HackerNews: exhausted retries.")
    return []
