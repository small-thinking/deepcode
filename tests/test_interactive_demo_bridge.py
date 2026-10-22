import json
import shutil
import subprocess
import unittest
from pathlib import Path


class InteractiveDemoBridgeTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node is required to exercise demo rendering")
    def test_coding_demo_tab_supports_static_diagrams_without_an_iframe(self):
        source = Path("frontend/app.js").read_text(encoding="utf-8")
        functions = source[source.index("function hasCodingInteractiveDemos("):source.index("function renderProblemBlock(")]
        problem = json.loads(Path("problems/110-two-layer-numpy-network/problem.json").read_text())
        self.assertEqual(len(problem["assets"]), 3)
        self.assertTrue(all(asset["section"] == "interactive_demo" for asset in problem["assets"]))
        script = """
const assert = require('node:assert/strict');
const isSystemDesignProblem = p => p.evaluation?.type === 'system_design';
const state = {activeTab: 'description'};
const renderProblemDescription = () => 'prompt';
const renderProblemTests = () => '';
const renderCustomTests = () => '';
const renderProblemEnvironment = () => '';
const renderDataLinkSetup = () => '';
const renderInteractiveDemos = (p, section) => (p.interactive_demos || [])
  .filter(d => d.section === section).map(() => '<iframe></iframe>').join('');
const renderProblemAssets = (p, section) => (p.assets || [])
  .filter(a => a.section === section).map(a => `<img alt="${a.alt}">`).join('');
""" + functions + "\nconst problem = " + json.dumps(problem) + ";\n" + """
assert.equal(hasCodingInteractiveDemos(problem), true);
const html = renderProblemTab(problem, {}, 'demo');
assert.equal((html.match(/<img /g) || []).length, 3);
assert.ok(!html.includes('<iframe'));
assert.equal(renderProblemTab(problem, {}, 'description'), 'prompt');
assert.ok(renderProblemPanels(problem, {}).includes('id="problem-demo-panel"'));
assert.equal(hasCodingInteractiveDemos({...problem, assets: []}), false);
assert.equal(hasCodingInteractiveDemos({...problem, evaluation: {type: 'system_design'}}), false);
const mixed = {...problem, interactive_demos: [{section: 'interactive_demo'}]};
const mixedHtml = renderProblemTab(mixed, {}, 'demo');
assert.ok(mixedHtml.startsWith('<iframe></iframe><img '));
assert.equal(hasCodingInteractiveDemos({...mixed, assets: []}), true);
"""
        subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)

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
