# 🤖 ai-news-whatsapp

> Wakes up at 8 AM. Reads the AI internet so you don't have to. Picks
> the 10 things worth your morning coffee. Pushes them to WhatsApp.
> Goes back to sleep.

```
┌──────────────────────────────────────────────────────────┐
│  07:59:42  scraping  twitter…   [✓]   42 tweets          │
│  07:59:51  scraping  hackernews… [✓]   30 stories         │
│  07:59:58  scraping  rss feeds…  [✓]   147 items          │
│  08:00:05  scraping  youtube…    [✓]   18 videos          │
│  08:00:11  scraping  instagram…  [✓]   12 posts           │
│  08:00:14  → 487 candidates                                │
│  08:00:14  → ranking with Claude…                          │
│  08:00:23  → top 10 selected                               │
│  08:00:24  → WhatsApp delivered ✓                          │
│  08:00:24  back to bed.                                    │
└──────────────────────────────────────────────────────────┘
```

## The before

I was drowning. Five tabs open every morning. The "AI thing of the
day" Slack channel had 200 unread. Twitter is algorithmic chaos,
Hacker News is endless, RSS overflows, YouTube unwatched, Instagram
somehow on the list.

So I built the bot. Now I get one WhatsApp message, ten bullets, ten
links, and a hot take on what's actually new vs what's just loud.

## How it works

```
scrapers/         pull raw firehose from 5 sources
  ├─ twitter.py
  ├─ hackernews.py
  ├─ rss_feeds.py
  ├─ youtube.py
  └─ instagram.py
processor.py      dedupe near-dupes · LLM-rank by signal
database.py       SQLite memory: "did I send this already?"
notifier.py       format → Twilio → WhatsApp
main.py           schedule + orchestrate
```

The interesting bit is `processor.py`. The LLM doesn't just summarize
— it judges whether a tweet is news or noise, whether a paper is novel
or a press release in disguise. The bar I tuned it to:

> *"Would you screenshot this and send it to a friend?"*

Anything that doesn't pass that bar dies in dedupe.

## Stack

`Python` `tweepy` `feedparser` `openai` `twilio` `schedule` `sqlite`

No framework. One process. Runs anywhere with internet and 50 MB of
disk.

## Get it running

```bash
cp .env.example .env       # add: TWITTER_BEARER, TWILIO_*, OPENAI_API_KEY
pip install -r requirements.txt
python main.py
```

Set `DAILY_SEND_TIME=08:00` and `TOP_ITEMS_COUNT=10` in `.env`. Leave
it running on a $5 VPS, a Pi, your old laptop in a drawer.

## What I learned the hard way

**Twitter v2 free tier hates you.** 1,500 fetches/month. Burned through
it in a week. RSS now does most of the heavy lifting.

**Instagram parsing is a war you can't win.** Selectors break every
six weeks. I treat that scraper as best-effort.

**LLM ranking destroys rule-based ranking.** I tried keyword scoring,
recency × engagement, PageRank-style. Nothing beat *"ask Claude to
pick the 10 a smart person would care about."*

**SQLite is enough.** The memory table is 1,000 rows. Postgres would
be vanity.

## Things it doesn't do (yet)

- No personalization — every user gets the same 10. Should learn from
  what I tap on.
- No threading — long stories arrive as standalone tweets, no
  follow-up the next day.
- No search — "what did the bot send last Tuesday?" is just scrolling
  WhatsApp.

## Vibe

Small. Sharp. Single-purpose. The kind of side project you forget
exists until your phone buzzes at 8 AM and you remember:

> *Oh right. I built that.*
