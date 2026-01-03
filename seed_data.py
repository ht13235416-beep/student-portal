import os
import psycopg2
from werkzeug.security import generate_password_hash
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# ---------- USERS ----------
users = [
    ("registrar", generate_password_hash("admin123"), "registrar"),
    ("teacher1", generate_password_hash("teach123"), "teacher"),
    ("student1", generate_password_hash("stud123"), "student"),
    ("student2", generate_password_hash("stud123"), "student"),
]

cur.executemany(
    """
    INSERT INTO users (username, password_hash, role)
    VALUES (%s, %s, %s)
    ON CONFLICT (username) DO NOTHING
    """,
    users
)

# ---------- USER ID MAP ----------
cur.execute("SELECT id, username FROM users")
user_map = {row[1]: row[0] for row in cur.fetchall()}

# ---------- STUDENTS ----------
cur.executemany(
    """
    INSERT INTO students (id, student_number, full_name)
    VALUES (%s, %s, %s)
    ON CONFLICT (id) DO NOTHING
    """,
    [
        (user_map["student1"], "NGUC-001", "Abel Tesfaye"),
        (user_map["student2"], "NGUC-002", "Liya Kebede"),
    ]
)

# ---------- TEACHER ----------
cur.execute(
    """
    INSERT INTO teachers (id, full_name, department)
    VALUES (%s, %s, %s)
    ON CONFLICT (id) DO NOTHING
    """,
    (user_map["teacher1"], "Dr. Solomon Bekele", "Computer Science")
)

# ---------- COURSES ----------
cur.executemany(
    """
    INSERT INTO courses (course_code, course_name, credit_hours, teacher_id)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (course_code) DO NOTHING
    """,
    [
        ("CS101", "Introduction to Computing", 3, user_map["teacher1"]),
        ("CS102", "Data Structures", 4, user_map["teacher1"]),
    ]
)

# ---------- COURSE IDS ----------
cur.execute("SELECT id FROM courses WHERE course_code = %s", ("CS101",))
cs101 = cur.fetchone()[0]

cur.execute("SELECT id FROM courses WHERE course_code = %s", ("CS102",))
cs102 = cur.fetchone()[0]

# ---------- ENROLLMENTS ----------
enrollments = [
    (user_map["student1"], cs101),
    (user_map["student1"], cs102),
    (user_map["student2"], cs101),
]

cur.executemany(
    """
    INSERT INTO enrollments (student_id, course_id)
    VALUES (%s, %s)
    ON CONFLICT DO NOTHING
    """,
    enrollments
)

# ---------- GRADES ----------
cur.execute("SELECT id FROM enrollments")
for (eid,) in cur.fetchall():
    cur.execute(
        """
        INSERT INTO grades (enrollment_id, status, entered_at)
        VALUES (%s, 'draft', %s)
        ON CONFLICT DO NOTHING
        """,
        (eid, datetime.utcnow())
    )

conn.commit()
cur.close()
conn.close()

print("PostgreSQL seed data inserted successfully.")
