import sqlite3

def init_db():
    conn = sqlite3.connect('entertainment_ai.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_title TEXT,
            user_feedback TEXT,
            rating TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_feedback(movie_title, user_feedback, rating):
    conn = sqlite3.connect('entertainment_ai.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO feedbacks (movie_title, user_feedback, rating) 
        VALUES (?, ?, ?)
    ''', (movie_title, user_feedback, rating))
    conn.commit()
    conn.close()