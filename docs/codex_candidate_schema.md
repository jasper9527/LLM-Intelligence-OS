# Codex Discovery Candidate Schema

Codex discovery tasks write JSONL records under `data/codex_discovery/candidates/`.

Required fields:
- `title`
- either `url` or `evidence_note`
- `content_type`
- `source`
- `date`
- `short_summary`
- `credibility`: `high`, `medium`, or `low`
- `novelty`: `breakout`, `notable`, or `incremental`
- `relevance`: `high`, `medium`, or `low`
- `why_it_matters`
- `why_maybe_not`
- `uncertainty`
- `route_suggestion`

Optional fields mirror Event Stream fields such as `area_tags`, `method_tags`, `task_tags`, `job_tags`, `signal_tags`, `company`, `team`, `location`, `positive_signals`, and `red_flags`.
