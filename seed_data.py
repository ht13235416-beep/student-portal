import os
import psycopg2
from werkzeug.security import generate_password_hash

def seed_data():
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set")

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # USERS
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

    # USER MAP
    cur.execute("SELECT id, username FROM users")
    user_map = {u: i for i, u in cur.fetchall()}

    # STUDENTS (NO student_number)
    cur.executemany(
        """
        INSERT INTO students (id, full_name)
        VALUES (%s, %s)
        ON CONFLICT (id) DO NOTHING
        """,
        [
            (user_map["student1"], "Abel Tesfaye"),
            (user_map["student2"], "Liya Kebede"),
        ]
    )

    # TEACHER
    cur.execute(
        """
        INSERT INTO teachers (id, full_name, department)
        VALUES (%s, %s, %s)
        ON CONFLICT (id) DO NOTHING
        """,
        (user_map["teacher1"], "Dr. Solomon Bekele", "Computer Science")
    )

    # COURSES
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

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Seed data inserted")


