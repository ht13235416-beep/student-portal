import psycopg2
import os
from werkzeug.security import generate_password_hash

DATABASE_URL = os.environ.get("DATABASE_URL")

def ensure_db_ready():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Create table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL
    );
    """)

    # Seed only if empty
    cur.execute("SELECT COUNT(*) FROM users;")
    count = cur.fetchone()[0]

    if count == 0:
        users = [
            ("registrar", generate_password_hash("admin123"), "registrar"),
            ("teacher", generate_password_hash("teacher123"), "teacher"),
            ("student", generate_password_hash("student123"), "student"),
        ]

        cur.executemany(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
            users
        )

    conn.commit()
    cur.close()
    conn.close()
