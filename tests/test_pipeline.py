from __future__ import annotations

import importlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


class PipelineTestCase(unittest.TestCase):
    def make_root(self) -> tuple[Path, object]:
        temp_dir = Path(tempfile.mkdtemp(prefix="llm-intel-os-"))
        for relative in ("config", "templates", "data/landscape"):
            source = REPO_ROOT / relative
            target = temp_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source, target, dirs_exist_ok=True)
        for relative in ("data/weekly", "data/monthly", "data/raw", "data/processed", "site"):
            (temp_dir / relative).mkdir(parents=True, exist_ok=True)
        for relative in ("data/events.jsonl", "data/papers.jsonl", "data/jobs.jsonl", "data/sources.jsonl", "data/raw/manual_submissions.jsonl"):
            (temp_dir / relative).write_text("", encoding="utf-8")
        os.environ["INTEL_OS_ROOT"] = str(temp_dir)
        sys.modules.pop("intel", None)
        intel = importlib.import_module("intel")
        intel.ensure_layout()
        return temp_dir, intel

    def tearDown(self) -> None:
        os.environ.pop("INTEL_OS_ROOT", None)

    def test_manual_submission_enters_draft_and_candidate_tag_queue(self) -> None:
        root, intel = self.make_root()
        try:
            submission = {
                "submission_id": "manual-001",
                "source_id": "manual-submission",
                "title": "Verifier-heavy reasoning paper",
                "url": "https://example.com/verifier-paper",
                "date": "2026-06-20",
                "content_type": "paper",
                "summary": "A manual paper import focused on verifier-guided reasoning.",
                "suggested_tags": {"area_tags": ["area:custom-future-area"]},
            }
            (root / "data/raw/manual_submissions.jsonl").write_text(json.dumps(submission) + "\n", encoding="utf-8")

            result = intel.run_collect(include_scheduled=False, include_manual=True)
            events = intel.load_jsonl(root / "data/events.jsonl")
            candidate_tags = intel.load_json(root / "data/processed/candidate_tags.json", [])

            self.assertEqual(result["new_events"], 1)
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["status"], "draft")
            self.assertTrue(any(item["tag"] == "area:custom-future-area" for item in candidate_tags))
        finally:
            shutil.rmtree(root)

    def test_publish_refresh_and_site_build_produce_reading_surfaces(self) -> None:
        root, intel = self.make_root()
        try:
            submissions = [
                {
                    "submission_id": "paper-001",
                    "source_id": "manual-submission",
                    "title": "Reasoning verifier benchmark paper",
                    "url": "https://example.com/reasoning-paper",
                    "date": "2026-06-20",
                    "content_type": "paper",
                    "summary": "Benchmark-focused reasoning paper with verifier discussion.",
                    "problem": "Improving reasoning reliability.",
                    "method_summary": "Uses verifier-guided selection.",
                    "key_contribution": "Connects verification with benchmark gains.",
                    "limitations": "Needs broader replication.",
                    "why_it_matters": "Useful for current reasoning and eval hiring trends.",
                    "why_maybe_not": "Small evaluation footprint so far.",
                    "suggested_tags": {"area_tags": ["area:reasoning-verifier-reward"]},
                },
                {
                    "submission_id": "job-001",
                    "source_id": "manual-submission",
                    "title": "Agent Systems Engineer",
                    "url": "https://example.com/agent-job",
                    "date": "2026-06-20",
                    "content_type": "job_description",
                    "summary": "Hiring for agent infrastructure and browser automation.",
                    "company": "Example AI",
                    "team": "Agent Platform",
                    "location": "San Francisco",
                    "job_species": "agent-systems-engineer",
                    "positive_signals": ["agent capability demand"],
                    "suggested_tags": {"area_tags": ["area:agent-tool-use-computer-use"]},
                },
            ]
            (root / "data/raw/manual_submissions.jsonl").write_text(
                "\n".join(json.dumps(item) for item in submissions) + "\n",
                encoding="utf-8",
            )

            intel.run_collect(include_scheduled=False, include_manual=True)
            event_ids = [item["id"] for item in intel.load_jsonl(root / "data/events.jsonl")]
            intel.update_event_status(event_ids, "published")
            refresh = intel.refresh_derived_outputs()
            pages = intel.build_site()

            self.assertGreaterEqual(refresh["papers"], 1)
            self.assertGreaterEqual(refresh["jobs"], 1)
            self.assertEqual(len(pages), 8)
            self.assertTrue((root / "site/events.html").exists())
            self.assertTrue((root / "site/drafts.html").exists())
            self.assertTrue(list((root / "data/weekly").glob("*.json")))
            events_html = (root / "site/events.html").read_text(encoding="utf-8")
            research_html = (root / "site/research.html").read_text(encoding="utf-8")
            self.assertIn("filter-credibility", events_html)
            self.assertIn("Research problem", research_html)
        finally:
            shutil.rmtree(root)

    def test_landscape_updates_stay_in_drafts(self) -> None:
        root, intel = self.make_root()
        try:
            official_path = root / "data/landscape/reasoning-verifier-reward.json"
            before = official_path.read_text(encoding="utf-8")
            submission = {
                "submission_id": "paper-002",
                "source_id": "manual-submission",
                "title": "Breakthrough verifier signal",
                "url": "https://example.com/breakthrough",
                "date": "2026-06-20",
                "content_type": "paper",
                "summary": "Frontier benchmark result with verifier-led gains and visible limitation discussion.",
                "suggested_tags": {"area_tags": ["area:reasoning-verifier-reward"]},
            }
            (root / "data/raw/manual_submissions.jsonl").write_text(json.dumps(submission) + "\n", encoding="utf-8")

            intel.run_collect(include_scheduled=False, include_manual=True)
            event_ids = [item["id"] for item in intel.load_jsonl(root / "data/events.jsonl")]
            intel.update_event_status(event_ids, "published")
            intel.refresh_derived_outputs()

            draft_files = list((root / "data/processed/landscape_drafts").glob("*.json"))
            after = official_path.read_text(encoding="utf-8")
            self.assertTrue(draft_files)
            self.assertEqual(before, after)
        finally:
            shutil.rmtree(root)


if __name__ == "__main__":
    unittest.main()
