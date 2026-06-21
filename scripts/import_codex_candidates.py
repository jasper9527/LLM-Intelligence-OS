from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from intel import (
    EVENTS_PATH,
    ROOT,
    classify_event,
    dedupe_events,
    load_events,
    normalize_list,
    route_event,
    save_events,
    signal_tag_for_content_type,
    stable_hash,
    taxonomy_sets,
    utc_now,
    load_routing_config,
    update_review_summary,
)

CANDIDATE_DIR = ROOT / "data" / "codex_discovery" / "candidates"
STATE_PATH = ROOT / "data" / "codex_discovery" / "import_state.json"


def load_state() -> set[str]:
    if not STATE_PATH.exists():
        return set()
    return set(json.loads(STATE_PATH.read_text(encoding="utf-8")).get("imported_candidate_ids", []))


def save_state(ids: set[str]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps({"imported_candidate_ids": sorted(ids)}, indent=2), encoding="utf-8")


def iter_candidates() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(CANDIDATE_DIR.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            record["candidate_file"] = str(path.relative_to(ROOT))
            records.append(record)
    return records


def candidate_id(record: dict[str, Any]) -> str:
    return record.get("candidate_id") or stable_hash([record.get("url", ""), record.get("title", ""), record.get("date", "")])


def to_event(record: dict[str, Any]) -> dict[str, Any]:
    cid = candidate_id(record)
    content_type = record.get("content_type", "note")
    event = {
        "id": stable_hash(["codex-discovery", record.get("url", ""), record.get("title", ""), record.get("date", "")]),
        "date": record.get("date", ""),
        "title": record.get("title", "Untitled"),
        "url": record.get("url", ""),
        "source": record.get("source", "Codex Discovery"),
        "source_id": record.get("source_id", "codex-discovery"),
        "source_type": record.get("source_type", "codex_discovery"),
        "content_type": content_type,
        "short_summary": record.get("short_summary", record.get("summary", "")),
        "entities": normalize_list(record.get("entities")),
        "entity_tags": normalize_list(record.get("entity_tags", record.get("entities"))),
        "area_tags": normalize_list(record.get("area_tags")),
        "method_tags": normalize_list(record.get("method_tags")),
        "task_tags": normalize_list(record.get("task_tags")),
        "job_tags": normalize_list(record.get("job_tags")),
        "signal_tags": normalize_list(record.get("signal_tags")) + [signal_tag_for_content_type(content_type)],
        "novelty": record.get("novelty", "notable"),
        "credibility": record.get("credibility", "medium"),
        "relevance": record.get("relevance", "medium"),
        "routed_to": normalize_list(record.get("route_suggestion")),
        "status": "draft",
        "ingestion_mode": "codex_discovery",
        "collector_kind": "codex_discovery",
        "snapshot_path": record.get("candidate_file", ""),
        "collected_at": utc_now(),
        "problem": record.get("problem", ""),
        "method_summary": record.get("method_summary", ""),
        "key_contribution": record.get("key_contribution", ""),
        "limitations": record.get("limitations", record.get("uncertainty", "")),
        "why_it_matters": record.get("why_it_matters", ""),
        "why_maybe_not": record.get("why_maybe_not", ""),
        "company": record.get("company", ""),
        "team": record.get("team", ""),
        "location": record.get("location", ""),
        "job_species": record.get("job_species", "general"),
        "positive_signals": normalize_list(record.get("positive_signals")),
        "red_flags": normalize_list(record.get("red_flags")),
        "common_keywords": normalize_list(record.get("common_keywords")),
        "codex_candidate_id": cid,
        "uncertainty": record.get("uncertainty", ""),
    }
    event, _ = classify_event(event, taxonomy_sets())
    event = route_event(event, load_routing_config())
    return event


def main() -> int:
    imported = load_state()
    new_events = []
    for record in iter_candidates():
        cid = candidate_id(record)
        if cid in imported:
            continue
        new_events.append(to_event(record))
        imported.add(cid)
    if new_events:
        save_events(dedupe_events(load_events() + new_events))
        save_state(imported)
    update_review_summary()
    print(f"imported={len(new_events)} events_path={EVENTS_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
