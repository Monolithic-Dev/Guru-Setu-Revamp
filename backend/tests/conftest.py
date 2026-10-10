"""Shared fixtures (T1.P2.2). Nobody else edits this file; extra fixtures live in each owner's own test file.

Tests run against the compose Neo4j and reseed once per session (A-23). The database is WIPED at session start.

`fresh_seed` runs `python -m scripts.seed --reset` when P4's loader exists, then idempotently MERGEs the few nodes
these tests rely on (the personas, one mentor link, one opening). With the full seed those MERGEs are no-ops, because
the ids below are the ones backend.md section 10 defines. Before the loader lands they build a small stand-in graph.
"""
import os
import subprocess
import sys
from pathlib import Path

# Must be set before `app.main` is imported (it builds the app and reads settings at import time).
os.environ.setdefault("TODAY_OVERRIDE", "2026-10-10")
os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")  # local runs; compose sets bolt://neo4j:7687

import bcrypt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parents[1]
DEMO_PASSWORD = "Demo@123"  # synthetic demo password (README)

# persona key -> (user_id, role, label)
PERSONAS = {
    "aarav": ("u-aarav", "student"),
    "diya": ("u-diya", "student"),
    "meera": ("u-meera", "faculty"),
    "arjun": ("u-arjun", "faculty"),
    "suresh": ("u-suresh", "hod"),
    "kavya": ("u-kavya", "iqac"),
}


def _ensure_stand_in_graph() -> None:
    """MERGE the nodes the P2 tests need. No-ops where the full seed already created them."""
    from app.core.database import get_driver

    hashed = bcrypt.hashpw(DEMO_PASSWORD.encode(), bcrypt.gensalt(4)).decode()  # cost 4: tests only
    with get_driver().session() as session:
        session.run("MERGE (:Department {code: 'CSE'}) ").consume()
        for key, (uid, role) in PERSONAS.items():
            labels = {"student": "Student", "faculty": "Faculty", "hod": "Staff", "iqac": "Staff"}[role]
            session.run(
                f"""
                MERGE (u:User {{user_id: $uid}})
                ON CREATE SET u.email = $email, u.password_hash = $hash, u.name = $name, u.role = $role,
                              u.dept_code = 'CSE', u.created_at = '2026-01-01T00:00:00.000Z'
                SET u:{labels}
                """,
                uid=uid, email=f"{key}@demo.gurusetu", hash=hashed, name=key.capitalize(), role=role,
            ).consume()
        session.run(
            """
            MATCH (a:Student {user_id: 'u-aarav'})
            SET a.roll_no = coalesce(a.roll_no, 'CB.EN.U4CSE24001'), a.year = 3
            WITH a MATCH (d:Student {user_id: 'u-diya'})
            SET d.roll_no = coalesce(d.roll_no, 'CB.EN.U4CSE24902'), d.year = 3
            WITH a, d MATCH (m:Faculty {user_id: 'u-meera'}) SET m.employee_id = coalesce(m.employee_id, 'E-MEERA')
            WITH a, d, m MATCH (j:Faculty {user_id: 'u-arjun'}) SET j.employee_id = coalesce(j.employee_id, 'E-ARJUN')
            WITH a, d, m, j
            MERGE (m)-[l:MENTORS {id: 'mt-meera-aarav'}]->(a)
              ON CREATE SET l.type = 'assigned', l.status = 'active', l.since = '2026-05-01'
            MERGE (j)-[l2:MENTORS {id: 'mt-arjun-diya'}]->(d)
              ON CREATE SET l2.type = 'assigned', l2.status = 'active', l2.since = '2026-05-01'
            MERGE (o:Opening {id: 'op-edge-ai'})
              ON CREATE SET o.title = 'Edge AI for Agriculture', o.description = 'Stand-in opening for tests.',
                            o.status = 'open', o.created_at = '2026-09-01T00:00:00.000Z'
            MERGE (m)-[:POSTED]->(o)
            """
        ).consume()


@pytest.fixture(scope="session")
def client() -> TestClient:
    from app.main import app

    with TestClient(app) as test_client:  # runs the lifespan: schema applied, Neo4j reachable
        yield test_client


# P1's test modules run against the full seed, so they go first. P2's modules rebuild a small stand-in graph of their
# own (below) and edit it freely, so they go last and cannot disturb the seed P1's tests read.
P1_MODULES = {"test_embedding", "test_extraction", "test_matching", "test_scorer", "test_verification"}


def pytest_collection_modifyitems(items):
    items.sort(key=lambda item: 0 if item.module.__name__.rsplit(".", 1)[-1] in P1_MODULES else 1)  # stable


@pytest.fixture(scope="module", autouse=True)
def _p2_stand_in_graph(request, fresh_seed):
    """Every P2 module starts from the same small graph: wipe everything, then the personas (plain names, one
    mentor link each, one opening). The module's own `world` fixture then adds what it needs."""
    if request.module.__name__.rsplit(".", 1)[-1] in P1_MODULES:
        return
    from app.core.database import get_driver

    with get_driver().session() as session:
        session.run("MATCH (n) DETACH DELETE n").consume()
    _ensure_stand_in_graph()


@pytest.fixture(scope="session")
def fresh_seed(client: TestClient) -> None:
    seed_script = BACKEND_DIR / "scripts" / "seed.py"
    ran_seed = False
    if seed_script.exists():
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "scripts.seed", "--reset"], cwd=BACKEND_DIR, capture_output=True, text=True
        )
        ran_seed = result.returncode == 0
    if not ran_seed:
        from app.core.database import get_driver

        with get_driver().session() as session:
            session.run("MATCH (n) DETACH DELETE n").consume()
    _ensure_stand_in_graph()


def _auth_header(user_id: str, role: str) -> dict[str, str]:
    from app.core.security import create_token

    token, _ = create_token(user_id, role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def aarav(fresh_seed) -> dict[str, str]:
    return _auth_header(*PERSONAS["aarav"])


@pytest.fixture
def diya(fresh_seed) -> dict[str, str]:
    return _auth_header(*PERSONAS["diya"])


@pytest.fixture
def meera(fresh_seed) -> dict[str, str]:
    return _auth_header(*PERSONAS["meera"])


@pytest.fixture
def arjun(fresh_seed) -> dict[str, str]:
    return _auth_header(*PERSONAS["arjun"])


@pytest.fixture
def suresh(fresh_seed) -> dict[str, str]:
    return _auth_header(*PERSONAS["suresh"])


@pytest.fixture
def kavya(fresh_seed) -> dict[str, str]:
    return _auth_header(*PERSONAS["kavya"])


@pytest.fixture(autouse=True)
def _reset_login_limiter():
    from app.services.auth import reset_login_limiter

    reset_login_limiter()
    yield
    reset_login_limiter()
