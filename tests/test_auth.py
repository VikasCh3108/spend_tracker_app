"""Tests for JWT authentication: register, login, protected routes."""


class TestRegister:
    def test_register_success(self, client):
        r = client.post(
            "/api/v1/auth/register",
            json={"username": "newuser", "password": "password123"},
        )
        assert r.status_code == 201
        assert "access_token" in r.json()
        assert r.json()["token_type"] == "bearer"

    def test_register_duplicate(self, client, auth_headers):
        # auth_headers fixture registers "testuser"
        r = client.post(
            "/api/v1/auth/register",
            json={"username": "testuser", "password": "testpass123"},
        )
        assert r.status_code == 409
        assert "already registered" in r.json()["detail"]

    def test_register_short_username(self, client):
        r = client.post(
            "/api/v1/auth/register",
            json={"username": "ab", "password": "password123"},
        )
        assert r.status_code == 422

    def test_register_short_password(self, client):
        r = client.post(
            "/api/v1/auth/register",
            json={"username": "validuser", "password": "123"},
        )
        assert r.status_code == 422

    def test_register_missing_username(self, client):
        r = client.post(
            "/api/v1/auth/register",
            json={"password": "password123"},
        )
        assert r.status_code == 422

    def test_register_missing_password(self, client):
        r = client.post(
            "/api/v1/auth/register",
            json={"username": "validuser"},
        )
        assert r.status_code == 422


class TestLogin:
    def test_login_success(self, client, auth_headers):
        r = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "testpass123"},
        )
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_login_wrong_password(self, client, auth_headers):
        r = client.post(
            "/api/v1/auth/login",
            data={"username": "testuser", "password": "wrongpassword"},
        )
        assert r.status_code == 401
        assert "Incorrect" in r.json()["detail"]

    def test_login_nonexistent_user(self, client):
        r = client.post(
            "/api/v1/auth/login",
            data={"username": "nobody", "password": "password123"},
        )
        assert r.status_code == 401


class TestProtectedRoutes:
    def test_get_me_with_token(self, client, auth_headers):
        r = client.get("/api/v1/auth/me", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["username"] == "testuser"

    def test_get_me_without_token(self, client):
        r = client.get("/api/v1/auth/me")
        assert r.status_code == 401

    def test_get_me_invalid_token(self, client):
        r = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalidtoken"},
        )
        assert r.status_code == 401

    def test_post_expenses_without_token(self, client):
        r = client.post(
            "/api/v1/expenses/",
            json={"amount": 50.0, "category": "food", "date": "2024-01-15"},
        )
        assert r.status_code == 401

    def test_get_expenses_without_token(self, client):
        r = client.get("/api/v1/expenses/")
        assert r.status_code == 401

    def test_get_summary_without_token(self, client):
        r = client.get("/api/v1/summary/")
        assert r.status_code == 401

    def test_get_insights_without_token(self, client):
        r = client.get("/api/v1/insights/")
        assert r.status_code == 401

    def test_all_endpoints_with_valid_token(self, client, auth_headers):
        """All protected endpoints should return 200/201 with valid token."""
        r = client.post(
            "/api/v1/expenses/",
            json={"amount": 50.0, "category": "food", "date": "2024-01-15"},
            headers=auth_headers,
        )
        assert r.status_code == 201

        r = client.get("/api/v1/expenses/", headers=auth_headers)
        assert r.status_code == 200

        r = client.get("/api/v1/summary/", headers=auth_headers)
        assert r.status_code == 200

        r = client.get("/api/v1/insights/", headers=auth_headers)
        assert r.status_code == 200
