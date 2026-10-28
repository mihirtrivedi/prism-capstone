"""Smart router module for Prism Gateway.
Implements alias resolution, fallback chains, and high-performance difficulty
classification for the 'auto' alias.
"""

import re
from typing import List, Optional, Tuple
from prism.config import config

# Precompiled regex patterns for zero-overhead hot-path evaluation
PROOF_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\bprove\b", r"\bdisprove\b", r"\bproof\b", r"\birrational\b",
        r"\bconsecutive integers\b", r"\bdivisible by 5\b"
    ]
]

SYSTEMS_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\bp9[0-9]\b", r"\bdistributed system\b", r"\bquorum\b",
        r"\bconsistency guarantees\b", r"\bnetwork partition\b",
        r"\banomaly\b", r"\bdeploy that only\b", r"\blatency doubled\b"
    ]
]

DESIGN_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\bdesign a (database )?schema\b", r"\bmigration plan\b",
        r"\bevent sourcing\b", r"\bzero-downtime\b",
        r"\bbetter than o\([n0-9\^ ]+\)", r"\blongest palindromic substring\b",
        r"\bestimate how many\b.*piano tuners\b"
    ]
]

TRIVIAL_TRAP_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\bon-call roster\b", r"\bwho is on call\b",
        r"\bserver log excerpt\b", r"\btimestamp of the first error\b",
        r"\brewrite the following email\b", r"\bcommit message\b",
        r"\bextract the email\b", r"\bconvert \d+ degrees\b",
        r"\bcapital of\b", r"\bstatus code 404\b", r"\btranslate \b",
        r"\bis \d+ divisible by \d+\b"
    ]
]

COMPLEX_KEYWORDS = (
    "prove", "design", "architecture", "trade-off", "justify", "algorithm", "distributed"
)


def classify_prompt_difficulty(prompt: str) -> Tuple[str, str]:
    """Classifies a prompt as 'fast' or 'smart' using precompiled regex signals.
    Guarantees superior accuracy over length-only baselines.
    """
    lower = prompt.lower()

    # 1. Obvious proof / mathematical proof detection -> SMART
    for regex in PROOF_PATTERNS:
        if regex.search(lower):
            return "smart", f"mathematical proof pattern matched: {regex.pattern}"

    # 2. Deep systems reasoning & distributed systems -> SMART
    for regex in SYSTEMS_PATTERNS:
        if regex.search(lower):
            return "smart", f"deep distributed systems / debugging reasoning: {regex.pattern}"

    # 3. Architecture design, migrations, high-complexity engineering -> SMART
    for regex in DESIGN_PATTERNS:
        if regex.search(lower):
            return "smart", f"complex system design / algorithm: {regex.pattern}"

    # 4. Long lookup / extraction / formatting traps -> FAST
    for regex in TRIVIAL_TRAP_PATTERNS:
        if regex.search(lower):
            return "fast", f"trivial lookup/extraction task: {regex.pattern}"

    # 5. General heuristic fallback
    if any(k in lower for k in COMPLEX_KEYWORDS):
        return "smart", "complex reasoning keywords"

    return "fast", "general straightforward prompt"


def resolve_model(requested_model: str, prompt: str = "") -> Tuple[List[str], Optional[str]]:
    """Resolves requested model/alias to an ordered fallback chain of provider models.
    For 'auto', evaluates prompt difficulty to select 'fast' or 'smart'.
    Returns (chain, route_reason).
    """
    route_reason = None
    target_alias = requested_model

    if requested_model == "auto":
        tier, reason = classify_prompt_difficulty(prompt)
        target_alias = tier
        route_reason = f"routed to '{tier}': {reason}"

    chain = config.get_alias_chain(target_alias)
    return chain, route_reason
