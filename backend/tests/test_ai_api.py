import json

import pytest
from fastapi.testclient import TestClient

from app import main


class FakeOpenRouterClient:
    def __init__(self, response: dict) -> None:
        self.response = response
        self.messages: list[dict[str, str]] = []

    def complete_json(
        self, messages: list[dict[str, str]], response_schema: dict
    ) -> dict:
        self.messages = messages
        assert response_schema["title"] == "AssistantResponse"
        return self.response

    def close(self) -> None:
        pass


@pytest.fixture
def client(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(main, "DATABASE_PATH", tmp_path / "project-management.db")
    with TestClient(main.app) as test_client:
        yield test_client


def login(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    assert response.status_code == 200


def test_chat_applies_multiple_operations_and_returns_the_updated_board(
    client: TestClient,
) -> None:
    fake = FakeOpenRouterClient(
        {
            "reply": "I updated the board.",
            "operations": [
                {
                    "operation": "rename_column",
                    "column_id": "col-review",
                    "title": "Approval",
                },
                {
                    "operation": "move_card",
                    "card_id": "card-1",
                    "column_id": "col-done",
                    "position": 0,
                },
                {
                    "operation": "create_card",
                    "column_id": "col-backlog",
                    "title": "AI follow-up",
                    "details": "Created by the assistant.",
                },
            ],
        }
    )
    main.app.dependency_overrides[main.get_openrouter_client] = lambda: fake
    try:
        login(client)
        response = client.post(
            "/api/ai/chat",
            json={
                "message": "Move the roadmap card to Done and create a follow-up.",
                "history": [{"role": "user", "content": "Please help."}],
            },
        )
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == "I updated the board."
    assert body["board"]["columns"][3]["title"] == "Approval"
    assert "card-1" == body["board"]["columns"][4]["cardIds"][0]
    assert any(
        card["title"] == "AI follow-up" for card in body["board"]["cards"].values()
    )
    assert "Current board JSON" in fake.messages[-1]["content"]
    assert "Move the roadmap card to Done and create a follow-up." in fake.messages[-1]["content"]
    assert "Please help." in json.dumps(fake.messages)


def test_chat_rolls_back_all_operations_when_one_is_invalid(
    client: TestClient,
) -> None:
    fake = FakeOpenRouterClient(
        {
            "reply": "This should not be applied.",
            "operations": [
                {
                    "operation": "create_card",
                    "column_id": "col-backlog",
                    "title": "Should roll back",
                    "details": "",
                },
                {
                    "operation": "move_card",
                    "card_id": "missing-card",
                    "column_id": "col-done",
                    "position": 0,
                },
            ],
        }
    )
    main.app.dependency_overrides[main.get_openrouter_client] = lambda: fake
    try:
        login(client)
        response = client.post(
            "/api/ai/chat",
            json={"message": "Make these changes."},
        )
        board = client.get("/api/board").json()
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 404
    assert all(card["title"] != "Should roll back" for card in board["cards"].values())


def test_chat_accepts_a_reply_without_board_operations(client: TestClient) -> None:
    fake = FakeOpenRouterClient(
        {"reply": "Your board is up to date.", "operations": []}
    )
    main.app.dependency_overrides[main.get_openrouter_client] = lambda: fake
    try:
        login(client)
        response = client.post(
            "/api/ai/chat",
            json={"message": "Is anything waiting for review?"},
        )
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["reply"] == "Your board is up to date."


def test_chat_rejects_malformed_provider_output(client: TestClient) -> None:
    fake = FakeOpenRouterClient(
        {
            "reply": "This is malformed.",
            "operations": [{"operation": "unknown_operation"}],
        }
    )
    main.app.dependency_overrides[main.get_openrouter_client] = lambda: fake
    try:
        login(client)
        response = client.post(
            "/api/ai/chat",
            json={"message": "Make a change."},
        )
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 502
    assert response.json() == {"detail": "OpenRouter returned an invalid board response"}


def test_chat_rejects_an_invalid_column_without_partial_changes(
    client: TestClient,
) -> None:
    fake = FakeOpenRouterClient(
        {
            "reply": "This should not be applied.",
            "operations": [
                {
                    "operation": "create_card",
                    "column_id": "col-backlog",
                    "title": "Should roll back",
                    "details": "",
                },
                {
                    "operation": "rename_column",
                    "column_id": "missing-column",
                    "title": "Invalid",
                },
            ],
        }
    )
    main.app.dependency_overrides[main.get_openrouter_client] = lambda: fake
    try:
        login(client)
        response = client.post(
            "/api/ai/chat",
            json={"message": "Make these changes."},
        )
        board = client.get("/api/board").json()
    finally:
        main.app.dependency_overrides.clear()

    assert response.status_code == 404
    assert all(card["title"] != "Should roll back" for card in board["cards"].values())


def test_chat_rejects_an_oversized_message(client: TestClient) -> None:
    login(client)
    response = client.post(
        "/api/ai/chat",
        json={"message": "x" * 5001},
    )

    assert response.status_code == 422
