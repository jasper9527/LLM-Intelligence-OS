# Codex Automation Setup

This repository contains **repository-side definitions** for Codex automation tasks. It does not create the Codex Cloud schedules by itself.

Codex automation has two layers:

1. **Codex Cloud schedule**: created in the Codex UI. This decides the repository, branch, frequency, network access, commit behavior, and prompt text or prompt file reference.
2. **Repository-side workflow assets**: stored in this repo. These include task metadata, prompt files, output paths, validation/import commands, and review pages.

The files in this repository are intended to make the Codex UI setup deterministic and repeatable. To actually run on a timer, create scheduled tasks in Codex Cloud and point them at the prompt files listed in `config/automation.yaml`.

Recommended first schedules:

| Task | Prompt | Suggested schedule |
| --- | --- | --- |
| LLM Intelligence OS / Daily Discovery | `config/prompts/codex_daily_discovery.md` | `0 1 * * *` |
| LLM Intelligence OS / Weekly Deep Discovery | `config/prompts/codex_weekly_deep_discovery.md` | `0 2 * * 0` |

Optional later schedules:

| Task | Prompt | Suggested schedule |
| --- | --- | --- |
| LLM Intelligence OS / Source Scout | `config/prompts/codex_source_scout.md` | `0 3 1,15 * *` |
| LLM Intelligence OS / Monthly Synthesis Candidate | `config/prompts/codex_monthly_synthesis_candidate.md` | `0 4 28 * *` |

When a scheduled run writes candidates, the expected local tail commands are:

```bash
python scripts/validate_codex_candidates.py
python scripts/import_codex_candidates.py
python scripts/review.py
python scripts/build_site.py
```

The Discovery page is generated at `site/discovery.html` and shows candidate evidence plus run logs for manual review before publishing.
