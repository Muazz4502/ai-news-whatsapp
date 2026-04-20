import sqlite3
import hashlib
from urllib.parse import urlparse, urlunparse
from config import DB_PATH


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def initialize():
    """Create tables if they don't exist. Called once at startup."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seen_articles (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                url_hash TEXT UNIQUE NOT NULL,
                url      TEXT NOT NULL,
                title    TEXT,
                source   TEXT,
                seen_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def make_hash(url: str) -> str:
    """Normalize URL (strip query/fragment, lowercase) then SHA-256."""
    parsed = urlparse(url.lower().strip())
    normalized = urlunparse(parsed._replace(query="", fragment=""))
    return hashlib.sha256(normalized.encode()).hexdigest()


def is_seen(url: str) -> bool:
    h = make_hash(url)
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM seen_articles WHERE url_hash = ?", (h,)
        ).fetchone()
    return row is not None


def mark_seen(url: str, title: str, source: str):
    h = make_hash(url)
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO seen_articles (url_hash, url, title, source) VALUES (?,?,?,?)",
            (h, url, title, source),
        )
        conn.commit()


def purge_old_entries(days: int = 30):
    """Remove entries older than N days to keep the database small."""
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM seen_articles WHERE seen_at < datetime('now', ?)",
            (f"-{days} days",),
        )
        conn.commit()
