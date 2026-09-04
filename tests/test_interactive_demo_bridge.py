import shutil
import subprocess
import unittest
from pathlib import Path


class InteractiveDemoBridgeTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node is required to exercise the JS bridge")
    def test_scroll_requires_known_visible_frame_and_matching_version(self):
        source = Path("frontend/app.js").read_text(encoding="utf-8")
        handler = source.split("function handleInteractiveDemoMessage(event) {", 1)[1]
        handler = handler.split('\nwindow.addEventListener("message", handleInteractiveDemoMessage)', 1)[0]
        script = """
const assert = require('node:assert/strict');
let scrolls = 0;
let visible = true;
const knownSource = {};
const frame = {
  dataset: {demoSchemaVersion: '1'},
  getClientRects: () => visible ? [{}] : [],
  scrollIntoView: options => {
    assert.deepEqual(options, {block: 'start', behavior: 'instant'});
    scrolls++;
  },
};
const interactiveDemoFrameForSource = source => source === knownSource ? frame : null;
""" + "function handleInteractiveDemoMessage(event) {" + handler + """
const data = {type: 'deepcode:interactive-demo-scroll-start', version: 1};
handleInteractiveDemoMessage({source: {}, data});
handleInteractiveDemoMessage({source: knownSource, data: {...data, version: 2}});
visible = false;
handleInteractiveDemoMessage({source: knownSource, data});
assert.equal(scrolls, 0);
visible = true;
handleInteractiveDemoMessage({source: knownSource, data});
assert.equal(scrolls, 1);
"""
        subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
