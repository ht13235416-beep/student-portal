from flask import Flask, render_template, request, session, redirect, url_for
from werkzeug.security import check_password_hash
import os
import psycopg2
from psycopg2.extras import RealDictCursor


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback")

def get_db():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    return psycopg2.connect(
        database_url,
        cursor_factory=RealDictCursor
    )

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        cur = db.cursor()
        cur.execute(
            "SELECT id, password_hash, role FROM users WHERE username=%s",
            (username,)
        )
        user = cur.fetchone()
        db.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["role"] = user["role"]

            if user["role"] == "student":
                return redirect(url_for("student_dashboard"))
            elif user["role"] == "teacher":
                return redirect(url_for("teacher_dashboard"))
            elif user["role"] == "registrar":
                return redirect(url_for("registrar_dashboard"))

    return render_template("login.html")

@app.route("/teacher", methods=["GET", "POST"])
def teacher_dashboard():
    if session.get("role") != "teacher":
        return redirect(url_for("login"))

    teacher_id = session["user_id"]
    db = get_db()
    cur = db.cursor()

    # Handle grade update
    if request.method == "POST":
        grade_id = request.form["grade_id"]
        letter_grade = request.form["letter_grade"]
        action = request.form["action"]

        if action == "save":
            cur.execute("""
                UPDATE grades
                SET letter_grade=%s, entered_by=%s, status='draft'
                WHERE id=%s AND status='draft'
            """, (letter_grade, teacher_id, grade_id))

        elif action == "submit":
            cur.execute("""
                UPDATE grades
                SET letter_grade=%s, status='submitted', entered_by=%s
                WHERE id=%s AND status='draft'
            """, (letter_grade, teacher_id, grade_id))

        db.commit()

    # Fetch teacher data
    cur.execute("""
        SELECT
            grades.id AS grade_id,
            students.full_name AS student_name,
            courses.course_code,
            courses.course_name,
            grades.letter_grade,
            grades.status
        FROM grades
        JOIN enrollments ON grades.enrollment_id = enrollments.id
        JOIN students ON enrollments.student_id = students.id
        JOIN courses ON enrollments.course_id = courses.id
        WHERE courses.teacher_id = %s
        ORDER BY courses.course_code, students.full_name
    """, (teacher_id,))

    rows = cur.fetchall()
    db.close()
    print("DEBUG ROW:", dict(rows[0]) if rows else "NO ROWS")
    return render_template("teacher.html", rows=rows)

@app.route("/student")
def student_dashboard():
    if session.get("role") != "student":
        return redirect(url_for("login"))

    db = get_db()
    cur = db.cursor()

    # map logged-in user → student
    cur.execute(
        "SELECT id FROM students WHERE id = %s",
        (session["user_id"],)
    )
    student = cur.fetchone()

    if not student:
        db.close()
        return "Student profile missing", 400

    student_id = student["id"]

    # fetch enrolled courses + grades
    cur.execute(
        """
        SELECT
            courses.course_code,
            courses.course_name,
            courses.credit_hours,
            grades.letter_grade,
            grades.status
        FROM enrollments
        JOIN courses ON enrollments.course_id = courses.id
        LEFT JOIN grades ON grades.enrollment_id = enrollments.id
        WHERE enrollments.student_id = %s
        ORDER BY courses.course_code
        """,
        (student_id,)
    )

    rows = cur.fetchall()

    grade_points = {
        "A": 4.0, "A-": 3.7,
        "B+": 3.3, "B": 3.0, "B-": 2.7,
        "C+": 2.3, "C": 2.0,
        "D": 1.0, "F": 0.0
    }

    total_points = 0
    total_credits = 0

    for row in rows:
        if row["status"] != "locked":
            continue

        if row["letter_grade"] in grade_points:
            total_points += grade_points[row["letter_grade"]] * row["credit_hours"]
            total_credits += row["credit_hours"]

    gpa = round(total_points / total_credits, 2) if total_credits else 0

    db.close()
    return render_template("student.html", rows=rows, gpa=gpa)

@app.route("/registrar", methods=["GET", "POST"])
def registrar_dashboard():
    if session.get("role") != "registrar":
        return redirect(url_for("login"))

    registrar_id = session["user_id"]
    db = get_db()
    cur = db.cursor()

    # 🔥 HANDLE APPROVE / REJECT / LOCK
    if request.method == "POST":
        grade_id = request.form["grade_id"]
        action = request.form["action"]

        if action == "approve":
            cur.execute("""
                UPDATE grades
                SET status='approved', approved_by=%s, approved_at=CURRENT_TIMESTAMP
                WHERE id=%s AND status='submitted'
            """, (registrar_id, grade_id))

        elif action == "reject":
            cur.execute("""
                UPDATE grades
                SET status='draft'
                WHERE id=%s AND status='submitted'
            """, (grade_id,))

        elif action == "lock":
            cur.execute("""
                UPDATE grades
                SET status='locked'
                WHERE id=%s AND status='approved'
            """, (grade_id,))

        db.commit()

    # STUDENTS
    cur.execute("SELECT id, full_name FROM students")
    students = cur.fetchall()

    # COURSES
    cur.execute("SELECT id, course_code, course_name FROM courses")
    courses = cur.fetchall()

    # GRADES WAITING REVIEW
    cur.execute("""
        SELECT
            grades.id AS grade_id,
            students.full_name AS student_name,
            courses.course_code,
            grades.letter_grade,
            grades.status
        FROM grades
        JOIN enrollments ON grades.enrollment_id = enrollments.id
        JOIN students ON enrollments.student_id = students.id
        JOIN courses ON enrollments.course_id = courses.id
        WHERE grades.status IN ('submitted', 'approved')
        ORDER BY courses.course_code, students.full_name
    """)
    rows = cur.fetchall()

    db.close()

    return render_template(
        "registrar.html",
        students=students,
        courses=courses,
        rows=rows
    )


@app.route("/registrar/enroll", methods=["POST"])
def enroll_student():
    if session.get("role") != "registrar":
        return redirect(url_for("login"))

    student_id = request.form["student_id"]
    course_ids = request.form.getlist("course_ids")

    db = get_db()
    cur = db.cursor()

    for course_id in course_ids:
        try:
            cur.execute("""
                INSERT INTO enrollments (student_id, course_id)
                VALUES (%s, %s)
            """, (student_id, course_id))

           INSERT INTO enrollments (student_id, course_id)
VALUES (%s, %s)
RETURNING id

enrollment_id = cur.fetchone()["id"]


            cur.execute("""
                INSERT INTO grades (enrollment_id)
                VALUES (%s)
            """, (enrollment_id,))

        except psycopg2.IntegrityError:
    db.rollback()
    continue

            continue

    db.commit()
    db.close()

    return redirect(url_for("registrar_dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))
if __name__ == "__main__":
    app.run(debug=True)

