import pytest
from fastapi.testclient import TestClient

from app import main
from app.main import FRONTEND_STATIC_DIR, WEB_DIR




@pytest.fixture
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(main, "DATABASE_PATH", tmp_path / "project-management.db")
    with TestClient(main.app) as test_client:
        yield test_client


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_hello_api(client: TestClient) -> None:
    response = client.get("/api/hello")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello from the Project Management API"}


def test_index_serves_example_page(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    expected_marker = (
        "Kanban Studio" if WEB_DIR == FRONTEND_STATIC_DIR else "Project Management MVP"
    )
    assert expected_marker in response.text


def test_login_rejects_invalid_credentials(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid username or password"}


def test_login_creates_session(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )

    assert response.status_code == 200
    assert response.json() == {"authenticated": True, "username": "user"}
    assert "pm_session=" in response.headers["set-cookie"]
    assert "httponly" in response.headers["set-cookie"].lower()

    current_user = client.get("/api/auth/me")
    assert current_user.status_code == 200
    assert current_user.json() == {"authenticated": True, "username": "user"}


def test_logout_clears_session(client: TestClient) -> None:
    client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )

    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    assert response.json() == {"authenticated": False}
    assert client.get("/api/auth/me").status_code == 401


def test_board_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/board")

    assert response.status_code == 401


def test_board_is_seeded_for_authenticated_user(client: TestClient) -> None:
    client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )

    response = client.get("/api/board")

    assert response.status_code == 200
    board = response.json()
    assert len(board["columns"]) == 5
    assert board["columns"][0]["title"] == "Backlog"
    assert board["cards"]["card-1"]["title"] == "Align roadmap themes"


def test_board_mutations_update_cards_and_columns(client: TestClient) -> None:
    client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )

    renamed = client.patch(
        "/api/board/columns/col-backlog",
        json={"title": "Ideas"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["columns"][0]["title"] == "Ideas"

    created = client.post(
        "/api/board/cards",
        json={"column_id": "col-backlog", "title": "New card", "details": "Notes"},
    )
    assert created.status_code == 200
    new_card_id = next(
        card_id
        for card_id in created.json()["cards"]
        if card_id not in {"card-1", "card-2", "card-3", "card-4", "card-5", "card-6", "card-7", "card-8"}
    )

    edited = client.patch(
        f"/api/board/cards/{new_card_id}",
        json={"title": "Edited card", "details": "Updated notes"},
    )
    assert edited.status_code == 200
    assert edited.json()["cards"][new_card_id]["title"] == "Edited card"

    moved = client.post(
        f"/api/board/cards/{new_card_id}/move",
        json={"column_id": "col-review", "position": 0},
    )
    assert moved.status_code == 200
    assert moved.json()["columns"][3]["cardIds"][0] == new_card_id

    deleted = client.delete(f"/api/board/cards/{new_card_id}")
    assert deleted.status_code == 200
    assert new_card_id not in deleted.json()["cards"]

    moved_to_end = client.post(
        "/api/board/cards/card-4/move",
        json={"column_id": "col-review", "position": 1},
    )
    assert moved_to_end.status_code == 200
    assert moved_to_end.json()["columns"][3]["cardIds"][-1] == "card-4"


def test_board_changes_persist_across_client_restart(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    database_path = tmp_path / "project-management.db"
    monkeypatch.setattr(main, "DATABASE_PATH", database_path)

    with TestClient(main.app) as first_client:
        first_client.post(
            "/api/auth/login",
            json={"username": "user", "password": "password"},
        )
        first_client.patch(
            "/api/board/columns/col-review",
            json={"title": "Approval"},
        )

    with TestClient(main.app) as second_client:
        second_client.post(
            "/api/auth/login",
            json={"username": "user", "password": "password"},
        )
        response = second_client.get("/api/board")

    assert response.status_code == 200
    assert response.json()["columns"][3]["title"] == "Approval"


def test_board_rejects_invalid_resources(client: TestClient) -> None:
    client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )

    missing_column = client.patch(
        "/api/board/columns/no-such-column",
        json={"title": "Missing"},
    )
    invalid_card = client.patch(
        "/api/board/cards/no-such-card",
        json={"title": "Missing", "details": ""},
    )

    assert missing_column.status_code == 404
    assert invalid_card.status_code == 404


def test_card_can_move_into_an_empty_column(client: TestClient) -> None:
    client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    assert client.delete("/api/board/cards/card-6").status_code == 200

    response = client.post(
        "/api/board/cards/card-4/move",
        json={"column_id": "col-review", "position": 0},
    )

    assert response.status_code == 200
    assert response.json()["columns"][3]["cardIds"] == ["card-4"]


def test_card_can_move_from_backlog_to_each_other_column(client: TestClient) -> None:
    client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )

    for column_id in ("col-discovery", "col-progress", "col-review", "col-done"):
        response = client.post(
            "/api/board/cards/card-1/move",
            json={"column_id": column_id, "position": 0},
        )
        assert response.status_code == 200
        board = response.json()
        target_column = next(
            column for column in board["columns"] if column["id"] == column_id
        )
        assert target_column["cardIds"][0] == "card-1"
