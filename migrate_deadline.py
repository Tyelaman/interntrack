import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).with_name("interntrack.db")


def main():
    """Add the deadline column without deleting existing data."""

    with sqlite3.connect(DATABASE_PATH) as connection:
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(applications)"
            )
        }

        if "application_deadline" in columns:
            print("application_deadline already exists.")
            return

        connection.execute(
            """
            ALTER TABLE applications
            ADD COLUMN application_deadline DATE
            """
        )

        print("Added application_deadline column.")


if __name__ == "__main__":
    main()