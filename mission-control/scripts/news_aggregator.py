#!/usr/bin/env python3
"""News Aggregator for Mission Control - RSS/API fetcher and API server"""
from flask import Flask, jsonify
from pathlib import Path
import json
import feedparser
import sqlite3
from datetime import datetime, timedelta
import requests

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
                    
                    try:
                        conn.execute('''
                            INSERT INTO stories (title, url, source, summary, category, published_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (title, url, source, summary, category, published))
                        conn.commit()
                        new_count += 1
                    except sqlite3.IntegrityError:
                        pass  # already exists
            except Exception as e:
                print(f"Error fetching {feed_url}: {e}")
    
    conn.close()
    return new_count

@app.get('/api/news/stories')
def list_stories():
    category = requests.args.get('category', '')
    search = requests.args.get('search', '')
    
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
    count = fetch_rss()
    return jsonify({'ok': True, 'new_stories': count})

if __name__ == '__main__':
    init_db()
    # Initial fetch
    fetch_rss()
    app.run(host='127.0.0.1', port=8877, debug=False)
