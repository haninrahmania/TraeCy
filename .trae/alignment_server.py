"""
Alignment MCP Server
====================

A custom MCP server for the cross-team PM pipeline. It exposes ONE tool,
`score_alignment`, which takes a team's completed deliverables and that team's
goals, and returns a semantic-similarity match score per goal plus the
deliverable ids that support each goal.

Design notes:
- This server does deterministic MATH only. It does not fetch data and holds no
  credentials (the Alignment agent passes goals + deliverables in). Qualitative
  judgment (on_track / at_risk / off_track + rationale) is the agent's job, via
  the `assess-goal-alignment` skill. Keeping scoring here makes it reproducible.

- Two scoring backends:
    * "embeddings" (default): sentence-transformers all-MiniLM-L6-v2. Captures
      semantic similarity (synonyms, paraphrase). Downloads the model on first
      run from Hugging Face -> pre-download at home before the event.
    * "tfidf": scikit-learn TF-IDF cosine. No download, fully offline, lexical
      only. Resilience fallback if venue wifi blocks the model download.
  Select with the env var: ALIGNMENT_BACKEND=tfidf (defaults to embeddings)

- IMPORTANT: thresholds are backend-specific. Embedding cosine for related pairs
  sits ~0.4-0.7; TF-IDF for the same pairs sits much lower (~0.2-0.3). The
  default supporting threshold below assumes embeddings. If you switch to
  tfidf, lower it (≈0.10) and re-tune the skill's status thresholds to match.

Usage:
    python alignment_server.py

For TRAE config (custom MCP via settings -> command/args):
    command: python
    args: ["/abs/path/to/alignment_server.py"]
    env: {}  # or {"ALIGNMENT_BACKEND": "tfidf"}
"""

import os
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("alignment")

BACKEND = os.environ.get("ALIGNMENT_BACKEND", "embeddings").lower()
_DEFAULT_THRESHOLD = 0.10 if BACKEND == "tfidf" else 0.40

_model = None


def _text_of(item: dict) -> str:
    """Flatten a deliverable (or goal) into a single string for vectorizing."""
    title = (item.get("title") or item.get("goal_text") or "").strip()
    desc = (item.get("description") or "").strip()
    return f"{title}. {desc}".strip(". ").strip()


def _sim_matrix(goal_texts: list[str], deliv_texts: list[str]):
    """Return an [n_goals x n_deliverables] cosine-similarity matrix."""
    if not goal_texts or not deliv_texts:
        return [[0.0] * len(deliv_texts) for _ in goal_texts]

    if BACKEND == "tfidf":
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vec = TfidfVectorizer(stop_words="english")
        M = vec.fit_transform(goal_texts + deliv_texts)
        G, D = M[: len(goal_texts)], M[len(goal_texts) :]
        return cosine_similarity(G, D).tolist()

    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("all-MiniLM-L6-v2")
    g = _model.encode(goal_texts, normalize_embeddings=True)
    d = _model.encode(deliv_texts, normalize_embeddings=True)
    return (g @ d.T).tolist()

# def _status(match_score, supporting):
#     if not supporting:        return "off_track"   # unaddressed
#     if match_score >= 0.40:   return "on_track"
#     if match_score >= 0.26:   return "at_risk"
#     return "off_track"


def _score(deliverables: list[dict], goals: list[dict], threshold: float) -> dict:
    """Core scoring. Pure function, no I/O. Unit-testable."""
    deliv_texts = [_text_of(d) for d in deliverables]
    goal_texts = [_text_of(g) for g in goals]
    sim = _sim_matrix(goal_texts, deliv_texts)

    results = []
    for i, goal in enumerate(goals):
        row = sim[i] if i < len(sim) else []
        per_deliverable = [
            {"id": deliverables[j].get("id"), "score": round(float(row[j]), 3)}
            for j in range(len(deliverables))
        ]
        supporting = [pd["id"] for pd in per_deliverable if pd["score"] >= threshold]
        match_score = round(
            max((pd["score"] for pd in per_deliverable), default=0.0), 3
        )
        results.append(
            {
                "goal_id": goal.get("goal_id"),
                "goal_text": goal.get("goal_text"),
                "match_score": match_score,
                # "status": _status(match_score, supporting),
                "supporting_deliverables": supporting,
                "per_deliverable": sorted(per_deliverable, key=lambda x: -x["score"]),
            }
        )
    return {"backend": BACKEND, "threshold": threshold, "results": results}


@mcp.tool()
def score_alignment(
    deliverables: list[dict],
    goals: list[dict],
    threshold: float = _DEFAULT_THRESHOLD,
) -> dict:
    """Score how well a team's completed deliverables advance its goals.

    Args:
        deliverables: list of {id, title, description} for completed work.
        goals: list of {goal_id, goal_text} for the team's goals/KPIs.
        threshold: minimum cosine similarity for a deliverable to count as
            "supporting" a goal. Backend-specific (see module docstring).

    Returns:
        {
          "backend": str,
          "threshold": float,
          "results": [
            {
              "goal_id": str,
              "goal_text": str,
              "match_score": float,        # best deliverable match, 0.0-1.0
              "supporting_deliverables": [id, ...],
              "per_deliverable": [{"id": id, "score": float}, ...]
            }
          ]
        }

    A goal with an empty supporting_deliverables list is unaddressed.
    """
    return _score(deliverables, goals, threshold)


if __name__ == "__main__":
    if BACKEND == "embeddings":
        _sim_matrix(["warmup"], ["warmup"])   # loads the model at startup, not on first query
    mcp.run()
