from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_from_directory
)

import os
import mysql.connector

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)

app.secret_key = "campusconnect_secret_key"


# ============================================================
# UPLOAD SETTINGS
# ============================================================

UPLOAD_FOLDER = os.path.join(
    app.root_path,
    "uploads"
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg"
}


def allowed_file(filename):

    return (
        "." in filename
        and
        filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# ============================================================
# MYSQL CONNECTION
# ============================================================

def get_db_connection():

    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Tamanna@123",
        database="campusconnect"
    )


# ============================================================
# CREATE USERS TABLE
# ============================================================

def create_users_table():

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INT AUTO_INCREMENT PRIMARY KEY,

            name VARCHAR(100) NOT NULL,

            email VARCHAR(100) UNIQUE NOT NULL,

            password VARCHAR(255) NOT NULL,

            role VARCHAR(20) NOT NULL

        )
    """)

    connection.commit()

    cursor.close()
    connection.close()


# ============================================================
# CREATE COMPLAINTS TABLE
# ============================================================

def create_complaints_table():

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (

            id INT AUTO_INCREMENT PRIMARY KEY,

            user_id INT NOT NULL,

            title VARCHAR(150) NOT NULL,

            category VARCHAR(50) NOT NULL,

            location VARCHAR(150) NOT NULL,

            description TEXT NOT NULL,

            priority VARCHAR(20) NOT NULL,

            photo VARCHAR(255),

            status VARCHAR(30) DEFAULT 'Pending',

            admin_remark TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
            REFERENCES users(id)
            ON DELETE CASCADE

        )
    """)

    connection.commit()

    cursor.close()
    connection.close()


# ============================================================
# CREATE NOTICES TABLE
# ============================================================

def create_notices_table():

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notices (

            id INT AUTO_INCREMENT PRIMARY KEY,

            title VARCHAR(150) NOT NULL,

            description TEXT NOT NULL,

            posted_by INT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            photo VARCHAR(255) NULL,

            FOREIGN KEY (posted_by)
            REFERENCES users(id)
            ON DELETE CASCADE

        )
    """)

    connection.commit()

    cursor.close()
    connection.close()


# ============================================================
# CREATE LOST & FOUND TABLE
# ============================================================

def create_lost_found_table():

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lost_found (

            id INT AUTO_INCREMENT PRIMARY KEY,

            user_id INT NOT NULL,

            item_name VARCHAR(150) NOT NULL,

            type VARCHAR(20) NOT NULL,

            location VARCHAR(150) NOT NULL,

            description TEXT NOT NULL,

            photo VARCHAR(255),

            status VARCHAR(30) DEFAULT 'Reported',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
            REFERENCES users(id)

            ON DELETE CASCADE

        )
    """)

    connection.commit()

    cursor.close()
    connection.close()


# ============================================================
# CREATE LOST & FOUND RESPONSES TABLE
# ============================================================

def create_lost_found_responses_table():

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lost_found_responses (

            id INT AUTO_INCREMENT PRIMARY KEY,

            item_id INT NOT NULL,

            user_id INT NOT NULL,

            message TEXT NOT NULL,

            photo VARCHAR(255),

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (item_id)
            REFERENCES lost_found(id)
            ON DELETE CASCADE,

            FOREIGN KEY (user_id)
            REFERENCES users(id)
            ON DELETE CASCADE

        )
    """)

    connection.commit()

    cursor.close()
    connection.close()


# ============================================================
# CREATE DEMO USERS
# ============================================================

def create_demo_users():

    connection = get_db_connection()
    cursor = connection.cursor()

    demo_users = [

        (
            "Demo Student",
            "student@campusconnect.com",
            "student123",
            "student"
        ),

        (
            "System Admin",
            "admin@campusconnect.com",
            "admin123",
            "admin"
        )

    ]

    for name, email, password, role in demo_users:

        cursor.execute(
            """
            SELECT id

            FROM users

            WHERE email = %s
            """,
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user is None:

            hashed_password = generate_password_hash(
                password
            )

            cursor.execute(
                """
                INSERT INTO users
                (
                    name,
                    email,
                    password,
                    role
                )

                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    name,
                    email,
                    hashed_password,
                    role
                )
            )

    connection.commit()

    cursor.close()
    connection.close()


# ============================================================
# HOME / LOGIN
# ============================================================

@app.route("/")
def home():

    return render_template(
        "login.html"
    )


# ============================================================
# STUDENT REGISTRATION
# ============================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():
    if session.get("role") in ("student", "admin"):
        if session.get("role") == "student":
            return redirect(url_for("student_dashboard"))
        return redirect(url_for("admin_dashboard"))

    error = None
    success = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password or not confirm_password:
            error = "Please fill in all fields."

        elif password != confirm_password:
            error = "Passwords do not match."

        elif len(password) < 6:
            error = "Password must be at least 6 characters."

        else:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            existing_user = cursor.fetchone()

            if existing_user:
                error = "An account with this email already exists."
            else:
                hashed_password = generate_password_hash(password)

                cursor.execute(
                    """
                    INSERT INTO users
                    (
                        name,
                        email,
                        password,
                        role
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        name,
                        email,
                        hashed_password,
                        "student"
                    )
                )

                connection.commit()
                cursor.close()
                connection.close()

                return redirect(url_for("home"))

            cursor.close()
            connection.close()

    return render_template(
        "register.html",
        error=error,
        success=success
    )



# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["POST"]
)
def login():

    email = request.form.get(
        "email"
    )

    password = request.form.get(
        "password"
    )

    selected_role = request.form.get(
        "role"
    )

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT *

        FROM users

        WHERE email = %s
        """,
        (email,)
    )

    user = cursor.fetchone()

    cursor.close()
    connection.close()

    if user is None:

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    if not check_password_hash(
        user["password"],
        password
    ):

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    if user["role"] != selected_role:

        return render_template(
            "login.html",
            error="Selected role does not match this account."
        )

    session["user_id"] = user["id"]

    session["name"] = user["name"]

    session["role"] = user["role"]


    if user["role"] == "student":

        return redirect(
            url_for(
                "student_dashboard"
            )
        )


    if user["role"] == "admin":

        return redirect(
            url_for(
                "admin_dashboard"
            )
        )


    return redirect(
        url_for("home")
    )


# ============================================================
# STUDENT DASHBOARD
# ============================================================

@app.route(
    "/student-dashboard"
)
def student_dashboard():

    if session.get("role") != "student":

        return redirect(
            url_for("home")
        )

    return render_template(
        "student_dashboard.html",
        name=session.get("name")
    )


# ============================================================
# STUDENT PROFILE
# ============================================================

@app.route(
    "/student/profile"
)
def student_profile():

    if session.get("role") != "student":

        return redirect(
            url_for("home")
        )

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT

            id,
            name,
            email,
            role

        FROM users

        WHERE id = %s
        """,
        (
            session.get("user_id"),
        )
    )

    user = cursor.fetchone()

    cursor.close()
    connection.close()

    if not user:

        session.clear()

        return redirect(
            url_for("home")
        )

    return render_template(
        "student_profile.html",
        user=user
    )


# ============================================================
# STUDENT COMPLAINTS
# ============================================================

@app.route(
    "/complaints"
)
def complaints():

    if session.get("role") != "student":

        return redirect(
            url_for("home")
        )

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT *

        FROM complaints

        WHERE user_id = %s

        ORDER BY created_at DESC
        """,
        (
            session.get("user_id"),
        )
    )

    complaints_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "complaints.html",
        complaints=complaints_list
    )


# ============================================================
# NEW COMPLAINT PAGE - COMPATIBILITY
# ============================================================

@app.route(
    "/complaints/new"
)
def new_complaint():

    if session.get("role") != "student":

        return redirect(
            url_for("home")
        )

    return redirect(
        url_for("complaints")
    )


# ============================================================
# SUBMIT COMPLAINT
# ============================================================

@app.route(
    "/complaints/new",
    methods=["POST"]
)
def submit_complaint():

    if session.get("role") != "student":

        return redirect(
            url_for("home")
        )

    title = request.form.get(
        "title",
        ""
    ).strip()

    category = request.form.get(
        "category",
        ""
    ).strip()

    location = request.form.get(
        "location",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    priority = request.form.get(
        "priority",
        "Low"
    ).strip()

    photo = request.files.get(
        "photo"
    )

    filename = None


    if photo and photo.filename != "":

        if allowed_file(
            photo.filename
        ):

            filename = secure_filename(
                photo.filename
            )

            photo.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )


    if title and category and location and description:

        connection = get_db_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO complaints
            (
                user_id,
                title,
                category,
                location,
                description,
                priority,
                photo
            )

            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                session.get("user_id"),
                title,
                category,
                location,
                description,
                priority,
                filename
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

    else:

        if filename:

            photo_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            if os.path.exists(photo_path):

                os.remove(photo_path)


    return redirect(
        url_for("complaints")
    )


# ============================================================
# DELETE STUDENT COMPLAINT
# ============================================================

@app.route(
    "/complaints/delete/<int:complaint_id>"
)
def delete_complaint(
    complaint_id
):

    if session.get("role") != "student":

        return redirect(
            url_for("home")
        )

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT photo

        FROM complaints

        WHERE id = %s

        AND user_id = %s
        """,
        (
            complaint_id,
            session.get("user_id")
        )
    )

    complaint = cursor.fetchone()


    if complaint:

        if complaint["photo"]:

            photo_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                complaint["photo"]
            )

            if os.path.exists(photo_path):

                os.remove(photo_path)


        cursor.execute(
            """
            DELETE FROM complaints

            WHERE id = %s

            AND user_id = %s
            """,
            (
                complaint_id,
                session.get("user_id")
            )
        )

        connection.commit()


    cursor.close()
    connection.close()

    return redirect(
        url_for("complaints")
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route(
    "/admin-dashboard"
)
def admin_dashboard():

    if session.get("role") != "admin":

        return redirect(
            url_for("home")
        )

    return render_template(
        "admin_dashboard.html",
        name=session.get("name")
    )


# ============================================================
# ADMIN COMPLAINTS
# ============================================================

@app.route(
    "/admin/complaints"
)
def admin_complaints():

    if session.get("role") != "admin":

        return redirect(
            url_for("home")
        )

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT

            complaints.id,

            complaints.title,

            complaints.category,

            complaints.location,

            complaints.description,

            complaints.priority,

            complaints.photo,

            complaints.status,

            complaints.admin_remark,

            complaints.created_at,

            users.name AS student_name,

            users.email AS student_email

        FROM complaints

        JOIN users

        ON complaints.user_id = users.id

        ORDER BY complaints.created_at DESC
        """
    )

    complaints_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "admin_complaints.html",
        complaints=complaints_list
    )


# ============================================================
# UPDATE COMPLAINT
# ============================================================

@app.route(
    "/admin/complaints/update/<int:complaint_id>",
    methods=["POST"]
)
def update_complaint(
    complaint_id
):

    if session.get("role") != "admin":

        return redirect(
            url_for("home")
        )

    status = request.form.get(
        "status",
        "Pending"
    ).strip()

    admin_remark = request.form.get(
        "admin_remark",
        ""
    ).strip()

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE complaints

        SET
            status = %s,
            admin_remark = %s

        WHERE id = %s
        """,
        (
            status,
            admin_remark,
            complaint_id
        )
    )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect(
        url_for("admin_complaints")
    )


# ============================================================
# ADMIN MANAGE USERS
# ============================================================

@app.route(
    "/admin/users"
)
def admin_users():

    if session.get("role") != "admin":

        return redirect(
            url_for("home")
        )

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT

            id,
            name,
            email,
            role

        FROM users

        ORDER BY id ASC
        """
    )

    users = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "admin_users.html",
        users=users
    )


# ============================================================
# ADMIN NOTICES
# ============================================================

@app.route(
    "/admin/notices",
    methods=["GET", "POST"]
)
def admin_notices():

    if session.get("role") != "admin":

        return redirect(
            url_for("home")
        )

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )


    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        photo = request.files.get(
            "photo"
        )

        filename = None


        if photo and photo.filename != "":

            if allowed_file(
                photo.filename
            ):

                filename = secure_filename(
                    photo.filename
                )

                photo.save(
                    os.path.join(
                        app.config["UPLOAD_FOLDER"],
                        filename
                    )
                )


        if title and description:

            cursor.execute(
                """
                INSERT INTO notices
                (
                    title,
                    description,
                    posted_by,
                    photo
                )

                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    title,
                    description,
                    session.get("user_id"),
                    filename
                )
            )

            connection.commit()


        else:

            if filename:

                photo_path = os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )

                if os.path.exists(photo_path):

                    os.remove(photo_path)


    cursor.execute(
        """
        SELECT

            notices.id,

            notices.title,

            notices.description,

            notices.created_at,

            notices.photo,

            users.name AS admin_name

        FROM notices

        JOIN users

        ON notices.posted_by = users.id

        ORDER BY notices.created_at DESC
        """
    )

    notices = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "admin_notices.html",
        notices=notices
    )


# ============================================================
# STUDENT NOTICES
# ============================================================

@app.route(
    "/student/notices"
)
def student_notices():

    if session.get("role") != "student":

        return redirect(
            url_for("home")
        )

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT

            notices.id,

            notices.title,

            notices.description,

            notices.created_at,

            notices.photo,

            users.name AS admin_name

        FROM notices

        JOIN users

        ON notices.posted_by = users.id

        ORDER BY notices.created_at DESC
        """
    )

    notices = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "student_notices.html",
        notices=notices
    )


# ============================================================
# ADMIN DELETE NOTICE
# ============================================================

@app.route(
    "/admin/notices/delete/<int:notice_id>"
)
def delete_notice(
    notice_id
):

    if session.get("role") != "admin":

        return redirect(
            url_for("home")
        )

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT photo

        FROM notices

        WHERE id = %s
        """,
        (
            notice_id,
        )
    )

    notice = cursor.fetchone()


    if notice and notice["photo"]:

        photo_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            notice["photo"]
        )

        if os.path.exists(photo_path):

            os.remove(photo_path)


    cursor.execute(
        """
        DELETE FROM notices

        WHERE id = %s
        """,
        (
            notice_id,
        )
    )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect(
        url_for("admin_notices")
    )


# ============================================================
# STUDENT LOST & FOUND
# ============================================================

@app.route(
    "/lost-found"
)
def lost_found():

    if session.get("role") != "student":

        return redirect(
            url_for("home")
        )


    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )


    # Show all reports so students can help each other.
    cursor.execute(
        """
        SELECT
            lost_found.id,
            lost_found.user_id,
            lost_found.item_name,
            lost_found.type,
            lost_found.location,
            lost_found.description,
            lost_found.photo,
            lost_found.status,
            lost_found.created_at,
            users.name AS student_name,
            users.email AS student_email

        FROM lost_found

        JOIN users
        ON lost_found.user_id = users.id

        ORDER BY lost_found.created_at DESC
        """
    )

    items = cursor.fetchall()


    # Load all responses for the displayed reports.
    cursor.execute(
        """
        SELECT
            lost_found_responses.id,
            lost_found_responses.item_id,
            lost_found_responses.message,
            lost_found_responses.photo,
            lost_found_responses.created_at,
            users.name AS responder_name,
            users.email AS responder_email

        FROM lost_found_responses

        JOIN users
        ON lost_found_responses.user_id = users.id

        ORDER BY lost_found_responses.created_at ASC
        """
    )

    responses = cursor.fetchall()


    cursor.close()
    connection.close()


    # Group responses by report ID.
    response_map = {}

    for response in responses:

        response_map.setdefault(
            response["item_id"],
            []
        ).append(response)


    for item in items:

        item["responses"] = response_map.get(
            item["id"],
            []
        )


    return render_template(
        "lost_found.html",
        items=items,
        current_user_id=session.get("user_id")
    )


# ============================================================
# SUBMIT LOST & FOUND REPORT
# ============================================================
# ============================================================
# SUBMIT LOST & FOUND REPORT
# ============================================================

@app.route(
    "/lost-found/new",
    methods=["POST"]
)
def submit_lost_found():

    if session.get("role") != "student":

        return redirect(
            url_for("home")
        )

    item_name = request.form.get(
        "item_name",
        ""
    ).strip()

    item_type = request.form.get(
        "type",
        ""
    ).strip()

    location = request.form.get(
        "location",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    photo = request.files.get(
        "photo"
    )

    filename = None


    if photo and photo.filename != "":

        if allowed_file(
            photo.filename
        ):

            filename = secure_filename(
                photo.filename
            )

            photo.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )


    if item_name and item_type and location and description:

        connection = get_db_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO lost_found
            (
                user_id,
                item_name,
                type,
                location,
                description,
                photo
            )

            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                session.get("user_id"),
                item_name,
                item_type,
                location,
                description,
                filename
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

    else:

        if filename:

            photo_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            if os.path.exists(photo_path):

                os.remove(photo_path)


    return redirect(
        url_for("lost_found")
    )


# ============================================================
# STUDENT UPDATE OWN LOST & FOUND STATUS
# ============================================================

@app.route(
    "/lost-found/update/<int:item_id>",
    methods=["POST"]
)
def student_update_lost_found(
    item_id
):

    if session.get("role") != "student":

        return redirect(
            url_for("home")
        )


    status = request.form.get(
        "status",
        "Reported"
    ).strip()


    allowed_statuses = {
        "Reported",
        "Searching",
        "Found",
        "Claimed",
        "Resolved"
    }


    if status not in allowed_statuses:

        return redirect(
            url_for("lost_found")
        )


    connection = get_db_connection()
    cursor = connection.cursor()


    # Ownership check:
    # only the student who created this report
    # can change its status.
    cursor.execute(
        """
        UPDATE lost_found

        SET status = %s

        WHERE id = %s
        AND user_id = %s
        """,
        (
            status,
            item_id,
            session.get("user_id")
        )
    )


    connection.commit()

    cursor.close()
    connection.close()


    return redirect(
        url_for("lost_found")
    )


# ============================================================
# STUDENT DELETE OWN LOST & FOUND REPORT
# ============================================================

@app.route(
    "/lost-found/delete/<int:item_id>",
    methods=["POST"]
)
def delete_lost_found(item_id):

    if session.get("role") != "student":

        return redirect(
            url_for("home")
        )


    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # Get the report first so we can remove its uploaded photo too.
    cursor.execute(
        """
        SELECT photo
        FROM lost_found
        WHERE id = %s
        AND user_id = %s
        """,
        (
            item_id,
            session.get("user_id")
        )
    )

    item = cursor.fetchone()

    if item:

        cursor.execute(
            """
            DELETE FROM lost_found
            WHERE id = %s
            AND user_id = %s
            """,
            (
                item_id,
                session.get("user_id")
            )
        )

        connection.commit()

        # Remove the report photo from the uploads folder if it exists.
        if item.get("photo"):

            photo_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                item["photo"]
            )

            if os.path.exists(photo_path):

                try:
                    os.remove(photo_path)
                except OSError:
                    pass

    cursor.close()
    connection.close()


    return redirect(
        url_for("lost_found")
    )


# ============================================================
# STUDENT RESPONDS TO A LOST & FOUND REPORT
# ============================================================

@app.route(
    "/lost-found/respond/<int:item_id>",
    methods=["POST"]
)
def respond_lost_found(
    item_id
):

    if session.get("role") != "student":

        return redirect(
            url_for("home")
        )


    message = request.form.get(
        "message",
        ""
    ).strip()


    photo = request.files.get(
        "photo"
    )


    filename = None


    if photo and photo.filename != "":

        if allowed_file(
            photo.filename
        ):

            filename = secure_filename(
                photo.filename
            )

            photo.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )


    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )


    # Fetch the report owner.
    cursor.execute(
        """
        SELECT
            user_id

        FROM lost_found

        WHERE id = %s
        """,
        (
            item_id,
        )
    )


    item = cursor.fetchone()


    # Prevent invalid reports and prevent
    # a student from responding to their own report.
    if (
        not item
        or item["user_id"] == session.get("user_id")
        or not message
    ):

        cursor.close()
        connection.close()


        if filename:

            photo_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            if os.path.exists(
                photo_path
            ):

                os.remove(
                    photo_path
                )


        return redirect(
            url_for("lost_found")
        )


    cursor.execute(
        """
        INSERT INTO lost_found_responses
        (
            item_id,
            user_id,
            message,
            photo
        )

        VALUES
        (
            %s,
            %s,
            %s,
            %s
        )
        """,
        (
            item_id,
            session.get("user_id"),
            message,
            filename
        )
    )


    connection.commit()

    cursor.close()
    connection.close()


    return redirect(
        url_for("lost_found")
    )


# ============================================================
# ADMIN LOST & FOUND
# ============================================================

@app.route(
    "/admin/lost-found"
)
def admin_lost_found():

    if session.get("role") != "admin":

        return redirect(
            url_for("home")
        )

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT

            lost_found.id,

            lost_found.item_name,

            lost_found.type,

            lost_found.location,

            lost_found.description,

            lost_found.photo,

            lost_found.status,

            lost_found.created_at,

            users.name AS student_name,

            users.email AS student_email

        FROM lost_found

        JOIN users

        ON lost_found.user_id = users.id

        ORDER BY lost_found.created_at DESC
        """
    )

    items = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "admin_lost_found.html",
        items=items
    )


# ============================================================
# UPDATE LOST & FOUND STATUS
# ============================================================

@app.route(
    "/admin/lost-found/update/<int:item_id>",
    methods=["POST"]
)
def update_lost_found(
    item_id
):

    if session.get("role") != "admin":

        return redirect(
            url_for("home")
        )

    status = request.form.get(
        "status",
        "Reported"
    ).strip()

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE lost_found

        SET status = %s

        WHERE id = %s
        """,
        (
            status,
            item_id
        )
    )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect(
        url_for("admin_lost_found")
    )


# ============================================================
# SERVE UPLOADED FILES
# ============================================================

@app.route(
    "/uploads/<filename>"
)
def uploaded_file(filename):

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route(
    "/logout"
)
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    os.makedirs(
        UPLOAD_FOLDER,
        exist_ok=True
    )

    create_users_table()

    create_demo_users()

    create_complaints_table()

    create_notices_table()

    create_lost_found_table()

    create_lost_found_responses_table()

    app.run(
        debug=True
    )
