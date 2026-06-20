# Raw Inputs

This directory stores two kinds of upstream evidence:

- `manual_submissions.jsonl`: operator-fed candidate material.
- `snapshots/`: timestamped raw fetch results from scheduled collectors.

Each manual submission should be one JSON object per line. Suggested fields:

```json
{"submission_id":"manual-001","source_id":"manual-submission","title":"Candidate paper or job","url":"https://example.com","date":"2026-06-20","content_type":"paper","summary":"Why this matters","suggested_tags":{"area_tags":["area:agent-tool-use-computer-use"]}}
```
