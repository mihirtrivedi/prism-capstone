"""One-command routing evaluation script for Prism Gateway.
Evaluates the 'auto' alias router against data/routing_eval.jsonl.
Usage:
    python eval_router.py
"""

import json
from pathlib import Path
from prism.router import classify_prompt_difficulty

ROOT = Path(__file__).resolve().parent
EVAL_PATH = ROOT / "data" / "routing_eval.jsonl"


def run_eval():
    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        cases = [json.loads(line) for line in f if line.strip()]

    results = []
    correct = 0

    print(f"\nEvaluating {len(cases)} benchmark prompts for 'auto' routing difficulty:\n")
    print(f"{'ID':<12} {'EXPECTED':<10} {'ACTUAL':<10} {'STATUS':<8} {'PROMPT'}")
    print("-" * 80)

    for c in cases:
        actual_tier, reason = classify_prompt_difficulty(c["prompt"])
        is_correct = (actual_tier == c["expected_tier"])
        if is_correct:
            correct += 1
            status_str = "PASS"
        else:
            status_str = "FAIL"

        results.append({
            "id": c["id"],
            "expected": c["expected_tier"],
            "actual": actual_tier,
            "status": status_str,
            "reason": reason,
            "prompt": c["prompt"][:60] + "..."
        })

        print(f"{c['id']:<12} {c['expected_tier']:<10} {actual_tier:<10} {status_str:<8} {c['prompt'][:45]}...")

    accuracy = correct / len(cases) if cases else 0.0
    summary = {
        "total": len(cases),
        "correct": correct,
        "accuracy": round(accuracy, 4),
        "cases": results
    }

    print("-" * 80)
    print(f"Summary: {correct}/{len(cases)} correct ({accuracy * 100:.1f}% accuracy)\n")
    return summary


if __name__ == "__main__":
    run_eval()

