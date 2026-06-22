# Cloud Automation Task Design and Prompts

## 0. Purpose

This document defines the cloud automation structure for LLM Intelligence OS and provides ready-to-use prompts for recurring Codex/cloud tasks. The goal is to let information acquisition, review, report generation, and site refresh run in a cloud workspace without depending on a local machine.

The automation system should stay aligned with the product boundary: it is an information infrastructure, not a career-decision agent. Tasks should collect, organize, summarize, route, and preserve evidence. They should not produce personal execution plans or tell the user which direction to choose.

## 1. Top-down task architecture

The cloud automation should be split into task layers rather than one large recurring task.

```text
Layer 1: Source Health and Configuration
    ↓
Layer 2: Daily Collection
    ↓
Layer 3: Review Surface Refresh
    ↓
Layer 4: Radar Maintenance
    ↓
Layer 5: Weekly Brief
    ↓
Layer 6: Monthly Review
    ↓
Layer 7: Site Build and Deployment Check
```

Each task should be independently runnable. If a later task fails, earlier collected evidence should remain intact.

## 2. Operating rules for all automation tasks

All recurring tasks must follow these rules:

1. Keep the system information-focused. Do not output personal career decisions or personal learning plans.
2. Preserve raw evidence where possible: URL, title, source, collection date, snapshot path, and routing status.
3. Prefer draft/review states over direct publication when uncertainty is high.
4. Keep negative signals, red flags, and breakout signals even if they conflict with familiar directions.
5. Do not silently delete evidence. Archive or reject with a reason instead.
6. Do not add low-quality sources directly to deep modules without source-quality notes.
7. Keep generated reports navigational. Deep summaries belong in module records.
8. Commit only meaningful changes. If there are no changes, report that no commit is needed.
9. If a command fails because of network, dependency, or provider limits, record the limitation clearly.
10. Rebuild the static site after any change that affects user-facing pages.

## 3. Recommended task schedule

| Task | Suggested cadence | Primary goal | Human attention needed |
| --- | --- | --- | --- |
| Source health check | weekly | Detect broken or stale sources | Low |
| Daily collect | daily, or 1-2 times daily | Capture new stable-source signals | Low |
| Review refresh | after daily collect | Update draft review surface | Medium |
| Radar maintenance | every 2-3 days | Update job/research/source/landscape summaries | Medium |
| Weekly brief | weekly | Create weekly navigation report | Medium |
| Monthly review | monthly | Synthesize durable field changes | High |
| Site build/deploy check | after publish/report generation | Keep HTML current | Low |

## 4. Task dependency graph

```text
source_health_check
    └─ informs source configuration but does not block collection

daily_collect
    ├─ writes raw snapshots
    ├─ updates events
    └─ updates review summary

review_refresh
    ├─ reads events and review summary
    └─ rebuilds drafts page

radar_maintenance
    ├─ reads reviewed/published events
    ├─ updates jobs, papers, sources, and landscape drafts
    └─ rebuilds module pages

weekly_brief
    ├─ reads this week's events and radar records
    ├─ writes weekly report
    └─ rebuilds reports and dashboard

monthly_review
    ├─ reads monthly events, weekly reports, radar records, and landscape cards
    ├─ writes monthly report
    └─ proposes durable landscape updates

site_build_deploy_check
    ├─ runs static-site build
    └─ verifies site artifacts exist
```

## 5. Manual submission path

Manual submissions should remain a first-class ingestion path because some high-value signals are not safe or practical to scrape automatically.

Recommended flow:

```text
User submits link/note/interview feedback
    ↓
data/raw/manual_submissions.jsonl
    ↓
manual queue collector
    ↓
Event Stream draft
    ↓
review/publish/reject
    ↓
Job Radar / Research Radar / Tech Landscape / Weekly Brief
```

Manual submissions should support privacy flags later. Until privacy handling is implemented, sensitive personal or interview details should be summarized and anonymized before publication.

## 6. Prompt: Source health check

Use this prompt for a weekly source-health task.

```text
You are maintaining LLM Intelligence OS in a cloud workspace.

Goal:
Check whether configured information sources are still usable, correctly scoped, and aligned with the system's information-only purpose.

Context:
- This system tracks LLM algorithm research, jobs, companies, source quality, weekly briefs, and monthly reviews.
- It must not become a personal decision agent or generic news aggregator.
- Prefer stable sources that can be collected from the cloud without local state.

Tasks:
1. Inspect `config/sources.yaml`, `config/automation.yaml`, and source-related code.
2. For each enabled source, classify health as `healthy`, `stale`, `broken`, or `needs_review`.
3. Check whether each source has a clear source type, collector kind, cadence, credibility default, coverage, noise level, bias, best-for, and not-good-for notes.
4. Do not add random new sources. If a source should be added, propose it in a short candidate list with rationale and risks.
5. If safe, run a lightweight collection or fetch check for enabled sources.
6. Do not publish or delete records.
7. Produce a concise source-health summary and list exact files changed, if any.

Expected output:
- Source health table.
- Broken or risky sources.
- Candidate sources to consider, clearly marked as proposals.
- Commands run and whether they passed.
```

## 7. Prompt: Daily collect

Use this prompt for the main daily cloud collection task.

```text
You are running the daily collection task for LLM Intelligence OS in a cloud workspace.

Goal:
Collect new evidence from configured stable sources, preserve raw snapshots, normalize events, update the review surface, and rebuild the static site if user-facing files change.

Hard boundaries:
- Do not make career decisions or personal action plans.
- Do not directly publish uncertain information.
- Preserve negative, red-flag, and breakout signals.
- Do not delete evidence silently.

Steps:
1. Check the working tree with `git status --short --branch`.
2. Inspect `config/sources.yaml` and confirm which sources are enabled.
3. Install dependencies only if needed.
4. Run the configured daily collect entrypoint, currently `python scripts/collect.py`.
5. Run the review refresh entrypoint if available, currently `python scripts/review.py`.
6. Rebuild the site with `python scripts/build_site.py` if collection or review changed data/site inputs.
7. Inspect changes to `data/raw/snapshots/`, `data/events.jsonl`, `data/processed/`, and `site/`.
8. Summarize what was collected by source and how many new draft events were created.
9. Commit meaningful changes with a clear message. If there are no changes, do not commit.

Expected output:
- Number of records collected per source.
- New events by content type and source type.
- Any failed sources and likely cause.
- Whether the static site was rebuilt.
- Commit hash if changes were committed.
```

## 8. Prompt: Review refresh

Use this prompt when collection has already run and the draft review surface should be updated.

```text
You are refreshing the review surface for LLM Intelligence OS.

Goal:
Make newly collected draft events easy to inspect without prematurely publishing them.

Steps:
1. Check current git status.
2. Run `python scripts/review.py`.
3. Run `python scripts/build_site.py` if review outputs affect static pages.
4. Inspect `data/processed/review_summary.json`, candidate tag files, draft pages, and site outputs.
5. Verify that draft, published, and rejected statuses remain distinct.
6. Do not publish all records automatically unless explicitly instructed.
7. Commit only meaningful review/site changes.

Expected output:
- Draft count.
- Candidate tags that need human review.
- Landscape draft candidates, if any.
- Commands run and result.
- Commit hash if committed.
```

## 9. Prompt: Radar maintenance

Use this prompt every 2-3 days.

```text
You are maintaining the radar modules for LLM Intelligence OS.

Goal:
Update Job & Company Radar, Research Radar, Source Map, and Tech Landscape draft state from reviewed evidence.

Boundaries:
- Do not convert radar observations into personal recommendations.
- Do not force every event into a fixed category.
- Preserve open questions and uncertainty.
- Keep red flags, negative signals, and low-confidence notes visible.

Steps:
1. Inspect recent events, jobs, papers, sources, and landscape drafts.
2. Run available radar update scripts:
   - `python scripts/update_jobs.py`
   - `python scripts/update_research.py`
   - `python scripts/update_landscape.py`
3. Rebuild the static site with `python scripts/build_site.py`.
4. Inspect changes to `data/jobs.jsonl`, `data/papers.jsonl`, `data/sources.jsonl`, `data/processed/landscape_drafts/`, and `site/`.
5. Summarize updates by module.
6. Commit meaningful changes.

Expected output:
- Job species updated.
- Research records updated.
- Source quality changes.
- Landscape draft changes.
- Unresolved questions for human review.
- Commit hash if committed.
```

## 10. Prompt: Weekly brief

Use this prompt once per week.

```text
You are generating the weekly brief for LLM Intelligence OS.

Goal:
Create a weekly navigation report that helps the user decide what to inspect more deeply. The weekly brief is not a full information dump and not a personal decision memo.

Required structure:
1. Information density.
2. Top 5 signals.
3. Job & Company Radar updates.
4. Research Radar updates.
5. Tech Landscape updates.
6. Breakout signals.
7. Reading queue.
8. Open questions for next week.

Boundaries:
- Do not tell the user which career direction to choose.
- Do not create personal learning plans or application plans.
- Include negative and red-flag signals when present.
- Keep deep details linked or referenced rather than copying everything into the brief.

Steps:
1. Check the date and determine the report week.
2. Inspect this week's events, jobs, papers, sources, landscape drafts, and prior weekly report if present.
3. Run `python scripts/generate_weekly.py`.
4. Rebuild the site with `python scripts/build_site.py`.
5. Inspect the generated weekly report and reports page.
6. Verify that the report is navigational, concise, and evidence-linked.
7. Commit meaningful changes.

Expected output:
- Weekly report path.
- Top signals count.
- Breakout/negative/red-flag signals included.
- Reading queue summary.
- Open questions.
- Commit hash if committed.
```

## 11. Prompt: Monthly review

Use this prompt once per month.

```text
You are generating the monthly review for LLM Intelligence OS.

Goal:
Synthesize durable changes in the external LLM algorithm environment. The monthly review should update understanding, not merely concatenate weekly briefs.

Required structure:
1. Overall field changes.
2. Job-market review.
3. Research-trend review.
4. Tech Landscape update summary.
5. Breakout review.
6. Watchlist for next month.
7. Questions requiring human discussion.

Boundaries:
- Do not decide the user's career direction.
- Do not use scores as a substitute for evidence.
- Do not erase uncertainty or disagreement.
- Call out source limitations and evidence gaps.

Steps:
1. Identify the month being reviewed.
2. Inspect monthly events, weekly reports, radar records, source records, and landscape cards/drafts.
3. Run `python scripts/generate_monthly.py`.
4. Run `python scripts/update_landscape.py` if the monthly review indicates durable landscape changes.
5. Rebuild the site with `python scripts/build_site.py`.
6. Inspect generated monthly report and changed landscape files.
7. Commit meaningful changes.

Expected output:
- Monthly report path.
- Main durable changes.
- Landscape cards updated or proposed.
- Evidence gaps and disagreements.
- Human discussion questions.
- Commit hash if committed.
```

## 12. Prompt: Site build and deployment check

Use this prompt after any data/report/template change.

```text
You are checking the static site build for LLM Intelligence OS.

Goal:
Ensure the HTML reading layer is up to date and deployable.

Steps:
1. Run `python scripts/build_site.py`.
2. Run `python scripts/deploy.py` if deployment manifest refresh is needed.
3. Verify expected site files exist:
   - `site/index.html`
   - `site/events.html`
   - `site/jobs.html`
   - `site/research.html`
   - `site/landscape.html`
   - `site/sources.html`
   - `site/reports.html`
4. Inspect `site/deploy-manifest.json` if present.
5. Do not change source data unless required to fix a build error.
6. Commit meaningful generated-site changes.

Expected output:
- Build status.
- Missing pages, if any.
- Deployment manifest status.
- Commit hash if committed.
```

## 13. Prompt: Manual submission ingestion

Use this prompt when the user adds manual links or notes.

```text
You are ingesting manual submissions into LLM Intelligence OS.

Goal:
Convert user-provided links, notes, interview feedback, or observations into the same evidence pipeline as automated sources.

Boundaries:
- Preserve privacy. Do not publish sensitive personal details.
- Summarize private signals at a safe abstraction level.
- Do not treat a single anecdote as broad market evidence.
- Keep source type and confidence explicit.

Steps:
1. Inspect `data/raw/manual_submissions.jsonl`.
2. Validate each new submission has at least title, date or inferred date, summary/notes, content type, and source type.
3. Run `python scripts/collect.py` so the manual queue collector can ingest new submissions if enabled/supported.
4. Run `python scripts/review.py`.
5. Rebuild the site with `python scripts/build_site.py`.
6. Summarize new manual events and any privacy concerns.
7. Commit meaningful changes.

Expected output:
- Manual submissions processed.
- Events created.
- Privacy red flags.
- Candidate tags or routes needing human review.
- Commit hash if committed.
```

## 14. Minimal first-week rollout

For the first week, use only these tasks:

1. Daily collect.
2. Review refresh.
3. Weekly brief.
4. Site build and deployment check.

Do not add many new sources in the first run. The first objective is to verify that cloud execution, data mutation, review pages, reports, and site rebuilds work reliably.

## 15. First sources to consider after the pipeline is stable

After the first cloud task loop is stable, consider adding sources in this order:

1. More arXiv categories: cs.CL, cs.LG, cs.CV.
2. OpenReview for conference and workshop signals.
3. Company research/blog feeds from major frontier labs and Chinese LLM teams.
4. Additional official job boards, especially Greenhouse, Lever, or Ashby boards.
5. GitHub/Hugging Face release sources for model and benchmark movement.
6. Manual submissions for high-value social, interview, and private signals.

Do not add social platforms as unattended core sources until source-quality and privacy handling are stronger.
