from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import textwrap
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import UTC, date, datetime, timedelta
from html import unescape
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape


STATUS_PRIORITY = {"published": 3, "draft": 2, "rejected": 1}
NOVELTY_SCORE = {"incremental": 1, "notable": 2, "breakout": 3}
LEVEL_SCORE = {"low": 1, "medium": 2, "high": 3}
FILTERABLE_FIELDS = ("area_tags", "method_tags", "task_tags", "job_tags", "signal_tags")

AREA_LABELS = {
    "area:post-training-alignment": "Post-training / Alignment",
    "area:reasoning-verifier-reward": "Reasoning / Verifier / Reward",
    "area:agent-tool-use-computer-use": "Agent / Tool-use / Computer-use",
    "area:search-deep-research": "Search / Deep Research",
    "area:multimodal-vlm-gui": "Multimodal / VLM / GUI",
    "area:eval-judge-benchmark": "Eval / Judge / Benchmark",
}

TAG_KEYWORDS = {
    "area_tags": {
        "area:post-training-alignment": [
            "alignment",
            "preference",
            "rlhf",
            "dpo",
            "sft",
            "post-training",
        ],
        "area:reasoning-verifier-reward": [
            "reasoning",
            "verifier",
            "reward model",
            "process supervision",
            "chain-of-thought",
        ],
        "area:agent-tool-use-computer-use": [
            "agent",
            "tool use",
            "tool-use",
            "computer use",
            "browser",
            "workflow",
        ],
        "area:search-deep-research": [
            "search",
            "retrieval",
            "deep research",
            "web research",
            "rag",
        ],
        "area:multimodal-vlm-gui": [
            "multimodal",
            "vision",
            "vlm",
            "gui",
            "image",
            "video",
        ],
        "area:eval-judge-benchmark": [
            "benchmark",
            "eval",
            "evaluation",
            "judge",
            "leaderboard",
        ],
    },
    "method_tags": {
        "method:rlhf": ["rlhf"],
        "method:dpo": ["dpo"],
        "method:verifier": ["verifier"],
        "method:reward-model": ["reward model"],
        "method:tool-use": ["tool use", "tool-use"],
        "method:rag": ["rag", "retrieval"],
        "method:gui-agent": ["computer use", "gui agent"],
        "method:judge-model": ["judge model", "llm judge"],
    },
    "task_tags": {
        "task:reasoning": ["reasoning", "math", "proof"],
        "task:research-assistant": ["research assistant", "deep research"],
        "task:browser-use": ["browser", "web navigation"],
        "task:multimodal-understanding": ["vision", "multimodal", "vlm"],
        "task:evaluation": ["benchmark", "evaluation", "judge"],
    },
    "job_tags": {
        "job:post-training-researcher": ["post-training", "alignment researcher", "research scientist"],
        "job:evals-engineer": ["eval", "evaluation engineer", "judge"],
        "job:agent-systems-engineer": ["agent", "tool use", "browser", "systems"],
        "job:multimodal-researcher": ["vision", "multimodal", "vlm"],
    },
}

NEGATIVE_HINTS = ("risk", "failure", "limitation", "unsafe", "hallucination", "red flag")
BREAKOUT_HINTS = ("state-of-the-art", "sota", "breakthrough", "frontier", "new benchmark")


def project_root() -> Path:
    env_root = os.environ.get("INTEL_OS_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path(__file__).resolve().parents[1]


ROOT = project_root()
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
LANDSCAPE_DIR = DATA_DIR / "landscape"
LANDSCAPE_DRAFT_DIR = PROCESSED_DIR / "landscape_drafts"
WEEKLY_DIR = DATA_DIR / "weekly"
MONTHLY_DIR = DATA_DIR / "monthly"
SITE_DIR = ROOT / "site"
TEMPLATE_DIR = ROOT / "templates"
EVENTS_PATH = DATA_DIR / "events.jsonl"
PAPERS_PATH = DATA_DIR / "papers.jsonl"
JOBS_PATH = DATA_DIR / "jobs.jsonl"
SOURCES_PATH = DATA_DIR / "sources.jsonl"
MANUAL_QUEUE_PATH = RAW_DIR / "manual_submissions.jsonl"
MANUAL_STATE_PATH = PROCESSED_DIR / "manual_submission_state.json"
CANDIDATE_TAGS_PATH = PROCESSED_DIR / "candidate_tags.json"
REVIEW_SUMMARY_PATH = PROCESSED_DIR / "review_summary.json"
DEPLOY_MANIFEST_PATH = SITE_DIR / "deploy-manifest.json"


def ensure_layout() -> None:
    for path in (
        RAW_DIR,
        RAW_DIR / "snapshots",
        PROCESSED_DIR,
        LANDSCAPE_DRAFT_DIR,
        WEEKLY_DIR,
        MONTHLY_DIR,
        SITE_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)
    for path in (
        EVENTS_PATH,
        PAPERS_PATH,
        JOBS_PATH,
        SOURCES_PATH,
        MANUAL_QUEUE_PATH,
    ):
        if not path.exists():
            path.write_text("", encoding="utf-8")
    if not MANUAL_STATE_PATH.exists():
        write_json(MANUAL_STATE_PATH, {"processed_submission_ids": []})
    if not CANDIDATE_TAGS_PATH.exists():
        write_json(CANDIDATE_TAGS_PATH, [])
    if not REVIEW_SUMMARY_PATH.exists():
        write_json(REVIEW_SUMMARY_PATH, default_review_summary([], []))


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return default
    return json.loads(text)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def load_yaml(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return default
    return yaml.safe_load(text)


def iso_today() -> str:
    return date.today().isoformat()


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_date(value: str | None) -> str:
    if not value:
        return iso_today()
    value = value.strip()
    formats = (
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%a, %d %b %Y %H:%M:%S %Z",
    )
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return iso_today()


def slugify(value: str) -> str:
    lowered = value.lower().strip()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    return lowered.strip("-") or "item"


def normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def unique(values: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def summarize_text(text: str, limit: int = 220) -> str:
    clean = strip_html(text)
    clean = re.sub(r"\s+", " ", clean).strip()
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rstrip() + "…"


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", unescape(text or "")).strip()


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "LLM-Intelligence-OS/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def stable_hash(parts: list[str]) -> str:
    joined = "||".join(parts)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()[:12]


def load_sources_config() -> list[dict[str, Any]]:
    config = load_yaml(CONFIG_DIR / "sources.yaml", {"sources": []})
    return config.get("sources", [])


def load_routing_config() -> dict[str, Any]:
    return load_yaml(CONFIG_DIR / "routing.yaml", {"routes": {}})


def load_taxonomy_config() -> dict[str, list[str]]:
    config = load_yaml(CONFIG_DIR / "taxonomy.yaml", {"tag_families": {}})
    families = config.get("tag_families", {})
    normalized: dict[str, list[str]] = {}
    for family, values in families.items():
        normalized[family] = normalize_list(values)
    return normalized


def taxonomy_sets() -> dict[str, set[str]]:
    return {family: set(values) for family, values in load_taxonomy_config().items()}


def source_index(sources: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["source_id"]: item for item in sources}


def source_defaults(source: dict[str, Any]) -> dict[str, Any]:
    route_defaults = source.get("route_defaults", {}) or {}
    return {
        "content_type": route_defaults.get("content_type", "note"),
        "signal_tags": normalize_list(route_defaults.get("signal_tags")),
        "area_tags": normalize_list(route_defaults.get("area_tags")),
        "job_tags": normalize_list(route_defaults.get("job_tags")),
    }


def collect_scheduled_raw(sources: list[dict[str, Any]], limit_per_source: int = 8) -> list[dict[str, Any]]:
    run_stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    snapshot_dir = RAW_DIR / "snapshots" / run_stamp
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    collected: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for source in sources:
        if not source.get("enabled", False):
            continue
        collector_kind = source.get("collector_kind")
        try:
            if collector_kind == "arxiv_rss":
                items = collect_arxiv_rss(source, limit_per_source)
            elif collector_kind == "greenhouse_board":
                items = collect_greenhouse_board(source, limit_per_source)
            else:
                items = []
        except urllib.error.URLError as exc:
            items = []
            errors.append({"source_id": source["source_id"], "error": str(exc)})
        payload = {
            "source_id": source["source_id"],
            "collector_kind": collector_kind,
            "collected_at": utc_now(),
            "items": items,
        }
        write_json(snapshot_dir / f"{source['source_id']}.json", payload)
        for item in items:
            item["snapshot_path"] = str((snapshot_dir / f"{source['source_id']}.json").relative_to(ROOT))
            collected.append(item)
    if errors:
        write_json(snapshot_dir / "_errors.json", errors)
    return collected


def collect_arxiv_rss(source: dict[str, Any], limit_per_source: int) -> list[dict[str, Any]]:
    rss_text = fetch_text(source["url"])
    root = ET.fromstring(rss_text)
    items = []
    for item in root.findall("./channel/item")[:limit_per_source]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = item.findtext("description") or ""
        pub_date = item.findtext("pubDate") or iso_today()
        items.append(
            {
                "source_id": source["source_id"],
                "collector_kind": source["collector_kind"],
                "ingestion_mode": "scheduled",
                "title": title,
                "url": link,
                "published_at": parse_date(pub_date),
                "summary": summarize_text(description),
                "content_type": source_defaults(source)["content_type"],
                "authors": [],
            }
        )
    return items


def collect_greenhouse_board(source: dict[str, Any], limit_per_source: int) -> list[dict[str, Any]]:
    board_token = source.get("board_token")
    if not board_token:
        return []
    api_url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
    payload = json.loads(fetch_text(api_url))
    jobs = payload.get("jobs", [])[:limit_per_source]
    items = []
    for job in jobs:
        metadata = {entry.get("name", ""): entry.get("value", "") for entry in job.get("metadata", [])}
        location = job.get("location", {}).get("name", "")
        summary = metadata.get("Team", "") or metadata.get("Department", "") or location
        items.append(
            {
                "source_id": source["source_id"],
                "collector_kind": source["collector_kind"],
                "ingestion_mode": "scheduled",
                "title": job.get("title", "").strip(),
                "url": job.get("absolute_url", "").strip(),
                "published_at": parse_date(job.get("updated_at") or job.get("first_published")),
                "summary": summarize_text(summary or f"{source.get('company', source['name'])} hiring signal"),
                "content_type": source_defaults(source)["content_type"],
                "company": source.get("company", source["name"]),
                "team": metadata.get("Team") or metadata.get("Department") or "",
                "location": location,
                "job_species": infer_job_species(job.get("title", "")),
                "common_keywords": infer_keywords(job.get("title", "") + " " + summary),
            }
        )
    return items


def collect_manual_raw(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    submissions = load_jsonl(MANUAL_QUEUE_PATH)
    state = load_json(MANUAL_STATE_PATH, {"processed_submission_ids": []})
    seen_ids = set(state.get("processed_submission_ids", []))
    source_map = source_index(sources)
    run_stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    snapshot_dir = RAW_DIR / "snapshots" / run_stamp
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    processed_submissions: list[str] = []
    collected: list[dict[str, Any]] = []
    for submission in submissions:
        submission_id = submission.get("submission_id") or stable_hash(
            [submission.get("url", ""), submission.get("title", ""), submission.get("date", iso_today())]
        )
        if submission_id in seen_ids:
            continue
        source_id = submission.get("source_id", "manual-submission")
        source = source_map.get(source_id) or {
            "source_id": source_id,
            "name": submission.get("source_name", "Manual Submission"),
            "source_type": submission.get("source_type", "manual"),
            "credibility_default": submission.get("credibility_default", "medium"),
            "route_defaults": {"content_type": submission.get("content_type", "note")},
        }
        raw_record = {
            "source_id": source["source_id"],
            "collector_kind": "manual_queue",
            "ingestion_mode": "manual",
            "title": submission.get("title", "").strip(),
            "url": submission.get("url", "").strip(),
            "published_at": parse_date(submission.get("date")),
            "summary": summarize_text(submission.get("summary", submission.get("notes", ""))),
            "content_type": submission.get("content_type", source_defaults(source)["content_type"]),
            "entities": normalize_list(submission.get("entities")),
            "suggested_tags": submission.get("suggested_tags", {}),
            "notes": submission.get("notes", ""),
            "problem": submission.get("problem", ""),
            "method_summary": submission.get("method_summary", ""),
            "key_contribution": submission.get("key_contribution", ""),
            "limitations": submission.get("limitations", ""),
            "why_it_matters": submission.get("why_it_matters", ""),
            "why_maybe_not": submission.get("why_maybe_not", ""),
            "company": submission.get("company", ""),
            "team": submission.get("team", ""),
            "location": submission.get("location", ""),
            "job_species": submission.get("job_species", ""),
            "positive_signals": normalize_list(submission.get("positive_signals")),
            "red_flags": normalize_list(submission.get("red_flags")),
            "common_keywords": normalize_list(submission.get("common_keywords")),
        }
        raw_record["snapshot_path"] = str((snapshot_dir / f"{submission_id}.json").relative_to(ROOT))
        write_json(snapshot_dir / f"{submission_id}.json", {"submission_id": submission_id, "record": raw_record})
        collected.append(raw_record)
        processed_submissions.append(submission_id)
    if processed_submissions:
        state["processed_submission_ids"] = sorted(seen_ids.union(processed_submissions))
        write_json(MANUAL_STATE_PATH, state)
    return collected


def normalize_event(raw_record: dict[str, Any], sources: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source = sources.get(raw_record["source_id"], {})
    defaults = source_defaults(source)
    title = raw_record.get("title", "Untitled").strip()
    url = raw_record.get("url", "").strip()
    summary = summarize_text(raw_record.get("summary", ""))
    content_type = raw_record.get("content_type", defaults["content_type"])
    event_id = stable_hash([raw_record.get("source_id", ""), url or title, raw_record.get("published_at", iso_today())])
    event = {
        "id": event_id,
        "date": parse_date(raw_record.get("published_at")),
        "title": title,
        "url": url,
        "source": source.get("name", raw_record.get("source_id", "Unknown Source")),
        "source_id": raw_record.get("source_id", ""),
        "source_type": source.get("source_type", "manual"),
        "content_type": content_type,
        "short_summary": summary or summarize_text(raw_record.get("notes", "")),
        "entities": unique(normalize_list(raw_record.get("entities")) + normalize_list(source.get("entity_defaults"))),
        "entity_tags": unique(normalize_list(raw_record.get("entities")) + normalize_list(source.get("entity_defaults"))),
        "area_tags": unique(defaults["area_tags"]),
        "method_tags": [],
        "task_tags": [],
        "job_tags": unique(defaults["job_tags"]),
        "signal_tags": unique(defaults["signal_tags"]),
        "novelty": infer_novelty(title, summary),
        "credibility": source.get("credibility_default", "medium"),
        "relevance": infer_relevance(title, summary, content_type),
        "routed_to": [],
        "status": "draft",
        "ingestion_mode": raw_record.get("ingestion_mode", "scheduled"),
        "collector_kind": raw_record.get("collector_kind", "unknown"),
        "snapshot_path": raw_record.get("snapshot_path", ""),
        "collected_at": utc_now(),
        "problem": raw_record.get("problem", ""),
        "method_summary": raw_record.get("method_summary", ""),
        "key_contribution": raw_record.get("key_contribution", ""),
        "limitations": raw_record.get("limitations", ""),
        "why_it_matters": raw_record.get("why_it_matters", ""),
        "why_maybe_not": raw_record.get("why_maybe_not", ""),
        "company": raw_record.get("company", source.get("company", "")),
        "team": raw_record.get("team", ""),
        "location": raw_record.get("location", ""),
        "job_species": raw_record.get("job_species", infer_job_species(title)),
        "positive_signals": unique(normalize_list(raw_record.get("positive_signals"))),
        "red_flags": unique(normalize_list(raw_record.get("red_flags"))),
        "common_keywords": unique(normalize_list(raw_record.get("common_keywords"))),
        "suggested_tags": raw_record.get("suggested_tags", {}),
    }
    return event


def infer_novelty(title: str, summary: str) -> str:
    haystack = f"{title} {summary}".lower()
    if any(hint in haystack for hint in BREAKOUT_HINTS):
        return "breakout"
    if "benchmark" in haystack or "release" in haystack or "new" in haystack:
        return "notable"
    return "incremental"


def infer_relevance(title: str, summary: str, content_type: str) -> str:
    haystack = f"{title} {summary}".lower()
    if content_type in {"paper", "technical_report", "job_description", "hiring_post"}:
        return "high"
    if "llm" in haystack or "language model" in haystack or "research" in haystack:
        return "high"
    if "agent" in haystack or "alignment" in haystack:
        return "medium"
    return "low"


def infer_job_species(title: str) -> str:
    lowered = title.lower()
    if "research" in lowered and "engineer" not in lowered:
        return "research-scientist"
    if "eval" in lowered or "benchmark" in lowered:
        return "evals-engineer"
    if "agent" in lowered or "tool" in lowered:
        return "agent-systems-engineer"
    if "vision" in lowered or "multimodal" in lowered:
        return "multimodal-researcher"
    if "engineer" in lowered:
        return "ml-engineer"
    return "general"


def infer_keywords(text: str) -> list[str]:
    keywords = []
    lowered = text.lower()
    for family in ("area_tags", "method_tags", "task_tags", "job_tags"):
        for tag, hints in TAG_KEYWORDS[family].items():
            if any(hint in lowered for hint in hints):
                keywords.append(tag.split(":", 1)[1])
    return unique(keywords)


def classify_event(event: dict[str, Any], taxonomy: dict[str, set[str]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    text = " ".join(
        [
            event.get("title", ""),
            event.get("short_summary", ""),
            event.get("problem", ""),
            event.get("method_summary", ""),
            event.get("key_contribution", ""),
            event.get("why_it_matters", ""),
            event.get("company", ""),
            event.get("team", ""),
        ]
    ).lower()
    candidates: list[dict[str, Any]] = []
    for family, mapping in TAG_KEYWORDS.items():
        inferred = list(event.get(family, []))
        for tag, hints in mapping.items():
            if any(hint in text for hint in hints):
                inferred.append(tag)
        event[family] = unique(inferred)
    signal_tags = list(event.get("signal_tags", []))
    signal_tags.append(signal_tag_for_content_type(event["content_type"]))
    if any(hint in text for hint in NEGATIVE_HINTS) or event.get("red_flags"):
        signal_tags.extend(["signal:negative", "signal:red-flag"])
    if event.get("novelty") == "breakout":
        signal_tags.append("signal:breakout")
    if event["content_type"] == "benchmark":
        signal_tags.append("signal:benchmark")
    if event["content_type"] == "repository":
        signal_tags.append("signal:repo")
    event["signal_tags"] = unique(signal_tags)
    suggested = event.get("suggested_tags", {}) or {}
    for family in FILTERABLE_FIELDS:
        for tag in normalize_list(suggested.get(family)):
            if tag not in taxonomy.get(family, set()):
                candidates.append(
                    {
                        "family": family,
                        "tag": tag,
                        "reason": "manual-suggested",
                        "example_event_id": event["id"],
                        "example_title": event["title"],
                    }
                )
            else:
                event[family] = unique(list(event.get(family, [])) + [tag])
    event.pop("suggested_tags", None)
    return event, candidates


def signal_tag_for_content_type(content_type: str) -> str:
    mapping = {
        "paper": "signal:paper",
        "technical_report": "signal:paper",
        "benchmark": "signal:benchmark",
        "repository": "signal:repo",
        "job_description": "signal:jd",
        "hiring_post": "signal:jd",
    }
    return mapping.get(content_type, "signal:note")


def route_event(event: dict[str, Any], routing: dict[str, Any]) -> dict[str, Any]:
    routed_to: list[str] = []
    for route_name, rule in routing.get("routes", {}).items():
        if event["content_type"] in normalize_list(rule.get("content_types")):
            routed_to.append(route_name)
    if event.get("area_tags") and (event["novelty"] == "breakout" or any(tag in event["signal_tags"] for tag in ("signal:negative", "signal:red-flag"))):
        routed_to.append("landscape")
    event["routed_to"] = unique(routed_to)
    return event


def event_fingerprint(event: dict[str, Any]) -> str:
    return event.get("url") or f"{event.get('source_id', '')}:{event.get('title', '').lower()}"


def merge_event_records(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    for key, value in incoming.items():
        if key in FILTERABLE_FIELDS or key in {"entities", "entity_tags", "positive_signals", "red_flags", "common_keywords", "routed_to"}:
            merged[key] = unique(normalize_list(existing.get(key)) + normalize_list(value))
        elif key == "status":
            merged[key] = max((existing.get("status", "draft"), value), key=lambda item: STATUS_PRIORITY.get(item, 0))
        elif value not in ("", [], None):
            merged[key] = value
    return merged


def dedupe_events(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for record in records:
        fingerprint = event_fingerprint(record)
        if fingerprint in deduped:
            deduped[fingerprint] = merge_event_records(deduped[fingerprint], record)
        else:
            deduped[fingerprint] = record
    return sort_records(list(deduped.values()), "date")


def sort_records(records: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    return sorted(records, key=lambda record: (record.get(key, ""), record.get("title", "")), reverse=True)


def load_events() -> list[dict[str, Any]]:
    ensure_layout()
    return load_jsonl(EVENTS_PATH)


def save_events(events: list[dict[str, Any]]) -> None:
    write_jsonl(EVENTS_PATH, sort_records(events, "date"))


def load_candidate_tags() -> list[dict[str, Any]]:
    return load_json(CANDIDATE_TAGS_PATH, [])


def save_candidate_tags(candidates: list[dict[str, Any]]) -> None:
    ordered = sorted(
        {
            (item["family"], item["tag"], item.get("example_event_id", "")): item
            for item in candidates
        }.values(),
        key=lambda item: (item["family"], item["tag"], item.get("example_title", "")),
    )
    write_json(CANDIDATE_TAGS_PATH, ordered)


def default_review_summary(draft_events: list[dict[str, Any]], all_events: list[dict[str, Any]]) -> dict[str, Any]:
    recommended = [
        item["id"]
        for item in draft_events
        if LEVEL_SCORE.get(item.get("credibility", "low"), 0) >= 2 and LEVEL_SCORE.get(item.get("relevance", "low"), 0) >= 2
    ]
    return {
        "generated_at": utc_now(),
        "draft_count": len(draft_events),
        "published_count": sum(1 for item in all_events if item.get("status") == "published"),
        "recommended_publish_ids": recommended[:12],
    }


def run_collect(include_scheduled: bool = True, include_manual: bool = True, limit_per_source: int = 8) -> dict[str, Any]:
    ensure_layout()
    source_configs = load_sources_config()
    source_map = source_index(source_configs)
    taxonomy = taxonomy_sets()
    routing = load_routing_config()
    existing_events = load_events()
    new_raw_records: list[dict[str, Any]] = []
    if include_scheduled:
        new_raw_records.extend(collect_scheduled_raw(source_configs, limit_per_source))
    if include_manual:
        new_raw_records.extend(collect_manual_raw(source_configs))
    new_events: list[dict[str, Any]] = []
    candidate_tags = load_candidate_tags()
    for raw_record in new_raw_records:
        event = normalize_event(raw_record, source_map)
        event, new_candidates = classify_event(event, taxonomy)
        event = route_event(event, routing)
        candidate_tags.extend(new_candidates)
        new_events.append(event)
    merged = dedupe_events(existing_events + new_events)
    save_events(merged)
    save_candidate_tags(candidate_tags)
    draft_events = [item for item in merged if item.get("status") == "draft"]
    review = default_review_summary(draft_events, merged)
    write_json(REVIEW_SUMMARY_PATH, review)
    return {
        "new_events": len(new_events),
        "total_events": len(merged),
        "draft_events": len(draft_events),
        "candidate_tags": len(load_candidate_tags()),
    }


def update_review_summary() -> dict[str, Any]:
    events = load_events()
    draft_events = [item for item in events if item.get("status") == "draft"]
    summary = default_review_summary(draft_events, events)
    write_json(REVIEW_SUMMARY_PATH, summary)
    return summary


def update_event_status(ids: list[str], status: str) -> dict[str, Any]:
    events = load_events()
    target_ids = set(ids)
    updated = 0
    for event in events:
        if event["id"] in target_ids:
            event["status"] = status
            updated += 1
    save_events(events)
    update_review_summary()
    return {"updated": updated, "status": status}


def publish_recommended() -> dict[str, Any]:
    summary = update_review_summary()
    return update_event_status(summary.get("recommended_publish_ids", []), "published")


def derive_papers(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    papers: list[dict[str, Any]] = []
    for event in events:
        if event.get("status") != "published":
            continue
        if event.get("content_type") not in {"paper", "technical_report", "benchmark", "repository"}:
            continue
        problem = event.get("problem") or summarize_text(event.get("short_summary", "Research signal"), 160)
        method_summary = event.get("method_summary") or summarize_text(event.get("short_summary", ""), 180)
        why_it_matters = event.get("why_it_matters") or default_why_it_matters(event)
        why_maybe_not = event.get("why_maybe_not") or default_why_maybe_not(event)
        papers.append(
            {
                "paper_id": event["id"],
                "title": event["title"],
                "date": event["date"],
                "url": event["url"],
                "code_url": "",
                "problem": problem,
                "method_summary": method_summary,
                "key_contribution": event.get("key_contribution") or summarize_text(event.get("short_summary", ""), 180),
                "difference_from_existing": summarize_text(event.get("short_summary", "Differentiation requires deeper reading."), 180),
                "evidence_strength": event.get("credibility", "medium"),
                "limitations": event.get("limitations") or why_maybe_not,
                "area_tags": event.get("area_tags", []),
                "method_tags": event.get("method_tags", []),
                "task_tags": event.get("task_tags", []),
                "job_relevance_tags": event.get("job_tags", []),
                "read_priority": "high" if event.get("relevance") == "high" else "medium",
                "why_it_matters": why_it_matters,
                "why_maybe_not": why_maybe_not,
                "status": event["status"],
                "event_id": event["id"],
            }
        )
    return sort_records(papers, "date")


def default_why_it_matters(event: dict[str, Any]) -> str:
    if event.get("area_tags"):
        labels = [AREA_LABELS.get(tag, tag) for tag in event["area_tags"][:2]]
        return f"Relevant to {', '.join(labels)} and likely useful for tracking frontier movement."
    return "Potentially relevant to the current LLM research and hiring landscape."


def default_why_maybe_not(event: dict[str, Any]) -> str:
    if event.get("credibility") == "low":
        return "Needs corroboration from stronger evidence before treating it as durable direction."
    return "Requires deeper reading to separate durable signal from short-term attention."


def derive_jobs(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    for event in events:
        if event.get("status") != "published":
            continue
        if event.get("content_type") not in {"job_description", "hiring_post", "team_announcement"}:
            continue
        jobs.append(
            {
                "job_id": event["id"],
                "company": event.get("company") or event.get("source"),
                "team": event.get("team", ""),
                "title": event["title"],
                "url": event["url"],
                "date": event["date"],
                "job_species": event.get("job_species") or infer_job_species(event["title"]),
                "location": event.get("location", ""),
                "source": event.get("source"),
                "credibility": event.get("credibility", "medium"),
                "positive_signals": unique(
                    normalize_list(event.get("positive_signals"))
                    + infer_positive_signals(event.get("title", ""), event.get("short_summary", ""))
                ),
                "red_flags": unique(
                    normalize_list(event.get("red_flags"))
                    + infer_red_flags(event.get("title", ""), event.get("short_summary", ""))
                ),
                "common_keywords": unique(
                    normalize_list(event.get("common_keywords"))
                    + infer_keywords(event.get("title", "") + " " + event.get("short_summary", ""))
                ),
                "market_value_summary": summarize_text(
                    event.get("short_summary")
                    or f"{event.get('company') or event.get('source')} appears to be hiring in {event.get('job_species') or 'LLM roles'}."
                ),
                "status": event["status"],
                "event_id": event["id"],
            }
        )
    return sort_records(jobs, "date")


def infer_positive_signals(title: str, summary: str) -> list[str]:
    text = f"{title} {summary}".lower()
    hints = []
    if "research" in text:
        hints.append("research investment")
    if "agent" in text or "tool" in text:
        hints.append("agent capability demand")
    if "reasoning" in text or "eval" in text:
        hints.append("reasoning/evals demand")
    return hints


def infer_red_flags(title: str, summary: str) -> list[str]:
    text = f"{title} {summary}".lower()
    hints = []
    if "contract" in text:
        hints.append("contract-heavy signal")
    if "onsite" in text and "remote" not in text:
        hints.append("onsite-only requirement")
    if "generalist" in text:
        hints.append("broad scope may hide unclear role boundaries")
    return hints


def derive_source_records(events: list[dict[str, Any]], source_configs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, dict[str, int]] = {}
    for event in events:
        source_id = event.get("source_id")
        if not source_id:
            continue
        counts.setdefault(source_id, {"published": 0, "draft": 0})
        counts[source_id][event.get("status", "draft")] = counts[source_id].get(event.get("status", "draft"), 0) + 1
    records = []
    for source in source_configs:
        source_count = counts.get(source["source_id"], {})
        credibility = source.get("credibility_default", "medium")
        records.append(
            {
                "source_id": source["source_id"],
                "name": source["name"],
                "type": source.get("source_type", "unknown"),
                "url": source.get("url", ""),
                "coverage": source.get("coverage", ""),
                "signal_quality": credibility,
                "noise_level": source.get("noise_level", "medium"),
                "bias": source.get("bias", "unknown"),
                "best_for": source.get("best_for", ""),
                "not_good_for": source.get("not_good_for", ""),
                "update_frequency": source.get("cadence", source.get("update_frequency", "manual")),
                "last_checked": iso_today(),
                "notes": f"published={source_count.get('published', 0)} draft={source_count.get('draft', 0)}",
            }
        )
    return sorted(records, key=lambda item: item["name"].lower())


def load_landscape_cards() -> list[dict[str, Any]]:
    cards = []
    for path in sorted(LANDSCAPE_DIR.glob("*.json")):
        cards.append(load_json(path, {}))
    return cards


def build_landscape_drafts(events: list[dict[str, Any]], official_cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_area: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        if event.get("status") != "published":
            continue
        for area_tag in normalize_list(event.get("area_tags")):
            by_area.setdefault(area_tag, []).append(event)
    official_by_name = {card["name"]: card for card in official_cards}
    drafts: list[dict[str, Any]] = []
    for area_tag, tagged_events in by_area.items():
        label = AREA_LABELS.get(area_tag, area_tag)
        official = official_by_name.get(label, {})
        recent = sort_records(tagged_events, "date")[:5]
        controversies = [
            summarize_text(item["title"], 120)
            for item in recent
            if any(tag in item.get("signal_tags", []) for tag in ("signal:negative", "signal:red-flag"))
        ]
        watch_level = "high" if any("signal:breakout" in item.get("signal_tags", []) for item in recent) else official.get("watch_level", "medium")
        draft = {
            "name": label,
            "definition": official.get("definition", "Auto-generated landscape draft."),
            "scope": official.get("scope", []),
            "not_scope": official.get("not_scope", []),
            "current_state": f"Recent published evidence count: {len(tagged_events)}.",
            "key_methods": unique([tag.split(":", 1)[1] for event in recent for tag in normalize_list(event.get("method_tags"))]),
            "key_tasks": unique([tag.split(":", 1)[1] for event in recent for tag in normalize_list(event.get("task_tags"))]),
            "key_benchmarks": [item["title"] for item in recent if item.get("content_type") == "benchmark"],
            "representative_papers": [item["title"] for item in recent if item.get("content_type") in {"paper", "technical_report"}],
            "representative_companies": unique([item.get("company") for item in recent if item.get("company")]),
            "job_relevance": official.get("job_relevance", "Linked to hiring and research demand in current radar."),
            "risks": official.get("risks", []),
            "controversies": controversies or official.get("controversies", []),
            "open_questions": unique(
                [item.get("why_maybe_not") for item in recent if item.get("why_maybe_not")]
                or official.get("open_questions", [])
            ),
            "recent_developments": [item["title"] for item in recent],
            "negative_signals": controversies,
            "watch_level": watch_level,
            "last_updated": iso_today(),
            "status": "draft",
            "event_ids": [item["id"] for item in recent],
        }
        drafts.append(draft)
    return sorted(drafts, key=lambda item: item["name"].lower())


def write_landscape_drafts(drafts: list[dict[str, Any]]) -> None:
    for path in LANDSCAPE_DRAFT_DIR.glob("*.json"):
        path.unlink()
    for draft in drafts:
        write_json(LANDSCAPE_DRAFT_DIR / f"{slugify(draft['name'])}.json", draft)


def load_landscape_drafts() -> list[dict[str, Any]]:
    drafts = []
    for path in sorted(LANDSCAPE_DRAFT_DIR.glob("*.json")):
        drafts.append(load_json(path, {}))
    return drafts


def ranking_score(event: dict[str, Any]) -> int:
    return (
        NOVELTY_SCORE.get(event.get("novelty", "incremental"), 0) * 3
        + LEVEL_SCORE.get(event.get("credibility", "low"), 0) * 2
        + LEVEL_SCORE.get(event.get("relevance", "low"), 0)
    )


def date_window(records: list[dict[str, Any]], days: int) -> list[dict[str, Any]]:
    cutoff = date.today() - timedelta(days=days)
    selected = []
    for record in records:
        try:
            record_date = date.fromisoformat(record.get("date", iso_today()))
        except ValueError:
            continue
        if record_date >= cutoff:
            selected.append(record)
    return selected


def report_link(event: dict[str, Any]) -> str:
    routed = event.get("routed_to", [])
    if "research" in routed or event.get("content_type") in {"paper", "technical_report", "benchmark", "repository"}:
        return f"research.html#{event['id']}"
    if "jobs" in routed or event.get("content_type") in {"job_description", "hiring_post", "team_announcement"}:
        return f"jobs.html#{event['id']}"
    return f"events.html#{event['id']}"


def report_item(event: dict[str, Any]) -> dict[str, str]:
    return {
        "title": event["title"],
        "event_id": event["id"],
        "summary": event.get("short_summary", ""),
        "link": report_link(event),
    }


def generate_weekly_report(events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if events is None:
        events = [item for item in load_events() if item.get("status") == "published"]
    weekly_events = date_window(events, 7)
    ranked = sorted(weekly_events, key=ranking_score, reverse=True)
    highlights = [report_item(item) for item in ranked[:5]]
    jobs = [report_item(item) for item in ranked if item.get("content_type") in {"job_description", "hiring_post", "team_announcement"}][:5]
    research = [report_item(item) for item in ranked if item.get("content_type") in {"paper", "technical_report", "benchmark", "repository"}][:5]
    breakout = [report_item(item) for item in ranked if "signal:breakout" in item.get("signal_tags", [])][:5]
    read_queue = [report_item(item) for item in ranked if item.get("relevance") == "high"][:6]
    open_questions = [item.get("why_maybe_not") or default_why_maybe_not(item) for item in ranked[:5]]
    report_date = date.today().strftime("%Y-W%V")
    report = {
        "report_id": report_date,
        "title": f"Weekly Brief {report_date}",
        "period_start": (date.today() - timedelta(days=6)).isoformat(),
        "period_end": iso_today(),
        "generated_at": utc_now(),
        "highlights": highlights,
        "job_changes": jobs,
        "research_changes": research,
        "breakout": breakout,
        "read_queue": read_queue,
        "open_questions": unique([item for item in open_questions if item])[:5],
    }
    write_json(WEEKLY_DIR / f"{report_date}.json", report)
    return report


def generate_monthly_report(events: list[dict[str, Any]] | None = None, landscape_drafts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if events is None:
        events = [item for item in load_events() if item.get("status") == "published"]
    if landscape_drafts is None:
        landscape_drafts = load_landscape_drafts()
    monthly_events = date_window(events, 31)
    ranked = sorted(monthly_events, key=ranking_score, reverse=True)
    period = date.today().strftime("%Y-%m")
    report = {
        "report_id": period,
        "title": f"Monthly Review {period}",
        "period": period,
        "generated_at": utc_now(),
        "top_changes": [report_item(item) for item in ranked[:8]],
        "breakout_signals": [report_item(item) for item in ranked if "signal:breakout" in item.get("signal_tags", [])][:5],
        "negative_signals": [report_item(item) for item in ranked if "signal:negative" in item.get("signal_tags", [])][:5],
        "landscape_drafts": [{"name": draft["name"], "watch_level": draft["watch_level"]} for draft in landscape_drafts[:8]],
        "open_questions": unique(
            [
                item.get("why_maybe_not") or default_why_maybe_not(item)
                for item in ranked
                if item.get("why_maybe_not") or item.get("credibility") != "high"
            ]
        )[:8],
    }
    write_json(MONTHLY_DIR / f"{period}.json", report)
    return report


def refresh_derived_outputs() -> dict[str, int]:
    ensure_layout()
    source_configs = load_sources_config()
    events = load_events()
    papers = derive_papers(events)
    jobs = derive_jobs(events)
    source_records = derive_source_records(events, source_configs)
    write_jsonl(PAPERS_PATH, papers)
    write_jsonl(JOBS_PATH, jobs)
    write_jsonl(SOURCES_PATH, source_records)
    landscape_drafts = build_landscape_drafts(events, load_landscape_cards())
    write_landscape_drafts(landscape_drafts)
    generate_weekly_report([item for item in events if item.get("status") == "published"])
    generate_monthly_report([item for item in events if item.get("status") == "published"], landscape_drafts)
    update_review_summary()
    return {
        "papers": len(papers),
        "jobs": len(jobs),
        "sources": len(source_records),
        "landscape_drafts": len(landscape_drafts),
    }


def weekly_reports() -> list[dict[str, Any]]:
    return [load_json(path, {}) for path in sorted(WEEKLY_DIR.glob("*.json"), reverse=True)]


def monthly_reports() -> list[dict[str, Any]]:
    return [load_json(path, {}) for path in sorted(MONTHLY_DIR.glob("*.json"), reverse=True)]


def page_counts() -> dict[str, int]:
    return {
        "events": len(load_events()),
        "published_events": len([item for item in load_events() if item.get("status") == "published"]),
        "papers": len(load_jsonl(PAPERS_PATH)),
        "jobs": len(load_jsonl(JOBS_PATH)),
        "sources": len(load_jsonl(SOURCES_PATH)),
        "landscape": len(load_landscape_cards()),
        "landscape_drafts": len(load_landscape_drafts()),
    }


def build_context() -> dict[str, Any]:
    refresh_derived_outputs()
    events = load_events()
    published_events = [item for item in events if item.get("status") == "published"]
    draft_events = [item for item in events if item.get("status") == "draft"]
    papers = load_jsonl(PAPERS_PATH)
    jobs = load_jsonl(JOBS_PATH)
    sources = load_jsonl(SOURCES_PATH)
    landscape = load_landscape_cards()
    landscape_drafts = load_landscape_drafts()
    weekly = weekly_reports()
    monthly = monthly_reports()
    latest_weekly = weekly[0] if weekly else generate_weekly_report(published_events)
    latest_monthly = monthly[0] if monthly else generate_monthly_report(published_events, landscape_drafts)
    breakout_events = [item for item in published_events if "signal:breakout" in item.get("signal_tags", [])][:6]
    read_queue = sorted(
        [item for item in draft_events + published_events if item.get("relevance") == "high"],
        key=ranking_score,
        reverse=True,
    )[:8]
    counts = page_counts()
    review_summary = load_json(REVIEW_SUMMARY_PATH, default_review_summary(draft_events, events))
    return {
        "counts": counts,
        "events": published_events,
        "draft_events": draft_events,
        "papers": papers,
        "jobs": jobs,
        "sources": sources,
        "landscape": landscape,
        "landscape_drafts": landscape_drafts,
        "candidate_tags": load_candidate_tags(),
        "weekly_reports": weekly,
        "monthly_reports": monthly,
        "latest_weekly": latest_weekly,
        "latest_monthly": latest_monthly,
        "breakout_events": breakout_events,
        "read_queue": read_queue,
        "review_summary": review_summary,
        "event_filter_options": {
            "source_types": sorted({item.get("source_type", "") for item in published_events if item.get("source_type")}),
            "area_tags": sorted({tag for item in published_events for tag in normalize_list(item.get("area_tags"))}),
            "signal_tags": sorted({tag for item in published_events for tag in normalize_list(item.get("signal_tags"))}),
            "credibility": ["high", "medium", "low"],
        },
    }


def build_site() -> list[Path]:
    ensure_layout()
    context = build_context()
    environment = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    rendered_pages: list[Path] = []
    for template_name, output_name, title in (
        ("index.html", "index.html", "LLM Intelligence OS"),
        ("events.html", "events.html", "Event Stream"),
        ("jobs.html", "jobs.html", "Job & Company Radar"),
        ("research.html", "research.html", "Research Radar"),
        ("landscape.html", "landscape.html", "Tech Landscape"),
        ("sources.html", "sources.html", "Source Map"),
        ("reports.html", "reports.html", "Reports"),
        ("drafts.html", "drafts.html", "Draft Review"),
    ):
        template = environment.get_template(template_name)
        output = template.render(title=title, **context)
        path = SITE_DIR / output_name
        path.write_text(output, encoding="utf-8")
        rendered_pages.append(path)
    return rendered_pages


def deploy_preview() -> dict[str, Any]:
    ensure_layout()
    if not (SITE_DIR / "index.html").exists():
        build_site()
    manifest = {
        "target": "codex-preview-adapter",
        "generated_at": utc_now(),
        "entrypoint": "index.html",
        "pages": sorted(path.name for path in SITE_DIR.glob("*.html")),
        "note": "This adapter isolates deployment metadata for Codex static preview.",
    }
    write_json(DEPLOY_MANIFEST_PATH, manifest)
    deployment_note = textwrap.dedent(
        """
        # Deployment Adapter

        The site/ directory is the only deployment artifact for v1.
        This manifest is intentionally platform-neutral so Codex preview integration
        can consume it without coupling collection or rendering code to a provider.
        """
    ).strip()
    (SITE_DIR / "DEPLOYMENT.md").write_text(deployment_note + "\n", encoding="utf-8")
    return manifest


def format_counts(result: dict[str, Any]) -> str:
    return ", ".join(f"{key}={value}" for key, value in result.items())


def main_collect(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect scheduled and manual intelligence inputs.")
    parser.add_argument("--skip-scheduled", action="store_true")
    parser.add_argument("--skip-manual", action="store_true")
    parser.add_argument("--limit-per-source", type=int, default=8)
    args = parser.parse_args(argv)
    result = run_collect(
        include_scheduled=not args.skip_scheduled,
        include_manual=not args.skip_manual,
        limit_per_source=args.limit_per_source,
    )
    print(format_counts(result))
    return 0


def main_refresh(_: list[str] | None = None) -> int:
    result = refresh_derived_outputs()
    print(format_counts(result))
    return 0


def main_build(_: list[str] | None = None) -> int:
    pages = build_site()
    print(f"rendered={len(pages)}")
    return 0


def main_review(_: list[str] | None = None) -> int:
    summary = update_review_summary()
    print(json.dumps(summary, ensure_ascii=False))
    return 0


def main_publish(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Publish or reject reviewed events.")
    parser.add_argument("--ids", nargs="*", default=[])
    parser.add_argument("--reject-ids", nargs="*", default=[])
    parser.add_argument("--all-recommended", action="store_true")
    args = parser.parse_args(argv)
    if args.reject_ids:
        result = update_event_status(args.reject_ids, "rejected")
    elif args.all_recommended:
        result = publish_recommended()
    else:
        result = update_event_status(args.ids, "published")
    refresh_derived_outputs()
    print(format_counts(result))
    return 0


def main_deploy(_: list[str] | None = None) -> int:
    manifest = deploy_preview()
    print(json.dumps(manifest, ensure_ascii=False))
    return 0
