import os

import certifi
from dotenv import load_dotenv

# Fix macOS SSL certificate issues globally
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

load_dotenv()


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise ValueError(
            f"Missing required environment variable: {key}\n"
            f"Copy .env.example to .env and fill in your credentials."
        )
    return val


# Twitter/X API v2
TWITTER_BEARER_TOKEN = _require("TWITTER_BEARER_TOKEN")

# Twilio WhatsApp
TWILIO_ACCOUNT_SID = _require("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = _require("TWILIO_AUTH_TOKEN")
TWILIO_FROM = _require("TWILIO_WHATSAPP_FROM")
TWILIO_TO = _require("TWILIO_WHATSAPP_TO")

# OpenAI (summary generation)
OPENAI_API_KEY = _require("OPENAI_API_KEY")

# Scheduling
DAILY_SEND_TIME = os.getenv("DAILY_SEND_TIME", "10:00")

# Storage
DB_PATH = os.getenv("DB_PATH", "ai_news.db")

# Scraper constants
HOURS_LOOKBACK = 24
TOP_ITEMS_COUNT = 5
MAX_TWEET_RESULTS = 50
