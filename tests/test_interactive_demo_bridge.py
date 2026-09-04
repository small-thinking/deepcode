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

    @unittest.skipUnless(shutil.which("node"), "Node is required to exercise tabs")
    def test_coding_tabs_preserve_nodes_lazy_load_and_support_keyboard(self):
        source = Path("frontend/app.js").read_text(encoding="utf-8")
        functions = source[source.index("function activateProblemTab("):source.index("function renderProblemTab(")]
        loader = source[source.index("function loadInteractiveDemos("):source.index("function interactiveDemoFrameForSource(")]
        script = """
const assert = require('node:assert/strict');
const state = {activeTab: 'description'};
let loads = 0, focused = null;
const frame = {
  dataset: {src: '/problem-demos/example/assets/demo.html'},
  addEventListener: () => {},
  setAttribute: (name, value) => {assert.equal(name, 'src'); loads++;},
  removeAttribute: () => {delete frame.dataset.src;},
};
const postInteractiveDemoTheme = () => {};
const names = ['description', 'tests', 'environment', 'demo'];
const tabs = names.map(name => ({dataset: {tab: name}, classList: {toggle: () => {}},
  setAttribute: function(key, value) {this[key] = value;}, focus: () => {focused = name;}}));
const panels = names.map(name => ({dataset: {problemPanel: name}, hidden: name !== 'description',
  querySelectorAll: () => name === 'demo' && frame.dataset.src ? [frame] : []}));
const document = {
  querySelector: selector => panels.find(p => selector.includes('"' + p.dataset.problemPanel + '"')),
  querySelectorAll: selector => selector === '.tab[data-tab]' ? tabs : panels,
};
// No render, editor, or teardown function is available: switching must only toggle existing nodes.
""" + functions + loader + """
activateProblemTab('description');
assert.equal(loads, 0);
activateProblemTab('demo');
assert.equal(loads, 1);
assert.equal(panels[3].hidden, false);
assert.equal(panels[0].hidden, true);
assert.equal(tabs[3]['aria-selected'], 'true');
activateProblemTab('tests');
activateProblemTab('demo');
assert.equal(loads, 1);
assert.equal(tabs[3].tabIndex, 0);
let prevented = 0;
handleProblemTabKeydown({key: 'ArrowRight', currentTarget: tabs[3], preventDefault: () => prevented++});
assert.equal(state.activeTab, 'description');
assert.equal(focused, 'description');
handleProblemTabKeydown({key: 'End', currentTarget: tabs[0], preventDefault: () => prevented++});
assert.equal(state.activeTab, 'demo');
assert.equal(prevented, 2);
activateProblemTab('invalid');
assert.equal(state.activeTab, 'demo');
"""
        subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
