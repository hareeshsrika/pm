from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Runtime settings read from environment variables."""

    database_path: Path
    openrouter_api_key: str | None
    session_secret: str


def get_settings() -> Settings:
    database_path = Path(os.getenv("DATABASE_PATH", "data/project-management.db"))
    api_key = os.getenv("OPENROUTER_API_KEY") or None
    session_secret = os.getenv(
        "SESSION_SECRET", "development-only-session-secret"
    )
    return Settings(
        database_path=database_path,
        openrouter_api_key=api_key,
        session_secret=session_secret,
    )
