# ai-news-whatsapp

> Wakes up at 8 AM, reads the AI internet, picks the 10 things worth
> your morning coffee, pushes them to WhatsApp. Goes back to sleep.

I was drowning. Five tabs of AI news every morning. The "AI thing of
the day" Slack channel had 200 unread. Twitter algorithmic, Hacker
News chaotic, RSS overflowing, YouTube unwatched, Instagram somehow on
the list.

So I built the bot.

```
07:59  scraping twitter…  hackernews…  rss…  youtube…  instagram…
08:00  → ranking 487 candidates
08:00  → top 10 selected
08:00  → WhatsApp delivered ✓
08:00  back to bed
```

## The pipeline

```
scrapers/         pull raw firehose from 5 sources
  twitter.py
  hackernews.py
  rss_feeds.py
  youtube.py
  instagram.py
processor.py      dedupe near-dupes, LLM-rank by signal
database.py       SQLite memory: "have I sent you this already?"
notifier.py       format → Twilio → WhatsApp
main.py           schedule + orchestrate
```

The interesting bit is `processor.py`. The LLM doesn't just summarize —
it judges whether a tweet is news or noise, whether a paper is novel or
a press release in disguise. The bar is "would you screenshot this and
send it to a friend?"

## Stack

Python · `tweepy` · `feedparser` · `openai` · `twilio` · `schedule` ·
SQLite. No framework. One process. Runs anywhere.

## Spinning it up

```bash
cp .env.example .env
# Fill in: TWITTER_BEARER_TOKEN, TWILIO_*, OPENAI_API_KEY, …
pip install -r requirements.txt
python main.py
```

Set `DAILY_SEND_TIME` and `TOP_ITEMS_COUNT` in `.env`. Leave it running
on a $5 VPS, a Pi, your old laptop in a drawer — anywhere with
internet and 50MB of disk.

## What I learned building it

- **Twitter v2 free tier hates you.** 1500 fetches/month. Burned through
  it in a week. RSS does most of the heavy lifting now.
- **Instagram parsing is a war you can't win.** The selectors break
  every six weeks. I treat that scraper as "best effort."
- **LLM ranking >>> rule-based ranking.** Tried keyword scoring, tried
  recency × engagement, tried PageRank-style. None beat "ask GPT to
  pick the 10 a smart person would care about."
- **SQLite is enough.** The memory table is a thousand rows. Postgres
  would be vanity.

## Things it doesn't do (yet)

- Personalization — every user gets the same 10. Should weight by what
  I tap on.
- Threading — long stories arrive as standalone tweets, no follow-up.
- Search — "what did the bot send last Tuesday?" is just scrolling
  WhatsApp.

## Vibe

Small, sharp, single-purpose. The kind of side project you forget you
have until your phone buzzes at 8 AM and you remember: oh right,
I built that.
