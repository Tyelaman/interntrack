# InternTrack

InternTrack is a full-stack internship discovery and application tracking web app built with Flask and PostgreSQL.

Users can search for internships, save opportunities, track application progress, add deadlines and notes, and view their activity from a dashboard.

**Live Demo:** https://interntrack-pearl.vercel.app

## Features

- User registration and login
- Internship search through the Adzuna API
- Keyword and location-based search
- Paginated search results
- Save internship listings
- Track application status
- Add application deadlines and notes
- Filter applications by status
- Dashboard with application statistics and upcoming deadlines
- Duplicate application prevention
- CSRF protection and server-side validation
- User-specific authorization
- Automated tests and CI

## Tech Stack

**Backend:** Python, Flask, PostgreSQL, SQLite, CS50 SQL, SQLAlchemy  
**Frontend:** HTML, CSS, Bootstrap, JavaScript, Jinja  
**Services:** Adzuna API, Neon PostgreSQL, Vercel  
**Testing & Tools:** pytest, Ruff, Git, GitHub, GitHub Actions

## Architecture

InternTrack uses:

- **SQLite** for local development and automated tests
- **PostgreSQL on Neon** for production
- **Vercel** for deployment
- **Adzuna API** for internship listings

The application reads the database connection from `DATABASE_URL`, allowing the same Flask application to work with both SQLite and PostgreSQL.

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
```

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/Tyelaman/interntrack.git
cd interntrack
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

For development and testing:

```bash
python -m pip install -r requirements-dev.txt
```

### 4. Configure environment variables

Create a `.env` file:

```env
SECRET_KEY=your_secret_key
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
```

InternTrack uses SQLite locally by default.

To use PostgreSQL instead:

```env
DATABASE_URL=your_postgresql_connection_string
```

### 5. Initialize SQLite

```bash
python -m sqlite3 interntrack.db
```

Then:

```sql
.read schema.sql
.quit
```

### 6. Run InternTrack

```bash
python -m flask --app app run --debug
```

Open:

```text
http://127.0.0.1:5000
```

## Testing

Run the test suite:

```bash
python -m pytest
```

Run Ruff:

```bash
ruff check .
ruff format --check .
```

GitHub Actions automatically runs the test and quality checks on pushes and pull requests.

## Security

InternTrack includes:

- Werkzeug password hashing
- Flask-WTF CSRF protection
- Parameterized SQL queries
- User-scoped database operations
- Server-side input validation
- Signed cookie-based sessions
- HTTPS-only session cookies in production
- Environment variables for secrets and credentials

## Database

InternTrack uses two main tables:

### `users`

Stores user IDs, usernames, and password hashes.

### `applications`

Stores internship information including:

- Company and title
- Location and job URL
- Application status
- Deadline
- Notes
- Posting and saved dates

The combination of:

```text
(user_id, source, external_id)
```

is unique, preventing a user from saving the same internship multiple times.

## Deployment

InternTrack is deployed on **Vercel** with its production PostgreSQL database hosted on **Neon**.

Production environment variables:

```text
SECRET_KEY
ADZUNA_APP_ID
ADZUNA_APP_KEY
DATABASE_URL
```

## Screenshots

Screenshots coming soon.

## Acknowledgements

Internship listing data is provided by the Adzuna API.

InternTrack began as a CS50x final project and was later expanded with PostgreSQL, automated testing, CI, security improvements, application deadlines, notes, and production deployment.
