import os
import psycopg2
from werkzeug.security import generate_password_hash
from datetime import datetime

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

cur.execute("""
INSERT INTO users (username, password_hash, role)
VALUES
('registrar', %s, 'registrar'),
('teacher1', %s, 'teacher'),
('student1', %s, 'student'),
('student2', %s, 'student')
RETURNING id, username;
""", (
    generate_password_hash("admin123"),
    generate_password_hash("teach123"),
    generate_password_hash("stud123"),
    generate_password_hash("stud123")
))

user_map = {u: i for i, u in cur.fetchall()}

cur.execute("""
INSERT INTO students VALUES
(%s,'NGUC-001','Abel Tesfaye'),
(%s,'NGUC-002','Liya Kebede');
""", (user_map["student1"], user_map["student2"]))

cur.execute("""
INSERT INTO teachers VALUES
(%s,'Dr. Solomon Bekele','Computer Science');
""", (user_map["teacher1"],))

cur.execute("""
INSERT INTO courses (course_code, course_name, credit_hours, teacher_id)
VALUES
('CS101','Intro to Computing',3,%s),
('CS102','Data Structures',4,%s)
RETURNING id;
""", (user_map["teacher1"], user_map["teacher1"]))

course_ids = [r[0] for r in cur.fetchall()]

cur.execute("""
INSERT INTO enrollments (student_id, course_id)
VALUES
(%s,%s),
(%s,%s),
(%s,%s)
RETURNING id;
""", (
    user_map["student1"], course_ids[0],
    user_map["student1"], course_ids[1],
    user_map["student2"], course_ids[0]
))

for (eid,) in cur.fetchall():
    cur.execute(
        "INSERT INTO grades (enrollment_id, entered_at) VALUES (%s,%s)",
        (eid, datetime.now())
    )

conn.commit()
conn.close()

print("PostgreSQL seed data inserted.")

