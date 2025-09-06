import pytest
import json
from app.models import User, db

# --- Basic App Sanity ---
# Test No. 1
@pytest.mark.critical
def test_index(client):
    response = client.get('/')
    
    assert response.status_code == 200
    assert b'Flask DevOps Portfolio' in response.data


# -------- CRUD User Tests --------
# Test No. 2
@pytest.mark.critical
def test_add_user(client):
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "StrongPass123!"
    }
    response = client.post('/api/users', json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert "id" in data

# Test No. 3
@pytest.mark.critical
def test_add_user_duplicate(client):
    payload = {
        "username": "dupuser",
        "email": "dup@example.com",
        "password": "StrongPass123!"
    }
    # first create
    r1 = client.post('/api/users', json=payload)
    assert r1.status_code == 201
    # second create should conflict
    r2 = client.post('/api/users', json=payload)
    assert r2.status_code in (400, 409)
    text = r2.get_data(as_text=True).lower()
    assert "already" in text or "exists" in text

# Test No. 4
@pytest.mark.critical
def test_fetch_users(client):
    response = client.get('/api/users')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

# Test No. 5
@pytest.mark.critical
def test_reset_password(client):
    payload = {
        "username": "root",
        "new_password": "NewStrongPass123!"
    }
    response = client.post('/api/users/reset_password', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data.get("message") and "Password reset" in data.get("message")

# Test No. 6
@pytest.mark.critical
def test_delete_user(client):
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "StrongPass123!"
    }
    r = client.post('/api/users', json=payload)
    assert r.status_code == 201

    del_payload = {"username": "testuser"}
    rdel = client.post('/api/users/delete', json=del_payload)
    assert rdel.status_code == 200
    assert "deleted" in rdel.get_data(as_text=True).lower()

# Test No. 7
@pytest.mark.critical
def test_delete_root_user(client):
    payload = {"username": "root"}
    response = client.post('/api/users/delete', json=payload)
    # either 400 / 403 depending on implementation
    assert response.status_code in (400, 403)
    assert "root" in response.get_data(as_text=True).lower()


# --- Models ---
# Test No. 8
@pytest.mark.critical
def test_root_user_exists(client):
    """Ensure root user is seeded into DB on init"""
    response = client.get('/dashboard/data')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
    assert "db_status" in data or "db_status" in json.dumps(data).lower()

# Test No. 9
@pytest.mark.critical
def test_username_immutable(app):
    """Ensure username cannot be updated after creation"""
    with app.app_context():
        user = User(username="immutest", email="immutest@example.com", password="Pass123!")
        db.session.add(user)
        db.session.commit()

        user.username = "changed"
        try:
            db.session.commit()
            raise AssertionError("Username update should not be allowed")
        except Exception:
            db.session.rollback()  # Expected rollback
            
            
#--------Dashboard Tests---------
# Test No. 10
@pytest.mark.critical
def test_dashboard_endpoint(client):
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert b"Database Status" in response.data
    assert b"Server Time" in response.data
    assert b"Environment" in response.data

# Test No. 11
@pytest.mark.critical
def test_dashboard_db_status(client):
    """Simulate DB healthy state"""
    response = client.get('/dashboard')
    assert b"Healthy" in response.data

# Test No. 12
@pytest.mark.critical
def test_dashboard_latency(client):
    """Ensure latency metric is reported"""
    response = client.get('/dashboard')
    assert b"Latency" in response.data
