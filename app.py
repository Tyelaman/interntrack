from datetime import datetime
import math
import os

from cs50 import SQL
from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required
from jobs import JobSearchError, search_jobs


# Load environment variables from .env
load_dotenv()

# Configure application
app = Flask(__name__)

# Retrieve secret key from environment variable
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

if not app.config["SECRET_KEY"]:
    raise RuntimeError("Missing SECRET_KEY in .env")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "session_files"
Session(app)

# Configure CS50 Library to use SQLite
db = SQL("sqlite:///interntrack.db")
db.execute("PRAGMA foreign_keys = ON")


@app.template_filter("format_date")
def format_date(value):
    """Convert stored timestamps into readable dates."""

    if not value:
        return "Date unavailable"

    if isinstance(value, datetime):
        parsed_date = value
    else:
        try:
            parsed_date = datetime.fromisoformat(
                str(value).replace("Z", "+00:00")
            )
        except ValueError:
            return str(value)

    return (
        f"{parsed_date.strftime('%b')} "
        f"{parsed_date.day}, "
        f"{parsed_date.year}"
    )


@app.route("/update-status", methods=["POST"])
@login_required
def update_status():
    """Update the status of a saved application."""

    application_id = request.form.get("application_id")
    status = request.form.get("status")
    return_status = request.form.get("return_status", "All")

    allowed_statuses = [
        "Saved",
        "Applied",
        "Online Assessment",
        "Interview",
        "Rejected",
        "Offer",
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
        session["user_id"],
    )

    # Prevent a modified form from sending an invalid filter
    if return_status not in ["All", *allowed_statuses]:
        return_status = "All"

    flash("Application status updated.", "success")

    return redirect(
        url_for("applications", status=return_status)
    )

@app.route("/update-details", methods=["POST"])
@login_required
def update_details():
    """Update sponsorship information and personal notes."""

    application_id = request.form.get("application_id")
    sponsorship = request.form.get("sponsorship")
    notes = request.form.get("notes", "").strip()
    return_status = request.form.get("return_status", "All")

    allowed_sponsorship_values = [
        "Yes",
        "No",
        "Unknown",
    ]

    allowed_status_filters = [
        "All",
        "Saved",
        "Applied",
        "Online Assessment",
        "Interview",
        "Rejected",
        "Offer",
    ]

    if not application_id:
        return apology("missing application ID", 400)

    if sponsorship not in allowed_sponsorship_values:
        return apology("invalid sponsorship value", 400)

    if len(notes) > 1000:
        return apology(
            "notes must be 1000 characters or fewer",
            400,
        )

    if return_status not in allowed_status_filters:
        return_status = "All"

    db.execute(
        """
        UPDATE applications
        SET sponsorship = ?, notes = ?
        WHERE id = ? AND user_id = ?
        """,
        sponsorship,
        notes,
        application_id,
        session["user_id"],
    )

    flash("Application details updated.", "success")

    return redirect(
        url_for("applications", status=return_status)
    )

@app.route("/delete-application", methods=["POST"])
@login_required
def delete_application():
    """Delete an application belonging to the logged-in user."""

    application_id = request.form.get("application_id")
    return_status = request.form.get("return_status", "All")
    user_id = session["user_id"]

    if not application_id:
        return apology("missing application ID", 400)

    db.execute(
        """
        DELETE FROM applications
        WHERE id = ? AND user_id = ?
        """,
        application_id,
        user_id,
    )

    allowed_return_statuses = [
        "All",
        "Saved",
        "Applied",
        "Online Assessment",
        "Interview",
        "Rejected",
        "Offer",
    ]

    if return_status not in allowed_return_statuses:
        return_status = "All"

    flash("Application deleted.", "success")

    return redirect(
        url_for("applications", status=return_status)
    )


@app.route("/save", methods=["POST"])
@login_required
def save():
    """Save an internship to the user's tracker."""

    external_id = request.form.get("external_id")
    title = request.form.get("title")
    company = request.form.get("company")
    location = request.form.get("location")
    description = request.form.get("description")
    apply_url = request.form.get("apply_url")
    posted_at = request.form.get("posted_at")

    user_id = session["user_id"]

    if not external_id or not title or not company:
        return apology("missing required job information", 400)

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
            posted_at,
        )

    except ValueError:
        flash("This internship is already saved.", "warning")
        return redirect(url_for("applications"))

    flash("Internship saved to your tracker.", "success")
    return redirect(url_for("applications"))


@app.route("/applications")
@login_required
def applications():
    """Display and filter the user's saved applications."""

    selected_status = request.args.get("status", "All")

    allowed_statuses = [
        "All",
        "Saved",
        "Applied",
        "Online Assessment",
        "Interview",
        "Rejected",
        "Offer",
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
            session["user_id"],
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
            selected_status,
        )

    return render_template(
        "applications.html",
        applications=saved_jobs,
        selected_status=selected_status,
    )


@app.route("/discover")
@login_required
def discover():
    """Search for internships using the Adzuna API."""

    jobs = []

    keyword = request.args.get("keyword", "").strip()
    location = request.args.get("location", "").strip()
    page = request.args.get("page", 1, type=int)

    if page < 1:
        page = 1

    results_per_page = 10
    total_results = 0
    total_pages = 0
    error_message = None
    searched = bool(keyword)

    if searched:
        try:
            jobs, total_results = search_jobs(
                keyword,
                location,
                page,
            )

            total_pages = math.ceil(
                total_results / results_per_page
            )

        except JobSearchError as error:
            error_message = str(error)

    return render_template(
        "discover.html",
        jobs=jobs,
        keyword=keyword,
        location=location,
        searched=searched,
        page=page,
        total_pages=total_pages,
        total_results=total_results,
        error_message=error_message,
    )


@app.route("/")
@login_required
def index():
    """Display dashboard statistics."""

    user_id = session["user_id"]

    result = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM applications
        WHERE user_id = ?
        """,
        user_id,
    )

    total = result[0]["count"]

    status_rows = db.execute(
        """
        SELECT status, COUNT(*) AS count
        FROM applications
        WHERE user_id = ?
        GROUP BY status
        """,
        user_id,
    )

    status_counts = {
        "Applied": 0,
        "Interview": 0,
        "Rejected": 0,
        "Offer": 0,
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
        user_id,
    )

    return render_template(
        "index.html",
        total=total,
        applied=status_counts["Applied"],
        interviewing=status_counts["Interview"],
        rejected=status_counts["Rejected"],
        offers=status_counts["Offer"],
        recent_applications=recent_applications,
    )


@app.after_request
def after_request(response):
    """Ensure responses are not cached."""

    response.headers["Cache-Control"] = (
        "no-cache, no-store, must-revalidate"
    )
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"

    return response


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log a user in."""

    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            return apology("must provide username", 403)

        if not password:
            return apology("must provide password", 403)

        rows = db.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            username,
        )

        if (
            len(rows) != 1
            or not check_password_hash(rows[0]["hash"], password)
        ):
            return apology(
                "invalid username and/or password",
                403,
            )

        session["user_id"] = rows[0]["id"]

        return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Log the user out."""

    session.clear()

    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register a new user."""

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("must provide username", 400)

        if not password:
            return apology("must provide password", 400)

        if not confirmation:
            return apology(
                "must provide the confirmed password",
                400,
            )

        if password != confirmation:
            return apology("passwords must match", 400)

        hashed_password = generate_password_hash(password)

        try:
            db.execute(
                """
                INSERT INTO users (username, hash)
                VALUES (?, ?)
                """,
                username,
                hashed_password,
            )

        except ValueError:
            return apology("username already exists", 400)

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")