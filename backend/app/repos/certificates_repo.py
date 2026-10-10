"""Cypher for certificates (Evidence, ENT-05). Never returns `file_path` except through `get_file_path`
(the only caller is the file route, which checks scope first)."""
from typing import Any

# Fields of the `Certificate` response model. `file_path` and `duplicate_of` are deliberately absent.
CERT_FIELDS = """
    e.id AS id, e.status AS status, e.media_type AS media_type, e.holder_name AS holder_name, e.title AS title,
    e.issuer AS issuer, e.issue_date AS issue_date, e.level AS level, e.type AS type,
    coalesce(e.skills, []) AS skills, e.certificate_id AS certificate_id, e.verify_url AS verify_url,
    e.confidence AS confidence, coalesce(e.reasons, []) AS reasons, e.source AS source,
    e.review_reason AS review_reason, e.created_at AS created_at, e.updated_at AS updated_at
"""


def list_for_student(tx, student_id: str, limit: int = 100) -> list[dict[str, Any]]:
    return [
        r.data()
        for r in tx.run(
            f"""
            MATCH (:Student {{user_id: $sid}})-[:SUBMITTED]->(e:Evidence)
            RETURN {CERT_FIELDS}
            ORDER BY e.created_at DESC, e.id
            LIMIT $limit
            """,
            sid=student_id,
            limit=limit,
        )
    ]
