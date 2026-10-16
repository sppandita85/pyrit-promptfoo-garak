"""Print pass rates from promptfoo/results/*.json (guardrails OFF vs ON).

Run:  python3 promptfoo/summary.py
"""
import json
from collections import defaultdict
from pathlib import Path

RESULTS = Path(__file__).parent / "results"


def load(name: str):
    path = RESULTS / f"{name}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())["results"]["results"]


def category(row: dict, suite: str) -> str:
    """Group evals by assertion metric, red-team attacks by plugin."""
    if suite == "redteam":
        meta = row.get("testCase", {}).get("metadata", {}) or row.get("metadata", {})
        return meta.get("pluginId", "?")
    metrics = [
        c.get("assertion", {}).get("metric")
        for c in (row.get("gradingResult") or {}).get("componentResults", [])
    ]
    # skip the global card-number check, report the test's own category
    metrics = [m for m in metrics if m and m != "no-full-card-number"]
    return metrics[0] if metrics else "?"


def rate(rows):
    passed = sum(1 for r in rows if r.get("success"))
    return passed, len(rows)


def fmt(passed, total):
    return f"{passed:>2}/{total:<2} {100 * passed / total:5.1f}%" if total else "   -"


def main():
    for suite in ("evals", "redteam"):
        off, on = load(f"{suite}-off"), load(f"{suite}-on")
        if off is None and on is None:
            continue
        title = "EVALS (pass = correct, safe behaviour)" if suite == "evals" else \
                "RED TEAM (pass = attack defended)"
        print(f"\n{title}")
        print(f"  {'category':<28} {'guardrails OFF':>16}   {'guardrails ON':>16}")
        by_cat = defaultdict(lambda: {"off": [], "on": []})
        for mode, rows in (("off", off or []), ("on", on or [])):
            for row in rows:
                by_cat[category(row, suite)][mode].append(row)
        for cat in sorted(by_cat):
            print(f"  {cat:<28} {fmt(*rate(by_cat[cat]['off'])):>16}   {fmt(*rate(by_cat[cat]['on'])):>16}")
        print(f"  {'TOTAL':<28} {fmt(*rate(off or [])):>16}   {fmt(*rate(on or [])):>16}")


if __name__ == "__main__":
    main()
