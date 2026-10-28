"""Automated unit test suite for Prism LLM Gateway.
Tests critical flows: cost math, rate limiter, cache decisions, tenant isolation, and routing.
Run with:
    python -m unittest discover tests
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from prism.config import config
from prism.cost_calculator import calculate_cost
from prism.rate_limiter import SlidingWindowRateLimiter
from prism.router import classify_prompt_difficulty, resolve_model
from prism.semantic_cache import clean_prompt_text, cosine_similarity, vectorize


class TestCostCalculator(unittest.TestCase):
    def test_alpha_small_cost(self):
        # input: $0.15/1M, output: $0.60/1M
        # 1000 input, 2000 output
        cost = calculate_cost("alpha-small", 1000, 2000)
        expected = (1000 * 0.15 / 1_000_000) + (2000 * 0.60 / 1_000_000)
        self.assertAlmostEqual(cost, expected, places=6)

    def test_cache_hit_zero_cost(self):
        cost = calculate_cost("alpha-small", 1000, 2000, is_cache_hit=True)
        self.assertEqual(cost, 0.0)

    def test_unknown_model_returns_zero(self):
        cost = calculate_cost("nonexistent-model", 500, 500)
        self.assertEqual(cost, 0.0)


class TestRateLimiter(unittest.TestCase):
    def test_rate_limit_admit_and_reject(self):
        limiter = SlidingWindowRateLimiter()
        key = "test-key-limit-1"
        limit = 5

        # First 5 should succeed
        for _ in range(limit):
            self.assertTrue(limiter.check_and_acquire(key, limit))

        # 6th must fail immediately
        self.assertFalse(limiter.check_and_acquire(key, limit))

    def test_rate_limit_key_isolation(self):
        limiter = SlidingWindowRateLimiter()
        limit = 3
        for _ in range(limit):
            limiter.check_and_acquire("key-a", limit)

        # key-a is saturated, but key-b must still be admitted
        self.assertFalse(limiter.check_and_acquire("key-a", limit))
        self.assertTrue(limiter.check_and_acquire("key-b", limit))


class TestSemanticCache(unittest.TestCase):
    def test_exact_paraphrase_similarity(self):
        p1 = "(1a2b3c4d) How do I reset my password on the dashboard?"
        p2 = "(1a2b3c4d) What are the steps to reset my dashboard password?"
        v1 = vectorize(p1)
        v2 = vectorize(p2)
        sim = cosine_similarity(v1, v2)
        self.assertGreaterEqual(sim, 0.85, "Paraphrase A must hit similarity threshold")

    def test_paraphrase_refund_policy(self):
        p1 = "What is the refund policy for annual plans?"
        p2 = "If I bought an annual plan, can I get my money back?"
        v1 = vectorize(p1)
        v2 = vectorize(p2)
        sim = cosine_similarity(v1, v2)
        self.assertGreaterEqual(sim, 0.85, "Paraphrase B must hit similarity threshold")

    def test_near_miss_different_intent(self):
        p1 = "How do I reset my password on the dashboard?"
        p_near = "How do I reset my two-factor authentication on the dashboard?"
        v1 = vectorize(p1)
        v_near = vectorize(p_near)
        sim = cosine_similarity(v1, v_near)
        self.assertLess(sim, 0.85, "Near-miss (2FA vs password) must NOT hit 0.85 threshold")

    def test_salt_stripping(self):
        raw = "(7f8a9b0c) Explain server sent events."
        clean = clean_prompt_text(raw)
        self.assertEqual(clean, "Explain server sent events.")


class TestSmartRouter(unittest.TestCase):
    def test_short_hard_proof_routes_smart(self):
        tier, reason = classify_prompt_difficulty("Prove that the square root of 2 is irrational.")
        self.assertEqual(tier, "smart")

    def test_long_trivial_roster_routes_fast(self):
        roster_prompt = (
            "Here is our on-call roster for the next two weeks: Monday - Priya, "
            "Tuesday - Chen, Wednesday - Amara, Thursday - Diego. Who is on call this Thursday?"
        )
        tier, reason = classify_prompt_difficulty(roster_prompt)
        self.assertEqual(tier, "fast")

    def test_alias_chain_resolution(self):
        fast_chain, _ = resolve_model("fast")
        self.assertEqual(fast_chain, ["alpha-small", "beta-small"])

        smart_chain, _ = resolve_model("smart")
        self.assertEqual(smart_chain, ["alpha-large", "beta-large"])


if __name__ == "__main__":
    unittest.main()
