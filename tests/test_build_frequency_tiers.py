import tempfile
import unittest
from pathlib import Path

from scripts.build_frequency_tiers import build_plan


class BuildFrequencyTiersTest(unittest.TestCase):
    def test_normalizes_uuid_record_ids_to_the_catalog_form(self):
        with tempfile.TemporaryDirectory() as tmp:
            problems_root = Path(tmp) / "problems"
            problem_dir = problems_root / "101-toy"
            problem_dir.mkdir(parents=True)
            (problem_dir / "problem.json").write_text(
                '{"slug": "toy", "companies": ["Airbnb"]}', encoding="utf-8"
            )

            plan = build_plan(
                [
                    {
                        "record_id": "3cf6ce51-456d-8102-bae9-c6263f064d5e",
                        "company": "Airbnb",
                        "seen_count": 1,
                        "slug": "toy",
                    }
                ],
                problems_root,
                "2026-09-02",
            )

        self.assertEqual(
            plan["problems"]["toy"]["interview_frequency"]["Airbnb"]["source_record_ids"],
            ["3cf6ce51456d8102bae9c6263f064d5e"],
        )

    def test_combines_company_signals_without_retaining_raw_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            problems_root = Path(tmp) / "problems"
            problem_dir = problems_root / "101-toy"
            problem_dir.mkdir(parents=True)
            (problem_dir / "problem.json").write_text(
                '{"slug": "toy", "companies": ["Mistral AI"]}', encoding="utf-8"
            )

            plan = build_plan(
                [
                    {"record_id": "row-1", "company": "MistraAI", "seen_count": 1, "slug": "toy"},
                    {"record_id": "row-2", "company": "MicrosoftAI", "seen_count": 1, "slug": "toy"},
                ],
                problems_root,
                "2026-08-30",
            )

        entry = plan["problems"]["toy"]
        self.assertEqual(entry["companies"], ["Mistral AI", "MicrosoftAI"])
        self.assertEqual(entry["interview_frequency"]["Mistral AI"]["stars"], 1)
        self.assertEqual(entry["interview_frequency"]["MicrosoftAI"]["stars"], 1)
        self.assertEqual(entry["interview_frequency_total"], {"stars": 2, "synced_at": "2026-08-30"})
        self.assertNotIn("seen_count", str(entry))

    def test_maps_gdm_source_label_to_google_deepmind(self):
        with tempfile.TemporaryDirectory() as tmp:
            problems_root = Path(tmp) / "problems"
            problem_dir = problems_root / "101-toy"
            problem_dir.mkdir(parents=True)
            (problem_dir / "problem.json").write_text(
                '{"slug": "toy", "companies": ["Google DeepMind"]}', encoding="utf-8"
            )

            plan = build_plan(
                [{"record_id": "row-1", "company": "GDM", "seen_count": 1, "slug": "toy"}],
                problems_root,
                "2026-08-30",
            )

        entry = plan["problems"]["toy"]
        self.assertEqual(entry["companies"], ["Google DeepMind"])
        self.assertEqual(entry["interview_frequency"]["Google DeepMind"]["stars"], 1)
