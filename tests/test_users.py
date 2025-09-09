#tests/test_users.py

def test_user_add_and_delete(db_session, user_factory):
    # Add user via model
    from app.models import User
    user, pw, email = user_factory(username="testuser")
    

    assert User.query.count() == 1

    # Delete user
    db_session.delete(user)
    db_session.commit()

    assert User.query.count() == 0

def test_add_user_route(pg_client, user_factory):
    creds = user_factory(username="test_user_01", create=False)

    response = pg_client.post(
        "/api/users",
        data={
            "username": creds["username"],
            "email": creds["email"],
            "password_hash": creds["password"]
        },
        content_type="application/json")
    if response.status_code not in (200, 201, 302):
        print(response.status_code)
        print(response.get_data(as_text=True))
        print(response.headers)
    assert response.status_code in (200, 201, 302)
