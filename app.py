from cs50 import SQL
from jobs import search_jobs
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
import math
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "session_files"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///interntrack.db")
db.execute("PRAGMA foreign_keys = ON")

@app.route("/update-status", methods=["POST"])
@login_required
def update_status():
    application_id = request.form.get("application_id")
    status = request.form.get("status")

    allowed_statuses = [
        "Saved",
        "Applied",
        "Online Assessment",
        "Interview",
        "Rejected",
        "Offer"
    ]

    if not application_id:
        return apology("missing application ID", 400)

    if status not in allowed_statuses:
        return apology("invalid application status", 400)

    db.execute(
        """
        UPDATE applications
        SET status = ?
        WHERE id = ? AND user_id = ?
        """,
        status,
        application_id,
        session["user_id"]
    )

    return redirect("/applications")

@app.route("/delete-application", methods=["POST"])
@login_required
def delete_application():
    # Get application_id from the submitted form
    application_id = request.form.get("application_id")
    user_id = session["user_id"]
    # Validate that application_id exists
    if not application_id:
        return apology("missing application ID", 400)
    # Delete the application only when:
    # id matches application_id
    # user_id matches session["user_id"]
    db.execute(
        """DELETE FROM applications
        WHERE id = ? AND user_id = ?""",
        application_id,
        user_id
    )
    # Redirect back to /applications
    return redirect("/applications")

@app.route("/save", methods=["POST"])
@login_required
def save():
    
    # 1. Get the job information from request.form
    external_id = request.form.get("external_id")
    title = request.form.get("title")
    company = request.form.get("company")
    location = request.form.get("location")
    description = request.form.get("description")
    apply_url = request.form.get("apply_url")
    posted_at = request.form.get("posted_at")
    # 2. Get the user ID from session
    user_id = session["user_id"]

    # 3. Validate essential fields
    # external_id, title, and company should exist
    if not external_id or not title or not company:
        return apology("missing required job information", 400)

    # 4. Insert the job into applications
    # Use ? placeholders
    try:
        db.execute(
            """
            INSERT INTO applications
                (
                    user_id,
                    source,
                    external_id,
                    title,
                    company,
                    location,
                    description,
                    apply_url,
                    posted_at
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            user_id,
            "Adzuna",
            external_id,
            title,
            company,
            location,
            description,
            apply_url,
            posted_at
        )
    except ValueError:
        return apology("this internship is already saved", 400)

    # Handles duplicate saves
    # 6. Redirect to the applications

    return redirect("/applications")

@app.route("/applications")
@login_required
def applications():
    selected_status = request.args.get("status", "All")

    allowed_statuses = [
        "All",
        "Saved",
        "Applied",
        "Online Assessment",
        "Interview",
        "Rejected",
        "Offer"
    ]

    if selected_status not in allowed_statuses:
        return apology("invalid status filter", 400)
    
    if selected_status == "All":
        saved_jobs = db.execute(
            """
            SELECT *
            FROM applications
            WHERE user_id = ?
            ORDER BY saved_at DESC
            """,
            session["user_id"]
        )
    else:
        saved_jobs = db.execute(
            """
            SELECT *
            FROM applications
            WHERE user_id = ? AND status = ?
            ORDER BY saved_at DESC
            """,
            session["user_id"],
            selected_status
        )
    return render_template("applications.html", applications=saved_jobs, selected_status=selected_status)

@app.route("/discover")
@login_required
def discover():
    jobs = []

    keyword = request.args.get("keyword", "").strip()
    location = request.args.get("location", "").strip()
    page = request.args.get("page", 1, type=int)

    if page < 1:
        page = 1

    results_per_page = 10
    total_results = 0
    total_pages = 0
    searched = bool(keyword)

    if searched:
        jobs, total_results = search_jobs(
            keyword,
            location,
            page
        )

        total_pages = math.ceil(
            total_results / results_per_page
        )

    return render_template(
        "discover.html",
        jobs=jobs,
        keyword=keyword,
        location=location,
        searched=searched,
        page=page,
        total_pages=total_pages,
        total_results=total_results
    )
@app.route("/")
@login_required
def index():
    user_id = session["user_id"]
    result = db.execute("SELECT COUNT(*) AS count FROM applications WHERE user_id = ?", user_id)
    total = result[0]["count"]

    status_rows = db.execute(
        """
        SELECT status, COUNT(*) AS count
        FROM applications
        WHERE user_id = ?
        GROUP BY status
        """,
        user_id
    )
    status_counts = {
        "Applied": 0,
        "Interview": 0,
        "Rejected": 0,
        "Offer": 0
    }
    for row in status_rows:
        if row["status"] in status_counts:
            status_counts[row["status"]] = row["count"]
    
    recent_applications = db.execute(
        """
        SELECT title, company, status, saved_at, apply_url
        FROM applications
        WHERE user_id = ?
        ORDER BY saved_at DESC
        LIMIT 3
        """,
        user_id
    )

    return render_template(
        "index.html",
        total=total,
        applied=status_counts["Applied"],
        interviewing=status_counts["Interview"],
        rejected=status_counts["Rejected"],
        offers=status_counts["Offer"],
        recent_applications=recent_applications
    )

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")



@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 400)

        # Ensure confirmed password was submitted
        elif not confirmation:
            return apology("must provide the confirmed password", 400)

        elif password != confirmation:
            return apology("passwords must match", 400)

        hashed_password = generate_password_hash(password)
        try:
            db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hashed_password)
        except ValueError:
            return apology("username already exists", 400)
        return redirect("/login")
    else:
        return render_template("register.html")

