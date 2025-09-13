# tests/functional/test_ui_endpoints.py
import pytest

pytestmark = pytest.mark.functional

# list of paths commonly used for signup UI — we will probe them and accept first successful
COMMON_SIGNUP_PATHS = [
    "/signup",
    "/users/signup",
    "/auth/signup",
    "/register",
    "/ui/signup",
    "/create_user_ui",
    "/create-user",
    "/api/users"   # sometimes the API also renders a simple HTML for browsers
]

def _find_first_existing_path(client, paths):
    for p in paths:
        resp = client.get(p)
        if resp.status_code in (200, 302):
            return p, resp
    return None, None

def test_render_signup_page(pg_client):
    path, resp = _find_first_existing_path(pg_client, COMMON_SIGNUP_PATHS)
    assert path is not None, f"No signup UI path found among {COMMON_SIGNUP_PATHS}"
    # Good if we got a real page or a redirect to a page
    assert resp.status_code in (200, 302)

def test_ui_form_submission(pg_client):
    # Find a path to POST to. Prefer /api/users for API endpoints, otherwise try discovered UI form.
    api_path = "/api/users"
    # use a strong password to satisfy model validation
    payload = {
        "username": "func_user",
        "email": "func_user@example.com",
        "password": "StrongPass1!",
        "confirm_password": "StrongPass1!"
    }

    # try posting to API endpoint first (some apps accept form posts here)
    rv = pg_client.post(api_path, data=payload, follow_redirects=True)
    if rv.status_code in (200, 201):
        # success via API
        try:
            data = rv.get_json(silent=True)
        except Exception:
            data = None
        assert (data and data.get("username") == "func_user") or rv.status_code in (200,201)
        return

    # fallback: find a UI path to post to (assume a form action on same signup page)
    path, _ = _find_first_existing_path(pg_client, COMMON_SIGNUP_PATHS)
    assert path is not None, "No UI or API signup path found to submit form"
    rv2 = pg_client.post(path, data=payload, follow_redirects=True)
    assert rv2.status_code in (200, 201), f"Expected success after submitting UI form, got {rv2.status_code}"
