import os
import psycopg2
from seed_data import seed_data


def ensure_db_ready():
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # ---------- USERS ----------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT CHECK (role IN ('student', 'teacher', 'registrar')) NOT NULL
    );
    """)

    # ---------- STUDENTS ----------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
        full_name TEXT NOT NULL
    );
    """)

    # ---------- TEACHERS ----------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
        full_name TEXT NOT NULL,
        department TEXT NOT NULL
    );
    """)

    # ---------- COURSES ----------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id SERIAL PRIMARY KEY,
        course_code TEXT UNIQUE NOT NULL,
        course_name TEXT NOT NULL,
        credit_hours INTEGER NOT NULL,
        teacher_id INTEGER NOT NULL REFERENCES teachers(id)
    );
    """)

    # ---------- ENROLLMENTS ----------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS enrollments (
        id SERIAL PRIMARY KEY,
        student_id INTEGER NOT NULL REFERENCES students(id),
        course_id INTEGER NOT NULL REFERENCES courses(id),
        UNIQUE (student_id, course_id)
    );
    """)

    # ---------- GRADES ----------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS grades (
        id SERIAL PRIMARY KEY,
        enrollment_id INTEGER NOT NULL REFERENCES enrollments(id),
        letter_grade TEXT,
        status TEXT CHECK (status IN ('draft', 'submitted', 'approved', 'locked'))
            NOT NULL DEFAULT 'draft',
        entered_by INTEGER REFERENCES teachers(id),
        approved_by INTEGER REFERENCES users(id),
        approved_at TIMESTAMP
    );
    """)

    # ---------- SEED DATA (SAME CONNECTION) ----------
    seed_data(cur)

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Database schema + seed completed")
