# ai-news-whatsapp

Wakes up every morning, reads the AI internet so you don't have to,
picks the bits worth your attention, and pushes them to your WhatsApp.

It's a bot that hates noise.

## What it does

1. **Scrapes** five places where AI news lives — Twitter/X, RSS feeds,
   Hacker News, YouTube, Instagram.
2. **Dedupes + ranks** the firehose into the top items worth reading.
3. **Sends** the digest to your WhatsApp via Twilio.
4. **Remembers** what it sent so it never spams you the same story twice.

## Why

The "AI thing of the day" Slack channel was at 200 unread.
Manually checking five feeds is a part-time job.
A daily 10-bullet WhatsApp summary is enough.

## Stack

Python · `tweepy`, `feedparser`, `requests`, `openai`, `twilio`, `schedule` ·
SQLite for memory.

## Setup

```bash
cp .env.example .env
# Fill in: TWITTER_BEARER_TOKEN, TWILIO_*, OPENAI_API_KEY, ...
pip install -r requirements.txt
python main.py
```

The script schedules itself for `DAILY_SEND_TIME` (configure in `.env`)
and keeps running. Run it on a tiny VPS, a Raspberry Pi, or just leave
your laptop on.

## How it's wired

```
scrapers/      → pull raw items from each source
processor.py   → dedupe + rank (LLM-assisted)
database.py    → SQLite, "have I sent this already?"
notifier.py    → format + send WhatsApp via Twilio
main.py        → schedule + orchestrate
```

## Tuning

- Top N per day: `TOP_ITEMS_COUNT` in `.env`
- Send time (24h): `DAILY_SEND_TIME` in `.env`
- Source mix: comment out scrapers in `main.run_daily_job()`

## Heads-up

- Twitter/X v2 free tier rate-limits hard. Expect dropped fetches.
- Instagram scraping is fragile; expect to fix the parser quarterly.
- Twilio WhatsApp sandbox needs you to text a join code first.
