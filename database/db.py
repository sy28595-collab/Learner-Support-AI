import sqlite3
from pathlib import Path


# Database path
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "support.db"

SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"


# Database connection
def get_connection():

    connection = sqlite3.connect(DB_PATH)

    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# Initialize database
def init_db():

    with get_connection() as connection:

        schema = SCHEMA_PATH.read_text(encoding="utf-8")

        connection.executescript(schema)

    print("Database initialized successfully!")


# Check database tables
def get_tables():

    with get_connection() as connection:

        result = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

    return [row["name"] for row in result]