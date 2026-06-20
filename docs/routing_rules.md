# Routing Rules

Every normalized event enters `data/events.jsonl` first. Routing decides which durable modules should receive additional updates.

- Research papers, technical reports, benchmark releases, and notable repositories route to Research Radar.
- Hiring pages, job descriptions, team announcements, and recruiter notes route to Job & Company Radar.
- Repeated signals, field-level shifts, controversies, and open questions route to Tech Landscape candidates.
- Source behavior observations route to Source Map.
- Weekly and monthly reports link back to module records rather than duplicating all detail.
