import time
import logging
from datetime import datetime, timezone, timedelta

import tweepy

from config import TWITTER_BEARER_TOKEN, HOURS_LOOKBACK, MAX_TWEET_RESULTS

logger = logging.getLogger(__name__)

AI_QUERY = (
    "(artificial intelligence OR machine learning OR LLM OR GPT OR "
    "Claude OR Gemini OR OpenAI OR Anthropic OR deep learning OR "
    "neural network OR transformer model) lang:en -is:retweet"
)


def fetch_tweets() -> list[dict]:
    """
    Search recent tweets about AI from the last 24h.
    Returns list of dicts: {title, url, source, score, published_at}
    """
    client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN, wait_on_rate_limit=True)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=HOURS_LOOKBACK)

    backoff = 1
    for attempt in range(5):
        try:
            response = client.search_recent_tweets(
                query=AI_QUERY,
                max_results=min(MAX_TWEET_RESULTS, 100),
                start_time=cutoff,
                tweet_fields=["public_metrics", "created_at", "entities"],
            )
            if not response.data:
                logger.info("Twitter: no results returned.")
                return []

            results = []
            for tweet in response.data:
                m = tweet.public_metrics or {}
                engagement = (
                    m.get("like_count", 0)
                    + m.get("retweet_count", 0) * 3
                    + m.get("reply_count", 0)
                )

                # Prefer article URL from entities over tweet permalink
                url = f"https://twitter.com/i/web/status/{tweet.id}"
                entities = tweet.entities or {}
                for u in entities.get("urls", []):
                    expanded = u.get("expanded_url", "")
                    if expanded and "twitter.com" not in expanded and "t.co" not in expanded:
                        url = expanded
                        break

                results.append({
                    "title": tweet.text[:280].strip(),
                    "url": url,
                    "source": "Twitter/X",
                    "score": engagement,
                    "published_at": tweet.created_at,
                })
            logger.info(f"Twitter: fetched {len(results)} tweets.")
            return results

        except tweepy.TooManyRequests:
            logger.warning(f"Twitter rate limit hit. Backing off {backoff}s.")
            time.sleep(backoff)
            backoff = min(backoff * 2, 64)
        except tweepy.TweepyException as e:
            logger.error(f"Twitter API error: {e}")
            return []

    logger.error("Twitter: exhausted retries.")
    return []
