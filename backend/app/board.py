from pathlib import Path
import sqlite3
from uuid import uuid4

from pydantic import BaseModel, Field

from .database import connection, utc_now


class BoardNotFoundError(Exception):
    pass


class BoardValidationError(Exception):
    pass


class ColumnRename(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class CardCreate(BaseModel):
    column_id: str
    title: str = Field(min_length=1, max_length=200)
    details: str = Field(default="", max_length=5000)


class CardUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    details: str = Field(default="", max_length=5000)


class CardMove(BaseModel):
    column_id: str
    position: int = Field(default=0, ge=0)


def _find_board_id(database: sqlite3.Connection, user_id: str) -> str:
    row = database.execute(
        "SELECT id FROM boards WHERE user_id = ?", (user_id,)
    ).fetchone()
    if row is None:
        raise BoardNotFoundError("Board not found")
    return row["id"]


def _load_board(database: sqlite3.Connection, board_id: str) -> dict:
    board = database.execute(
        "SELECT id FROM boards WHERE id = ?", (board_id,)
    ).fetchone()
    if board is None:
        raise BoardNotFoundError("Board not found")

    columns = database.execute(
        "SELECT id, title FROM \"columns\" WHERE board_id = ? ORDER BY position",
        (board_id,),
    ).fetchall()
    cards = database.execute(
        "SELECT id, column_id, title, details FROM cards WHERE board_id = ? ORDER BY column_id, position",
        (board_id,),
    ).fetchall()

    card_map = {
        row["id"]: {
            "id": row["id"],
            "title": row["title"],
            "details": row["details"],
        }
        for row in cards
    }
    card_ids_by_column: dict[str, list[str]] = {}
    for row in cards:
        card_ids_by_column.setdefault(row["column_id"], []).append(row["id"])

    return {
        "id": board_id,
        "columns": [
            {
                "id": row["id"],
                "title": row["title"],
                "cardIds": card_ids_by_column.get(row["id"], []),
            }
            for row in columns
        ],
        "cards": card_map,
    }


def get_board(database_path: Path, user_id: str) -> dict:
    with connection(database_path) as database:
        return _load_board(database, _find_board_id(database, user_id))


def rename_column(database_path: Path, user_id: str, column_id: str, title: str) -> dict:
    title = title.strip()
    if not title:
        raise BoardValidationError("Column title cannot be empty")

    with connection(database_path) as database:
        board_id = _find_board_id(database, user_id)
        result = database.execute(
            "UPDATE \"columns\" SET title = ? WHERE id = ? AND board_id = ?",
            (title, column_id, board_id),
        )
        if result.rowcount == 0:
            raise BoardNotFoundError("Column not found")
        database.execute(
            "UPDATE boards SET updated_at = ? WHERE id = ?",
            (utc_now(), board_id),
        )
        return _load_board(database, board_id)


def create_card(database_path: Path, user_id: str, card: CardCreate) -> dict:
    title = card.title.strip()
    details = card.details.strip()
    if not title:
        raise BoardValidationError("Card title cannot be empty")

    with connection(database_path) as database:
        board_id = _find_board_id(database, user_id)
        column = database.execute(
            "SELECT id FROM \"columns\" WHERE id = ? AND board_id = ?",
            (card.column_id, board_id),
        ).fetchone()
        if column is None:
            raise BoardNotFoundError("Column not found")
        position = database.execute(
            "SELECT COALESCE(MAX(position) + 1, 0) AS next_position FROM cards WHERE column_id = ?",
            (card.column_id,),
        ).fetchone()["next_position"]
        timestamp = utc_now()
        database.execute(
            "INSERT INTO cards (id, board_id, column_id, title, details, position, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (f"card-{uuid4().hex[:12]}", board_id, card.column_id, title, details, position, timestamp, timestamp),
        )
        database.execute(
            "UPDATE boards SET updated_at = ? WHERE id = ?",
            (timestamp, board_id),
        )
        return _load_board(database, board_id)


def update_card(database_path: Path, user_id: str, card_id: str, card: CardUpdate) -> dict:
    title = card.title.strip()
    details = card.details.strip()
    if not title:
        raise BoardValidationError("Card title cannot be empty")

    with connection(database_path) as database:
        board_id = _find_board_id(database, user_id)
        result = database.execute(
            "UPDATE cards SET title = ?, details = ?, updated_at = ? WHERE id = ? AND board_id = ?",
            (title, details, utc_now(), card_id, board_id),
        )
        if result.rowcount == 0:
            raise BoardNotFoundError("Card not found")
        database.execute(
            "UPDATE boards SET updated_at = ? WHERE id = ?",
            (utc_now(), board_id),
        )
        return _load_board(database, board_id)


def delete_card(database_path: Path, user_id: str, card_id: str) -> dict:
    with connection(database_path) as database:
        board_id = _find_board_id(database, user_id)
        card = database.execute(
            "SELECT column_id FROM cards WHERE id = ? AND board_id = ?",
            (card_id, board_id),
        ).fetchone()
        if card is None:
            raise BoardNotFoundError("Card not found")
        column_id = card["column_id"]
        database.execute("DELETE FROM cards WHERE id = ?", (card_id,))
        _normalize_column(database, column_id)
        database.execute(
            "UPDATE boards SET updated_at = ? WHERE id = ?",
            (utc_now(), board_id),
        )
        return _load_board(database, board_id)


def move_card(database_path: Path, user_id: str, card_id: str, move: CardMove) -> dict:
    with connection(database_path) as database:
        board_id = _find_board_id(database, user_id)
        card = database.execute(
            "SELECT column_id FROM cards WHERE id = ? AND board_id = ?",
            (card_id, board_id),
        ).fetchone()
        if card is None:
            raise BoardNotFoundError("Card not found")
        target = database.execute(
            "SELECT id FROM \"columns\" WHERE id = ? AND board_id = ?",
            (move.column_id, board_id),
        ).fetchone()
        if target is None:
            raise BoardNotFoundError("Column not found")

        source_column_id = card["column_id"]
        source_ids = [
            row["id"]
            for row in database.execute(
                "SELECT id FROM cards WHERE column_id = ? ORDER BY position",
                (source_column_id,),
            ).fetchall()
        ]
        if source_column_id == move.column_id:
            source_ids.remove(card_id)
            source_ids.insert(min(move.position, len(source_ids)), card_id)
            _rewrite_positions(database, source_column_id, source_ids)
        else:
            target_ids = [
                row["id"]
                for row in database.execute(
                    "SELECT id FROM cards WHERE column_id = ? ORDER BY position",
                    (move.column_id,),
                ).fetchall()
            ]
            source_ids.remove(card_id)
            target_ids.insert(min(move.position, len(target_ids)), card_id)
            _rewrite_positions(database, source_column_id, source_ids)
            database.execute(
                "UPDATE cards SET column_id = ? WHERE id = ?",
                (move.column_id, card_id),
            )
            _rewrite_positions(database, move.column_id, target_ids)

        database.execute(
            "UPDATE boards SET updated_at = ? WHERE id = ?",
            (utc_now(), board_id),
        )
        return _load_board(database, board_id)


def _normalize_column(database: sqlite3.Connection, column_id: str) -> None:
    ids = [
        row["id"]
        for row in database.execute(
            "SELECT id FROM cards WHERE column_id = ? ORDER BY position",
            (column_id,),
        ).fetchall()
    ]
    _rewrite_positions(database, column_id, ids)


def _rewrite_positions(
    database: sqlite3.Connection, column_id: str, card_ids: list[str]
) -> None:
    # Stage rows at distinct negative positions before assigning their final order.
    database.execute(
        "UPDATE cards SET position = -1000000000 - rowid WHERE column_id = ?",
        (column_id,),
    )
    for position, card_id in enumerate(card_ids):
        database.execute(
            "UPDATE cards SET position = ? WHERE id = ?",
            (position, card_id),
        )
