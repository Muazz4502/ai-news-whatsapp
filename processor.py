import logging
from datetime import datetime, timezone

import openai

from config import OPENAI_API_KEY
from database import is_seen

logger = logging.getLogger(__name__)


def deduplicate(items: list[dict]) -> list[dict]:
    """Remove items already seen in SQLite and duplicates within this batch."""
    seen_this_run: set[str] = set()
    unique = []
    for item in items:
        url = item.get("url", "").strip()
        if not url:
            continue
        if url in seen_this_run:
            continue
        if is_seen(url):
            logger.debug(f"Skipping already-seen URL: {url}")
            continue
        seen_this_run.add(url)
        unique.append(item)
    return unique


def _rank_score(item: dict) -> float:
    """
    Normalized ranking across all source types.
    - Tracked creators (YouTube/Instagram) get a high base score so they
      always compete with news articles.
    - RSS items (score=0) get a baseline so they aren't invisible.
    - Recency boosts fresher content.
    """
    source = item.get("source", "")
    base = float(item.get("score", 0))

    # Give tracked creator content a strong baseline
    if source.startswith("YouTube /") or source.startswith("Instagram /"):
        base += 50
    elif source.startswith("Twitter"):
        base += 10  # Tweets already have engagement scores
    else:
        # RSS/news articles: give a baseline so they compete
        base += 20

    # Recency boost
    published = item.get("published_at")
    if published:
        now = datetime.now(timezone.utc)
        age_hours = (now - published).total_seconds() / 3600
        if age_hours <= 6:
            base *= 1.3
        elif age_hours <= 12:
            base *= 1.15

    return base


def rank_and_select(items: list[dict], top_n: int = 10) -> list[dict]:
    """Pick top N ensuring a mix of sources (creators + news)."""
    ranked = sorted(items, key=_rank_score, reverse=True)
    return ranked[:top_n]


def generate_summary(items: list[dict]) -> str:
    """Use Claude to generate a 50-70 word summary of the top news items."""
    titles = [item.get("title", "No title").strip() for item in items]
    titles_text = "\n".join(f"- {t}" for t in titles)

    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=150,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Here are today's top AI news headlines:\n{titles_text}\n\n"
                        "Write a 50-70 word summary paragraph covering the key themes "
                        "and highlights from these headlines. Be concise and informative. "
                        "Do not use bullet points or lists. Just a single paragraph."
                    ),
                }
            ],
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        return ""


def format_whatsapp_message(items: list[dict], max_chars: int = 1500) -> str:
    """Format selected items into a WhatsApp-friendly message.
    Twilio sandbox has a 1600 char limit; we cap at 1500 for safety.
    """
    today = datetime.now().strftime("%b %d, %Y")
    header = f"*AI News — {today}*\n\n"
    footer = "\n\n_AI News Bot_"

    summary = generate_summary(items)
    summary_block = f"{summary}\n\n" if summary else ""

    budget = max_chars - len(header) - len(footer) - len(summary_block)
    links_header = "*Links:*\n"
    budget -= len(links_header)
    body_lines = []

    for i, item in enumerate(items, 1):
        title = item.get("title", "No title").strip()
        if len(title) > 80:
            title = title[:77] + "..."
        url = item.get("url", "").strip()
        entry = f"{i}. {title}\n{url}"

        if len("\n\n".join(body_lines + [entry])) > budget:
            break
        body_lines.append(entry)

    return header + summary_block + links_header + "\n\n".join(body_lines) + footer


def process_all(all_items: list[dict], top_n: int = 10) -> tuple[str, list[dict]]:
    """
    Full pipeline: deduplicate -> rank -> select -> format.
    Returns (formatted_message, selected_items).
    Caller should mark selected_items as seen after successful delivery.
    """
    unique = deduplicate(all_items)
    logger.info(f"Deduplication: {len(unique)} unique items from {len(all_items)} total.")

    if not unique:
        return (
            "*AI News Digest*\n\nNo new AI stories found in the last 24 hours.",
            [],
        )

    selected = rank_and_select(unique, top_n=top_n)
    message = format_whatsapp_message(selected)
    return message, selected
