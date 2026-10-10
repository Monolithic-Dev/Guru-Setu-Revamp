"""Security tests (test-strategy section 2.1; SEC-01..05, 09-11, 20, 21).

TEST-04/05/06/08/12 are added with the routes they exercise (certificates, mentoring, exports).
"""
import logging
import time

import jwt
import pytest

from app.core.config import ConfigError, Settings
from app.core.errors import ApiError
from app.core.security import (
    ALGORITHM,
    create_token,
    decode_token,
    hash_password,
    password_too_long,
    verify_password,
)
from tests.conftest import PERSONAS

PUBLIC = {("post", "/auth/login"), ("get", "/health")}
FORBIDDEN_KEYS = {"password_hash", "embedding", "file_path"}
METHODS = {"get", "post", "put", "patch", "delete"}


def _routes(client):
    """(method, path) of every route the app serves, from the OpenAPI document of the running app."""
    paths = client.app.openapi()["paths"]
    return [(m, p.removeprefix("/api/v1")) for p, ops in paths.items() for m in ops if m in METHODS]


def _concrete(path: str) -> str:
    out = path
    while "{" in out:
        start, end = out.index("{"), out.index("}")
        out = out[:start] + "x" + out[end + 1 :]
    return "/api/v1" + out


def _scan(obj, found):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in FORBIDDEN_KEYS:
                found.append(key)
            _scan(value, found)
    elif isinstance(obj, list):
        for item in obj:
            _scan(item, found)


# ---- unit: hashing and tokens (T1.P2.1) -------------------------------------------------------------------------


def test_password_hash_roundtrip_and_limits():
    hashed = hash_password("Demo@123")
    assert hashed.startswith("$2b$12$")  # bcrypt cost 12
    assert verify_password("Demo@123", hashed)
    assert not verify_password("demo@123", hashed)
    assert not verify_password("Demo@123", "not-a-hash")  # a malformed hash never raises
    too_long = "a" * 73
    assert password_too_long(too_long)
    assert not password_too_long("a" * 72)
    with pytest.raises(ValueError):
        hash_password(too_long)
    assert not verify_password(too_long, hashed)


def test_token_roundtrip_and_tamper():
    token, expires = create_token("u-aarav", "student")
    claims = decode_token(token)
    assert claims["sub"] == "u-aarav" and claims["role"] == "student" and claims["exp"] > claims["iat"]
    assert expires.tzinfo is not None
    with pytest.raises(ApiError) as bad:
        decode_token(token[:-2] + "xx")  # tampered signature
    assert bad.value.code == "UNAUTHENTICATED" and bad.value.status == 401


def test_token_rejects_alg_none_wrong_key_and_missing_claims():
    from app.core.config import get_settings

    secret = get_settings().jwt_secret_key
    now = int(time.time())
    for forged in (
        jwt.encode({"sub": "u-aarav", "iat": now, "exp": now + 60}, key=None, algorithm="none"),
        jwt.encode({"sub": "u-aarav", "iat": now, "exp": now + 60}, "x" * 40, algorithm=ALGORITHM),
        jwt.encode({"iat": now, "exp": now + 60}, secret, algorithm=ALGORITHM),  # no sub
    ):
        with pytest.raises(ApiError) as exc:
            decode_token(forged)
        assert exc.value.status == 401


# ---- API: TEST-01 .. TEST-03 ------------------------------------------------------------------------------------


def test_01_no_secret_fields_in_any_get_response(client, aarav, meera, arjun, suresh, kavya):
    found: list[str] = []
    scanned = 0
    for headers in (aarav, meera, arjun, suresh, kavya):
        for method, path in _routes(client):
            if method != "get" or "{" in path:
                continue
            response = client.get(_concrete(path), headers=headers)
            assert response.status_code != 404, path  # the route must be reached, not just missed
            if response.headers.get("content-type", "").startswith("application/json"):
                _scan(response.json(), found)
                scanned += 1
    assert scanned > 0
    login = client.post("/api/v1/auth/login", json={"email": "aarav@demo.gurusetu", "password": "Demo@123"})
    assert login.status_code == 200
    _scan(login.json(), found)
    assert found == []


def test_02_removed_routes_are_404(client, aarav):
    for method, path in [
        ("post", "/api/v1/auth/register"),
        ("post", "/api/v1/auth/verify-identity"),
        ("post", "/api/v1/auth/reset-password"),
        ("post", "/api/v1/users/upload-profile-picture"),
        ("get", "/api/v1/dashboard/student/home"),
        ("get", "/api/v1/recommend/recommendations/student/openings"),
        ("get", "/uploads/anything.png"),
    ]:
        response = getattr(client, method)(path, headers=aarav)
        assert response.status_code == 404, (method, path)


def test_03_unauthenticated(client):
    now = int(time.time())
    wrong_key = jwt.encode({"sub": "u-aarav", "iat": now, "exp": now + 600}, "k" * 40, "HS256")
    bearers = [None, "Bearer abc", f"Bearer {wrong_key}", "Basic abc", "Bearer"]
    checked = 0
    for method, path in _routes(client):
        if (method, path) in PUBLIC:
            continue
        for value in bearers:
            headers = {"Authorization": value} if value else {}
            response = client.request(method.upper(), _concrete(path), headers=headers)
            assert response.status_code == 401, (method, path, value)
            assert response.json()["code"] == "UNAUTHENTICATED"
            checked += 1
    assert checked > 0  # at least /me is protected


# ---- API: TEST-09 .. TEST-11 ------------------------------------------------------------------------------------


def test_09_login_rate_limit(client, fresh_seed):
    body = {"email": "aarav@demo.gurusetu", "password": "wrong-password"}
    statuses = [client.post("/api/v1/auth/login", json=body).status_code for _ in range(10)]
    assert statuses == [401] * 10
    eleventh = client.post("/api/v1/auth/login", json=body)
    assert eleventh.status_code == 429
    assert eleventh.json()["code"] == "RATE_LIMITED"
    assert int(eleventh.headers["Retry-After"]) >= 1


def test_10_cors_headers_and_weak_secret(client, aarav):
    evil = client.options(
        "/api/v1/me", headers={"Origin": "http://evil.test", "Access-Control-Request-Method": "GET"}
    )
    assert "access-control-allow-origin" not in evil.headers
    allowed = client.options(
        "/api/v1/me", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"}
    )
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:3000"

    me = client.get("/api/v1/me", headers=aarav)
    assert me.headers["x-content-type-options"] == "nosniff"
    assert me.headers["referrer-policy"] == "no-referrer"
    assert me.headers["x-frame-options"] == "DENY"
    assert me.headers["x-request-id"]

    with pytest.raises(ConfigError, match="JWT_SECRET_KEY"):
        Settings(jwt_secret_key="short-key", neo4j_password="x" * 12, llm_provider="none", _env_file=None)
    with pytest.raises(ConfigError, match="NEO4J_PASSWORD"):
        Settings(jwt_secret_key="k" * 40, neo4j_password="short", llm_provider="none", _env_file=None)
    with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY"):
        Settings(jwt_secret_key="k" * 40, neo4j_password="x" * 12, llm_provider="anthropic", _env_file=None)


def test_11_expired_token_and_identical_login_failures(client, fresh_seed):
    from app.core.config import get_settings

    now = int(time.time())
    expired = jwt.encode(
        {"sub": "u-aarav", "role": "student", "iat": now - 7200, "exp": now - 3600},
        get_settings().jwt_secret_key,
        algorithm="HS256",
    )
    response = client.get("/api/v1/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401 and response.json()["code"] == "TOKEN_EXPIRED"

    wrong_password = client.post("/api/v1/auth/login", json={"email": "aarav@demo.gurusetu", "password": "nope"})
    unknown_email = client.post("/api/v1/auth/login", json={"email": "ghost@demo.gurusetu", "password": "nope"})
    assert wrong_password.status_code == unknown_email.status_code == 401

    def without_request_id(body):
        return {k: v for k, v in body.items() if k != "request_id"}

    assert without_request_id(wrong_password.json()) == without_request_id(unknown_email.json())
    assert wrong_password.json()["code"] == "INVALID_CREDENTIALS"

    too_long = client.post("/api/v1/auth/login", json={"email": "aarav@demo.gurusetu", "password": "a" * 100})
    assert too_long.status_code == 401  # bcrypt's 72-byte limit is handled, not a 500


# ---- API: login, /me, deps --------------------------------------------------------------------------------------


def test_login_returns_token_and_me_matches(client, fresh_seed):
    login = client.post("/api/v1/auth/login", json={"email": "Aarav@Demo.Gurusetu", "password": "Demo@123"})
    assert login.status_code == 200
    body = login.json()
    assert body["token_type"] == "bearer" and body["role"] == "student" and body["user_id"] == "u-aarav"
    me = client.get("/api/v1/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    data = me.json()
    assert set(data) == {"user_id", "name", "email", "role", "dept_code"}
    assert data["email"] == "aarav@demo.gurusetu" and data["role"] == "student" and data["dept_code"] == "CSE"


def test_token_for_deleted_user_is_401(client, fresh_seed):
    token, _ = create_token("u-does-not-exist", "student")
    response = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401 and response.json()["code"] == "UNAUTHENTICATED"


def test_role_comes_from_database_not_token(client, fresh_seed):
    token, _ = create_token("u-aarav", "hod")  # forged role claim
    me = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["role"] == "student"


def test_validation_error_is_problem_json_and_never_echoes_input(client):
    response = client.post("/api/v1/auth/login", json={"email": "not-an-email", "password": "SuperSecret!1"})
    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["code"] == "VALIDATION_FAILED" and body["request_id"] == response.headers["x-request-id"]
    assert any(err["field"] == "email" for err in body["errors"])
    assert "SuperSecret" not in response.text


def test_unknown_route_and_wrong_method_are_problem_json(client):
    missing = client.get("/api/v1/definitely-not-a-route")
    assert missing.status_code == 404 and missing.json()["code"] == "NOT_FOUND" and missing.json()["request_id"]
    wrong_method = client.get("/api/v1/auth/login")
    assert wrong_method.status_code == 405 and wrong_method.json()["code"] == "METHOD_NOT_ALLOWED"


def test_request_id_is_echoed_and_unsafe_ids_are_replaced(client):
    echoed = client.get("/api/v1/health", headers={"X-Request-ID": "trace-123"})
    assert echoed.headers["x-request-id"] == "trace-123"
    replaced = client.get("/api/v1/health", headers={"X-Request-ID": "bad id with spaces"})
    assert replaced.headers["x-request-id"] != "bad id with spaces"


def test_access_log_never_contains_credentials(client, aarav, caplog):
    secret_token = aarav["Authorization"].split(" ", 1)[1]
    with caplog.at_level(logging.INFO, logger="gurusetu.access"):
        client.get("/api/v1/me", headers=aarav)
        client.post("/api/v1/auth/login", json={"email": "aarav@demo.gurusetu", "password": "SuperSecret!1"})
    text = " ".join(str(r.msg) for r in caplog.records)
    assert "request" in text
    for forbidden in (secret_token, "Bearer", "SuperSecret", "Authorization"):
        assert forbidden not in text


def test_health_reports_database_and_llm_mode(client):
    body = client.get("/api/v1/health").json()
    assert body["status"] == "ok" and body["neo4j"] == "up"
    assert body["llm_provider"] in ("groq", "anthropic", "none")


# ---- scope helpers (T1.P2.3): Meera is the mentor of Aarav, Arjun is not -----------------------------------------


def test_scope_helpers(fresh_seed):
    from app.api import deps
    from app.core.database import run_read

    def call(fn, *args):
        return run_read(lambda tx: fn(tx, *args))

    assert call(deps.assert_mentor_of, "u-meera", "u-aarav") is None
    assert call(deps.assert_mentor_of, "u-meera", "u-aarav", "assigned") is None
    for faculty, student, kind in (("u-arjun", "u-aarav", None), ("u-meera", "u-aarav", "guide")):
        with pytest.raises(ApiError) as exc:
            call(deps.assert_mentor_of, faculty, student, kind)
        assert exc.value.status == 404 and exc.value.code == "NOT_FOUND"
    assert call(deps.assert_owner_of_opening, "u-meera", "op-edge-ai") is None
    with pytest.raises(ApiError):
        call(deps.assert_owner_of_opening, "u-arjun", "op-edge-ai")
    with pytest.raises(ApiError):
        call(deps.assert_applicant_of_own, "u-meera", "u-aarav")  # Aarav has not applied
    assert call(deps.assert_dept_hod, "u-suresh", "u-aarav") is None
    with pytest.raises(ApiError):
        call(deps.assert_dept_hod, "u-kavya", "u-aarav")  # IQAC is not an HOD

    def can_view(user, student):
        return run_read(lambda tx: deps.assert_self_or_scope(tx, user, student))

    student = deps.CurrentUser("u-aarav", "Aarav", "aarav@demo.gurusetu", "student", "CSE")
    other = deps.CurrentUser("u-diya", "Diya", "diya@demo.gurusetu", "student", "CSE")
    assert can_view(student, "u-aarav") is None
    with pytest.raises(ApiError):
        can_view(other, "u-aarav")


def test_personas_defined():
    assert set(PERSONAS) >= {"aarav", "meera", "arjun", "suresh", "kavya"}
