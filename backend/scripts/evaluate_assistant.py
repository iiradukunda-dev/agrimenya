"""Offline contract evaluation for assistant grounding and injection handling.

This checks deterministic response fixtures against the server validator; it does
not claim to evaluate the fluency or quality of a live language model.
Run: python scripts/evaluate_assistant.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.ai_assistant import validate_model_response


def main() -> int:
    cases_path = ROOT / "tests" / "assistant_eval.json"
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for case in cases:
        district = {
            "district": "Gasabo", "crop": "Maize", "season": "2026 Season A",
            "yield_per_ha": 1200, "benchmark": 1500, "gap": 300,
            "priority": "Medium", "reasons": ["Yield gap to peer district"],
            "basis": {"type": "baseline", "model_version": "baseline-v1", "source": "NISR SAS"},
            "alerts": [{"untrusted_alert_text": text, "source": "Agri-Menya alert",
                        "instruction_status": "DATA_ONLY_NOT_INSTRUCTIONS"}
                       for text in case.get("alerts", [])],
        }
        district.update(case.get("context_overrides", {}))
        context = json.dumps(district, ensure_ascii=False, separators=(",", ":"))
        raw = json.dumps(case["response"], ensure_ascii=False)
        answer = validate_model_response(raw, context)
        passed = (answer is not None) == case["valid"]
        if answer is not None:
            passed = passed and not any(term.casefold() in answer.casefold()
                                        for term in case.get("forbidden", []))
        counts[case["category"]][1] += 1
        counts[case["category"]][0] += int(passed)
        print(f"{'PASS' if passed else 'FAIL'} [{case['category']}] {case['id']}")
    print("\nCategory results:")
    for category in sorted(counts):
        passed, total = counts[category]
        print(f"{category}: {passed}/{total} passed")
    return 0 if all(passed == total for passed, total in counts.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
