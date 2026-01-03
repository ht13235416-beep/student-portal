import os
import psycopg2

DATABASE_URL = os.environ["DATABASE_URL"]

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT CHECK(role IN ('student','teacher','registrar')) NOT NULL
);

CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY REFERENCES users(id),
    student_number TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY REFERENCES users(id),
    full_name TEXT NOT NULL,
    department TEXT
);

CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    course_code TEXT UNIQUE NOT NULL,
    course_name TEXT NOT NULL,
    credit_hours INTEGER NOT NULL,
    teacher_id INTEGER REFERENCES teachers(id)
);

CREATE TABLE IF NOT EXISTS enrollments (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id),
    course_id INTEGER REFERENCES courses(id),
    UNIQUE(student_id, course_id)
);

CREATE TABLE IF NOT EXISTS grades (
    id SERIAL PRIMARY KEY,
    enrollment_id INTEGER REFERENCES enrollments(id),
    letter_grade TEXT,
    status TEXT CHECK(status IN ('draft','submitted','approved','locked')) DEFAULT 'draft',
    entered_by INTEGER,
    approved_by INTEGER,
    entered_at TIMESTAMP,
    approved_at TIMESTAMP
);
""")

conn.commit()
conn.close()

print("PostgreSQL schema created.")
