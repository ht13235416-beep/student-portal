import os
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# USERS
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT CHECK (role IN ('student', 'teacher', 'registrar')) NOT NULL
)
""")

# STUDENTS
cur.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY,
    student_number TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    CONSTRAINT fk_student_user
        FOREIGN KEY (id)
        REFERENCES users(id)
        ON DELETE CASCADE
)
""")

# TEACHERS
cur.execute("""
CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    department TEXT,
    CONSTRAINT fk_teacher_user
        FOREIGN KEY (id)
        REFERENCES users(id)
        ON DELETE CASCADE
)
""")

# COURSES
cur.execute("""
CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    course_code TEXT UNIQUE NOT NULL,
    course_name TEXT NOT NULL,
    credit_hours INTEGER NOT NULL,
    teacher_id INTEGER NOT NULL,
    CONSTRAINT fk_course_teacher
        FOREIGN KEY (teacher_id)
        REFERENCES teachers(id)
)
""")

# ENROLLMENTS
cur.execute("""
CREATE TABLE IF NOT EXISTS enrollments (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    UNIQUE (student_id, course_id),
    CONSTRAINT fk_enroll_student
        FOREIGN KEY (student_id)
        REFERENCES students(id),
    CONSTRAINT fk_enroll_course
        FOREIGN KEY (course_id)
        REFERENCES courses(id)
)
""")

# GRADES
cur.execute("""
CREATE TABLE IF NOT EXISTS grades (
    id SERIAL PRIMARY KEY,
    enrollment_id INTEGER NOT NULL,
    letter_grade TEXT,
    status TEXT CHECK (status IN ('draft', 'submitted', 'approved', 'locked'))
        NOT NULL DEFAULT 'draft',
    entered_by INTEGER,
    approved_by INTEGER,
    entered_at TIMESTAMP,
    approved_at TIMESTAMP,
    CONSTRAINT fk_grade_enrollment
        FOREIGN KEY (enrollment_id)
        REFERENCES enrollments(id),
    CONSTRAINT fk_grade_entered_by
        FOREIGN KEY (entered_by)
        REFERENCES teachers(id),
    CONSTRAINT fk_grade_approved_by
        FOREIGN KEY (approved_by)
        REFERENCES users(id)
)
""")

# AUDIT LOG
cur.execute("""
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# 🔥 POSTGRES TRIGGER (STATUS PROTECTION)
cur.execute("""
CREATE OR REPLACE FUNCTION prevent_illegal_grade_update()
RETURNS trigger AS $$
BEGIN
    IF OLD.status = 'locked' THEN
        RAISE EXCEPTION 'Locked grades cannot be modified';
    ELSIF OLD.status = 'approved' AND NEW.status NOT IN ('locked') THEN
        RAISE EXCEPTION 'Approved grades can only be locked';
    ELSIF OLD.status = 'submitted' AND NEW.status NOT IN ('approved', 'draft') THEN
        RAISE EXCEPTION 'Submitted grades can only be approved or rejected';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
""")

cur.execute("""
DROP TRIGGER IF EXISTS prevent_illegal_grade_update ON grades;
CREATE TRIGGER prevent_illegal_grade_update
BEFORE UPDATE ON grades
FOR EACH ROW
EXECUTE FUNCTION prevent_illegal_grade_update();
""")

conn.commit()
cur.close()
conn.close()

print("PostgreSQL database initialized successfully.")
import seed_data