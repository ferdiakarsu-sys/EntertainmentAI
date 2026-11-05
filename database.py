import sqlite3
from datetime import datetime

DB_NAME = "entertainment_ai.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id INTEGER UNIQUE,
            title TEXT,
            status TEXT, -- 'watched', 'liked', 'disliked'
            created_at TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def record_feedback(content_id, title, status):
    """Kullanıcının içerikle olan etkileşimini veritabanına işler veya günceller."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_feedback (content_id, title, status, created_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(content_id) DO UPDATE SET
            status = excluded.status,
            created_at = excluded.created_at
    """, (content_id, title, status, datetime.now()))
    conn.commit()
    conn.close()

def get_user_memory():
    """Yapay zekaya aktarılacak geçmiş izleme ve beğeni listesini döner."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT content_id, title, status FROM user_feedback")
    rows = cursor.fetchall()
    conn.close()

    watched_ids = set()
    watched_titles = []
    liked_titles = []
    disliked_titles = []

    for cid, title, status in rows:
        watched_ids.add(cid)
        watched_titles.append(title)
        if status == "liked":
            liked_titles.append(title)
        elif status == "disliked":
            disliked_titles.append(title)

    return {
        "watched_ids": watched_ids,
        "watched_titles": watched_titles,
        "liked_titles": liked_titles,
        "disliked_titles": disliked_titles
    }

init_db()