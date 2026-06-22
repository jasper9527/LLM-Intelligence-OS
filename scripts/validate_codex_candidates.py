from intel import validate_codex_candidates
import json


if __name__ == "__main__":
    result = validate_codex_candidates()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1 if result["invalid_candidates"] else 0)
