import psycopg2
import os
from seed_data import seed_data

def ensure_db_ready():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()

    # USERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT CHECK (role IN ('student','teacher','registrar')) NOT NULL
    );
    """)

    # STUDENTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
        full_name TEXT NOT NULL
    );
    """)

    # TEACHERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
        full_name TEXT NOT NULL,
        department TEXT
    );
    """)

    # COURSES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id SERIAL PRIMARY KEY,
        course_code TEXT UNIQUE NOT NULL,
        course_name TEXT NOT NULL,
        credit_hours INTEGER NOT NULL,
        teacher_id INTEGER REFERENCES teachers(id)
    );
    """)

    # ENROLLMENTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS enrollments (
        id SERIAL PRIMARY KEY,
        student_id INTEGER REFERENCES students(id),
        course_id INTEGER REFERENCES courses(id),
        UNIQUE(student_id, course_id)
    );
    """)

    # GRADES
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

    # ✅ SEED USING SAME CURSOR
    seed_data(cur)

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Database schema + seed completed")
