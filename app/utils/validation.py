# app/utils/validation.py
import re

# Strict whitelist: letters, digits, dot, underscore, hyphen. 3-30 chars.
USERNAME_RE = re.compile(r'^[A-Za-z0-9_.-]{3,30}$')

def valid_username(u: str) -> bool:
    """
    Return True only if username fully matches the whitelist.
    Keeps out quotes, spaces, SQL tokens like --, OR, etc.
    """
    if not isinstance(u, str):
        return False
    return bool(USERNAME_RE.fullmatch(u.strip()))
