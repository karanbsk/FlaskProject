def test_reject_sql_like_username(client):
    payload = {
        "username": "inject' OR 1=1 --",
        "email": "attacker@example.com",
        "password": "x"
    }
    res = client.post("/api/users", json=payload)
    assert res.status_code == 400, f"Expected 400, got {res.status_code} - {res.get_data(as_text=True)}"
