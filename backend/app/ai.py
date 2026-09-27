import json
import sqlite3
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from .board import (
    BoardNotFoundError,
    BoardValidationError,
    _find_board_id,
    _load_board,
    _rewrite_positions,
)
from .database import connection, utc_now


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=5000)


class CreateCardOperation(BaseModel):
    operation: Literal["create_card"]
    column_id: str
    title: str = Field(min_length=1, max_length=200)
    details: str = Field(default="", max_length=5000)


class UpdateCardOperation(BaseModel):
    operation: Literal["update_card"]
    card_id: str
    title: str = Field(min_length=1, max_length=200)
    details: str = Field(default="", max_length=5000)


class MoveCardOperation(BaseModel):
    operation: Literal["move_card"]
    card_id: str
    column_id: str
    position: int = Field(default=0, ge=0)


class RenameColumnOperation(BaseModel):
    operation: Literal["rename_column"]
    column_id: str
    title: str = Field(min_length=1, max_length=200)


class DeleteCardOperation(BaseModel):
    operation: Literal["delete_card"]
    card_id: str


BoardOperation = Annotated[
    CreateCardOperation
    | UpdateCardOperation
    | MoveCardOperation
    | RenameColumnOperation
    | DeleteCardOperation,
    Field(discriminator="operation"),
]


class AssistantResponse(BaseModel):
    reply: str = Field(min_length=1, max_length=5000)
    operations: list[BoardOperation] = Field(default_factory=list, max_length=20)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)


def response_schema() -> dict:
    return AssistantResponse.model_json_schema()


def build_messages(board: dict, request: ChatRequest) -> list[dict[str, str]]:
    board_json = json.dumps(board, separators=(",", ":"))
    messages = [
        {
            "role": "system",
            "content": (
                "You are a project-management board assistant. Answer the user "
                "and propose only valid operations against the supplied board. "
                "Use an empty operations list when no board change is needed. "
                "Never invent card or column IDs."
            ),
        }
    ]
    messages.extend(
        {"role": item.role, "content": item.content} for item in request.history
    )
    messages.append(
        {
            "role": "user",
            "content": f"Current board JSON:\n{board_json}\n\nUser request:\n{request.message}",
        }
    )
    return messages


def _require_column(
    database: sqlite3.Connection, board_id: str, column_id: str
) -> None:
    column = database.execute(
        'SELECT id FROM "columns" WHERE id = ? AND board_id = ?',
        (column_id, board_id),
    ).fetchone()
    if column is None:
        raise BoardNotFoundError("Column not found")


def _require_card(
    database: sqlite3.Connection, board_id: str, card_id: str
) -> sqlite3.Row:
    card = database.execute(
        "SELECT id, column_id FROM cards WHERE id = ? AND board_id = ?",
        (card_id, board_id),
    ).fetchone()
    if card is None:
        raise BoardNotFoundError("Card not found")
    return card


def _move_card(
    database: sqlite3.Connection,
    board_id: str,
    operation: MoveCardOperation,
) -> None:
    card = _require_card(database, board_id, operation.card_id)
    _require_column(database, board_id, operation.column_id)
    source_column_id = card["column_id"]

    source_ids = [
        row["id"]
        for row in database.execute(
            "SELECT id FROM cards WHERE column_id = ? ORDER BY position",
            (source_column_id,),
        ).fetchall()
    ]
    if source_column_id == operation.column_id:
        source_ids.remove(operation.card_id)
        source_ids.insert(min(operation.position, len(source_ids)), operation.card_id)
        _rewrite_positions(database, source_column_id, source_ids)
        return

    target_ids = [
        row["id"]
        for row in database.execute(
            "SELECT id FROM cards WHERE column_id = ? ORDER BY position",
            (operation.column_id,),
        ).fetchall()
    ]
    source_ids.remove(operation.card_id)
    target_ids.insert(min(operation.position, len(target_ids)), operation.card_id)
    _rewrite_positions(database, source_column_id, source_ids)
    database.execute(
        "UPDATE cards SET column_id = ? WHERE id = ?",
        (operation.column_id, operation.card_id),
    )
    _rewrite_positions(database, operation.column_id, target_ids)


def apply_board_operations(
    database_path, user_id: str, operations: list[BoardOperation]
) -> dict:
    with connection(database_path) as database:
        board_id = _find_board_id(database, user_id)
        timestamp = utc_now()

        for operation in operations:
            if isinstance(operation, CreateCardOperation):
                title = operation.title.strip()
                if not title:
                    raise BoardValidationError("Card title cannot be empty")
                _require_column(database, board_id, operation.column_id)
                position = database.execute(
                    "SELECT COALESCE(MAX(position) + 1, 0) AS next_position "
                    "FROM cards WHERE column_id = ?",
                    (operation.column_id,),
                ).fetchone()["next_position"]
                database.execute(
                    "INSERT INTO cards "
                    "(id, board_id, column_id, title, details, position, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        f"card-{uuid4().hex[:12]}",
                        board_id,
                        operation.column_id,
                        title,
                        operation.details.strip(),
                        position,
                        timestamp,
                        timestamp,
                    ),
                )
            elif isinstance(operation, UpdateCardOperation):
                title = operation.title.strip()
                if not title:
                    raise BoardValidationError("Card title cannot be empty")
                _require_card(database, board_id, operation.card_id)
                database.execute(
                    "UPDATE cards SET title = ?, details = ?, updated_at = ? "
                    "WHERE id = ? AND board_id = ?",
                    (
                        title,
                        operation.details.strip(),
                        timestamp,
                        operation.card_id,
                        board_id,
                    ),
                )
            elif isinstance(operation, MoveCardOperation):
                _move_card(database, board_id, operation)
            elif isinstance(operation, RenameColumnOperation):
                title = operation.title.strip()
                if not title:
                    raise BoardValidationError("Column title cannot be empty")
                _require_column(database, board_id, operation.column_id)
                database.execute(
                    'UPDATE "columns" SET title = ? WHERE id = ? AND board_id = ?',
                    (title, operation.column_id, board_id),
                )
            elif isinstance(operation, DeleteCardOperation):
                card = _require_card(database, board_id, operation.card_id)
                database.execute(
                    "DELETE FROM cards WHERE id = ? AND board_id = ?",
                    (operation.card_id, board_id),
                )
                remaining_ids = [
                    row["id"]
                    for row in database.execute(
                        "SELECT id FROM cards WHERE column_id = ? ORDER BY position",
                        (card["column_id"],),
                    ).fetchall()
                ]
                _rewrite_positions(database, card["column_id"], remaining_ids)

        database.execute(
            "UPDATE boards SET updated_at = ? WHERE id = ?", (timestamp, board_id)
        )
        return _load_board(database, board_id)
