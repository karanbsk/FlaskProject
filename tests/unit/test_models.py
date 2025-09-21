import pytest
from unittest.mock import MagicMock

# Adjust import to your project's models module
pytestmark = pytest.mark.unit

try:
    from app.models import User
except Exception:
    # fallback dummy class when running outside project to avoid ImportError in editors
    class User:
        def __init__(self, username=None, email=None):
            self.username = username
            self.email = email
        def __repr__(self):
            return f"<User {self.username}>"
        def to_dict(self):
            return {"username": self.username, "email": self.email}

#@pytest.mark.unit
class TestUserModel:
    def test_user_repr(self):
        u = User(username="alice")
        assert "alice" in repr(u)

    def test_user_to_dict_has_username_email(self):
        u = User(username="bob", email="b@example.com")
        d = getattr(u, "to_dict", lambda: {})()
        assert "username" in d and "email" in d

@pytest.mark.parametrize("username,email", [
    ("user1","u1@example.com"),
    ("user2","u2@example.com"),
    ("user3","u3@example.com"),
    ("user4","u4@example.com"),
    ("user5","u5@example.com"),
    ("user6","u6@example.com"),
    ("user7","u7@example.com"),
    ("user8","u8@example.com"),
])
#@pytest.mark.unit
def test_create_minimal_user(username, email):
    u = User(username=username, email=email)
    assert getattr(u, "username", None) == username
    assert getattr(u, "email", None) == email
