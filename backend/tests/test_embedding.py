"""MDL-02: the embedder and the two text builders.

These load the real MiniLM from the baked image, so they are the slowest tests
in P1's set - but they are the ones that would catch a wrong model, a wrong
dimension, or a text builder that drops the student's skills.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.ml import embedding
from app.ml.embedding import cosine, opening_text, student_text


@dataclass
class FakeSettings:
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"


@pytest.fixture(autouse=True)
def _settings(monkeypatch):
    monkeypatch.setattr(embedding, "get_settings", lambda: FakeSettings())


AARAV = {
    "dept_code": "CSE",
    "bio": "Interested in on-device deep learning for agriculture.",
    "interests": ["edge ai", "computer vision"],
    "skills": ["python", "pytorch", "deep learning"],
    "certificate_titles": ["Python for Everybody"],
}

EDGE_AI = {
    "title": "Edge AI for Agriculture",
    "description": (
        "Deploy deep learning models on low-power devices for crop disease "
        "detection in the field."
    ),
    "required_concepts": ["python", "pytorch", "deep learning", "computer vision"],
}


# -- Text builders (pure; the exact strings are contract) ---------------------


def test_student_text_shape():
    assert student_text(AARAV) == (
        "CSE student. Skills: python, pytorch, deep learning. "
        "Interests: edge ai, computer vision. "
        "Certificates: Python for Everybody. "
        "Interested in on-device deep learning for agriculture."
    )


def test_opening_text_shape():
    assert opening_text(EDGE_AI) == (
        "Edge AI for Agriculture. Deploy deep learning models on low-power "
        "devices for crop disease detection in the field. "
        "Requires: python, pytorch, deep learning, computer vision."
    )


def test_text_builders_tolerate_a_sparse_profile():
    """A student with no bio, skills or certificates must still embed."""
    text = student_text({"dept_code": "CSE", "skills": [], "interests": None, "bio": None})
    assert text.startswith("CSE student.")
    assert "None" not in text


def test_opening_text_tolerates_missing_description():
    text = opening_text({"title": "Untitled", "required_concepts": []})
    assert "None" not in text


# -- The model ----------------------------------------------------------------


def test_embedding_is_384_dimensional():
    """Must match the vector indexes in schema.cypher (audit H1)."""
    vectors = embedding.embed(["x"])
    assert len(vectors) == 1
    assert len(vectors[0]) == 384
    assert all(isinstance(v, float) for v in vectors[0])


def test_vectors_are_normalised():
    vector = embedding.embed_one("a certificate in deep learning")
    norm = sum(v * v for v in vector) ** 0.5
    assert norm == pytest.approx(1.0, abs=1e-5)


def test_embed_preserves_order_and_handles_a_batch():
    texts = ["python programming", "classical guitar", "deep learning"]
    vectors = embedding.embed(texts)
    assert len(vectors) == 3
    # The first and third are closer to each other than either is to the second.
    assert cosine(vectors[0], vectors[2]) > cosine(vectors[0], vectors[1])


def test_embed_of_nothing_is_nothing():
    assert embedding.embed([]) == []


def test_aarav_is_semantically_close_to_the_edge_ai_opening():
    """The G1 check: cosine(student_text(Aarav), opening_text(op-edge-ai)) > 0.3."""
    s, o = embedding.embed([student_text(AARAV), opening_text(EDGE_AI)])
    similarity = cosine(s, o)
    assert similarity > 0.3, f"cosine was {similarity:.3f}"


def test_unrelated_text_is_less_similar_than_related_text():
    unrelated = {
        "title": "Kathak Dance Workshop",
        "description": "Classical Indian dance technique and repertoire.",
        "required_concepts": ["dance"],
    }
    s, related, other = embedding.embed(
        [student_text(AARAV), opening_text(EDGE_AI), opening_text(unrelated)]
    )
    assert cosine(s, related) > cosine(s, other)


# -- cosine helper ------------------------------------------------------------


def test_cosine_edge_cases():
    assert cosine([], [1.0]) == 0.0
    assert cosine([0.0, 0.0], [1.0, 0.0]) == 0.0
    assert cosine([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    assert cosine([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)


def test_cosine_is_symmetric():
    a, b = embedding.embed(["pytorch", "deep learning"])
    assert cosine(a, b) == pytest.approx(cosine(b, a))
