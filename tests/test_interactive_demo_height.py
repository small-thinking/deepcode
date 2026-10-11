import shutil
import subprocess
import unittest
from pathlib import Path


@unittest.skipUnless(shutil.which("node"), "Node is required to exercise demo height messages")
class InteractiveDemoHeightTest(unittest.TestCase):
    def test_content_height_grows_and_shrinks_without_a_ceiling(self):
        source = Path("frontend/app.js").read_text()
        handlers = source[
            source.index("function interactiveDemoFrameForSource("):
            source.index('window.addEventListener("message", handleInteractiveDemoMessage)')
        ]
        script = """
const assert = require('node:assert/strict');
const styles = new Map();
const frame = {
  contentWindow: {},
  dataset: { demoSchemaVersion: '1', demoHeight: 'content' },
  style: { setProperty: (name, value) => styles.set(name, value) },
};
const document = { querySelectorAll: () => [frame] };
""" + handlers + """
const send = (height, overrides = {}) => handleInteractiveDemoMessage({
  source: frame.contentWindow,
  data: { type: 'deepcode:interactive-demo-height', version: 1, height },
  ...overrides,
});
send(6400.3);
assert.equal(styles.get('--interactive-demo-height'), '6401px');
send(1234);
assert.equal(styles.get('--interactive-demo-height'), '1234px');
send(200);
assert.equal(styles.get('--interactive-demo-height'), '320px');

send(9876, { source: {} });
send(9876, { data: { type: 'deepcode:interactive-demo-height', version: 2, height: 9876 } });
for (const height of [NaN, Infinity, -100, 0]) send(height);
assert.equal(styles.get('--interactive-demo-height'), '320px');
frame.dataset.demoHeight = 'fixed';
send(9876);
assert.equal(styles.get('--interactive-demo-height'), '320px');
"""
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
