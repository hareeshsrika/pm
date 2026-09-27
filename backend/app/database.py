from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Iterator


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS boards (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "columns" (
    id TEXT PRIMARY KEY,
    board_id TEXT NOT NULL,
    title TEXT NOT NULL,
    position INTEGER NOT NULL,
    UNIQUE (board_id, position),
    UNIQUE (board_id, id),
    FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cards (
    id TEXT PRIMARY KEY,
    board_id TEXT NOT NULL,
    column_id TEXT NOT NULL,
    title TEXT NOT NULL,
    details TEXT NOT NULL,
    position INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (column_id, position),
    UNIQUE (board_id, id),
    FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE,
    FOREIGN KEY (board_id, column_id)
        REFERENCES "columns"(board_id, id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_columns_board_position
    ON "columns" (board_id, position);

CREATE INDEX IF NOT EXISTS idx_cards_column_position
    ON cards (column_id, position);
"""

INITIAL_COLUMNS = [
    ("col-backlog", "Backlog"),
    ("col-discovery", "Discovery"),
    ("col-progress", "In Progress"),
    ("col-review", "Review"),
    ("col-done", "Done"),
]

INITIAL_CARDS = [
    ("card-1", "col-backlog", "Align roadmap themes", "Draft quarterly themes with impact statements and metrics."),
    ("card-2", "col-backlog", "Gather customer signals", "Review support tags, sales notes, and churn feedback."),
    ("card-3", "col-discovery", "Prototype analytics view", "Sketch initial dashboard layout and key drill-downs."),
    ("card-4", "col-progress", "Refine status language", "Standardize column labels and tone across the board."),
    ("card-5", "col-progress", "Design card layout", "Add hierarchy and spacing for scanning dense lists."),
    ("card-6", "col-review", "QA micro-interactions", "Verify hover, focus, and loading states."),
    ("card-7", "col-done", "Ship marketing page", "Final copy approved and asset pack delivered."),
    ("card-8", "col-done", "Close onboarding sprint", "Document release notes and share internally."),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@contextmanager
def connection(database_path: Path) -> Iterator[sqlite3.Connection]:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    database = sqlite3.connect(database_path)
    database.row_factory = sqlite3.Row
    database.execute("PRAGMA foreign_keys = ON")
    try:
        yield database
    except Exception:
        database.rollback()
        raise
    else:
        database.commit()
    finally:
        database.close()


def initialize_database(database_path: Path) -> None:
    with connection(database_path) as database:
        database.executescript(SCHEMA)
        user = database.execute(
            "SELECT id FROM users WHERE username = ?", ("user",)
        ).fetchone()
        if user is not None:
            return

        timestamp = utc_now()
        user_id = "user-1"
        board_id = "board-user-1"
        database.execute(
            "INSERT INTO users (id, username, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (user_id, "user", None, timestamp),
        )
        database.execute(
            "INSERT INTO boards (id, user_id, name, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (board_id, user_id, "My Project", timestamp, timestamp),
        )
        database.executemany(
            "INSERT INTO \"columns\" (id, board_id, title, position) VALUES (?, ?, ?, ?)",
            [(column_id, board_id, title, position) for position, (column_id, title) in enumerate(INITIAL_COLUMNS)],
        )
        card_positions: dict[str, int] = {}
        card_rows = []
        for card_id, column_id, title, details in INITIAL_CARDS:
            position = card_positions.get(column_id, 0)
            card_positions[column_id] = position + 1
            card_rows.append(
                (card_id, board_id, column_id, title, details, position, timestamp, timestamp)
            )
        database.executemany(
            "INSERT INTO cards (id, board_id, column_id, title, details, position, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            card_rows,
        )


def find_user_id(database_path: Path, username: str) -> str | None:
    with connection(database_path) as database:
        row = database.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        return row["id"] if row else None
