#!/usr/bin/env python3
"""News Aggregator for Mission Control - RSS/API fetcher and API server"""
from flask import Flask, jsonify
from pathlib import Path
import json
import feedparser
import sqlite3
from datetime import datetime, timedelta
import requests
import os

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data' / 'news.db'

RSS_FEEDS = {
    'civic_tech': [
        'https://www.govtech.com/rss',
        'https://www.codeforamerica.org/feed',
    ],
    'nonprofit': [
        'https://www.nonprofitquarterly.org/feed/',
        'https://www.philanthropy.com/rss',
    ],
    'education': [
        'https://www.educationdive.com/feeds/news/',
        'https://www.chronicle.com/section/News/feed/',
    ],
    'policy': [
        'https://www.brookings.edu/feed/',
        'https://www.csis.org/rss',
    ],
    'technology': [
        'https://techcrunch.com/feed/',
        'https://www.theverge.com/rss/index.xml',
    ]
}

app = Flask(__name__)

def load_gnews_key():
    # Priority: env var -> local .env
    key = os.getenv('GNEWS_API_KEY', '').strip()
    if key:
        return key
    envp = ROOT / '.env'
    if envp.exists():
        for line in envp.read_text(errors='ignore').splitlines():
            if line.startswith('GNEWS_API_KEY='):
                return line.split('=',1)[1].strip().strip('"').strip("'")
    return ''

def init_db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            source TEXT,
            summary TEXT,
            category TEXT,
            published_at TEXT,
            fetched_at TEXT DEFAULT CURRENT_TIMESTAMP,
            read BOOLEAN DEFAULT 0,
            bookmarked BOOLEAN DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def _insert_story(conn, title, url, source, summary, category, published):
    try:
        conn.execute('''
            INSERT INTO stories (title, url, source, summary, category, published_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, url, source, summary, category, published))
        conn.commit()
        return 1
    except sqlite3.IntegrityError:
        return 0


def fetch_rss():
    """Fetch all RSS feeds and store new stories."""
    conn = sqlite3.connect(DB)
    new_count = 0

    for category, feeds in RSS_FEEDS.items():
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:10]:  # top 10 per feed
                    title = entry.get('title', '')
                    url = entry.get('link', '')
                    summary = entry.get('summary', '')[:500]
                    source = feed.feed.get('title', 'Unknown')
                    published = entry.get('published', '')
                    new_count += _insert_story(conn, title, url, source, summary, category, published)
            except Exception as e:
                print(f"Error fetching {feed_url}: {e}")

    conn.close()
    return new_count


def fetch_gnews():
    """Fetch GNews API stories when key is configured."""
    key = load_gnews_key()
    if not key:
        return 0

    queries = {
        'civic_tech': 'civic technology OR digital government',
        'nonprofit': 'nonprofit OR philanthropy',
        'education': 'education technology OR learning',
        'policy': 'public policy OR governance',
        'technology': 'artificial intelligence OR open source'
    }

    conn = sqlite3.connect(DB)
    added = 0
    for category, q in queries.items():
        try:
            url = 'https://gnews.io/api/v4/search'
            params = {
                'q': q,
                'lang': 'en',
                'max': 10,
                'apikey': key
            }
            r = requests.get(url, params=params, timeout=20)
            if r.status_code != 200:
                continue
            data = r.json()
            for a in data.get('articles', []):
                title = a.get('title', '')
                link = a.get('url', '')
                source = (a.get('source') or {}).get('name', 'GNews')
                summary = (a.get('description') or '')[:500]
                published = a.get('publishedAt', '')
                added += _insert_story(conn, title, link, source, summary, category, published)
        except Exception as e:
            print(f"GNews fetch error ({category}): {e}")

    conn.close()
    return added

@app.get('/api/news/stories')
def list_stories():
    from flask import request
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    
    query = "SELECT * FROM stories WHERE 1=1"
    params = []
    
    if category:
        query += " AND category = ?"
        params.append(category)
    
    if search:
        query += " AND (title LIKE ? OR summary LIKE ?)"
        params.append(f"%{search}%")
        params.append(f"%{search}%")
    
    query += " ORDER BY published_at DESC LIMIT 100"
    
    rows = conn.execute(query, params).fetchall()
    conn.close()
    
    return jsonify({'items': [dict(r) for r in rows]})

@app.post('/api/news/stories/<int:story_id>/read')
def mark_read(story_id):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE stories SET read = 1 WHERE id = ?", (story_id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.post('/api/news/stories/<int:story_id>/bookmark')
def toggle_bookmark(story_id):
    conn = sqlite3.connect(DB)
    row = conn.execute("SELECT bookmarked FROM stories WHERE id = ?", (story_id,)).fetchone()
    new_val = 0 if (row and row[0]) else 1
    conn.execute("UPDATE stories SET bookmarked = ? WHERE id = ?", (new_val, story_id))
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'bookmarked': new_val})

@app.get('/api/news/categories')
def list_categories():
    return jsonify({'categories': list(RSS_FEEDS.keys())})

@app.post('/api/news/refresh')
def refresh_news():
    rss_count = fetch_rss()
    gnews_count = fetch_gnews()
    return jsonify({'ok': True, 'new_stories': rss_count + gnews_count, 'rss_new': rss_count, 'gnews_new': gnews_count})

if __name__ == '__main__':
    init_db()
    # Initial fetch
    fetch_rss()
    fetch_gnews()
    app.run(host='127.0.0.1', port=8877, debug=False)
