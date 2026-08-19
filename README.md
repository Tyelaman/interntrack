# InternTrack

InternTrack is a full-stack internship discovery and application tracking web app built with Flask and PostgreSQL.

Users can search for internship opportunities, save jobs, track application progress, add deadlines and notes, and view their application activity from a dashboard.

**Live Demo:** https://interntrack-pearl.vercel.app

## Features

- User registration and login
- Secure password hashing and cookie-based sessions
- Internship search using the Adzuna API
- Keyword and location-based search
- Paginated search results
- Save internship listings
- Track application status:
  - Saved
  - Applied
  - Online Assessment
  - Interview
  - Rejected
  - Offer
- Add application deadlines
- Add personal notes
- Filter applications by status
- Dashboard with application statistics
- Upcoming deadline tracking
- Duplicate application prevention
- CSRF protection and server-side validation
- User-specific authorization for application updates and deletion
- PostgreSQL production database
- Automated testing and CI

## Tech Stack

### Backend
- Python
- Flask
- CS50 SQL
- SQLAlchemy
- PostgreSQL
- SQLite

### Frontend
- HTML
- CSS
- Bootstrap
- JavaScript
- Jinja

### APIs & Services
- Adzuna Jobs API
- Neon PostgreSQL
- Vercel

### Testing & Development
- pytest
- Ruff
- Git
- GitHub
- GitHub Actions

## Architecture

InternTrack uses different databases depending on the environment:

- **Local development and automated tests:** SQLite
- **Production:** PostgreSQL hosted on Neon

The application reads the database connection from `DATABASE_URL`, allowing the same Flask application to work with both environments.

Internship listings are retrieved from the Adzuna API and normalized before being displayed to users.

## Project Structure

```text
interntrack/
├── .github/
│   └── workflows/
│       └── ci.yml
├── public/
│   └── styles.css
├── templates/
│   ├── apology.html
│   ├── applications.html
│   ├── discover.html
│   ├── index.html
│   ├── layout.html
│   ├── login.html
│   └── register.html
├── tests/
│   ├── conftest.py
│   ├── test_app.py
│   └── test_jobs.py
├── app.py
├── helpers.py
├── jobs.py
├── migrate_deadline.py
├── requirements.txt
├── requirements-dev.txt
├── ruff.toml
├── schema.sql
└── schema_postgres.sql

Local Setup
1. Clone the repository
git clone https://github.com/Tyelaman/interntrack.git
cd interntrack
2. Create a virtual environment
python -m venv .venv

On Windows PowerShell:

.\.venv\Scripts\Activate.ps1
3. Install dependencies
python -m pip install -r requirements.txt

For development and testing:

python -m pip install -r requirements-dev.txt
4. Configure environment variables

Create a .env file in the project root:

SECRET_KEY=your_secret_key
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key

DATABASE_URL is optional locally. If it is not provided, InternTrack uses:

sqlite:///interntrack.db

To use PostgreSQL instead:

DATABASE_URL=your_postgresql_connection_string
5. Initialize the local SQLite database
python -m sqlite3 interntrack.db

Then run:

.read schema.sql
.quit
6. Start the application
python -m flask --app app run --debug

Open:

http://127.0.0.1:5000
Testing

Run the automated test suite:

python -m pytest

Run linting:

ruff check .

Check formatting:

ruff format --check .

GitHub Actions automatically runs these checks for pushes and pull requests.

Security

InternTrack includes several security protections:

Passwords are hashed using Werkzeug
CSRF protection is enabled with Flask-WTF
Database queries use parameterized SQL
Application records are scoped to the authenticated user
Input lengths and URLs are validated server-side
Authentication sessions use signed cookies
Production cookies are HTTPS-only
API keys and database credentials are stored in environment variables rather than source code
Database Design

The application contains two primary tables:

users

Stores:

User ID
Unique username
Password hash
applications

Stores:

User ID
External job ID
Job source
Title
Company
Location
Description
Application URL
Posting date
Application status
Application deadline
Personal notes
Saved timestamp

A unique constraint on:

(user_id, source, external_id)

prevents the same user from saving the same job more than once.

Deployment

InternTrack is deployed on Vercel with PostgreSQL hosted on Neon.

Production configuration uses environment variables for:

SECRET_KEY
ADZUNA_APP_ID
ADZUNA_APP_KEY
DATABASE_URL
Screenshots

Screenshots will be added soon.

Acknowledgements

Internship listing data is provided by the Adzuna API.

InternTrack originally began as a CS50x final project and was later expanded with PostgreSQL, automated testing, CI, security improvements, application deadlines, notes, and production deployment.
