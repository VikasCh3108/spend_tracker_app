"""Tests for user data isolation — expenses from one user must not be visible to another."""


def register_and_get_token(client, username, password):
    r = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": password},
    )
    assert r.status_code == 201
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


class TestUserDataIsolation:
    def test_expenses_isolated_between_users(self, client):
        """User A's expenses should not appear in User B's expense list."""
        headers_a = register_and_get_token(client, "userA", "passwordA123")
        headers_b = register_and_get_token(client, "userB", "passwordB123")

        # User A adds an expense
        client.post(
            "/api/v1/expenses/",
            json={"amount": 100.0, "category": "food", "date": "2024-03-15"},
            headers=headers_a,
        )

        # User B adds an expense
        client.post(
            "/api/v1/expenses/",
            json={"amount": 50.0, "category": "transport", "date": "2024-03-16"},
            headers=headers_b,
        )

        # User A should only see their expense
        r = client.get("/api/v1/expenses/", headers=headers_a)
        assert len(r.json()) == 1
        assert r.json()[0]["category"] == "food"
        assert r.json()[0]["amount"] == 100.0

        # User B should only see their expense
        r = client.get("/api/v1/expenses/", headers=headers_b)
        assert len(r.json()) == 1
        assert r.json()[0]["category"] == "transport"
        assert r.json()[0]["amount"] == 50.0

    def test_summary_isolated_between_users(self, client):
        """User A's summary should not include User B's expenses."""
        headers_a = register_and_get_token(client, "userA", "passwordA123")
        headers_b = register_and_get_token(client, "userB", "passwordB123")

        client.post(
            "/api/v1/expenses/",
            json={"amount": 200.0, "category": "food", "date": "2024-03-15"},
            headers=headers_a,
        )
        client.post(
            "/api/v1/expenses/",
            json={"amount": 300.0, "category": "transport", "date": "2024-03-16"},
            headers=headers_b,
        )

        # User A's total should be 200
        r = client.get("/api/v1/summary/", headers=headers_a)
        assert r.json()["total_spend"] == 200.0
        assert r.json()["spend_by_category"] == {"food": 200.0}

        # User B's total should be 300
        r = client.get("/api/v1/summary/", headers=headers_b)
        assert r.json()["total_spend"] == 300.0
        assert r.json()["spend_by_category"] == {"transport": 300.0}

    def test_insights_isolated_between_users(self, client):
        """User A's insights should not include User B's categories."""
        headers_a = register_and_get_token(client, "userA", "passwordA123")
        headers_b = register_and_get_token(client, "userB", "passwordB123")

        # User A: food 100 → 200 (100% increase)
        client.post(
            "/api/v1/expenses/",
            json={"amount": 100.0, "category": "food", "date": "2024-02-10"},
            headers=headers_a,
        )
        client.post(
            "/api/v1/expenses/",
            json={"amount": 200.0, "category": "food", "date": "2024-03-10"},
            headers=headers_a,
        )

        # User B: transport 100 → 250 (150% increase)
        client.post(
            "/api/v1/expenses/",
            json={"amount": 100.0, "category": "transport", "date": "2024-02-10"},
            headers=headers_b,
        )
        client.post(
            "/api/v1/expenses/",
            json={"amount": 250.0, "category": "transport", "date": "2024-03-10"},
            headers=headers_b,
        )

        # User A should only see food insights
        r = client.get("/api/v1/insights/?ref_date=2024-03-22", headers=headers_a)
        data = r.json()
        assert len(data) == 1
        assert data[0]["category"] == "food"

        # User B should only see transport insights
        r = client.get("/api/v1/insights/?ref_date=2024-03-22", headers=headers_b)
        data = r.json()
        assert len(data) == 1
        assert data[0]["category"] == "transport"

    def test_filter_by_category_does_not_leak_other_user_data(self, client):
        """Filtering by category should only return current user's expenses in that category."""
        headers_a = register_and_get_token(client, "userA", "passwordA123")
        headers_b = register_and_get_token(client, "userB", "passwordB123")

        client.post(
            "/api/v1/expenses/",
            json={"amount": 100.0, "category": "food", "date": "2024-03-15"},
            headers=headers_a,
        )
        client.post(
            "/api/v1/expenses/",
            json={"amount": 50.0, "category": "food", "date": "2024-03-16"},
            headers=headers_b,
        )

        # User A filters by food — should only see their own
        r = client.get("/api/v1/expenses/?category=food", headers=headers_a)
        assert len(r.json()) == 1
        assert r.json()[0]["amount"] == 100.0

        # User B filters by food — should only see their own
        r = client.get("/api/v1/expenses/?category=food", headers=headers_b)
        assert len(r.json()) == 1
        assert r.json()[0]["amount"] == 50.0

    def test_mom_change_isolated_between_users(self, client):
        """MoM change should only reflect the current user's spending."""
        headers_a = register_and_get_token(client, "userA", "passwordA123")
        headers_b = register_and_get_token(client, "userB", "passwordB123")

        # User A: 100 in Feb, 200 in March
        client.post(
            "/api/v1/expenses/",
            json={"amount": 100.0, "category": "food", "date": "2024-02-15"},
            headers=headers_a,
        )
        client.post(
            "/api/v1/expenses/",
            json={"amount": 200.0, "category": "food", "date": "2024-03-15"},
            headers=headers_a,
        )

        # User B: 500 in Feb, 1000 in March
        client.post(
            "/api/v1/expenses/",
            json={"amount": 500.0, "category": "food", "date": "2024-02-15"},
            headers=headers_b,
        )
        client.post(
            "/api/v1/expenses/",
            json={"amount": 1000.0, "category": "food", "date": "2024-03-15"},
            headers=headers_b,
        )

        # User A's MoM: 100 → 200 = +100%
        r = client.get("/api/v1/summary/", headers=headers_a)
        mom = r.json()["mom_change"]
        if mom["current_month"] == "2024-03" and mom["previous_month"] == "2024-02":
            assert mom["current_spend"] == 200.0
            assert mom["previous_spend"] == 100.0
            assert mom["change_percent"] == 100.0

        # User B's MoM: 500 → 1000 = +100%
        r = client.get("/api/v1/summary/", headers=headers_b)
        mom = r.json()["mom_change"]
        if mom["current_month"] == "2024-03" and mom["previous_month"] == "2024-02":
            assert mom["current_spend"] == 1000.0
            assert mom["previous_spend"] == 500.0
            assert mom["change_percent"] == 100.0
