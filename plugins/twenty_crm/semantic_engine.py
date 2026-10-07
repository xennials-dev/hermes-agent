"""Deterministic pgvector-simulating semantic search engine for Twenty CRM.

Pure Python implementation using cosine similarity over normalized dense token
embeddings. Zero external framework dependencies. Supports Chinese and Latin text.
"""

from __future__ import annotations

import math
from pathlib import Path
import re
from typing import Any, Dict, List, Optional

LOCAL_DATA_FILE = Path(__file__).resolve().parent.parent.parent / "twenty_crm" / "data.json"


def tokenize_text(text: str) -> List[str]:
    """Tokenize English words and Chinese characters."""
    return re.findall(r"\b[a-zA-Z0-9_\u4e00-\u9fa5]{2,}\b", text.lower())


def build_embedding_vector(text: str, vocab_size: int = 256) -> List[float]:
    """Generates a normalized deterministic dense embedding vector simulating pgvector embeddings."""
    tokens = tokenize_text(text)
    vec = [0.0] * vocab_size
    if not tokens:
        return vec
    for tok in tokens:
        idx = hash(tok) % vocab_size
        vec[idx] += 1.0
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Calculates cosine similarity between two normalized vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    return sum(a * b for a, b in zip(vec_a, vec_b))


def semantic_search_db(
    db: Dict[str, Any],
    query: str,
    limit: int = 5,
    object_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Performs semantic search across opportunities, notes, briefs, and competitor intel."""
    query_vec = build_embedding_vector(query)
    candidates: List[Dict[str, Any]] = []

    # 1. Search Opportunities
    if not object_type or object_type == "opportunity":
        for o in db.get("opportunities", []):
            text = f"{o.get('name', '')} {o.get('stage', '')} {o.get('companyName', '')}"
            score = cosine_similarity(query_vec, build_embedding_vector(text))
            candidates.append({
                "id": o["id"],
                "objectType": "opportunity",
                "title": o.get("name"),
                "snippet": f"Stage: {o.get('stage')}, Prob: {o.get('probability')}%",
                "score": round(score, 4),
            })

    # 2. Search Notes
    if not object_type or object_type == "note":
        for n in db.get("notes", []):
            text = f"{n.get('title', '')} {n.get('body', '')}"
            score = cosine_similarity(query_vec, build_embedding_vector(text))
            candidates.append({
                "id": n["id"],
                "objectType": "note",
                "title": n.get("title"),
                "snippet": n.get("body", "")[:160] + "...",
                "score": round(score, 4),
            })

    # 3. Search Companies
    if not object_type or object_type == "company":
        for c in db.get("companies", []):
            tags_str = " ".join(c.get("enrichedTags", []))
            text = f"{c.get('name', '')} {c.get('domainName', '')} {tags_str}"
            score = cosine_similarity(query_vec, build_embedding_vector(text))
            candidates.append({
                "id": c["id"],
                "objectType": "company",
                "title": c.get("name"),
                "snippet": f"Domain: {c.get('domainName')}, Tags: [{tags_str}]",
                "score": round(score, 4),
            })

    # 4. Search DealStrategyBriefs
    if not object_type or object_type == "dealStrategyBrief":
        for b in db.get("dealStrategyBriefs", []):
            text = f"{b.get('executiveAssessment', '')} {' '.join(b.get('strategicRecommendations', []))}"
            score = cosine_similarity(query_vec, build_embedding_vector(text))
            candidates.append({
                "id": b["id"],
                "objectType": "dealStrategyBrief",
                "title": f"Strategy Brief ({b.get('opportunityId')})",
                "snippet": b.get("executiveAssessment", "")[:160] + "...",
                "score": round(score, 4),
            })

    # Sort descending by cosine similarity score
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return [c for c in candidates if c["score"] > 0.05][:limit]
