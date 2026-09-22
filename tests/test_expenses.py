"""Tests for expense CRUD operations and validation."""


class TestCreateExpense:
    def test_create_expense_success(self, client, auth_headers):
        r = client.post(
            "/api/v1/expenses/",
            json={"amount": 50.0, "category": "food", "date": "2024-01-15", "note": "lunch"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        data = r.json()
        assert data["amount"] == 50.0
        assert data["category"] == "food"
        assert data["note"] == "lunch"
        assert data["date"] == "2024-01-15"
        assert "id" in data
        assert "created_at" in data

    def test_create_expense_without_note(self, client, auth_headers):
        r = client.post(
            "/api/v1/expenses/",
            json={"amount": 25.0, "category": "transport", "date": "2024-01-15"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        assert r.json()["note"] is None

    def test_create_expense_negative_amount(self, client, auth_headers):
        r = client.post(
            "/api/v1/expenses/",
            json={"amount": -10.0, "category": "food", "date": "2024-01-15"},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_create_expense_zero_amount(self, client, auth_headers):
        r = client.post(
            "/api/v1/expenses/",
            json={"amount": 0, "category": "food", "date": "2024-01-15"},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_create_expense_empty_category(self, client, auth_headers):
        r = client.post(
            "/api/v1/expenses/",
            json={"amount": 10.0, "category": "", "date": "2024-01-15"},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_create_expense_missing_category(self, client, auth_headers):
        r = client.post(
            "/api/v1/expenses/",
            json={"amount": 10.0, "date": "2024-01-15"},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_create_expense_missing_date(self, client, auth_headers):
        r = client.post(
            "/api/v1/expenses/",
            json={"amount": 10.0, "category": "food"},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_create_expense_missing_amount(self, client, auth_headers):
        r = client.post(
            "/api/v1/expenses/",
            json={"category": "food", "date": "2024-01-15"},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_create_expense_long_category(self, client, auth_headers):
        r = client.post(
            "/api/v1/expenses/",
            json={"amount": 10.0, "category": "a" * 51, "date": "2024-01-15"},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_create_expense_long_note(self, client, auth_headers):
        r = client.post(
            "/api/v1/expenses/",
            json={"amount": 10.0, "category": "food", "date": "2024-01-15", "note": "x" * 501},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_create_expense_invalid_date_format(self, client, auth_headers):
        r = client.post(
            "/api/v1/expenses/",
            json={"amount": 10.0, "category": "food", "date": "01-15-2024"},
            headers=auth_headers,
        )
        assert r.status_code == 422


class TestListExpenses:
    def test_list_empty(self, client, auth_headers):
        r = client.get("/api/v1/expenses/", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_list_expenses_ordered_newest_first(self, client, auth_headers):
        for date in ["2024-01-10", "2024-03-20", "2024-02-15"]:
            client.post(
                "/api/v1/expenses/",
                json={"amount": 10.0, "category": "food", "date": date},
                headers=auth_headers,
            )
        r = client.get("/api/v1/expenses/", headers=auth_headers)
        dates = [e["date"] for e in r.json()]
        assert dates == ["2024-03-20", "2024-02-15", "2024-01-10"]

    def test_filter_by_category(self, client, auth_headers):
        client.post("/api/v1/expenses/", json={"amount": 10, "category": "food", "date": "2024-01-15"}, headers=auth_headers)
        client.post("/api/v1/expenses/", json={"amount": 20, "category": "transport", "date": "2024-01-16"}, headers=auth_headers)
        client.post("/api/v1/expenses/", json={"amount": 30, "category": "food", "date": "2024-01-17"}, headers=auth_headers)

        r = client.get("/api/v1/expenses/?category=food", headers=auth_headers)
        assert r.status_code == 200
        assert len(r.json()) == 2
        assert all(e["category"] == "food" for e in r.json())

    def test_filter_by_date_range(self, client, auth_headers):
        for date in ["2024-01-10", "2024-01-15", "2024-01-20", "2024-01-25"]:
            client.post("/api/v1/expenses/", json={"amount": 10, "category": "food", "date": date}, headers=auth_headers)

        r = client.get("/api/v1/expenses/?start_date=2024-01-12&end_date=2024-01-22", headers=auth_headers)
        dates = [e["date"] for e in r.json()]
        assert dates == ["2024-01-20", "2024-01-15"]

    def test_filter_by_category_and_date(self, client, auth_headers):
        client.post("/api/v1/expenses/", json={"amount": 10, "category": "food", "date": "2024-01-10"}, headers=auth_headers)
        client.post("/api/v1/expenses/", json={"amount": 20, "category": "transport", "date": "2024-01-15"}, headers=auth_headers)
        client.post("/api/v1/expenses/", json={"amount": 30, "category": "food", "date": "2024-01-20"}, headers=auth_headers)

        r = client.get("/api/v1/expenses/?category=food&start_date=2024-01-12&end_date=2024-01-25", headers=auth_headers)
        assert len(r.json()) == 1
        assert r.json()[0]["date"] == "2024-01-20"

    def test_filter_nonexistent_category(self, client, auth_headers):
        client.post("/api/v1/expenses/", json={"amount": 10, "category": "food", "date": "2024-01-10"}, headers=auth_headers)
        r = client.get("/api/v1/expenses/?category=nonexistent", headers=auth_headers)
        assert r.json() == []
