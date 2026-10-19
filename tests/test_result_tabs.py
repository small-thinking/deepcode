import shutil
import subprocess
import unittest
from pathlib import Path


@unittest.skipUnless(shutil.which("node"), "Node is required for result tab checks")
class ResultTabsTest(unittest.TestCase):
    def test_switching_cases_keeps_tabs_editor_and_scroll_positions(self):
        source = Path("frontend/app.js").read_text(encoding="utf-8")
        source = source.split("\n", 1)[1]  # browser module import
        source = source[:source.rindex("\ntry {\n  migrateExistingCodeDrafts")]
        script = r'''
const assert = require('node:assert/strict');
const tabStrip = {scrollLeft: 1240};
const editor = {selection: 'draft selection', scrollTop: 420};
let panelHtml = '';
const panel = {set outerHTML(value) {panelHtml = value;}};
const tabs = Array.from({length: 21}, (_, index) => ({
  dataset: {resultIndex: String(index)},
  active: index === 0,
  selected: String(index === 0),
  classList: {toggle(_, active) {tabs[index].active = active;}},
  setAttribute(name, value) {
    assert.equal(name, 'aria-selected');
    this.selected = value;
  },
  addEventListener(name, callback) {this[name] = callback;},
}));
const document = {
  querySelector(selector) {
    if (selector === '#run-results .result-case') return panel;
    if (selector === '.result-tabs') return tabStrip;
    if (selector === '#code-editor') return editor;
    return null;
  },
  querySelectorAll(selector) {return selector === '.result-tab' ? tabs : [];},
};
const localStorage = {getItem() {return null;}};
const window = {addEventListener() {}};
''' + source + r'''
render = () => {throw new Error('Tab selection must not rebuild the workspace');};
saveCode = () => {throw new Error('Tab selection must not touch the draft');};
state.runResult = {status: 'failed', passed: 1, total: 21,
  results: tabs.map((_, index) => ({
    name: `Stage ${index + 1}`, passed: index === 20, input: `Input ${index}`,
    expected_output: 'ok', actual_output: index === 20 ? 'ok' : 'Traceback\n'.repeat(index + 1),
  })),
};
state.activeResultIndex = 0;
bindEvents();
for (const index of [7, 20, 6, 0]) {
  tabs[index].click();
  assert.equal(state.activeResultIndex, index);
  assert.equal(tabStrip.scrollLeft, 1240);
  assert.equal(document.querySelector('#code-editor'), editor);
  assert.deepEqual(editor, {selection: 'draft selection', scrollTop: 420});
  assert.ok(panelHtml.includes(`id="result-case-${index}"`));
  assert.ok(panelHtml.includes(`aria-labelledby="result-tab-${index}"`));
  assert.ok(panelHtml.includes(`Input ${index}`));
  assert.ok(panelHtml.includes(`class="result-case ${index === 20 ? 'pass' : 'fail'}"`));
  assert.deepEqual(tabs.filter(tab => tab.active), [tabs[index]]);
  assert.deepEqual(tabs.filter(tab => tab.selected === 'true'), [tabs[index]]);
}
const previousPanel = panelHtml;
activateResultTab(99);
assert.equal(state.activeResultIndex, 0);
assert.equal(panelHtml, previousPanel);
'''
        result = subprocess.run(
            ["node", "--input-type=commonjs"], input=script, capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, result.stderr)
