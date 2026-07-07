def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_signup_returns_tokens(client, signup_payload):
    res = client.post("/api/auth/signup", json=signup_payload)
    assert res.status_code == 201
    body = res.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert "fintrack_refresh" in res.cookies


def test_signup_duplicate_email_conflicts(client, signup_payload):
    assert client.post("/api/auth/signup", json=signup_payload).status_code == 201
    assert client.post("/api/auth/signup", json=signup_payload).status_code == 409


def test_signup_rejects_short_password(client, signup_payload):
    signup_payload["password"] = "short"
    assert client.post("/api/auth/signup", json=signup_payload).status_code == 422


def test_login_and_me(client, signup_payload):
    client.post("/api/auth/signup", json=signup_payload)
    res = client.post(
        "/api/auth/login",
        json={"email": signup_payload["email"], "password": signup_payload["password"]},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == signup_payload["email"]
    assert me.json()["display_name"] == signup_payload["display_name"]
    assert "password_hash" not in me.json()


def test_login_wrong_password_rejected(client, signup_payload):
    client.post("/api/auth/signup", json=signup_payload)
    res = client.post(
        "/api/auth/login",
        json={"email": signup_payload["email"], "password": "wrong-password-123"},
    )
    assert res.status_code == 401


def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401
    assert (
        client.get("/api/auth/me", headers={"Authorization": "Bearer garbage"}).status_code
        == 401
    )


def test_refresh_rotates_token(client, signup_payload):
    client.post("/api/auth/signup", json=signup_payload)
    first_cookie = client.cookies.get("fintrack_refresh")

    res = client.post("/api/auth/refresh")
    assert res.status_code == 200
    assert res.json()["access_token"]
    second_cookie = client.cookies.get("fintrack_refresh")
    assert second_cookie != first_cookie

    # The rotated-out (revoked) token must no longer work.
    client.cookies.set("fintrack_refresh", first_cookie)
    assert client.post("/api/auth/refresh").status_code == 401


def test_logout_revokes_refresh_token(client, signup_payload):
    client.post("/api/auth/signup", json=signup_payload)
    cookie = client.cookies.get("fintrack_refresh")

    assert client.post("/api/auth/logout").status_code == 200

    client.cookies.set("fintrack_refresh", cookie)
    assert client.post("/api/auth/refresh").status_code == 401


def test_refresh_without_cookie_rejected(client):
    assert client.post("/api/auth/refresh").status_code == 401


def test_audit_log_records_events(client, signup_payload):
    from app.database import get_db as real_get_db
    from app.main import app as fastapi_app
    from app.models import AuditLog

    client.post("/api/auth/signup", json=signup_payload)
    client.post(
        "/api/auth/login",
        json={"email": signup_payload["email"], "password": "wrong-password-123"},
    )

    override = fastapi_app.dependency_overrides[real_get_db]
    db = next(override())
    events = [row.event_type for row in db.query(AuditLog).all()]
    assert "signup" in events
    assert "login_failure" in events
