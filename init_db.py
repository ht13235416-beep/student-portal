import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

# USERS
cur.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT CHECK(role IN ('student', 'teacher', 'registrar')) NOT NULL
)
""")

# STUDENTS
cur.execute("""
CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    student_number TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    FOREIGN KEY (id) REFERENCES users(id)
)
""")

# TEACHERS
cur.execute("""
CREATE TABLE teachers (
    id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    department TEXT,
    FOREIGN KEY (id) REFERENCES users(id)
)
""")

# COURSES
cur.execute("""
CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT UNIQUE NOT NULL,
    course_name TEXT NOT NULL,
    credit_hours INTEGER NOT NULL,
    teacher_id INTEGER NOT NULL,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id)
)
""")

# ENROLLMENTS
cur.execute("""
CREATE TABLE enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    UNIQUE(student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
)
""")

# GRADES
cur.execute("""
CREATE TABLE grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    enrollment_id INTEGER NOT NULL,
    letter_grade TEXT,
    status TEXT CHECK(status IN ('draft', 'submitted', 'approved', 'locked')) NOT NULL DEFAULT 'draft',
    entered_by INTEGER,
    approved_by INTEGER,
    entered_at DATETIME,
    approved_at DATETIME,
    FOREIGN KEY (enrollment_id) REFERENCES enrollments(id),
    FOREIGN KEY (entered_by) REFERENCES teachers(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
)
""")

# AUDIT LOG (OPTIONAL BUT REAL)
cur.execute("""
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
cur.execute("""
CREATE TRIGGER IF NOT EXISTS prevent_illegal_grade_update
BEFORE UPDATE ON grades
BEGIN
    SELECT
        CASE
            WHEN OLD.status = 'locked' THEN
                RAISE(ABORT, 'Locked grades cannot be modified')
            WHEN OLD.status = 'approved' AND NEW.status NOT IN ('locked') THEN
                RAISE(ABORT, 'Approved grades can only be locked')
            WHEN OLD.status = 'submitted' AND NEW.status NOT IN ('approved', 'draft') THEN
                RAISE(ABORT, 'Submitted grades can only be approved or rejected')
        END;
END;
""")

conn.commit()
conn.close()

print("Database initialized successfully.")
