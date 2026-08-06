PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,

    source TEXT NOT NULL DEFAULT 'Adzuna',
    external_id TEXT NOT NULL,

    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    description TEXT,
    apply_url TEXT,
    posted_at TEXT,

    status TEXT NOT NULL DEFAULT 'Saved'
        CHECK (
            status IN (
                'Saved',
                'Applied',
                'Online Assessment',
                'Interview',
                'Rejected',
                'Offer'
            )
        ),

    application_deadline DATE,

    notes TEXT NOT NULL DEFAULT '',

    saved_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    UNIQUE (user_id, source, external_id)
);

CREATE INDEX IF NOT EXISTS idx_applications_user_status
ON applications(user_id, status);

CREATE INDEX IF NOT EXISTS idx_applications_user_deadline
ON applications(user_id, application_deadline);