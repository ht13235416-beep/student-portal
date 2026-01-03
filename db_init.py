import os
import psycopg2
from werkzeug.security import generate_password_hash

def ensure_db_ready():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("⚠️ DATABASE_URL not set, skipping DB init")
        return

    conn = psycopg2.connect(database_url)
    cur = conn.cursor()

    # ---------- TABLES ----------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY REFERENCES users(id),
        full_name TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY REFERENCES users(id),
        full_name TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id SERIAL PRIMARY KEY,
        course_code TEXT UNIQUE NOT NULL,
        course_name TEXT NOT NULL,
        credit_hours INTEGER NOT NULL,
        teacher_id INTEGER REFERENCES teachers(id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS enrollments (
        id SERIAL PRIMARY KEY,
        student_id INTEGER REFERENCES students(id),
        course_id INTEGER REFERENCES courses(id),
        UNIQUE(student_id, course_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS grades (
        id SERIAL PRIMARY KEY,
        enrollment_id INTEGER REFERENCES enrollments(id),
        letter_grade TEXT,
        status TEXT DEFAULT 'draft',
        entered_by INTEGER,
        approved_by INTEGER,
        approved_at TIMESTAMP
    );
    """)

    # ---------- SEED USERS (SAFE) ----------
    users = [
        ("registrar", generate_password_hash("admin123"), "registrar"),
        ("teacher1", generate_password_hash("teach123"), "teacher"),
        ("student1", generate_password_hash("stud123"), "student"),
        ("student2", generate_password_hash("stud123"), "student"),
    ]

    for u in users:
        cur.execute("""
        INSERT INTO users (username, password_hash, role)
        VALUES (%s, %s, %s)
        ON CONFLICT (username) DO NOTHING
        """, u)

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Database ready")

