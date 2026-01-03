import psycopg2
import os

def ensure_db_ready():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()

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
        course_code TEXT NOT NULL,
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

    conn.commit()
    cur.close()
    conn.close()
