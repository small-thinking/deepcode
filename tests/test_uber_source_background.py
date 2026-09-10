import unittest
from pathlib import Path

from deepcode.problem_store import ProblemStore


ROOT = Path(__file__).resolve().parents[1]

NOTION_TO_SLUG = {
    "3d76ce51456d819fbf16f5b4950fcf03": "clip-symmetric-contrastive-loss",
    "3d66ce51456d8116a8e8f796e2e5f158": "l1-k-medoids-pickup-locations",
    "3d66ce51456d81848fd7d34e9a1a4ec6": "pytorch-projected-multihead-attention",
    "3d66ce51456d8192b499fe7f55f6285b": "linear-logistic-regression-training",
    "3d66ce51456d81b19c75c15c265079fc": "deterministic-markov-text-generator",
    "3d66ce51456d81d284dadb6bd7837e01": "order-completion-slice-metric",
    "3d76ce51456d8100b0affddec99b1d3e": "uber-eats-search-ml-system",
    "3d66ce51456d8119874ddea74757dea5": "payment-fraud-ml-system",
    "3d66ce51456d819e96f4fdb72083dc76": "marketplace-recommendation-eta-design",
    "3d76ce51456d813e99e9c4b76030d495": "end-to-end-project-deep-dive",
    "3d66ce51456d814ab567e94ece12a1cf": "ml-system-conflict-resolution",
    "3d76ce51456d81d8a273e693d8720eaa": "alien-dictionary-order",
    "3d66ce51456d81319399c204b4f712e7": "bounded-convex-minimization",
    "3d66ce51456d8140a8cce384e48c16b7": "longest-bounded-difference-subarray",
    "3d66ce51456d816eb77fe2a7be51e4f4": "robots-by-blocker-distances",
    "3d66ce51456d8179ac80e29bfc6f3b92": "sorted-squares-and-kth-square",
    "3d66ce51456d81a99802d5b9143a3e58": "phone-keypad-combination-count",
    "3d66ce51456d81d88c81e129f4d27b01": "static-and-streaming-islands",
}


class UberSourceBackgroundTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = ProblemStore(ROOT / "problems")

    def test_every_current_notion_uber_row_has_one_exact_mapping(self):
        uber = {problem["slug"]: problem for problem in self.store.list_problems(company="Uber")}
        self.assertEqual(set(uber), set(NOTION_TO_SLUG.values()))

        for record_id, slug in NOTION_TO_SLUG.items():
            with self.subTest(slug=slug):
                problem = uber[slug]
                frequency = problem["interview_frequency"]["Uber"]
                self.assertEqual(frequency["source_record_ids"], [record_id])

    def test_every_uber_mapping_exposes_notion_and_original_sources(self):
        for record_id, slug in NOTION_TO_SLUG.items():
            with self.subTest(slug=slug):
                problem = self.store.get_problem(slug)
                references = problem.get("references", [])
                urls = [reference["url"] for reference in references]
                self.assertIn(f"https://app.notion.com/p/{record_id}", urls)
                self.assertTrue(
                    any("app.notion.com" not in url for url in urls),
                    f"{slug} is missing its original interview source",
                )

    def test_corrected_conflict_prompt_is_behavioral(self):
        problem = self.store.get_problem("ml-system-conflict-resolution")
        self.assertEqual(problem["category"], "Behavioral")
        self.assertIn("real disagreement or conflict", problem["prompt"])
        self.assertNotIn("Choose an ML system", problem["prompt"])


if __name__ == "__main__":
    unittest.main()
