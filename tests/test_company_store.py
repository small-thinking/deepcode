import json
import tempfile
import unittest
from pathlib import Path

from deepcode.company_store import CompanyStore
from deepcode.problem_store import ProblemStore


class CompanyStoreTest(unittest.TestCase):
    def test_committed_harvey_profile_loads_and_links_to_harvey_problems(self):
        root = Path(__file__).resolve().parents[1]
        companies = CompanyStore(root / "companies")
        problems = ProblemStore(root / "problems").list_problems()

        harvey = companies.get_company("harvey", problems)

        self.assertEqual(harvey["stage"]["company_state"], "Private")
        self.assertEqual(harvey["stage"]["funding_stage"], "Growth round")
        self.assertEqual(
            {problem["slug"] for problem in harvey["related_problems"]},
            {
                "source-attribution-highlighter",
                "in-memory-unix-file-system",
                "text-editor",
                "spreadsheet-dependency-cycle",
            },
        )

    def test_lists_profiles_and_links_matching_problem_companies(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_company(root, "harvey", self._company("Harvey"))
            store = CompanyStore(root)
            problems = [
                {
                    "display_id": 2,
                    "slug": "filesystem",
                    "title": "In-Memory File System",
                    "category": "Systems Coding",
                    "difficulty": "medium",
                    "companies": ["HARVEY"],
                },
                {
                    "display_id": 1,
                    "slug": "unrelated",
                    "title": "Unrelated",
                    "companies": ["OpenAI"],
                },
            ]

            summary = store.list_companies(problems)
            detail = store.get_company("Harvey", problems)

            self.assertEqual(summary[0]["name"], "Harvey")
            self.assertEqual(summary[0]["problem_count"], 1)
            self.assertEqual([problem["slug"] for problem in detail["related_problems"]], ["filesystem"])
            self.assertEqual(detail["stage"]["funding_stage"], "Series B")

    def test_rejects_missing_stage_or_unsafe_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            broken = self._company("Broken")
            broken["stage"].pop("funding_stage")
            self._write_company(root, "broken", broken)

            with self.assertRaisesRegex(ValueError, "funding_stage"):
                CompanyStore(root).list_companies([])

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            broken = self._company("Broken")
            broken["links"] = [{"label": "Unsafe", "url": "javascript:alert(1)"}]
            self._write_company(root, "broken", broken)

            with self.assertRaisesRegex(ValueError, "links"):
                CompanyStore(root).list_companies([])

    def _write_company(self, root, slug, company):
        (root / f"{slug}.json").write_text(json.dumps(company), encoding="utf-8")

    def _company(self, name):
        return {
            "slug": name.casefold(),
            "name": name,
            "summary": "A company profile.",
            "stage": {
                "company_state": "Private",
                "funding_stage": "Series B",
                "source": {"label": "Funding", "url": "https://example.com/funding"},
            },
            "links": [{"label": "Website", "url": "https://example.com"}],
            "interview_process": {
                "stages": [
                    {
                        "name": "Technical screen",
                        "signal": "Public signal only.",
                        "evidence_tier": "Candidate report",
                        "sources": [{"label": "Source", "url": "https://example.com/source"}],
                    }
                ]
            },
            "references": [{"label": "Company", "url": "https://example.com"}],
        }


if __name__ == "__main__":
    unittest.main()
