from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def _unique_email() -> str:
    return f"test-{uuid4().hex}@example.com"


def _register_user(client: TestClient) -> tuple[str, dict]:
    email = _unique_email()

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": "Test User",
            "anonymous_id": "auth-test-anon",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    return payload["access_token"], payload


def _guest_recommendation(client: TestClient, anonymous_id: str) -> str:
    response = client.post(
        "/api/v1/recommendations",
        json={
            "skin_type": "combination",
            "concerns": ["dryness", "sebum"],
            "primary_concern": "dryness",
            "budget": "balanced",
            "experience": "beginner",
            "routine_preference": "balanced",
            "anonymous_id": anonymous_id,
        },
    )
    assert response.status_code == 200
    return response.json()["recommendation_id"]


def test_user_can_register() -> None:
    with TestClient(app) as client:
        _, payload = _register_user(client)

    assert payload["token_type"] == "bearer"
    assert payload["user"]["email"]
    assert payload["user"]["full_name"] == "Test User"
    assert payload["user"]["anonymous_id"] == "auth-test-anon"
    assert payload["profile"]["user_id"] == payload["user"]["user_id"]
    assert payload["profile"]["questionnaire_history"] == []


def test_duplicate_registration_returns_409() -> None:
    email = _unique_email()

    with TestClient(app) as client:
        first = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "StrongPassword123!",
                "full_name": "First User",
                "anonymous_id": "dup-anon",
            },
        )
        second = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "StrongPassword123!",
                "full_name": "Second User",
                "anonymous_id": "dup-anon-2",
            },
        )

    assert first.status_code == 201
    assert second.status_code == 409


def test_user_can_login() -> None:
    email = _unique_email()
    password = "StrongPassword123!"

    with TestClient(app) as client:
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Login User",
                "anonymous_id": "login-anon",
            },
        )
        assert register_response.status_code == 201

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

    assert login_response.status_code == 200
    payload = login_response.json()
    assert payload["access_token"]
    assert payload["user"]["email"] == email
    assert payload["profile"]["user_id"] == payload["user"]["user_id"]


def test_registration_claims_guest_recommendation_history() -> None:
    anonymous_id = f"register-claim-{uuid4().hex}"

    with TestClient(app) as client:
        recommendation_id = _guest_recommendation(client, anonymous_id)
        registered = client.post(
            "/api/v1/auth/register",
            json={
                "email": _unique_email(),
                "password": "StrongPassword123!",
                "full_name": "Guest Owner",
                "anonymous_id": anonymous_id,
            },
        )
        assert registered.status_code == 201
        auth_payload = registered.json()
        history = client.get(
            "/api/v1/users/me/recommendations",
            headers={
                "Authorization": f"Bearer {auth_payload['access_token']}"
            },
        )

    assert auth_payload["claimed_recommendations"] == 1
    assert history.status_code == 200
    assert history.json()["total"] == 1
    assert history.json()["items"][0]["recommendation_id"] == recommendation_id


def test_login_claims_only_current_browser_guest_recommendations() -> None:
    email = _unique_email()
    password = "StrongPassword123!"
    current_browser_id = f"login-claim-{uuid4().hex}"
    other_browser_id = f"other-browser-{uuid4().hex}"

    with TestClient(app) as client:
        registered = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "anonymous_id": f"registration-{uuid4().hex}",
            },
        )
        assert registered.status_code == 201
        claimed_id = _guest_recommendation(client, current_browser_id)
        _guest_recommendation(client, other_browser_id)

        logged_in = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": password,
                "anonymous_id": current_browser_id,
            },
        )
        assert logged_in.status_code == 200
        login_payload = logged_in.json()
        history = client.get(
            "/api/v1/users/me/recommendations",
            headers={
                "Authorization": f"Bearer {login_payload['access_token']}"
            },
        )

    assert login_payload["claimed_recommendations"] == 1
    assert history.status_code == 200
    assert history.json()["total"] == 1
    assert history.json()["items"][0]["recommendation_id"] == claimed_id


def test_swagger_oauth_token_endpoint_accepts_form_login() -> None:
    email = _unique_email()
    password = "StrongPassword123!"

    with TestClient(app) as client:
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Swagger OAuth User",
                "anonymous_id": "swagger-oauth-anon",
            },
        )
        assert register_response.status_code == 201

        token_response = client.post(
            "/api/v1/auth/token",
            data={
                "username": email,
                "password": password,
            },
        )

    assert token_response.status_code == 200
    payload = token_response.json()
    assert payload["access_token"]
    assert payload["token_type"] == "bearer"
    assert payload["user"]["email"] == email


def test_login_with_wrong_password_returns_401() -> None:
    email = _unique_email()

    with TestClient(app) as client:
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "StrongPassword123!",
                "full_name": "Wrong Password User",
                "anonymous_id": "wrong-password-anon",
            },
        )
        assert register_response.status_code == 201

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": "WrongPassword123!",
            },
        )

    assert login_response.status_code == 401


def test_get_me_requires_valid_token() -> None:
    with TestClient(app) as client:
        token, register_payload = _register_user(client)

        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == register_payload["user"]["user_id"]


def test_get_me_without_token_returns_401() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/users/me")

    assert response.status_code == 401


def test_user_can_update_profile() -> None:
    with TestClient(app) as client:
        token, _ = _register_user(client)

        response = client.patch(
            "/api/v1/users/me/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "age": 19,
                "skin_type": "combination",
                "concerns": ["acne", "sebum"],
                "primary_concern": "acne",
                "sensitivity_level": "medium",
                "budget": "balanced",
                "excluded_ingredients": ["fragrance"],
                "custom_restrictions": ["alcohol"],
                "experience": "guided",
                "routine_preference": "complete",
                "texture_preference": "lightweight",
                "values": ["comfort", "price_quality"],
            },
        )

    assert response.status_code == 200
    payload = response.json()

    assert payload["age"] == 19
    assert payload["skin_type"] == "combination"
    assert "acne" in payload["concerns"]
    assert payload["primary_concern"] == "acne"
    assert payload["sensitivity_level"] == "medium"
    assert payload["budget"] == "balanced"
    assert "fragrance" in payload["excluded_ingredients"]
    assert payload["routine_preference"] == "complete"
    assert payload["texture_preference"] == "lightweight"


def test_user_can_append_questionnaire_history() -> None:
    with TestClient(app) as client:
        token, _ = _register_user(client)

        response = client.post(
            "/api/v1/users/me/profile/questionnaire-history",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "recommendation_id": "rec-test-123",
                "age": 19,
                "skin_type": "combination",
                "concerns": ["acne", "sebum"],
                "primary_concern": "acne",
                "sensitivity_level": "medium",
                "budget": "balanced",
                "excluded_ingredients": ["fragrance"],
                "custom_restrictions": [],
                "experience": "guided",
                "routine_preference": "balanced",
                "texture_preference": "no_preference",
                "values": ["comfort", "price_quality"],
                "total_price_rub": 3440,
                "metadata": {"source": "test"},
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["questionnaire_history"]) == 1
    assert payload["questionnaire_history"][0]["recommendation_id"] == "rec-test-123"
    assert payload["questionnaire_history"][0]["age"] == 19
    assert payload["questionnaire_history"][0]["primary_concern"] == "acne"


def test_user_can_update_basic_info() -> None:
    with TestClient(app) as client:
        token, _ = _register_user(client)

        response = client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "full_name": "Updated User",
                "anonymous_id": "updated-anon",
            },
        )

    assert response.status_code == 200
    payload = response.json()

    assert payload["full_name"] == "Updated User"
    assert payload["anonymous_id"] == "updated-anon"

def test_registered_user_has_user_role() -> None:
    with TestClient(app) as client:
        _, payload = _register_user(client)

    assert payload["user"]["role"] == "user"


def test_registration_rejects_role_injection() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": _unique_email(),
                "password": "StrongPassword123!",
                "full_name": "Injected Admin",
                "role": "admin",
            },
        )

    assert response.status_code == 422


def test_profile_update_rejects_role_injection() -> None:
    with TestClient(app) as client:
        token, _ = _register_user(client)
        response = client.patch(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "full_name": "Still User",
                "role": "admin",
            },
        )

    assert response.status_code == 422

