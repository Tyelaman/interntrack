from datetime import date, datetime
import math
import os
from urllib.parse import urlparse

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
from flask_wtf.csrf import CSRFError, CSRFProtect
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
app.config["SESSION_FILE_DIR"] = os.getenv(
    "SESSION_FILE_DIR",
    "session_files",
)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
Session(app)
csrf = CSRFProtect(app)

# Configure CS50 Library to use SQLite
db = SQL(os.getenv("DATABASE_URL", "sqlite:///interntrack.db"))
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
            parsed_date = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return str(value)

    return f"{parsed_date.strftime('%b')} {parsed_date.day}, {parsed_date.year}"


def add_deadline_metadata(applications):
    """Add readable deadline information to application records."""

    today = date.today()

    for application in applications:
        deadline_value = application.get("application_deadline")

        application["deadline_input_value"] = ""
        application["deadline_label"] = "Unknown"
        application["deadline_class"] = "deadline-unknown"

        if not deadline_value:
            continue

        try:
            if isinstance(deadline_value, datetime):
                deadline_date = deadline_value.date()
            elif isinstance(deadline_value, date):
                deadline_date = deadline_value
            else:
                deadline_date = datetime.strptime(
                    str(deadline_value),
                    "%Y-%m-%d",
                ).date()
        except ValueError:
            continue

        application["deadline_input_value"] = deadline_date.isoformat()

        days_remaining = (deadline_date - today).days

        if days_remaining < 0:
            application["deadline_label"] = "Deadline passed"
            application["deadline_class"] = "deadline-passed"
        elif days_remaining == 0:
            application["deadline_label"] = "Due today"
            application["deadline_class"] = "deadline-today"
        elif days_remaining == 1:
            application["deadline_label"] = "Due tomorrow"
            application["deadline_class"] = "deadline-today"
        else:
            application["deadline_label"] = f"Due in {days_remaining} days"
            application["deadline_class"] = "deadline-upcoming"

    return applications


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

    return redirect(url_for("applications", status=return_status))


@app.route("/update-details", methods=["POST"])
@login_required
def update_details():
    """Update a saved application's deadline and personal notes."""

    application_id = request.form.get("application_id")
    deadline_input = request.form.get(
        "application_deadline",
        "",
    ).strip()
    notes = request.form.get("notes", "").strip()
    return_status = request.form.get("return_status", "All")

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

    if len(notes) > 1000:
        return apology(
            "notes must be 1000 characters or fewer",
            400,
        )

    application_deadline = None

    if deadline_input:
        try:
            application_deadline = (
                datetime.strptime(
                    deadline_input,
                    "%Y-%m-%d",
                )
                .date()
                .isoformat()
            )
        except ValueError:
            return apology(
                "deadline must be a valid date",
                400,
            )

    if return_status not in allowed_status_filters:
        return_status = "All"

    db.execute(
        """
        UPDATE applications
        SET application_deadline = ?, notes = ?
        WHERE id = ? AND user_id = ?
        """,
        application_deadline,
        notes,
        application_id,
        session["user_id"],
    )

    flash("Application details updated.", "success")

    return redirect(url_for("applications", status=return_status))


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

    return redirect(url_for("applications", status=return_status))


@app.route("/save", methods=["POST"])
@login_required
def save():
    """Save an internship to the user's tracker."""

    external_id = request.form.get("external_id", "").strip()
    title = request.form.get("title", "").strip()
    company = request.form.get("company", "").strip()
    location = request.form.get("location", "").strip() or None
    description = request.form.get("description", "").strip() or None
    apply_url = request.form.get("apply_url", "").strip() or None
    posted_at = request.form.get("posted_at", "").strip() or None

    user_id = session["user_id"]

    if not external_id or not title or not company:
        return apology("missing required job information", 400)

    maximum_lengths = {
        "external ID": (external_id, 255),
        "title": (title, 500),
        "company": (company, 255),
        "location": (location, 500),
        "description": (description, 20000),
        "apply URL": (apply_url, 2048),
        "posted date": (posted_at, 100),
    }

    for field_name, (value, maximum) in maximum_lengths.items():
        if value is not None and len(value) > maximum:
            return apology(
                f"{field_name} must be {maximum} characters or fewer",
                400,
            )

    if apply_url:
        parsed_apply_url = urlparse(apply_url)
        if (
            parsed_apply_url.scheme.lower() not in {"http", "https"}
            or not parsed_apply_url.netloc
        ):
            return apology(
                "job posting URL must use HTTP or HTTPS",
                400,
            )

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

    saved_jobs = add_deadline_metadata(saved_jobs)

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

            total_pages = math.ceil(total_results / results_per_page)

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
    upcoming_deadlines = db.execute(
        """
        SELECT
            id,
            title,
            company,
            status,
            application_deadline
        FROM applications
        WHERE
            user_id = ?
            AND application_deadline IS NOT NULL
            AND application_deadline >= ?
        ORDER BY application_deadline ASC
        LIMIT 5
        """,
        user_id,
        date.today().isoformat(),
    )

    upcoming_deadlines = add_deadline_metadata(upcoming_deadlines)

    return render_template(
        "index.html",
        total=total,
        applied=status_counts["Applied"],
        interviewing=status_counts["Interview"],
        rejected=status_counts["Rejected"],
        offers=status_counts["Offer"],
        recent_applications=recent_applications,
        upcoming_deadlines=upcoming_deadlines,
    )


@app.after_request
def after_request(response):
    """Ensure responses are not cached."""

    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"

    return response


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log a user in."""

    session.clear()

    if request.method == "POST":
        username = request.form.get("username", "").strip()
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

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
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
        username = request.form.get("username", "").strip()
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("must provide username", 400)

        if not 3 <= len(username) <= 50:
            return apology(
                "username must be between 3 and 50 characters",
                400,
            )

        if not password:
            return apology("must provide password", 400)

        if len(password) < 8:
            return apology(
                "password must be at least 8 characters",
                400,
            )

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


@app.errorhandler(CSRFError)
def handle_csrf_error(error):
    """Show a friendly response when CSRF validation fails."""

    return apology(
        "your form expired or could not be verified; please try again",
        400,
    )


@app.errorhandler(404)
def not_found(error):
    """Show a friendly response for unknown pages."""

    return apology("page not found", 404)


@app.errorhandler(500)
def internal_error(error):
    """Show a friendly response for unexpected server errors."""

    return apology("something went wrong; please try again later", 500)
