import psycopg2
import os
from werkzeug.security import generate_password_hash

def seed_data():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cur = conn.cursor()

    # ---- USERS ----
    cur.execute("SELECT COUNT(*) FROM users;")
    if cur.fetchone()[0] > 0:
        print("✅ Seed skipped (users already exist)")
        conn.close()
        return

    # USERS
    cur.execute("""
        INSERT INTO users (username, password_hash, role)
        VALUES
        ('student1', %s, 'student'),
        ('teacher1', %s, 'teacher'),
        ('registrar1', %s, 'registrar')
        RETURNING id;
    """, (
        generate_password_hash("student123"),
        generate_password_hash("teacher123"),
        generate_password_hash("registrar123")
    ))

    ids = [row[0] for row in cur.fetchall()]
    student_id, teacher_id, registrar_id = ids

    # STUDENT PROFILE
    cur.execute("""
        INSERT INTO students (id, full_name)
        VALUES (%s, 'Student One');
    """, (student_id,))

    # TEACHER PROFILE
    cur.execute("""
        INSERT INTO teachers (id, full_name)
        VALUES (%s, 'Teacher One');
    """, (teacher_id,))

    # COURSE
    cur.execute("""
        INSERT INTO courses (course_code, course_name, credit_hours, teacher_id)
        VALUES ('CS101', 'Intro to CS', 3, %s);
    """, (teacher_id,))

    conn.commit()
    conn.close()
    print("🚀 Database seeded successfully")
