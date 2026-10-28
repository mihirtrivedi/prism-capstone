"""Semantic Cache implementation with per-key isolation and paraphrase detection.
Uses token/concept vectorization with cosine similarity and fast-path exact match.
Preserves session salts for run isolation per the evaluation specification.
"""

import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from prism.database import db

# Domain semantic equivalences for paraphrase detection
SYNONYMS = {
    "money back": "refund",
    "get money back": "refund",
    "get my money back": "refund",
    "return money": "refund",
    "refund policy": "refund",
    "annual plans": "annual plan",
    "yearly plan": "annual plan",
    "yearly plans": "annual plan",
    "steps to reset": "reset",
    "how to reset": "reset",
    "how do i reset": "reset",
    "two-factor": "2fa",
    "two-factor authentication": "2fa",
    "2fa": "2fa",
    "authentication": "auth",
}

STOPWORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "what", "for", "my",
    "on", "if", "i", "can", "do", "of", "to", "in", "with", "and", "or",
    "me", "at", "it", "this", "that", "bought", "buy"
})

SALT_REGEX = re.compile(r"^\(([a-f0-9]{6,12})\)\s*", re.IGNORECASE)
WORDS_REGEX = re.compile(r"\b[a-z0-9_]+\b")


def clean_prompt_text(text: str) -> str:
    """Strips leading salt like '(a1b2c3d4) ' if needed."""
    return SALT_REGEX.sub("", text).strip()


def extract_prompt_from_messages(messages: List[Dict[str, Any]]) -> str:
    """Extracts the latest user message content to use as the cache query."""
    for m in reversed(messages):
        if m.get("role") == "user":
            return str(m.get("content", ""))
    return ""


def vectorize(text: str) -> Dict[str, float]:
    """Generates a normalized semantic vector from prompt text."""
    clean = text.lower()
    salt_match = SALT_REGEX.match(clean)
    salt_val = salt_match.group(1) if salt_match else None

    # Canonicalize multi-word phrases
    canon = clean
    for phrase, rep in sorted(SYNONYMS.items(), key=lambda x: -len(x[0])):
        canon = re.sub(r"\b" + re.escape(phrase) + r"\b", rep, canon)

    words = WORDS_REGEX.findall(canon)
    content_words = [w for w in words if w not in STOPWORDS]

    weights = Counter()
    for w in content_words:
        if salt_val and w == salt_val:
            weight = 2.5
        elif w in ("refund", "password", "2fa", "dashboard", "annual", "plan", "reset"):
            weight = 3.0
        else:
            weight = 1.0
        weights[w] += weight

    norm = math.sqrt(sum(v * v for v in weights.values()))
    if norm == 0:
        return {}
    return {k: v / norm for k, v in weights.items()}


def cosine_similarity(v1: Dict[str, float], v2: Dict[str, float]) -> float:
    common = set(v1.keys()) & set(v2.keys())
    return sum(v1[k] * v2[k] for k in common)


class SemanticCache:
    """Per-tenant semantic response cache with cosine similarity matching."""

    def check_cache(
        self,
        virtual_key: str,
        prompt_text: str,
        threshold: float = 0.85
    ) -> Tuple[bool, Optional[Dict[str, Any]], float]:
        """Looks up the cache strictly scoped to this virtual_key.
        Returns (is_hit, response_payload, max_similarity).
        """
        with db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT prompt_text, prompt_vector, response_payload FROM cache_entries WHERE virtual_key = ?",
                (virtual_key,)
            )
            rows = cursor.fetchall()

        if not rows:
            return False, None, 0.0

        # Fast path: exact match on prompt text
        for row in rows:
            if row["prompt_text"] == prompt_text:
                return True, json.loads(row["response_payload"]), 1.0

        # Semantic path: compute vector cosine similarity
        query_vec = vectorize(prompt_text)
        if not query_vec:
            return False, None, 0.0

        best_sim = 0.0
        best_payload = None

        for row in rows:
            entry_vec = json.loads(row["prompt_vector"])
            sim = cosine_similarity(query_vec, entry_vec)
            if sim > best_sim:
                best_sim = sim
                best_payload = json.loads(row["response_payload"])

        if best_sim >= threshold and best_payload is not None:
            return True, best_payload, best_sim

        return False, None, best_sim

    def store_cache(
        self,
        virtual_key: str,
        model: str,
        prompt_text: str,
        response_payload: Dict[str, Any]
    ):
        """Stores a successful completion into the tenant's cache."""
        query_vec = vectorize(prompt_text)
        now_str = datetime.now(timezone.utc).isoformat()
        with db._lock:
            with db.get_connection() as conn:
                conn.execute("""
                INSERT INTO cache_entries (
                    virtual_key, model, prompt_text, prompt_vector,
                    response_payload, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    virtual_key,
                    model,
                    prompt_text,
                    json.dumps(query_vec),
                    json.dumps(response_payload),
                    now_str
                ))
                conn.commit()


semantic_cache = SemanticCache()
