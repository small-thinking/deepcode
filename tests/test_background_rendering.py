import shutil
import subprocess
import unittest
from pathlib import Path


class BackgroundRenderingTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node is required to exercise rendering")
    def test_background_shows_links_or_an_explicit_source_gap(self):
        source = Path("frontend/app.js").read_text(encoding="utf-8")
        functions = []
        for name in ("escapeHtml", "renderProblemBlock", "renderReferences"):
            function = source[source.index(f"function {name}("):]
            functions.append(function.split("\nfunction ", 1)[0])
        script = """
const assert = require('node:assert/strict');
const PROBLEM_SECTION_CLASSES = {references: 'problem-references-section'};
""" + "\n".join(functions) + """
for (const references of [undefined, null, [], [{}]]) {
  const html = renderReferences(references);
  assert.match(html, />Background</);
  assert.match(html, /original interview source has not been linked/);
  assert.doesNotMatch(html, /<a /);
}
const html = renderReferences([{label: 'Interview <report>', url: 'https://example.org/post?a=1&b=2'}]);
assert.match(html, />Background</);
assert.match(html, /Interview &lt;report&gt;/);
assert.match(html, /href="https:\/\/example.org\/post\?a=1&amp;b=2"/);
assert.match(html, /rel="noopener noreferrer"/);
assert.doesNotMatch(html, /has not been linked/);
"""
        subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
