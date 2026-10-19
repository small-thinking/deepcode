import shutil
import subprocess
import unittest
from pathlib import Path


@unittest.skipUnless(shutil.which("node"), "Node is required for editor position checks")
class EditorRunPositionTest(unittest.TestCase):
    def test_runs_preserve_current_selection_scroll_and_keyboard_focus(self):
        source = Path("frontend/app.js").read_text(encoding="utf-8").split("\n", 1)[1]
        source = source[:source.rindex("\ntry {\n  migrateExistingCodeDrafts")]
        script = r'''
const assert = require('node:assert/strict');
const storage = new Map();
const localStorage = {getItem: key => storage.get(key) ?? null,
  setItem: (key, value) => storage.set(key, value)};
let fallback = null, kind = 'ace', storageFull = false;
const document = {activeElement: null,
  querySelector: selector => selector === '#code-editor-fallback' ? fallback : null,
  querySelectorAll: () => []};
const window = {addEventListener() {}};
const saveSubmittedCodeVersion = () => {if (storageFull) throw Error('Storage full');};
''' + source + r'''
const initialCode = '\tpass\n'.repeat(90);
const makeAce = code => {
  let selection = {start: {row: 0, column: 0}, end: {row: 0, column: 0}};
  let scrollTop = 0, scrollLeft = 0, focused = false;
  return {
    getValue: () => code,
    setValue(value) {code = value; selection = {}; scrollTop = scrollLeft = 0;},
    selection: {toJSON: () => structuredClone(selection),
      fromJSON: value => {selection = structuredClone(value);}},
    session: {getScrollTop: () => scrollTop, getScrollLeft: () => scrollLeft,
      setScrollTop: value => {scrollTop = value;}, setScrollLeft: value => {scrollLeft = value;}},
    isFocused: () => focused, focus: () => {focused = true;}, destroy() {},
  };
};
const makeFallback = code => ({value: code, selectionStart: 0, selectionEnd: 0,
  selectionDirection: 'none', scrollTop: 0, scrollLeft: 0,
  setSelectionRange(start, end, direction) {
    this.selectionStart = start; this.selectionEnd = end; this.selectionDirection = direction;
  },
  focus() {document.activeElement = this;},
});
renderDetail = () => {};
bindEvents = () => {};
activateProblemTab = () => {};
syncProblemTimer = () => {};
scrollPendingCustomTestIntoView = () => {};
startRunTimer = stopRunTimer = updateRunElapsed = () => {};
pauseProblemTimer = syncProblemStatus = () => {};
mountEditor = () => {
  codeEditor = kind === 'ace' ? makeAce(currentCode()) : null;
  fallback = kind === 'fallback' ? makeFallback(currentCode()) : null;
};
// Restoration must happen after the editor is mounted and resized.
applyPaneSizes = () => {
  if (codeEditor) codeEditor.session.setScrollTop(0);
  else if (fallback) fallback.scrollTop = 0;
};
const position = (focused, offset = 0) => kind === 'ace' ? {
  sessionKey: 'problem:workout',
  selection: [{start: {row: 53 + offset, column: 4},
    end: {row: 55 + offset, column: 12}, isBackwards: true}],
  scrollTop: 411 + offset, scrollLeft: 24, focused,
} : {
  sessionKey: 'problem:workout', selectionStart: 80 + offset, selectionEnd: 120 + offset,
  selectionDirection: 'backward', scrollTop: 411 + offset, scrollLeft: 24, focused,
};
state.view = 'problems';
state.selected = {slug: 'workout', starter_code: initialCode};
state.customTests = [{name: 'custom'}];
collectCustomTestInputs = () => {};
isMlCodingProblem = () => true;
let expected, finishPosition, mode;
runTestsWithStream = async payload => {
  assert.equal(payload.code, '    pass\n'.repeat(90));
  assert.deepEqual(captureEditorView(), expected); // start-of-run rerender
  restoreEditorView(finishPosition); // user moved while the run was in progress
  if (mode === 'error') throw Error('Runner unavailable');
  if (mode === 'fallback') return false;
  state.runResult = {status: mode};
  return true;
};
api = async () => ({status: 'failed'});
(async () => {
  for (kind of ['ace', 'fallback']) {
    for (const focused of [false, true]) {
      for (mode of ['passed', 'failed', 'error', 'fallback']) {
        storage.clear(); mountEditor();
        expected = position(focused);
        finishPosition = position(focused, 7);
        restoreEditorView(expected);
        await runTests();
        assert.deepEqual(captureEditorView(), finishPosition); // completion/error rerender
        assert.equal(state.running, false);
        if (mode === 'error') assert.equal(state.error, 'Runner unavailable');
      }
    }
    for (const customIndex of [0, null]) {
      storage.clear(); mountEditor();
      expected = finishPosition = position(true);
      restoreEditorView(expected);
      mode = 'failed';
      await runCustomTests(customIndex);
      assert.deepEqual(captureEditorView(), expected);
    }
    storage.clear(); mountEditor();
    expected = position(true); restoreEditorView(expected);
    storageFull = true;
    await runTests();
    assert.deepEqual(captureEditorView(), expected);
    assert.match(state.error, /Run cancelled/);
    storageFull = false;
    state.selected = {slug: 'other'}; mountEditor();
    const fresh = captureEditorView();
    restoreEditorView(expected);
    assert.deepEqual(captureEditorView(), fresh); // never restore into another problem
    state.selected = {slug: 'workout', starter_code: initialCode};
  }
})().catch(error => {console.error(error); process.exitCode = 1;});
'''
        result = subprocess.run(
            ["node", "--input-type=commonjs"], input=script, capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, result.stderr)
