# InternTrack

## Video URL: https://youtu.be/M6wjNmQahzQ
## Description

InternTrack is a Flask web application that helps users discover internships and organize the positions they are considering or applying to. The project combines internship search with a personal application tracker so that users do not need to search on one website and manage their progress somewhere else.

Users can create an account, search for internships by keyword and optional location, save interesting listings, update each application's status, filter their saved applications, and view a dashboard summarizing their progress. Internship listings are retrieved from the Adzuna API and normalized into a consistent structure before being displayed by the application.

InternTrack was created as a CS50x final project. It uses concepts covered throughout the course, including Python, Flask, SQL, authentication, sessions, HTML, CSS, Jinja templates, HTTP requests, external APIs, form validation, and CRUD database operations.

## Features

### User accounts

Users can register with a unique username and password. Passwords are not stored directly; they are hashed using Werkzeug before being saved. Flask sessions keep users logged in, and protected routes require authentication.

Each saved internship belongs to one specific user. Database queries include the logged-in user's ID so that one user cannot view, update, or delete another user's applications.

### Internship discovery

The Discover page lets users search by:

- Keyword, such as `software engineer intern`
- Optional location, such as `Boston, MA`

The server sends the search request to the Adzuna API. The API response is normalized in `jobs.py` so every result has predictable fields such as title, company, location, description, application URL, external ID, and posting date.

### Saving internships

Users can save an internship from the Discover page. The application stores the job in SQLite and associates it with the current user's ID.

A database uniqueness constraint prevents the same user from saving the same Adzuna listing more than once. Different users can still save the same listing independently.

### Application tracking

Saved internships appear on the Applications page. Users can:

- Add, update, or clear an application deadline
- Store personal notes for each application
- See whether a deadline is upcoming, due today, or passed
- View the nearest upcoming deadlines on the dashboard

Supported statuses are:

- Saved
- Applied
- Online Assessment
- Interview
- Rejected
- Offer

All update and delete queries verify both the application ID and the current user's ID.

### Dashboard

The dashboard also displays up to five upcoming application
deadlines, ordered from nearest to farthest.

- Total saved applications
- Number marked Applied
- Number marked Interview
- Number marked Rejected
- Number marked Offer
- Three most recently saved applications

The dashboard data is calculated from the logged-in user's records in SQLite.

## Technologies

- Python
- Flask
- Flask-Session
- SQLite
- CS50 SQL library
- HTML
- CSS
- Bootstrap
- Jinja
- Requests
- python-dotenv
- Werkzeug
- Adzuna API

## Project structure

```text
interntrack/
├── app.py
├── jobs.py
├── helpers.py
├── migrate_deadline.py
├── requirements.txt
├── schema.sql
├── .env
├── .gitignore
├── static/
│   └── styles.css
└── templates/
    ├── layout.html
    ├── index.html
    ├── discover.html
    ├── applications.html
    ├── login.html
    ├── register.html
    └── apology.html
```

### `app.py`

`app.py` contains the Flask application and its routes. It configures sessions and the SQLite database, handles registration and login, saves jobs, updates statuses, deletes applications, filters applications, and calculates dashboard statistics.

### `jobs.py`

`jobs.py` handles communication with the Adzuna API. It loads API credentials from environment variables, sends search requests, checks the HTTP response, and converts the raw API results into dictionaries with a consistent format for the templates.

### `helpers.py`

`helpers.py` contains shared helper functions, including the authentication decorator used to protect routes and the apology function used to display errors.

### `migrate_deadline.py`

`migrate_deadline.py` safely adds the nullable
`application_deadline` column to an existing SQLite database without
deleting current users or applications. It can be run multiple time

### Templates

The files in `templates/` define the user interface:

- `layout.html` contains the shared navigation bar and page structure.
- `index.html` displays the dashboard.
- `discover.html` contains the internship search form and search results.
- `applications.html` displays saved applications, filters, status controls, and delete controls.
- `login.html` and `register.html` contain the authentication forms.
- `apology.html` displays validation and application errors.

### `static/styles.css`

This file contains custom styling that supplements Bootstrap.

### `schema.sql`

`schema.sql` defines the `users` and `applications` tables, their constraints, and the application index. The applications table uses a foreign key to connect each saved internship to a user.

## Database design

The `users` table stores:

- User ID
- Unique username
- Password hash

The `applications` table stores:

- User ID
- Source and external job ID
- Title
- Company
- Location
- Description
- Application URL
- Original posting date
- Application status
- Time the listing was saved
- Application deadline, stored as a nullable date
- Personal notes

The combination of `user_id`, `source`, and `external_id` is unique. This prevents duplicate saves for one user while allowing separate users to track the same listing.

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Tyelaman/interntrack.git
cd interntrack
```

2. Create a virtual environment:

```bash
python -m venv .venv
```

3. Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

4. Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

5. Create a `.env` file in the project root:

```env
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
```

6. Initialize the database:

```bash
python -m sqlite3 interntrack.db
```

Then run:

```sql
.read schema.sql
.quit
```

7. Start the Flask development server:

```bash
flask run
```

8. Open the local address shown in the terminal, usually `http://127.0.0.1:5000`.

## Security and design decisions

API credentials are stored in `.env` rather than directly in the source code. The `.env` file must never be committed to GitHub.

Passwords are hashed before storage. Routes that display or modify personal application data require authentication. Update and delete queries include `user_id` checks to prevent users from changing records they do not own.

Hidden form inputs are used to submit normalized job information from the Discover page, but the user ID is never accepted from the browser. It is always read from the authenticated session.

The application uses parameterized SQL queries with `?` placeholders instead of constructing SQL commands from user input.

## Future improvements

Possible future additions include:

- Notes for each application
- Search pagination
- Better posting-date formatting
- More detailed dashboard statistics
- Automatic filtering of non-internship roles
- Improved API error messages
- Deployment to a public hosting service

## Acknowledgements

Internship listing data is provided by the Adzuna API. The project was built as a CS50x final project.