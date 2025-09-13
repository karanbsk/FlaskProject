import pytest
from app.models import User
from app import db as _db

@pytest.mark.regression
def test_duplicate_user_handled(pg_client, pg_app):
    """
    Regression check: attempting to create the same user twice should NOT result
    in two persisted users with the same email. Accept either:
      - the app returns a client error (4xx) on the second attempt; OR
      - the app returns success but the DB still contains only one user (deduped).
    """

    payload = {
        "username": "regdup",
        "email": "regdup@example.com",
        "password": "StrongPass1!",
        "confirm_password": "StrongPass1!"
    }

    # First create attempt
    r1 = pg_client.post("/api/users", data=payload, follow_redirects=True)
    assert r1.status_code in (200, 201, 302), f"Unexpected status on first create: {r1.status_code}"

    # Second create attempt (duplicate)
    r2 = pg_client.post("/api/users", data=payload, follow_redirects=True)

    # Either the app returns a client error (preferred), or it returns success but DB must not contain duplicate rows.
    if 400 <= r2.status_code < 500:
        # expected client-side rejection
        assert True
    else:
        # If the app returned success-ish, verify the DB contains exactly one user with that email
        with pg_app.app_context():
            users = User.query.filter_by(email=payload["email"]).all()
            assert len(users) == 1, f"Duplicate user persisted; found {len(users)} rows for email {payload['email']}"
