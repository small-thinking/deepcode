import contextlib
import io
import json
import unittest
from pathlib import Path


PROBLEM_DIR = Path(__file__).resolve().parents[1] / "problems/408-clip-symmetric-contrastive-loss"


class ClipLossCoverageTest(unittest.TestCase):
    def setUp(self):
        self.solution = (PROBLEM_DIR / "solution.py").read_text()
        self.cases = json.loads((PROBLEM_DIR / "tests.json").read_text())

    def run_case(self, code, index):
        namespace = {}
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(code, "<candidate>", "exec"), namespace)
            exec(compile(self.cases[index]["test"], "<visible-test>", "exec"), namespace)

    def test_float32_intermediates_pass_all_cases(self):
        candidate = self.solution.replace(
            "    images = F.normalize",
            "    output_dtype = image_embeddings.dtype\n"
            "    image_embeddings = image_embeddings.float()\n"
            "    text_embeddings = text_embeddings.float()\n"
            "    images = F.normalize",
        ).replace(
            "return (image_loss + text_loss) / 2",
            "return ((image_loss + text_loss) / 2).to(output_dtype)",
        )
        self.assertNotEqual(candidate, self.solution)
        for index, case in enumerate(self.cases):
            with self.subTest(case=case["name"]):
                self.run_case(candidate, index)

    def test_cases_reject_specific_contrastive_loss_mistakes(self):
        variants = (
            ("only image-to-text", "return (image_loss + text_loss) / 2", "return image_loss", 3),
            ("sum without average", "return (image_loss + text_loss) / 2", "return image_loss + text_loss", 3),
            ("missing transpose", "F.cross_entropy(logits.transpose(0, 1), labels)", "F.cross_entropy(logits, labels)", 3),
            ("wrong temperature", " / temperature", " * temperature", 6),
            ("wrong normalization axis", "dim=-1", "dim=0", 4),
            ("in-place normalization", "images = F.normalize(image_embeddings, dim=-1)", "images = image_embeddings.div_(image_embeddings.norm(dim=-1, keepdim=True))", 4),
            ("detached text features", "texts = F.normalize", "text_embeddings = text_embeddings.detach()\n    texts = F.normalize", 5),
            ("unstable log softmax", "F.cross_entropy(logits, labels)", "F.nll_loss(logits.softmax(dim=1).log(), labels)", 6),
        )
        for name, old, new, index in variants:
            with self.subTest(mistake=name):
                self.assertIn(old, self.solution)
                candidate = self.solution.replace(old, new)
                with self.assertRaises((AssertionError, RuntimeError, ValueError)):
                    self.run_case(candidate, index)


if __name__ == "__main__":
    unittest.main()
