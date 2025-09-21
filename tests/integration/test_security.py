# tests/integration/test_security.py
import pytest
from app.models import User
from app import db as _db

pytestmark = pytest.mark.integration

@pytest.mark.integration
def test_sql_injection_attempt(pg_client, pg_app):
    payload = {
        "username": "inject' OR 1=1 --",
        "email": "inject@example.com",
        "password": "Weak123!",
        "confirm_password": "Weak123!"
    }
    resp = pg_client.post("/api/users", data=payload, follow_redirects=True)
    assert resp.status_code in (200, 400, 422), f"Unexpected status: {resp.status_code}"

    # GOLDEN: malicious user should not exist
    with pg_app.app_context():
        assert User.query.filter_by(email="inject@example.com").first() is None

@pytest.mark.integration
def test_no_password_leak_in_api(pg_client, pg_app):
    payload = {
        "username": "secureuserpg",
        "email": "securepg@example.com",
        "password": "Secret123!",
        "confirm_password": "Secret123!"
    }
    r = pg_client.post("/api/users", data=payload, follow_redirects=True)
    assert r.status_code in (200, 201, 302)

    # query API or UI that lists users - ensure no raw password leakage
    r2 = pg_client.get("/api/users")
    assert b"Secret123!" not in r2.data
    assert b"password" not in r2.data.lower()
