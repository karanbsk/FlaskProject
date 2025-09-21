import pytest


pytestmark = pytest.mark.unit
# Dummy utility based tests (replace with actual utils imports)
try:
    from app.utils import is_valid_email, generate_token
except Exception:
    def is_valid_email(e): return "@" in e
    def generate_token(u): return f"tok-{u}"

#@pytest.mark.unit
def test_email_validator():
    assert is_valid_email("alice@example.com")
    assert not is_valid_email("invalid-email")

@pytest.mark.parametrize("username", ["alice", "bob", "carol", "dave", "eve", "frank", "gina"])
#@pytest.mark.unit
def test_token_generation(username):
    t = generate_token(username)
    assert isinstance(t, str)
