import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

conn = sqlite3.connect("database.db")
cur = conn.cursor()

# ---------- USERS ----------
users = [
    ("registrar", generate_password_hash("admin123"), "registrar"),
    ("teacher1", generate_password_hash("teach123"), "teacher"),
    ("student1", generate_password_hash("stud123"), "student"),
    ("student2", generate_password_hash("stud123"), "student"),
]

cur.executemany(
    "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
    users
)

# Get IDs
cur.execute("SELECT id, username FROM users")
user_map = {u: i for i, u in cur.fetchall()}

# ---------- STUDENTS ----------
cur.executemany("""
INSERT INTO students (id, student_number, full_name)
VALUES (?, ?, ?)
""", [
    (user_map["student1"], "NGUC-001", "Abel Tesfaye"),
    (user_map["student2"], "NGUC-002", "Liya Kebede"),
])

# ---------- TEACHER ----------
cur.execute("""
INSERT INTO teachers (id, full_name, department)
VALUES (?, ?, ?)
""", (user_map["teacher1"], "Dr. Solomon Bekele", "Computer Science"))

# ---------- COURSES ----------
cur.executemany("""
INSERT INTO courses (course_code, course_name, credit_hours, teacher_id)
VALUES (?, ?, ?, ?)
""", [
    ("CS101", "Introduction to Computing", 3, user_map["teacher1"]),
    ("CS102", "Data Structures", 4, user_map["teacher1"]),
])

# ---------- ENROLLMENTS ----------
cur.execute("SELECT id FROM courses WHERE course_code='CS101'")
cs101 = cur.fetchone()[0]

cur.execute("SELECT id FROM courses WHERE course_code='CS102'")
cs102 = cur.fetchone()[0]

enrollments = [
    (user_map["student1"], cs101),
    (user_map["student1"], cs102),
    (user_map["student2"], cs101),
]

cur.executemany("""
INSERT INTO enrollments (student_id, course_id)
VALUES (?, ?)
""", enrollments)

# ---------- GRADES ----------
cur.execute("SELECT id FROM enrollments")
for (eid,) in cur.fetchall():
    cur.execute("""
    INSERT INTO grades (enrollment_id, status, entered_at)
    VALUES (?, 'draft', ?)
    """, (eid, datetime.now()))

conn.commit()
conn.close()

print("Seed data inserted successfully.")
