from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_DIR = ROOT / "data" / "codex_discovery" / "candidates"
REQUIRED = {
    "title",
    "content_type",
    "source",
    "date",
    "short_summary",
    "credibility",
    "novelty",
    "relevance",
    "why_it_matters",
    "why_maybe_not",
    "uncertainty",
    "route_suggestion",
}
LEVELS = {"high", "medium", "low"}
NOVELTY = {"breakout", "notable", "incremental"}


def main() -> int:
    errors: list[str] = []
    files = sorted(CANDIDATE_DIR.glob("*.jsonl"))
    for path in files:
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"{path.relative_to(ROOT)}:{lineno}: invalid JSON: {exc}")
                continue
            missing = sorted(REQUIRED - set(record))
            if missing:
                errors.append(f"{path.relative_to(ROOT)}:{lineno}: missing {', '.join(missing)}")
            if not (record.get("url") or record.get("evidence_note")):
                errors.append(f"{path.relative_to(ROOT)}:{lineno}: requires url or evidence_note")
            if record.get("credibility") not in LEVELS:
                errors.append(f"{path.relative_to(ROOT)}:{lineno}: credibility must be high/medium/low")
            if record.get("relevance") not in LEVELS:
                errors.append(f"{path.relative_to(ROOT)}:{lineno}: relevance must be high/medium/low")
            if record.get("novelty") not in NOVELTY:
                errors.append(f"{path.relative_to(ROOT)}:{lineno}: novelty must be breakout/notable/incremental")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"validated_files={len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
