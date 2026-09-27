from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, status
from pydantic import BaseModel
from pydantic import ValidationError
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .board import (
    BoardNotFoundError,
    BoardValidationError,
    CardCreate,
    CardMove,
    CardUpdate,
    ColumnRename,
    create_card,
    delete_card,
    get_board,
    move_card,
    rename_column,
    update_card,
)
from .ai import (
    AssistantResponse,
    ChatRequest,
    apply_board_operations,
    build_messages,
    complete_incomplete_reply,
    response_schema,
)
from .config import get_settings
from .database import find_user_id, initialize_database
from .openrouter import (
    OpenRouterClient,
    OpenRouterConfigurationError,
    OpenRouterError,
)

BASE_DIR = Path(__file__).resolve().parent
EXAMPLE_STATIC_DIR = BASE_DIR / "static"
FRONTEND_STATIC_DIR = BASE_DIR.parent / "frontend-static"
WEB_DIR = (
    FRONTEND_STATIC_DIR
    if (FRONTEND_STATIC_DIR / "index.html").is_file()
    else EXAMPLE_STATIC_DIR
)

settings = get_settings()
DATABASE_PATH = settings.database_path


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database(DATABASE_PATH)
    yield


app = FastAPI(title="Project Management MVP", lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    session_cookie="pm_session",
    max_age=60 * 60 * 8,
    same_site="lax",
    https_only=False,
)


class LoginRequest(BaseModel):
    username: str
    password: str


def authenticated_user_id(request: Request) -> str:
    username = request.session.get("user_id")
    if not isinstance(username, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    user_id = find_user_id(DATABASE_PATH, username)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user_id


def board_error(error: Exception) -> HTTPException:
    if isinstance(error, BoardNotFoundError):
        return HTTPException(status_code=404, detail=str(error))
    return HTTPException(status_code=400, detail=str(error))


def get_openrouter_client() -> OpenRouterClient:
    return OpenRouterClient(settings.openrouter_api_key)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/hello")
def hello() -> dict[str, str]:
    return {"message": "Hello from the Project Management API"}


@app.post("/api/auth/login")
def login(credentials: LoginRequest, request: Request) -> dict[str, str | bool]:
    if credentials.username != "user" or credentials.password != "password":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    request.session["user_id"] = credentials.username
    return {"authenticated": True, "username": credentials.username}


@app.get("/api/auth/me")
def current_user(request: Request) -> dict[str, str | bool]:
    username = request.session.get("user_id")
    if username != "user":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return {"authenticated": True, "username": username}


@app.post("/api/auth/logout")
def logout(request: Request) -> dict[str, bool]:
    request.session.clear()
    return {"authenticated": False}


@app.post("/api/ai/chat")
def chat(
    payload: ChatRequest,
    request: Request,
    client: OpenRouterClient = Depends(get_openrouter_client),
) -> dict:
    user_id = authenticated_user_id(request)
    try:
        board = get_board(DATABASE_PATH, user_id)
        model_response = client.complete_json(
            build_messages(board, payload),
            response_schema(),
        )
        assistant_response = AssistantResponse.model_validate(model_response)
        updated_board = apply_board_operations(
            DATABASE_PATH, user_id, assistant_response.operations
        )
        return {
            "reply": complete_incomplete_reply(
                updated_board, payload.message, assistant_response.reply
            ),
            "operations": [
                operation.model_dump() for operation in assistant_response.operations
            ],
            "board": updated_board,
        }
    except (OpenRouterConfigurationError, OpenRouterError) as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except ValidationError as error:
        raise HTTPException(
            status_code=502, detail="OpenRouter returned an invalid board response"
        ) from error
    except (BoardNotFoundError, BoardValidationError) as error:
        raise board_error(error) from error
    finally:
        client.close()


@app.get("/api/board")
def read_board(request: Request) -> dict:
    user_id = authenticated_user_id(request)
    try:
        return get_board(DATABASE_PATH, user_id)
    except (BoardNotFoundError, BoardValidationError) as error:
        raise board_error(error) from error


@app.patch("/api/board/columns/{column_id}")
def rename_board_column(
    column_id: str, payload: ColumnRename, request: Request
) -> dict:
    user_id = authenticated_user_id(request)
    try:
        return rename_column(DATABASE_PATH, user_id, column_id, payload.title)
    except (BoardNotFoundError, BoardValidationError) as error:
        raise board_error(error) from error


@app.post("/api/board/cards")
def add_board_card(payload: CardCreate, request: Request) -> dict:
    user_id = authenticated_user_id(request)
    try:
        return create_card(DATABASE_PATH, user_id, payload)
    except (BoardNotFoundError, BoardValidationError) as error:
        raise board_error(error) from error


@app.patch("/api/board/cards/{card_id}")
def edit_board_card(
    card_id: str, payload: CardUpdate, request: Request
) -> dict:
    user_id = authenticated_user_id(request)
    try:
        return update_card(DATABASE_PATH, user_id, card_id, payload)
    except (BoardNotFoundError, BoardValidationError) as error:
        raise board_error(error) from error


@app.delete("/api/board/cards/{card_id}")
def remove_board_card(card_id: str, request: Request) -> dict:
    user_id = authenticated_user_id(request)
    try:
        return delete_card(DATABASE_PATH, user_id, card_id)
    except (BoardNotFoundError, BoardValidationError) as error:
        raise board_error(error) from error


@app.post("/api/board/cards/{card_id}/move")
def move_board_card(
    card_id: str, payload: CardMove, request: Request
) -> dict:
    user_id = authenticated_user_id(request)
    try:
        return move_card(DATABASE_PATH, user_id, card_id, payload)
    except (BoardNotFoundError, BoardValidationError) as error:
        raise board_error(error) from error


# Keep this mount after API routes so `/health` and `/api/*` are handled by FastAPI.
app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="frontend")
