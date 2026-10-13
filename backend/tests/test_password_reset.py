from concurrent.futures import ThreadPoolExecutor
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def _email() -> str:
    return f"reset-{uuid4().hex}@example.com"


def _register(
    client: TestClient,
    email: str,
    password: str = "StrongPassword123!",
) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Reset User",
            "anonymous_id": "password-reset-test",
        },
    )

    assert response.status_code == 201
    return response.json()


def _extract_token(reset_url: str) -> str:
    parsed = urlparse(reset_url)
    fragment = parsed.fragment
    query = fragment.split("?", 1)[1] if "?" in fragment else parsed.query
    values = parse_qs(query)

    return values["token"][0]


def test_forgot_password_unknown_email_does_not_reveal_account() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": _email()},
        )

    assert response.status_code == 200
    payload = response.json()
    assert "Если аккаунт существует" in payload["message"]
    assert payload["dev_reset_url"] is None


def test_forgot_password_existing_user_returns_dev_reset_url() -> None:
    email = _email()

    with TestClient(app) as client:
        _register(client, email)

        response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": email},
        )

    assert response.status_code == 200
    payload = response.json()
    assert "Если аккаунт существует" in payload["message"]
    assert payload["dev_reset_url"]
    assert "/#reset?" in payload["dev_reset_url"]
    assert "token=" in payload["dev_reset_url"]


def test_reset_password_changes_password_and_old_password_stops_working() -> None:
    email = _email()
    old_password = "StrongPassword123!"
    new_password = "NewStrongPassword123!"

    with TestClient(app) as client:
        registration = _register(client, email, old_password)

        forgot_response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": email},
        )
        assert forgot_response.status_code == 200

        token = _extract_token(forgot_response.json()["dev_reset_url"])

        reset_response = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": token,
                "new_password": new_password,
            },
        )

        assert reset_response.status_code == 200
        assert reset_response.json()["message"] == "Пароль успешно обновлён."

        old_login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": old_password,
            },
        )

        new_login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": new_password,
            },
        )

        old_token_response = client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": f"Bearer {registration['access_token']}"
            },
        )

    assert old_login_response.status_code == 401
    assert new_login_response.status_code == 200
    assert old_token_response.status_code == 401


def test_reset_token_cannot_be_reused() -> None:
    email = _email()

    with TestClient(app) as client:
        _register(client, email)

        forgot_response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": email},
        )
        assert forgot_response.status_code == 200

        token = _extract_token(forgot_response.json()["dev_reset_url"])

        first_reset = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": token,
                "new_password": "NewStrongPassword123!",
            },
        )

        second_reset = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": token,
                "new_password": "AnotherStrongPassword123!",
            },
        )

    assert first_reset.status_code == 200
    assert second_reset.status_code == 400


def test_reset_token_is_consumed_atomically() -> None:
    email = _email()
    passwords = [
        "ConcurrentPasswordOne123!",
        "ConcurrentPasswordTwo123!",
    ]

    with TestClient(app) as client:
        _register(client, email)
        forgot_response = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": email},
        )
        assert forgot_response.status_code == 200
        token = _extract_token(forgot_response.json()["dev_reset_url"])

        def reset(password: str):
            return client.post(
                "/api/v1/auth/reset-password",
                json={
                    "token": token,
                    "new_password": password,
                },
            )

        with ThreadPoolExecutor(max_workers=2) as executor:
            responses = list(executor.map(reset, passwords))

        assert sorted(response.status_code for response in responses) == [200, 400]

        login_statuses = [
            client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": password},
            ).status_code
            for password in passwords
        ]

    assert sorted(login_statuses) == [200, 401]


def test_reset_password_rejects_invalid_token() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "invalid-token-invalid-token-invalid-token",
                "new_password": "NewStrongPassword123!",
            },
        )

    assert response.status_code == 400
