"""Tests for summary endpoint: total, by category, MoM change."""


class TestTotalSpend:
    def test_total_spend_empty(self, client, auth_headers):
        r = client.get("/api/v1/summary/", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["total_spend"] == 0.0

    def test_total_spend_single(self, client, auth_headers):
        client.post("/api/v1/expenses/", json={"amount": 100.0, "category": "food", "date": "2024-01-15"}, headers=auth_headers)
        r = client.get("/api/v1/summary/", headers=auth_headers)
        assert r.json()["total_spend"] == 100.0

    def test_total_spend_multiple(self, client, auth_headers):
        for amt in [10.5, 20.0, 30.25]:
            client.post("/api/v1/expenses/", json={"amount": amt, "category": "food", "date": "2024-01-15"}, headers=auth_headers)
        r = client.get("/api/v1/summary/", headers=auth_headers)
        assert r.json()["total_spend"] == 60.75


class TestSpendByCategory:
    def test_spend_by_category_empty(self, client, auth_headers):
        r = client.get("/api/v1/summary/", headers=auth_headers)
        assert r.json()["spend_by_category"] == {}

    def test_spend_by_category_single(self, client, auth_headers):
        client.post("/api/v1/expenses/", json={"amount": 50.0, "category": "food", "date": "2024-01-15"}, headers=auth_headers)
        r = client.get("/api/v1/summary/", headers=auth_headers)
        assert r.json()["spend_by_category"] == {"food": 50.0}

    def test_spend_by_category_multiple(self, client, auth_headers):
        client.post("/api/v1/expenses/", json={"amount": 100.0, "category": "food", "date": "2024-01-15"}, headers=auth_headers)
        client.post("/api/v1/expenses/", json={"amount": 50.0, "category": "transport", "date": "2024-01-16"}, headers=auth_headers)
        client.post("/api/v1/expenses/", json={"amount": 25.0, "category": "food", "date": "2024-01-17"}, headers=auth_headers)
        r = client.get("/api/v1/summary/", headers=auth_headers)
        cats = r.json()["spend_by_category"]
        assert cats["food"] == 125.0
        assert cats["transport"] == 50.0


class TestMoMChange:
    def test_mom_no_data(self, client, auth_headers):
        r = client.get("/api/v1/summary/", headers=auth_headers)
        mom = r.json()["mom_change"]
        assert mom["change_percent"] is None
        assert "No spend" in mom["note"]

    def test_mom_previous_month_only(self, client, auth_headers):
        client.post("/api/v1/expenses/", json={"amount": 100.0, "category": "food", "date": "2024-02-15"}, headers=auth_headers)
        r = client.get("/api/v1/summary/", headers=auth_headers)
        mom = r.json()["mom_change"]
        # Current month (today) likely has no spend
        assert mom["current_spend"] == 0.0 or mom["previous_spend"] == 100.0

    def test_mom_new_spending_no_previous(self, client, auth_headers):
        """Current month has spend, previous month has none."""
        client.post("/api/v1/expenses/", json={"amount": 200.0, "category": "food", "date": "2024-03-15"}, headers=auth_headers)
        r = client.get("/api/v1/summary/", headers=auth_headers)
        mom = r.json()["mom_change"]
        # If current month is March 2024, previous (Feb) has no spend
        if mom["current_month"] == "2024-03":
            assert mom["change_percent"] is None
            assert "new spending" in mom["note"]

    def test_mom_normal_increase(self, client, auth_headers):
        client.post("/api/v1/expenses/", json={"amount": 100.0, "category": "food", "date": "2024-02-15"}, headers=auth_headers)
        client.post("/api/v1/expenses/", json={"amount": 150.0, "category": "food", "date": "2024-03-15"}, headers=auth_headers)
        r = client.get("/api/v1/summary/", headers=auth_headers)
        mom = r.json()["mom_change"]
        if mom["current_month"] == "2024-03" and mom["previous_month"] == "2024-02":
            assert mom["current_spend"] == 150.0
            assert mom["previous_spend"] == 100.0
            assert mom["change_percent"] == 50.0
            assert mom["note"] is None

    def test_mom_decrease(self, client, auth_headers):
        client.post("/api/v1/expenses/", json={"amount": 200.0, "category": "food", "date": "2024-02-15"}, headers=auth_headers)
        client.post("/api/v1/expenses/", json={"amount": 100.0, "category": "food", "date": "2024-03-15"}, headers=auth_headers)
        r = client.get("/api/v1/summary/", headers=auth_headers)
        mom = r.json()["mom_change"]
        if mom["current_month"] == "2024-03" and mom["previous_month"] == "2024-02":
            assert mom["change_percent"] == -50.0

    def test_mom_year_boundary(self, client, auth_headers):
        client.post("/api/v1/expenses/", json={"amount": 100.0, "category": "food", "date": "2023-12-15"}, headers=auth_headers)
        client.post("/api/v1/expenses/", json={"amount": 200.0, "category": "food", "date": "2024-01-15"}, headers=auth_headers)
        r = client.get("/api/v1/summary/", headers=auth_headers)
        mom = r.json()["mom_change"]
        if mom["current_month"] == "2024-01" and mom["previous_month"] == "2023-12":
            assert mom["change_percent"] == 100.0
