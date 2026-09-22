"""Tests for insights endpoint: >20% spend increase flagging."""


class TestInsights:
    def test_insights_empty(self, client, auth_headers):
        r = client.get("/api/v1/insights/", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_insights_no_previous_month_spend(self, client, auth_headers):
        """Category only in current month — excluded from insights."""
        client.post("/api/v1/expenses/", json={"amount": 500.0, "category": "food", "date": "2024-02-15"}, headers=auth_headers)
        client.post("/api/v1/expenses/", json={"amount": 1000.0, "category": "shopping", "date": "2024-03-15"}, headers=auth_headers)
        r = client.get("/api/v1/insights/?ref_date=2024-03-22", headers=auth_headers)
        data = r.json()
        cats = [x["category"] for x in data]
        assert "shopping" not in cats  # no previous month spend
        assert "food" in cats

    def test_insights_flagged_above_threshold(self, client, auth_headers):
        client.post("/api/v1/expenses/", json={"amount": 100.0, "category": "food", "date": "2024-02-10"}, headers=auth_headers)
        client.post("/api/v1/expenses/", json={"amount": 150.0, "category": "food", "date": "2024-03-10"}, headers=auth_headers)
        r = client.get("/api/v1/insights/?ref_date=2024-03-22", headers=auth_headers)
        data = r.json()
        food = [x for x in data if x["category"] == "food"][0]
        assert food["increase_percent"] == 50.0
        assert food["flagged"] is True

    def test_insights_not_flagged_below_threshold(self, client, auth_headers):
        client.post("/api/v1/expenses/", json={"amount": 200.0, "category": "transport", "date": "2024-02-10"}, headers=auth_headers)
        client.post("/api/v1/expenses/", json={"amount": 210.0, "category": "transport", "date": "2024-03-10"}, headers=auth_headers)
        r = client.get("/api/v1/insights/?ref_date=2024-03-22", headers=auth_headers)
        data = r.json()
        transport = [x for x in data if x["category"] == "transport"][0]
        assert transport["increase_percent"] == 5.0
        assert transport["flagged"] is False

    def test_insights_exact_20_percent_not_flagged(self, client, auth_headers):
        """Exactly 20% increase — strictly > 20, so NOT flagged."""
        client.post("/api/v1/expenses/", json={"amount": 100.0, "category": "food", "date": "2024-02-10"}, headers=auth_headers)
        client.post("/api/v1/expenses/", json={"amount": 120.0, "category": "food", "date": "2024-03-10"}, headers=auth_headers)
        r = client.get("/api/v1/insights/?ref_date=2024-03-22", headers=auth_headers)
        data = r.json()
        assert data[0]["increase_percent"] == 20.0
        assert data[0]["flagged"] is False

    def test_insights_100_percent_decrease(self, client, auth_headers):
        """Previous spend exists, current month zero — -100%, not flagged."""
        client.post("/api/v1/expenses/", json={"amount": 300.0, "category": "food", "date": "2024-02-10"}, headers=auth_headers)
        r = client.get("/api/v1/insights/?ref_date=2024-03-22", headers=auth_headers)
        data = r.json()
        assert data[0]["current_month_spend"] == 0.0
        assert data[0]["increase_percent"] == -100.0
        assert data[0]["flagged"] is False

    def test_insights_sorting_flagged_first(self, client, auth_headers):
        client.post("/api/v1/expenses/", json={"amount": 100.0, "category": "food", "date": "2024-02-10"}, headers=auth_headers)
        client.post("/api/v1/expenses/", json={"amount": 200.0, "category": "transport", "date": "2024-02-10"}, headers=auth_headers)
        client.post("/api/v1/expenses/", json={"amount": 150.0, "category": "food", "date": "2024-03-10"}, headers=auth_headers)  # 50% increase
        client.post("/api/v1/expenses/", json={"amount": 210.0, "category": "transport", "date": "2024-03-10"}, headers=auth_headers)  # 5% increase
        r = client.get("/api/v1/insights/?ref_date=2024-03-22", headers=auth_headers)
        data = r.json()
        cats = [x["category"] for x in data]
        assert cats == ["food", "transport"]  # flagged first, then not flagged

    def test_insights_year_boundary(self, client, auth_headers):
        client.post("/api/v1/expenses/", json={"amount": 100.0, "category": "food", "date": "2023-12-15"}, headers=auth_headers)
        client.post("/api/v1/expenses/", json={"amount": 200.0, "category": "food", "date": "2024-01-15"}, headers=auth_headers)
        r = client.get("/api/v1/insights/?ref_date=2024-01-20", headers=auth_headers)
        data = r.json()
        assert data[0]["previous_month_spend"] == 100.0
        assert data[0]["current_month_spend"] == 200.0
        assert data[0]["increase_percent"] == 100.0
        assert data[0]["flagged"] is True
