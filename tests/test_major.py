import pytest
from app.models import User

# --- Security Tests ---
# Test 1
@pytest.mark.major
def test_no_password_leak_in_api(client):
    client.post('/users/add', data={
        "username": "secureuser",
        "email": "secure@example.com",
        "password": "Secret123!"
    })
    response = client.get('/users')
    assert b"Secret123!" not in response.data
    assert b"password" not in response.data.lower()

# Test 2
@pytest.mark.major
def test_sql_injection_attempt(client, app):
    print("TEST DB URI =", app.config.get("SQLALCHEMY_DATABASE_URI"))

    payload = {
        "username": "inject' OR 1=1 --",
        "email": "inject@example.com",
        "password": "Weak123!"
    }

    resp = client.post("/users/add", data=payload, follow_redirects=True)

    # Accept either re-render (200) or validation 4xx
    assert resp.status_code in (200, 400, 422), f"Unexpected status: {resp.status_code}"

    # Deterministic check: flash container or validation container must exist (helps confirm UI signalled a problem)
    assert (b'id="flashes"' in resp.data) or (b'id="validation-errors-create"' in resp.data) or (b'id="flash-messages"' in resp.data), \
        f"No flash/validation container found. Response start:\n{resp.data.decode('utf-8')[:800]}"

    # GOLDEN check: ensure DB has NOT created the malicious user
    with app.app_context():
        assert User.query.filter_by(email="inject@example.com").first() is None, "Malicious user was created in DB!"
    
#------ UI Tests ------
# Test 3
@pytest.mark.major
def test_user_list_page(client):
    response = client.get('/users')
    assert response.status_code == 200
    assert b"User List" in response.data

# Test 4
@pytest.mark.major
def test_flash_message_on_duplicate_user(client, app):
     r1 = client.post('/users/add',
                     data={
                         "username": "flashuser",
                         "email": "flash@example.com",
                         "password": "Pass123!"
                     },
                     follow_redirects=True)
     assert r1.status_code in (200, 302, 201)

    # try to create duplicate user and follow redirects to capture the flash
     r2 = client.post('/users/add',
                     data={
                         "username": "flashuser",
                         "email": "flash@example.com",
                         "password": "Pass123!"
                     },
                     follow_redirects=True)
     # the flash message should be rendered on the final page
     assert b"already exists" in r2.data or b"Invalid" in r2.data or r2.status_code in (400, 422)

    # also ensure only one row exists in DB
     with app.app_context():
        assert User.query.filter_by(email='flash@example.com').count() == 1
# Test 5
@pytest.mark.major
def test_reset_password_modal(client):
    response = client.get('/users')
    assert b"Reset Password" in response.data


#------ Error Handling Tests ------
# Test 6
@pytest.mark.major
def test_invalid_route(client):
    response = client.get('/nonexistent-page')
    assert response.status_code == 404
    assert b"Page Not Found" in response.data

# Test 7
@pytest.mark.major
def test_db_unavailable(monkeypatch, client):
    """Simulate DB failure by monkeypatching session.execute"""
    from app import db

    def broken_execute(*args, **kwargs):
        raise Exception("DB Down")

    monkeypatch.setattr(db.session, "execute", broken_execute)

    response = client.get('/dashboard')
    assert b"Database Error" in response.data or b"Unhealthy" in response.data
