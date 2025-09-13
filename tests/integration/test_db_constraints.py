#tests/integration/test_db_constraints.py
import pytest

pytestmark = pytest.mark.integration

def test_unique_email_constraint(pg_client):
    # create first user
    r1 = pg_client.post("/api/users", 
                        data={
                            "username":"a_unique",
                            "email":"dup@example.com",
                            "password":"StrongPass1!",
                            "confirm_password":"StrongPass1!"
                            },
        follow_redirects=True
                        )
    assert r1.status_code in (200, 201)

    # attempt duplicate email
    r2 = pg_client.post("/api/users",
                        data={
                            "username":"b_unique",
                            "email":"dup@example.com",
                            "password":"StrongPass1!",
                            "confirm_password":"StrongPass1!"
                            },
        follow_redirects=True
                        )
    # second request must be a client error (4xx) indicating duplicate or validation failure
    assert 400 <= r2.status_code < 500, f"Expected 4xx on duplicate, got {r2.status_code}"

def test_foreign_key_violation(client):
    # Try to create a resource that references a missing foreign key
    rv = client.post("/api/posts", data={"user_id": 999999, "title": "x"})
    assert rv.status_code >= 400
