import re
import secrets

def validate_password(password: str, confirm_password: str):
    """
    Validates password policy and confirm match.
    Returns (is_valid: bool, message: str).
    """

    # Check confirm match
    if password != confirm_password:
        return False, "Passwords do not match!"

    # Policy: at least 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."

    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one digit."

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."

    return True, "Password is valid."



_email_re = re.compile(r"^[^@]+@[^@]+\.[^@]+$")

def is_valid_email(email: str) -> bool:
    return bool(email and _email_re.match(email))

def generate_token(username: str) -> str:
    return secrets.token_urlsafe(16)
