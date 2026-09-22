import json
import shutil
import subprocess
import unittest
from pathlib import Path


@unittest.skipUnless(shutil.which("node"), "Node is required to exercise code versions")
class CodeVersionsTest(unittest.TestCase):
    def run_js(self, assertions, *, app_code=""):
        module_url = Path("frontend/code-versions.mjs").resolve().as_uri()
        script = f"""
import assert from 'node:assert/strict';
import {{ webcrypto }} from 'node:crypto';
import {{ codeVersionsKey, loadCodeVersions, saveCodeVersion, saveSubmittedCodeVersion, deleteCodeVersion, undoDeleteCodeVersion }} from {json.dumps(module_url)};
if (!globalThis.crypto) globalThis.crypto = webcrypto;
const entries = new Map();
const unsavedProblemDrafts = new Map();
let failKey = null;
const localStorage = {{
  getItem: key => entries.has(key) ? entries.get(key) : null,
  setItem(key, value) {{
    if (key === failKey) throw new Error('QuotaExceededError');
    entries.set(key, String(value));
  }},
}};
{app_code}
{assertions}
"""
        result = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def draft_functions(self):
        source = Path("frontend/app.js").read_text(encoding="utf-8")
        return source[source.index("function codeKey("):source.index("function validEditorHistory(")]

    def test_snapshots_keep_exact_text_and_previous_named_versions(self):
        self.run_js(r"""
const code = '\tprint("你好")  \r\n\n';
const first = saveCodeVersion(localStorage, 'alpha', code, '  Approach A  ')[0];
assert.equal(first.name, 'Approach A');
assert.equal(first.code, code);
assert.ok(Number.isFinite(Date.parse(first.createdAt)));
const second = saveCodeVersion(localStorage, 'alpha', '', 'Approach A')[0];
assert.notEqual(first.id, second.id);
assert.deepEqual(loadCodeVersions(localStorage, 'alpha'), [second, first]);
assert.equal(second.code, '');
const loaded = loadCodeVersions(localStorage, 'alpha');
loaded[1].code = 'changed outside storage';
assert.equal(loadCodeVersions(localStorage, 'alpha')[1].code, code);
assert.equal(saveCodeVersion(localStorage, 'alpha', 'third', '   ')[0].name, 'Version 3');
assert.deepEqual(loadCodeVersions(localStorage, 'alpha').slice(1), [second, first]);
""")

    def test_histories_are_isolated_and_append_to_latest_storage(self):
        self.run_js(r"""
localStorage.setItem('deepcode-code:alpha', 'working draft');
const first = saveCodeVersion(localStorage, 'alpha', 'A1', 'First')[0];
const beta = saveCodeVersion(localStorage, 'beta', 'B1', 'First')[0];
// An independent call represents another tab appending after the first read.
const otherTab = saveCodeVersion(localStorage, 'alpha', 'A2', 'Other tab')[0];
const latest = saveCodeVersion(localStorage, 'alpha', 'A3', 'Latest')[0];
assert.deepEqual(loadCodeVersions(localStorage, 'alpha'), [latest, otherTab, first]);
assert.deepEqual(loadCodeVersions(localStorage, 'beta'), [beta]);
assert.deepEqual(loadCodeVersions(localStorage, 'new-problem'), []);
assert.equal(localStorage.getItem('deepcode-code:alpha'), 'working draft');
""")

    def test_automatic_backups_reuse_exact_existing_code_only(self):
        self.run_js(r"""
const first = saveCodeVersion(localStorage, 'alpha', 'x\n', 'Manual')[0];
saveCodeVersion(localStorage, 'alpha', 'y\n', 'Other');
const before = localStorage.getItem(codeVersionsKey('alpha'));
failKey = codeVersionsKey('alpha');
saveCodeVersion(localStorage, 'alpha', 'x\n', 'Before reset', {onlyIfChanged: true});
assert.equal(localStorage.getItem(codeVersionsKey('alpha')), before);
failKey = null;
saveCodeVersion(localStorage, 'alpha', 'x', 'Before reset', {onlyIfChanged: true});
assert.equal(loadCodeVersions(localStorage, 'alpha').length, 3);
assert.deepEqual(loadCodeVersions(localStorage, 'alpha')[2], first);
""")

    def test_submissions_deduplicate_only_the_latest_exact_code(self):
        self.run_js(r"""
const original = '\tprint("你好")  \r\n\n';
const first = saveSubmittedCodeVersion(localStorage, 'alpha', original)[0];
assert.equal(first.code, original);
const before = localStorage.getItem(codeVersionsKey('alpha'));
// An unchanged submission needs no write, even if storage is now full.
failKey = codeVersionsKey('alpha');
assert.deepEqual(saveSubmittedCodeVersion(localStorage, 'alpha', original), [first]);
assert.equal(localStorage.getItem(codeVersionsKey('alpha')), before);
failKey = null;
const changed = saveSubmittedCodeVersion(localStorage, 'alpha', original.trim())[0];
const returned = saveSubmittedCodeVersion(localStorage, 'alpha', original)[0];
assert.notEqual(returned.id, first.id);
assert.deepEqual(loadCodeVersions(localStorage, 'alpha'), [returned, changed, first]);
const empty = saveSubmittedCodeVersion(localStorage, 'alpha', '')[0];
saveSubmittedCodeVersion(localStorage, 'alpha', '');
assert.deepEqual(loadCodeVersions(localStorage, 'alpha'), [empty, returned, changed, first]);
assert.deepEqual(loadCodeVersions(localStorage, 'beta'), []);
""")

    def test_delete_uses_selected_id_and_problem_even_with_duplicate_names(self):
        self.run_js(r"""
const first = saveCodeVersion(localStorage, 'alpha', 'first', 'Same name')[0];
const selected = saveCodeVersion(localStorage, 'alpha', 'selected', 'Same name')[0];
const latest = saveCodeVersion(localStorage, 'alpha', 'latest', 'Same name')[0];
const beta = saveCodeVersion(localStorage, 'beta', 'other problem', 'Same name')[0];
localStorage.setItem('deepcode-code:alpha', 'working draft');
assert.deepEqual(deleteCodeVersion(localStorage, 'alpha', selected.id), [latest, first]);
assert.deepEqual(loadCodeVersions(localStorage, 'alpha'), [latest, first]);
assert.deepEqual(loadCodeVersions(localStorage, 'beta'), [beta]);
assert.equal(localStorage.getItem('deepcode-code:alpha'), 'working draft');
failKey = codeVersionsKey('alpha');
assert.deepEqual(deleteCodeVersion(localStorage, 'alpha', beta.id), [latest, first]);
const before = new Map(entries);
assert.throws(() => deleteCodeVersion(localStorage, 'alpha', first.id), /Quota/);
assert.deepEqual(entries, before);
""")

    def test_undo_delete_restores_original_record_and_preserves_new_versions(self):
        self.run_js(r"""
const oldest = {id: 'old', name: 'Same name', code: 'old code', createdAt: '2026-09-20T00:00:00.000Z'};
const selected = {id: 'selected', name: 'Same name', code: '\tselected\r\n', createdAt: '2026-09-21T00:00:00.000Z'};
const newest = {id: 'new', name: 'Same name', code: 'new code', createdAt: '2026-09-22T00:00:00.000Z'};
localStorage.setItem(codeVersionsKey('alpha'), JSON.stringify({schemaVersion: 1, versions: [selected, oldest]}));
const beta = saveCodeVersion(localStorage, 'beta', 'other code', 'Same name')[0];
deleteCodeVersion(localStorage, 'alpha', selected.id);
// A subsequent save (possibly from another tab) must survive Undo.
localStorage.setItem(codeVersionsKey('alpha'), JSON.stringify({schemaVersion: 1, versions: [newest, oldest]}));
const before = new Map(entries);
failKey = codeVersionsKey('alpha');
assert.throws(() => undoDeleteCodeVersion(localStorage, 'alpha', selected), /Quota/);
assert.deepEqual(entries, before);
failKey = null;
assert.deepEqual(undoDeleteCodeVersion(localStorage, 'alpha', selected), [newest, selected, oldest]);
assert.deepEqual(loadCodeVersions(localStorage, 'alpha'), [newest, selected, oldest]);
assert.deepEqual(loadCodeVersions(localStorage, 'beta'), [beta]);
failKey = codeVersionsKey('alpha');
assert.deepEqual(undoDeleteCodeVersion(localStorage, 'alpha', selected), [newest, selected, oldest]);
""")

    def test_typing_updates_only_the_working_draft(self):
        source = Path("frontend/app.js").read_text(encoding="utf-8")
        save_function = source[source.index("function saveCode("):source.index("function updateCodeSaveStatus(")]
        self.run_js(r"""
const state = {view: 'problems', selected: {slug: 'alpha'}};
const codeKey = slug => `deepcode-code:${slug}`;
const updateCodeSaveStatus = () => {};
const saved = saveSubmittedCodeVersion(localStorage, 'alpha', 'submitted');
for (const draft of ['s', 'some', 'some edits', '']) saveCode(draft);
assert.equal(localStorage.getItem(codeKey('alpha')), '');
assert.deepEqual(loadCodeVersions(localStorage, 'alpha'), saved);
state.selected = {slug: 'beta'};
saveCode('new unsent draft');
assert.deepEqual(loadCodeVersions(localStorage, 'beta'), []);
""", app_code=save_function)

    def run_functions(self):
        source = Path("frontend/app.js").read_text(encoding="utf-8")
        return source[source.index("async function runTests("):source.index("async function runTestsWithStream(")]

    def test_runs_save_exact_payload_before_stream_or_fallback_even_on_failure(self):
        self.run_js(r"""
const state = {selected: {slug: 'alpha'}, running: false};
let payload, mode, streamCalls = 0, apiCalls = 0, timerStarts = 0, timerStops = 0;
const render = () => {};
const updateRunElapsed = () => {};
const startRunTimer = () => {timerStarts++;};
const stopRunTimer = () => {timerStops++;};
const syncProblemStatus = () => {};
const assertSaved = received => {
  assert.deepEqual(received, payload);
  assert.equal(loadCodeVersions(localStorage, 'alpha')[0].code, payload.code);
  assert.equal(state.running, true);
};
const runTestsWithStream = async received => {
  streamCalls++;
  assertSaved(received);
  if (mode === 'stream-error') throw new Error('Stream unavailable');
  if (mode === 'fallback') return false;
  state.runResult = {passed: false, error: 'Assertion failed'};
  return true;
};
const api = async (url, options) => {
  apiCalls++;
  assert.equal(url, '/api/problems/alpha/run');
  assert.equal(options.method, 'POST');
  assertSaved(JSON.parse(options.body));
  throw new Error('Runner unavailable');
};
for (mode of ['streamed-failure', 'stream-error', 'fallback']) {
  payload = {code: `\t${mode}  \r\n\n`, test_index: 0};
  await runPayload(payload, {testIndex: 0});
  assert.equal(loadCodeVersions(localStorage, 'alpha')[0].code, payload.code);
  assert.equal(state.running, false);
  assert.equal(state.runningTestIndex, null);
  if (mode === 'streamed-failure') assert.equal(state.runResult.passed, false);
  else assert.match(state.error, /unavailable/);
}
assert.equal(loadCodeVersions(localStorage, 'alpha').length, 3);
assert.equal(streamCalls, 3);
assert.equal(apiCalls, 1);
assert.equal(timerStarts, 3);
assert.equal(timerStops, 3);
""", app_code=self.run_functions())

    def test_run_aborts_before_execution_when_version_storage_is_full(self):
        self.run_js(r"""
const state = {selected: {slug: 'alpha'}, running: false, runResult: {previous: true}, runLogs: ['previous log']};
let rendered = 0;
const render = () => {rendered++;};
const startRunTimer = () => assert.fail('must not start timer');
const runTestsWithStream = async () => assert.fail('must not start stream');
const api = async () => assert.fail('must not call runner');
saveSubmittedCodeVersion(localStorage, 'alpha', 'previous code');
localStorage.setItem('deepcode-code:alpha', 'current draft');
const before = new Map(entries);
failKey = codeVersionsKey('alpha');
await runPayload({code: 'new submission'});
assert.deepEqual(entries, before);
assert.equal(state.running, false);
assert.deepEqual(state.runResult, {previous: true});
assert.deepEqual(state.runLogs, ['previous log']);
assert.match(state.error, /could not save a code version/i);
assert.equal(rendered, 1);
""", app_code=self.run_functions())

    def test_custom_runs_save_the_normalized_code_actually_submitted(self):
        self.run_js(r"""
const state = {selected: {slug: 'alpha'}, running: false, customTests: [{input: 'first'}, {input: 'second'}]};
let editor = '\tprint("custom")\r\n', collected = 0, calls = 0;
const normalized = '    print("custom")\n';
const isMlCodingProblem = () => true;
const collectCustomTestInputs = () => {collected++;};
const editorCode = () => editor;
const normalizePythonIndentation = () => normalized;
const setEditorCode = value => {editor = value;};
const saveCode = value => localStorage.setItem('deepcode-code:alpha', value);
const render = () => {};
const startRunTimer = () => {};
const stopRunTimer = () => {};
const updateRunElapsed = () => {};
const runTestsWithStream = async payload => {
  assert.equal(payload.code, normalized);
  assert.equal(payload.custom_only, true);
  assert.deepEqual(payload.custom_tests, calls ? state.customTests : [state.customTests[1]]);
  assert.equal(state.runningCustomTestIndex, calls ? 'all' : 1);
  assert.equal(loadCodeVersions(localStorage, 'alpha')[0].code, payload.code);
  calls++;
  state.runResult = {passed: false};
  return true;
};
await runCustomTests(1);
await runCustomTests();
assert.equal(calls, 2);
assert.equal(collected, 2);
assert.equal(editor, normalized);
assert.equal(localStorage.getItem('deepcode-code:alpha'), normalized);
assert.equal(loadCodeVersions(localStorage, 'alpha').length, 1);
""", app_code=self.run_functions())

    def test_corrupt_or_future_histories_are_never_overwritten(self):
        self.run_js(r"""
for (const raw of [
  '{broken json', 'null', '[]',
  JSON.stringify({schemaVersion: 2, versions: []}),
  JSON.stringify({schemaVersion: 1, versions: {}}),
  JSON.stringify({schemaVersion: 1, versions: [null]}),
  JSON.stringify({schemaVersion: 1, versions: [{id: 'x', name: 'Old', code: 12, createdAt: 'now'}]}),
]) {
  localStorage.setItem(codeVersionsKey('alpha'), raw);
  localStorage.setItem('deepcode-code:alpha', 'valuable working code');
  assert.throws(() => loadCodeVersions(localStorage, 'alpha'));
  assert.throws(() => saveCodeVersion(localStorage, 'alpha', 'new', 'New'));
  assert.equal(localStorage.getItem(codeVersionsKey('alpha')), raw);
  assert.equal(localStorage.getItem('deepcode-code:alpha'), 'valuable working code');
}
""")

    def test_storage_failure_preserves_existing_versions_and_draft(self):
        self.run_js(r"""
saveCodeVersion(localStorage, 'alpha', 'saved code', 'Saved');
localStorage.setItem('deepcode-code:alpha', 'current code');
const before = new Map(entries);
failKey = codeVersionsKey('alpha');
assert.throws(() => saveCodeVersion(localStorage, 'alpha', 'current code', 'New'), /Quota/);
assert.deepEqual(entries, before);
const unavailable = {getItem() {throw new Error('Storage unavailable');}, setItem() {assert.fail('must not write');}};
assert.throws(() => saveCodeVersion(unavailable, 'alpha', 'current', 'New'), /unavailable/);
""")

    def test_existing_drafts_and_playground_keep_their_storage_contract(self):
        self.run_js(r"""
const state = {view: 'problems', selected: {slug: 'alpha', starter_code: 'starter'}};
const PLAYGROUND_CODE_KEY = 'deepcode-playground-code';
const PLAYGROUND_STARTER_CODE = 'playground starter';
assert.equal(currentCode(), 'starter');
localStorage.setItem(codeKey('alpha'), '\tlegacy draft\r\n');
assert.equal(currentCode(), '\tlegacy draft\r\n');
syncStarterCode(state.selected);
assert.equal(currentCode(), '\tlegacy draft\r\n');
localStorage.setItem(codeKey('alpha'), '');
syncStarterCode(state.selected);
assert.equal(currentCode(), '');
state.view = 'playground';
assert.equal(currentCode(), PLAYGROUND_STARTER_CODE);
localStorage.setItem(PLAYGROUND_CODE_KEY, '');
assert.equal(currentCode(), '');
state.view = 'problems'; state.selected = null;
assert.equal(currentCode(), '');
""", app_code=self.draft_functions())

    def test_failed_autosave_survives_rerender_and_navigation_until_retry(self):
        source = Path("frontend/app.js").read_text(encoding="utf-8")
        save_function = source[source.index("function saveCode("):source.index("function updateCodeSaveStatus(")]
        toggle_function = source[source.index("function toggleResultsPanel("):source.index("function paramsFromFilters(")]
        self.run_js(r"""
const state = {view: 'problems', selected: {slug: 'alpha', starter_code: 'starter'}, layout: {resultsCollapsed: false}};
const PLAYGROUND_CODE_KEY = 'deepcode-playground-code';
const PLAYGROUND_STARTER_CODE = 'playground starter';
let notice, mountedCode, renderCalls = 0;
const updateCodeSaveStatus = (...args) => {notice = args;};
// Both Ace mounting and fallback rendering read currentCode().
const render = () => {mountedCode = currentCode(); renderCalls++;};
localStorage.setItem(codeKey('alpha'), 'last persisted draft');
failKey = codeKey('alpha');
const edited = '\tprint("你好")  \r\n\n';
saveCode(edited);
assert.equal(localStorage.getItem(codeKey('alpha')), 'last persisted draft');
assert.equal(notice[1], true);
toggleResultsPanel();
assert.equal(renderCalls, 1);
assert.equal(mountedCode, edited);
assert.equal(unsavedProblemDrafts.get('alpha'), edited);
state.selected = {slug: 'beta', starter_code: 'beta starter'};
assert.equal(currentCode(), 'beta starter');
saveCode('beta code');
assert.equal(currentCode(), 'beta code');
assert.equal(unsavedProblemDrafts.get('alpha'), edited);
state.selected = {slug: 'alpha', starter_code: 'starter'};
toggleResultsPanel();
assert.equal(mountedCode, edited);
// A deliberately empty unsaved draft must not fall back to stored code.
saveCode('');
toggleResultsPanel();
assert.equal(mountedCode, '');
assert.equal(unsavedProblemDrafts.has('alpha'), true);
assert.equal(localStorage.getItem(codeKey('alpha')), 'last persisted draft');
failKey = null;
saveCode(currentCode());
assert.equal(localStorage.getItem(codeKey('alpha')), '');
assert.equal(unsavedProblemDrafts.size, 0);
assert.equal(notice[0], 'Draft autosaved');
assert.notEqual(notice[1], true);
toggleResultsPanel();
assert.equal(mountedCode, '');
assert.equal(localStorage.getItem(codeKey('beta')), 'beta code');
""", app_code=self.draft_functions() + save_function + toggle_function)

    def test_starter_refresh_backs_up_displaced_code_and_keeps_restored_code(self):
        self.run_js(r"""
const problem = {slug: 'alpha', starter_code: 'new starter\n'};
localStorage.setItem(codeKey('alpha'), 'old starter\n');
localStorage.setItem(starterKey('alpha'), 'old starter\n');
syncStarterCode(problem);
assert.equal(localStorage.getItem(codeKey('alpha')), problem.starter_code);
assert.equal(loadCodeVersions(localStorage, 'alpha')[0].code, 'old starter\n');
const before = localStorage.getItem(codeVersionsKey('alpha'));
// Restoring old starter or empty code must survive the normal reopen path.
for (const restored of ['old starter\n', '']) {
  localStorage.setItem(codeKey('alpha'), restored);
  localStorage.setItem(starterKey('alpha'), restored);
  syncStarterCode(problem);
  syncStarterCode(problem);
  assert.equal(localStorage.getItem(codeKey('alpha')), restored);
  assert.equal(localStorage.getItem(codeVersionsKey('alpha')), before);
}
const legacy = 'class NGramCharModel:\n    def train(self, text):\n        pass\n    def generate(self, prompt="", max_new_chars=100):\n        pass\n    def evaluate(self, text):\n        pass';
localStorage.setItem(codeKey('alpha'), legacy);
syncStarterCode(problem);
assert.equal(localStorage.getItem(codeKey('alpha')), legacy);
// Deleting every snapshot must not make restored legacy code look untouched.
for (const version of loadCodeVersions(localStorage, 'alpha')) {
  deleteCodeVersion(localStorage, 'alpha', version.id);
}
assert.deepEqual(loadCodeVersions(localStorage, 'alpha'), []);
syncStarterCode(problem);
syncStarterCode(problem);
assert.equal(localStorage.getItem(codeKey('alpha')), legacy);
syncStarterCode({slug: 'fresh', starter_code: 'fresh starter'});
assert.equal(localStorage.getItem(codeKey('fresh')), 'fresh starter');
assert.deepEqual(loadCodeVersions(localStorage, 'fresh'), []);
""", app_code=self.draft_functions())

    def test_starter_refresh_aborts_if_backup_cannot_be_saved(self):
        self.run_js(r"""
const problem = {slug: 'alpha', starter_code: 'new starter'};
localStorage.setItem(codeKey('alpha'), 'old starter');
localStorage.setItem(starterKey('alpha'), 'old starter');
const before = new Map(entries);
failKey = codeVersionsKey('alpha');
assert.throws(() => syncStarterCode(problem), /Quota/);
assert.deepEqual(entries, before);
""", app_code=self.draft_functions())

    def test_reset_aborts_before_editor_or_server_changes_on_storage_failure(self):
        source = Path("frontend/app.js").read_text(encoding="utf-8")
        reset_function = source[source.index("async function resetCode()"):source.index("function problemCompleted(")]
        self.run_js(r"""
const state = {selected: {slug: 'alpha', starter_code: 'starter'}, runResult: {old: true}};
const editorCode = () => 'unsaved editor text';
const codeKey = slug => `deepcode-code:${slug}`;
let resetCalls = 0, apiCalls = 0, renderCalls = 0, notice;
const resetEditorHistory = () => {resetCalls++;};
const api = async () => {apiCalls++; return {};};
const render = () => {renderCalls++;};
const updateCodeSaveStatus = (...args) => {notice = args;};
localStorage.setItem(codeKey('alpha'), 'last persisted draft');
// Backup failure must not overwrite any previously saved draft.
failKey = codeVersionsKey('alpha');
await resetCode();
assert.equal(localStorage.getItem(codeKey('alpha')), 'last persisted draft');
assert.equal(localStorage.getItem(codeVersionsKey('alpha')), null);
assert.equal(resetCalls + apiCalls + renderCalls, 0);
assert.equal(notice[1], true);
assert.deepEqual(state.runResult, {old: true});
// If only replacement fails, the editor text is still backed up safely.
failKey = codeKey('alpha');
await resetCode();
assert.equal(localStorage.getItem(codeKey('alpha')), 'last persisted draft');
assert.equal(loadCodeVersions(localStorage, 'alpha')[0].code, 'unsaved editor text');
assert.equal(resetCalls + apiCalls + renderCalls, 0);
assert.deepEqual(state.runResult, {old: true});
""", app_code=reset_function)
