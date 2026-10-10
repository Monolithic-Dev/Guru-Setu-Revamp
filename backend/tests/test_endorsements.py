"""API-041 / REQ-027 (AC-027.1): a mentor endorses a mentee's skill and it reads Faculty-verified with their name.
Uses the hand-built graph from test_tracking: Meera mentors Aarav; Arjun does not."""
from tests.test_tracking import cypher, world  # noqa: F401  (autouse fixture: the base graph)

URL = "/api/v1/students/u-aarav/endorsements"


def _claim(concept: str = "pytorch") -> None:
    cypher(
        """
        MATCH (s:Student {user_id: 'u-aarav'})
        MERGE (c:Concept {name: $c})
        MERGE (s)-[h:HAS_SKILL]->(c)
        SET h.claimed = true, h.trust_level = 0, h.evidence_ids = [], h.endorsed_by = []
        """,
        c=concept,
    )


def _skill(profile: dict, concept: str) -> dict:
    return next(k for k in profile["skills"] if k["concept"] == concept)


def test_27_mentor_endorses_and_the_skill_reads_faculty_verified_by_name(client, meera, aarav):
    _claim()
    r = client.post(URL, json={"concept": "pytorch"}, headers=meera)
    assert r.status_code == 201, r.text
    skill = _skill(r.json(), "pytorch")  # the contract's 201 body is the student's profile
    assert skill["trust_level"] == 2
    assert skill["endorsed_by"] == ["Meera"]  # the faculty name (plain in this graph; "Dr. Meera Raman" on the seed), not an id (AC-027.1)
    # the student sees the same thing on their own profile
    mine = client.get("/api/v1/me/profile", headers=aarav).json()
    assert _skill(mine, "pytorch")["trust_level"] == 2
    assert _skill(mine, "pytorch")["endorsed_by"] == ["Meera"]


def test_27_endorsing_twice_is_harmless(client, meera):
    _claim()
    assert client.post(URL, json={"concept": "pytorch"}, headers=meera).status_code == 201
    r = client.post(URL, json={"concept": "pytorch"}, headers=meera)
    assert r.status_code == 201
    assert _skill(r.json(), "pytorch")["endorsed_by"] == ["Meera"]


def test_27_only_an_existing_skill_can_be_endorsed(client, meera):
    r = client.post(URL, json={"concept": "quantum gravity"}, headers=meera)
    assert r.status_code == 404  # endorsing must not invent a skill for the student


def test_27_scope_and_roles(client, arjun, suresh, aarav, kavya):
    _claim()
    body = {"concept": "pytorch"}
    assert client.post(URL, json=body, headers=arjun).status_code == 404  # faculty, but not Aarav's mentor
    assert client.post(URL, json=body, headers=suresh).status_code == 403  # HOD is not listed for this route
    assert client.post(URL, json=body, headers=aarav).status_code == 403  # a student cannot endorse themselves
    assert client.post(URL, json=body, headers=kavya).status_code == 403
    assert client.post(URL, json=body).status_code == 401
    mine = client.get("/api/v1/me/profile", headers=aarav).json()
    assert _skill(mine, "pytorch")["trust_level"] == 0  # none of the refusals changed anything


def test_27_validation(client, meera):
    assert client.post(URL, json={}, headers=meera).status_code == 422
    assert client.post(URL, json={"concept": ""}, headers=meera).status_code == 422
