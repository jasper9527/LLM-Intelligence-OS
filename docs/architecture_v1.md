# LLM Intelligence OS v1 Architecture Design

## 0. Design intent

LLM Intelligence OS is an information infrastructure for tracking the external environment around large language model algorithm work. It is not a career decision agent, a personal planning dashboard, a paper-summary bot, or a generic RSS reader.

The system exists to compensate for a weak local LLM algorithm environment by continuously building an external information field: jobs, companies, research, technical reports, benchmarks, open-source projects, source quality, controversies, negative evidence, and breakout signals.

The user owns final judgment. The system owns discovery, organization, summarization, routing, traceability, and long-term knowledge accumulation.

## 1. Product boundaries

### 1.1 Goals

The architecture should support these goals:

1. Discover important external signals before they are lost in daily noise.
2. Organize raw signals into maintainable modules instead of a single weekly dump.
3. Compress information with short summaries, evidence references, and tags.
4. Preserve breadth through breakout signals and uncategorized observations.
5. Preserve skepticism through negative signals, red flags, controversies, and source-quality notes.
6. Accumulate long-term field understanding through landscape cards and monthly reviews.
7. Publish a static HTML reading layer that is easy to open across devices.

### 1.2 Non-goals

The system must not:

1. Decide which research direction or job target the user should choose.
2. Produce personal learning plans, application plans, reminders, or execution dashboards.
3. Treat weekly briefs as the whole product.
4. Collapse all LLM algorithm work into a fixed taxonomy that cannot evolve.
5. Use scores as a substitute for evidence, disagreement, and stateful analysis.
6. Chase full-web coverage at the cost of source quality and maintainability.
7. Start with a complex frontend, database backend, login system, or multi-agent debate layer.

## 2. Architecture principles

### 2.1 Information first, decision second

The system may analyze what changed, why a signal matters, and what remains uncertain. It should avoid direct prescriptions such as "switch to this direction". When needed, it can surface decision-relevant context in neutral language: "this signal may affect the understanding of X, but evidence is incomplete because Y."

### 2.2 Modular responsibilities

No single module should own the entire intelligence workflow. Collection, routing, radar updates, landscape maintenance, reporting, and presentation are separate responsibilities. This keeps the system inspectable and prevents weekly reports from becoming an unmaintainable dumping ground.

### 2.3 Open taxonomy

The LLM algorithm field does not have a stable single hierarchy. Every item can carry multiple perspectives: entity, area, method, task, job relevance, signal type, maturity, and source type. Taxonomy files provide starting vocabularies, not permanent truth.

### 2.4 Traceable evidence

Every non-trivial summary should point back to evidence: URL, source name, source type, collection date, and routed module. Reports should summarize, but raw events remain available.

### 2.5 State over novelty

The system should not reset each week. Weekly reports are navigation pages; durable state lives in job species records, paper records, source records, and landscape cards.

### 2.6 Static-first delivery

The default delivery target is a static HTML site generated from JSONL, JSON, Markdown, and Jinja2 templates. This favors portability, transparency, and low maintenance over complex application behavior.

## 3. Module map

The ideal v1 system contains seven modules:

```text
External sources
    ↓
[1. Event Stream]
    ↓
[Router]
    ├─ [2. Job & Company Radar]
    ├─ [3. Research Radar]
    ├─ [4. Tech Landscape]
    ├─ [5. Source Map]
    └─ [Archive / Ignore]
    ↓
[6. Weekly Brief]
    ↓
[7. Monthly Review]
    ↓
Static HTML site
```

## 4. Module responsibilities

### 4.1 Event Stream

Event Stream is the sensing layer. It receives external items and performs minimum viable processing.

Responsibilities:

- collect configured sources;
- normalize raw records;
- deduplicate obvious repeats;
- generate short summaries;
- assign tags;
- estimate novelty, credibility, and relevance;
- route items to downstream modules;
- preserve low-level evidence for later inspection.

It should not perform deep career judgment or replace the downstream radar modules.

Minimum event fields:

```json
{
  "id": "event_YYYYMMDD_0001",
  "date": "YYYY-MM-DD",
  "title": "",
  "url": "",
  "source": "",
  "source_type": "",
  "content_type": "",
  "raw_summary": "",
  "short_summary": "",
  "entities": [],
  "area_tags": [],
  "method_tags": [],
  "task_tags": [],
  "job_tags": [],
  "signal_tags": [],
  "novelty": "low|medium|high",
  "credibility": "low|medium|high",
  "relevance": "low|medium|high",
  "routed_to": [],
  "status": "new|processed|archived|ignored",
  "created_at": "",
  "updated_at": ""
}
```

### 4.2 Job & Company Radar

Job & Company Radar is the employment-environment sensing layer. It tracks job species, company movement, JD language, hiring signals, and role-quality red flags.

Responsibilities:

- maintain evolving job species;
- record recent job and company signals;
- extract common keywords and requirements;
- distinguish algorithmic work from application delivery when evidence allows;
- track positive signals, red flags, and open questions;
- keep decisions outside the module.

Initial job species can include foundation model, post-training, reasoning, agent/tool-use, search/deep research, multimodal, AI coding, eval/data, safety, domain LLM, and training/serving infra. These are containers for observation, not fixed career recommendations.

Job species record shape:

```json
{
  "job_species": "",
  "aliases": [],
  "definition": "",
  "scope": "",
  "not_scope": "",
  "recent_job_signals": [],
  "companies": [],
  "common_keywords": [],
  "typical_tasks": [],
  "common_requirements": [],
  "positive_signals": [],
  "red_flags": [],
  "market_observation": "",
  "recent_changes": [],
  "open_questions": [],
  "last_updated": ""
}
```

### 4.3 Research Radar

Research Radar is the research-frontier sensing layer. It should not become a large pile of paper abstracts. Its main unit is the research problem and why that problem matters now.

Responsibilities:

- track papers, technical reports, benchmarks, and relevant repositories;
- summarize problem, method, evidence, limitations, and relevance;
- identify must-read and optional items;
- connect papers to landscape cards and job-relevance tags;
- detect emerging problems and disagreements.

Paper record shape:

```json
{
  "paper_id": "",
  "title": "",
  "authors": [],
  "venue_or_source": "",
  "date": "",
  "url": "",
  "code_url": "",
  "problem": "",
  "method_summary": "",
  "key_contribution": "",
  "evidence_strength": "weak|medium|strong",
  "limitations": "",
  "area_tags": [],
  "method_tags": [],
  "task_tags": [],
  "job_relevance_tags": [],
  "read_priority": "must_read|should_read|optional|archive",
  "why_it_matters": "",
  "why_maybe_not": "",
  "related_landscape_cards": [],
  "status": "new|summarized|queued|read|archived"
}
```

### 4.4 Tech Landscape

Tech Landscape is the long-term memory layer. It stores the current understanding of a technical area after repeated evidence has accumulated.

Responsibilities:

- maintain field cards for technical areas;
- record definitions, boundaries, representative work, adoption, risks, and controversies;
- accumulate recent developments and negative evidence;
- expose open questions instead of forcing premature conclusions;
- update from weekly and monthly review cycles.

Landscape card shape:

```json
{
  "name": "",
  "aliases": [],
  "definition": "",
  "scope": "",
  "not_scope": "",
  "why_it_matters": "",
  "current_state": "",
  "key_methods": [],
  "key_tasks": [],
  "key_benchmarks": [],
  "representative_papers": [],
  "representative_companies": [],
  "industry_adoption": "",
  "job_relevance": "",
  "risks": [],
  "controversies": [],
  "open_questions": [],
  "recent_developments": [],
  "negative_signals": [],
  "watch_level": "low|medium|high",
  "last_updated": ""
}
```

### 4.5 Source Map

Source Map evaluates information-source quality. It prevents the system from treating every source as equally reliable.

Responsibilities:

- record source identity, type, coverage, quality, bias, and limitations;
- distinguish fast-but-noisy sources from slow-but-authoritative sources;
- track last checked time and best-use cases;
- inform routing and report confidence.

Source record shape:

```json
{
  "source_id": "",
  "name": "",
  "type": "official_job|paper|company_blog|open_source|community|social|personal|newsletter",
  "url": "",
  "coverage": [],
  "signal_quality": "low|medium|high",
  "noise_level": "low|medium|high",
  "bias": "",
  "best_for": [],
  "not_good_for": [],
  "update_frequency": "",
  "last_checked": "",
  "notes": ""
}
```

### 4.6 Weekly Brief

Weekly Brief is a navigation layer, not a storage layer. It should help the user decide where to read deeper without burying all source material in one report.

Recommended structure:

```markdown
# Weekly Brief: YYYY-WW

## 0. Information density
## 1. Top 5 signals
## 2. Job & Company Radar updates
## 3. Research Radar updates
## 4. Tech Landscape updates
## 5. Breakout signals
## 6. Reading queue
## 7. Open questions for next week
```

### 4.7 Monthly Review

Monthly Review is the cognitive-sedimentation layer. It is not a concatenation of weekly briefs.

Recommended structure:

```markdown
# Monthly Review: YYYY-MM

## 1. Overall field changes
## 2. Job-market review
## 3. Research-trend review
## 4. Tech Landscape update summary
## 5. Breakout review
## 6. Watchlist for next month
## 7. Questions requiring human discussion
```

## 5. Routing design

Every event should pass through routing before it affects deeper modules.

### 5.1 Routing targets

- `event_stream`: default record of the item.
- `job_radar`: JD, hiring, team movement, interview feedback, or company role signal.
- `research_radar`: paper, technical report, benchmark, repository, or research discussion.
- `tech_landscape`: evidence that changes or challenges a field card.
- `source_map`: evidence about source quality or source behavior.
- `weekly_brief_candidate`: candidate for weekly navigation.
- `monthly_review_candidate`: candidate for durable synthesis.
- `archive`: low-value but retained.
- `ignore`: duplicate, irrelevant, or unusable.

### 5.2 Signal handling rules

- Job-related items can route to both Job Radar and Tech Landscape if they imply field adoption.
- Papers can route to both Research Radar and Tech Landscape if they update a field card.
- Model releases and technical reports can route to Event Stream, Research Radar, Job Radar, and Tech Landscape.
- Hype-heavy sources may stay in Event Stream unless corroborated.
- Negative evidence must not be discarded only because it conflicts with a current interest.
- Breakout signals must be preserved even when they do not fit existing tags.

### 5.3 Importance dimensions

The system should avoid popularity-only ranking. Importance should combine:

- `novelty`: whether the information is new relative to stored state;
- `credibility`: whether the source and evidence are reliable;
- `relevance`: whether it affects LLM algorithm, job, research, or field understanding;
- `scope`: whether the signal is isolated, repeated, or cross-source;
- `uncertainty`: what remains unknown.

## 6. Tagging design

The v1 taxonomy should provide starting vocabularies across six groups:

1. Entity tags: companies, institutions, models, benchmarks, products, people.
2. Area tags: pretraining, post-training, reasoning, agent, search, multimodal, coding, eval, data, safety, infra, domain LLM.
3. Method tags: SFT, DPO, RL, GRPO, PPO, RLVR, verifier, reward model, judge, retrieval, rerank, synthetic data, distillation, test-time scaling, architecture, MoE.
4. Task tags: math, code, tool-use, deep research, document understanding, video, GUI, medical, finance, education, security, office, data analysis.
5. Job tags: foundation model, post-training, reasoning, agent, search, multimodal, AI coding, eval/data, safety, domain LLM, infra.
6. Signal tags: job, paper, company, model release, benchmark, open source, hotspot, hype risk, negative, breakout, red flag, must read.

The taxonomy must allow `uncategorized`, `needs_review`, and new tags. Monthly review should check whether the taxonomy has become stale or too narrow.

## 7. Data layout

The ideal file-oriented v1 layout is:

```text
config/
  sources.yaml
  taxonomy.yaml
  routing.yaml
  automation.yaml
  prompts/

data/
  raw/
  processed/
  events.jsonl
  jobs.jsonl
  papers.jsonl
  sources.jsonl
  landscape/

reports/
  weekly/
  monthly/

scripts/
  collect.py
  normalize.py
  dedupe.py
  classify.py
  route.py
  update_jobs.py
  update_research.py
  update_landscape.py
  generate_weekly.py
  generate_monthly.py
  build_site.py
  deploy.py

templates/
  base.html
  index.html
  events.html
  jobs.html
  research.html
  landscape.html
  sources.html
  reports.html

site/
  index.html
  events.html
  jobs.html
  research.html
  landscape.html
  sources.html
  reports.html
  assets/
```

JSONL remains the preferred MVP storage format because it is easy to inspect, diff, and repair. SQLite can be introduced later if filtering, joins, or dataset size justify it.

## 8. Static site design

The HTML site should optimize reading, navigation, and traceability.

### 8.1 Dashboard

Dashboard should show:

- latest weekly brief;
- top signals;
- information density;
- recent job radar changes;
- research radar highlights;
- landscape cards updated recently;
- breakout signals;
- reading queue;
- freshness timestamps.

### 8.2 Event Stream page

Event Stream should support:

- chronological browsing;
- source and source-type filters;
- tag filters;
- novelty, credibility, and relevance indicators;
- search;
- raw evidence links;
- routed module links.

### 8.3 Job Radar page

Job Radar should show:

- job species list;
- recent signals by species;
- company distribution;
- common keywords;
- positive signals;
- red flags;
- open questions.

### 8.4 Research Radar page

Research Radar should show:

- recent papers and reports;
- must-read and should-read queues;
- problem summaries;
- method and task tags;
- evidence strength;
- limitations;
- related landscape cards.

### 8.5 Tech Landscape page

Tech Landscape should show:

- field-card list;
- definitions and boundaries;
- current state;
- recent developments;
- representative work;
- industry adoption;
- job relevance;
- risks, controversies, negative signals, and open questions.

### 8.6 Source Map page

Source Map should show:

- source list;
- coverage;
- signal quality;
- noise level;
- bias and limitations;
- best-use cases;
- last checked time.

### 8.7 Reports page

Reports should show:

- weekly brief archive;
- monthly review archive;
- recent report highlights;
- links back to underlying module records.

## 9. Automation design

### 9.1 Daily collect task

Frequency: 1-2 times per day.

Responsibilities:

- collect enabled sources;
- normalize records;
- dedupe;
- classify;
- route;
- update Event Stream;
- rebuild static site.

### 9.2 Radar update task

Frequency: every 2-3 days.

Responsibilities:

- refresh Job Radar aggregates;
- refresh Research Radar summaries;
- update source freshness;
- mark landscape-update candidates.

### 9.3 Weekly brief task

Frequency: once per week.

Responsibilities:

- summarize top signals;
- update report archive;
- produce reading queue;
- preserve breakout signals;
- list unresolved questions.

### 9.4 Monthly review task

Frequency: once per month.

Responsibilities:

- synthesize the month;
- update Tech Landscape cards;
- review taxonomy drift;
- review source quality;
- identify next-month watchlist and human discussion questions.

## 10. MVP implementation boundary

### 10.1 Must have

The MVP should include:

- configurable sources;
- Event Stream records;
- routeable events;
- Job Radar records;
- Research Radar records;
- basic Tech Landscape cards;
- Source Map records;
- Weekly Brief generation;
- simple Monthly Review scaffold;
- static HTML pages;
- unit tests for normalization, routing, and site generation.

### 10.2 Defer

The MVP should defer:

- scoring-based direction recommendations;
- personal task planning;
- complex database backend;
- React or Next.js frontend;
- login and multi-user features;
- full-text search backend;
- multi-agent debate;
- automated deep paper reading.

## 11. Acceptance criteria for four-week trial

After four weeks, the system should be judged by these criteria:

1. It surfaced important signals the user would not reliably see manually.
2. It separated raw events, radar updates, landscape state, and reports cleanly.
3. It made source quality and evidence traceable.
4. It preserved negative and breakout signals instead of reinforcing only familiar directions.
5. It produced weekly briefs that served as navigation pages rather than bloated essays.
6. It updated at least a small number of landscape cards with durable field understanding.
7. Its static site was easier to read and maintain than raw Markdown alone.

## 12. Open design questions before implementation

These questions should be aligned before larger code changes:

1. Which concrete source categories should be enabled first for the four-week trial?
2. How strict should the first routing thresholds be for novelty, credibility, and relevance?
3. Should reports be stored as Markdown, JSON, or both?
4. How much frontend filtering is enough for v1 without adding a frontend framework?
5. Which landscape cards should be initialized manually versus grown from collected evidence?
6. How should user-provided manual submissions enter the same pipeline as automated sources?
7. What minimum evidence is required before a signal can update a landscape card?
