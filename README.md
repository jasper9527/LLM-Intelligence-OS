# LLM Intelligence OS

LLM Intelligence OS is a Codex-friendly intelligence system for tracking LLM research, jobs, companies, sources, weekly briefs, and monthly reviews.

The system is intentionally scoped to **information work only**: it collects evidence, summarizes signals, routes items to modules, preserves controversies and negative evidence, and builds a static HTML reading layer. It does not maintain personal learning plans, application shortlists, execution reminders, or decision dashboards.

## Modules

1. **Event Stream**: all incoming external signals with minimal normalization, summary, tagging, dedupe, and routing.
2. **Job & Company Radar**: job species, company/team movement, JD signals, red flags, and recurring capability requirements.
3. **Research Radar**: papers, technical reports, benchmarks, repositories, and research-frontier signals.
4. **Tech Landscape**: durable field cards describing current state, scope, controversies, risks, and open questions.
5. **Source Map**: source quality, bias, noise, coverage, and best-use cases.
6. **Weekly Brief**: navigation-oriented weekly entry point for the most important changes.
7. **Monthly Review**: deeper monthly synthesis and landscape maintenance.

## Workflow

```bash
python -m pip install --index-url https://pypi.org/simple -r requirements.txt
python scripts/validate_codex_candidates.py
python scripts/import_codex_candidates.py
python scripts/collect.py
python scripts/review.py
python scripts/publish.py --all-recommended
python scripts/build_site.py
python scripts/deploy.py
```

Generated HTML is written to `site/`. Raw snapshots land in `data/raw/snapshots/`. Draft review metadata lands in `data/processed/`.

## Codex automation-first discovery

The preferred cloud workflow is now Codex automation-first:

1. Codex discovery tasks write candidate evidence to `data/codex_discovery/candidates/` and run logs to `data/codex_discovery/runs/`.
2. `python scripts/validate_codex_candidates.py` checks required fields, evidence presence, and level values.
3. `python scripts/import_codex_candidates.py` converts valid candidates into Event Stream draft records without publishing them.
4. `python scripts/review.py` and `site/discovery.html`/`site/drafts.html` expose candidates and drafts for review.
5. Existing scripted collectors remain as stable-source support for RSS/API/job-board inputs.

Reusable Codex automation prompts live in `config/prompts/`.

## GitHub Pages

This repository now includes a GitHub Pages workflow at `.github/workflows/deploy-pages.yml`. It builds `site/` on every push to `main` and deploys that artifact through GitHub Actions.

To turn on the public site:

1. Push this repository to GitHub as a public repository.
2. In GitHub, open `Settings -> Pages`.
3. Under `Build and deployment`, set `Source` to `GitHub Actions`.
4. Push to `main` again if needed, or run the `Deploy GitHub Pages` workflow manually from the `Actions` tab.

The site URL will be one of these:

- `https://YOUR-USERNAME.github.io/` if the repository name is `YOUR-USERNAME.github.io`
- `https://YOUR-USERNAME.github.io/LLM-Intelligence-OS/` if the repository name is `LLM-Intelligence-OS`

The workflow follows GitHub's recommended Pages pattern with `configure-pages`, `upload-pages-artifact`, and `deploy-pages`.

## Operator surfaces

- `data/raw/manual_submissions.jsonl`: queue for manual submissions that should enter the same draft pipeline as scheduled sources.
- `site/drafts.html`: review surface for draft events, candidate tags, landscape drafts, and publish recommendations.
- `scripts/publish.py --ids EVENT_ID ...`: explicit publish gate for moving reviewed events into the formal reading layer.
- `scripts/publish.py --reject-ids EVENT_ID ...`: reject items without deleting evidence.

## Scheduled sources

- `arXiv cs.AI` via RSS for research-frontier recall.
- `Anthropic Careers` via Greenhouse board JSON for high-signal hiring changes.
- `xAI Careers` via Greenhouse board JSON for frontier-product hiring changes.

## Status model

- `draft`: visible only in internal review surfaces.
- `published`: visible in formal pages and reports.
- `rejected`: retained in evidence history but excluded from formal pages.

## Repository layout

- `docs/`: product, taxonomy, routing, and source-quality policy.
- `config/`: editable YAML configuration for sources, taxonomy, routing, and automation cadence.
- `data/`: JSONL/JSON evidence and generated report stores.
- `scripts/`: Python automation and static-site generation entry points.
- `templates/`: Jinja2 templates for the static HTML UI.
- `site/`: generated static HTML output.

## Verification

```bash
python -m unittest discover -s tests
```
