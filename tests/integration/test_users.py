#tests/integrations/test_users.py
import pytest
from app.services.users_service import RootDeletionError
 
pytestmark = pytest.mark.integration
def test_user_add_and_delete(db_session, user_factory):
    # Add user via model
    from app.models import User
    user, raw_pw, email = user_factory(username="testuser", create=True)
    

    total = User.query.count()
    assert total == 2

    # Delete user
    db_session.delete(user)
    db_session.commit()

    total_after = User.query.count()
    assert total_after == 1
    
def test_add_user_route(pg_client, user_factory):
    creds = user_factory(username="test_user_01", create=False)
    payload = {
        "username": creds["username"],
        "email": creds["email"],
        "password": creds["password"],           # plain password from factory
        "confirm_password": creds["password"]
    }
    response = pg_client.post("/api/users",json=payload)

    assert response.status_code == 201
    data = response.get_json()
    assert data["username"] == creds["username"]
    assert "id" in data

def test_root_cannot_be_delete(db_session):
    from app.models import User

    root = User.query.filter_by(username="root").one_or_none()
    assert root is not None, "Root user must exist"

    # Deleting root via ORM should raise the domain-specific RootDeletionError
    with pytest.raises(RootDeletionError):
        db_session.delete(root)
        db_session.commit()

    # cleanup: rollback to leave session usable in later tests
    db_session.rollback()

    # ensure root still exists
    root_after = User.query.filter_by(username="root").one_or_none()
    assert root_after is not None
    
    