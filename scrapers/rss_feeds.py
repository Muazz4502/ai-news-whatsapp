import calendar
import logging
import time
from datetime import datetime, timezone, timedelta

import feedparser

from config import HOURS_LOOKBACK

logger = logging.getLogger(__name__)

# AI_DEDICATED feeds skip keyword filtering; GENERAL feeds require an AI keyword match.
FEEDS = {
    # AI-dedicated (no keyword filtering needed)
    "TechCrunch AI":          ("https://techcrunch.com/category/artificial-intelligence/feed/", True),
    "VentureBeat AI":         ("https://venturebeat.com/feed/", False),
    "Reddit MachineLearning": ("https://www.reddit.com/r/MachineLearning/.rss", True),
    "Reddit Artificial":      ("https://www.reddit.com/r/artificial/.rss", True),
    "Reddit LocalLLaMA":      ("https://www.reddit.com/r/LocalLLaMA/.rss", True),
    "Google DeepMind Blog":   ("https://deepmind.google/blog/rss.xml", True),
    "OpenAI Blog":            ("https://openai.com/blog/rss.xml", True),
    # General tech (require AI keyword in title/summary)
    "MIT Tech Review":        ("https://www.technologyreview.com/feed/", False),
    "The Verge":              ("https://www.theverge.com/rss/index.xml", False),
    "Wired":                  ("https://www.wired.com/feed/rss", False),
    "Ars Technica":           ("https://feeds.arstechnica.com/arstechnica/technology-lab", False),
    "Hacker News":            ("https://news.ycombinator.com/rss", False),
}

AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "llm", "gpt",
    "neural", "openai", "anthropic", "gemini", "deep learning",
    "chatbot", "transformer", "language model", "diffusion model",
]


def _parse_date(entry) -> datetime | None:
    for field in ("published_parsed", "updated_parsed"):
        t = getattr(entry, field, None)
        if t:
            return datetime.fromtimestamp(calendar.timegm(t), tz=timezone.utc)
    return None


def _is_ai_related(entry) -> bool:
    text = (
        getattr(entry, "title", "") + " " + getattr(entry, "summary", "")
    ).lower()
    return any(kw in text for kw in AI_KEYWORDS)


def fetch_rss_items() -> list[dict]:
    """
    Parse all RSS/Atom feeds and return AI-related articles from the last 24h.
    Returns list of dicts: {title, url, source, score, published_at}
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_LOOKBACK)
    results = []

    for source_name, (url, ai_dedicated) in FEEDS.items():
        try:
            feed = feedparser.parse(url)
            if feed.bozo:
                logger.warning(f"RSS parse warning for {source_name}: {feed.bozo_exception}")

            count = 0
            for entry in feed.entries:
                published = _parse_date(entry)
                # Skip entries older than the lookback window
                if published and published < cutoff:
                    continue

                link = getattr(entry, "link", None)
                title = getattr(entry, "title", "No title").strip()
                if not link:
                    continue

                # Apply keyword filter only for non-AI-dedicated feeds
                if not ai_dedicated and not _is_ai_related(entry):
                    continue

                results.append({
                    "title": title,
                    "url": link,
                    "source": source_name,
                    "score": 0,
                    "published_at": published,
                })
                count += 1

            logger.info(f"RSS {source_name}: fetched {count} items.")

        except Exception as e:
            logger.error(f"RSS error for {source_name}: {e}")
            time.sleep(1)

    return results
