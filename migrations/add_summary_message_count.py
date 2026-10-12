
import sqlite3
from pathlib import Path

DATABASE_PATH = Path("personal_ai.db")


def migrate():
    connection = sqlite3.connect(DATABASE_PATH)

    try:
        columns = connection.execute(
            "PRAGMA table_info(conversation_summaries)"
        ).fetchall()

        column_names = {column[1] for column in columns}

        if "last_summarized_message_count" not in column_names:
            connection.execute(
                """
                ALTER TABLE conversation_summaries
                ADD COLUMN last_summarized_message_count
                INTEGER NOT NULL DEFAULT 0
                """
            )
            connection.commit()
            print("Migration successful: column added.")
        else:
            print("Migration skipped: column already exists.")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    migrate()
