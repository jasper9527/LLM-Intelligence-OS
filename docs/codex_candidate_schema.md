# Codex Candidate Evidence Schema

Codex automation tasks write candidate evidence before anything enters the formal Event Stream. This keeps Codex-led discovery auditable and reviewable.

## Candidate files

```text
data/codex_discovery/candidates/YYYY-MM-DD.jsonl
```

Each line is one JSON object.

## Required fields

| Field | Type | Notes |
| --- | --- | --- |
| `candidate_id` | string | Stable id for this evidence item. |
| `discovery_run_id` | string | Run id linking the item to a discovery log. |
| `date_found` | string | Date the automation found the item. |
| `title` | string | Evidence title. |
| `source_name` | string | Human-readable source name. |
| `source_type` | string | `official`, `paper`, `company_blog`, `job_board`, `open_source`, `community`, `social`, `newsletter`, `personal`, or `unknown`. |
| `content_type` | string | `paper`, `technical_report`, `job_description`, `model_release`, `benchmark`, `repo`, `blog`, `discussion`, or `note`. |
| `short_summary` | string | One-paragraph summary. |
| `credibility` | string | `low`, `medium`, or `high`. |
| `novelty` | string | `incremental`, `notable`, or `breakout`. |
| `relevance` | string | `low`, `medium`, or `high`. |
| `route_suggestion` | array | Suggested destinations such as `research`, `jobs`, `landscape`, `sources`, `weekly_brief_candidate`, or `archive`. |

## Evidence requirement

A candidate with `should_enter_review: true` must include either `url` or `evidence_note`. Social/community items should be marked as weak evidence unless backed by an original source or cross-source confirmation.

## Optional fields

```json
{
  "candidate_id": "codex_20260621_001",
  "discovery_run_id": "daily_20260621",
  "date_found": "2026-06-21",
  "evidence_date": "2026-06-21",
  "title": "",
  "url": "",
  "source_name": "",
  "source_type": "official|paper|company_blog|job_board|open_source|community|social|newsletter|personal|unknown",
  "content_type": "paper|technical_report|job_description|model_release|benchmark|repo|blog|discussion|note",
  "short_summary": "",
  "why_it_matters": "",
  "why_maybe_not": "",
  "evidence_note": "",
  "credibility": "low|medium|high",
  "novelty": "incremental|notable|breakout",
  "relevance": "low|medium|high",
  "uncertainty": "",
  "entities": [],
  "area_tags": [],
  "method_tags": [],
  "task_tags": [],
  "job_tags": [],
  "signal_tags": [],
  "route_suggestion": [],
  "should_enter_review": true,
  "skip_reason": "",
  "created_by": "codex_automation"
}
```

## Run log files

```text
data/codex_discovery/runs/YYYY-MM-DD_daily.json
```

Run logs should record what the automation searched, checked, skipped, and could not access.

```json
{
  "run_id": "daily_20260621",
  "run_type": "daily_discovery",
  "started_at": "2026-06-21T00:00:00Z",
  "finished_at": "2026-06-21T00:10:00Z",
  "queries_or_focus_areas": [],
  "sources_checked": [],
  "candidates_written": 0,
  "items_skipped": [],
  "network_or_access_issues": [],
  "notes": ""
}
```
