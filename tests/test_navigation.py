import shutil
import subprocess
import unittest
from pathlib import Path


@unittest.skipUnless(shutil.which("node"), "Node is required for navigation checks")
class NavigationTest(unittest.TestCase):
    def test_filter_history_reload_and_native_links(self):
        source = Path("frontend/app.js").read_text()
        source = source.split("\n", 1)[1]  # browser module import
        source = source[:source.rindex("\ntry {\n  migrateExistingCodeDrafts")]
        script = r'''
const assert = require('node:assert/strict');
const callbacks = {};
const rows = [];
const location = {hash: ''};
const historyEntries = [];
const history = {
  pushState(_, __, route) { historyEntries.push(route); location.hash = route; },
  replaceState(_, __, route) { location.hash = route; },
};
const localStorage = {getItem() {return null;}};
const document = {
  querySelector() {return null;},
  querySelectorAll(selector) {return selector === 'tbody tr[data-slug]' ? rows : [];},
};
const window = {addEventListener(name, fn) {callbacks[name] = fn;}};
''' + source + r'''
render = () => {};
syncStarterCode = () => {};
syncSystemDesignAnswer = () => {};
loadCustomTests = async () => {};
loadDataLink = async () => {};
const requests = [];
api = async (url) => {
  requests.push(url);
  return url.startsWith('/api/problems/')
    ? {problem: {slug: 'example', evaluation: {type: 'system_design'}}}
    : {problems: [{slug: 'example', title: 'Example', companies: []}], categories: [], difficulties: []};
};
const settle = () => new Promise(resolve => setImmediate(resolve));
(async () => {
  bootFromHash(); await settle();
  assert.equal(location.hash, '#/');
  state.filters = {...DEFAULT_PROBLEM_FILTERS, company: 'Airbnb', category: 'ML Coding',
    search: 'A & B? 中文', difficulty: 'hard', sort: 'title', order: 'asc'};
  const expectedFilters = {...state.filters};
  await loadProblems();
  const listRoute = location.hash;
  assert.match(listRoute, /company=Airbnb/);
  assert.equal(historyEntries.length, 2);
  assert.deepEqual(filtersFromHash(), expectedFilters);
  assert.match(requests.at(-1), /company=Airbnb/);
  const detailRoute = problemRoute('example');
  const html = problemTable();
  assert.match(html, /<a class="problem-title-link" href="/);
  assert.ok(html.includes(escapeHtml(detailRoute)));
  location.hash = detailRoute; callbacks.hashchange(); await settle();
  assert.equal(state.selected.slug, 'example');
  assert.equal(location.hash, detailRoute);
  location.hash = listRoute; callbacks.hashchange(); await settle();
  assert.equal(state.selected, null);
  assert.deepEqual(state.filters, expectedFilters);
  state.filters = {...DEFAULT_PROBLEM_FILTERS};
  bootFromHash(); await settle();
  assert.deepEqual(state.filters, expectedFilters); // fresh load from URL
  location.hash = detailRoute; bootFromHash(); await settle();
  backToList(); callbacks.hashchange(); await settle();
  assert.equal(location.hash, listRoute); // new tab's in-app back
  location.hash = '#/'; callbacks.hashchange(); await settle();
  assert.deepEqual(state.filters, {...DEFAULT_PROBLEM_FILTERS});
  location.hash = '#/?sort=garbage&order=wrong';
  assert.equal(filtersFromHash().sort, 'frequency');
  assert.equal(filtersFromHash().order, 'desc');
  const click = {button: 0, target: {closest() {return null;}}};
  for (const modifier of ['metaKey', 'ctrlKey', 'shiftKey', 'altKey']) {
    assert.equal(isPlainClick({...click, [modifier]: true}), false);
  }
  assert.equal(isPlainClick({...click, button: 1}), false);
  assert.equal(isPlainClick(click), true);
  let rowClick;
  rows.push({dataset: {slug: 'example'}, addEventListener(_, fn) {rowClick = fn;}});
  bindEvents();
  location.hash = '#/';
  rowClick({...click, target: {closest() {return {};}}}); // native link must win
  assert.equal(location.hash, '#/');
  rowClick({...click, metaKey: true});
  assert.equal(location.hash, '#/');
  rowClick(click);
  assert.equal(location.hash, '#/problems/example');
  // A stale filtered response cannot overwrite a newly opened detail page.
  let resolveRequest;
  api = () => new Promise(resolve => {resolveRequest = resolve;});
  const loading = loadProblems();
  location.hash = '#/problems/example';
  state.selected = {slug: 'example'};
  resolveRequest({problems: [{slug: 'stale'}]});
  await loading;
  assert.equal(state.selected.slug, 'example');
  assert.notEqual(state.problems[0].slug, 'stale');
})().catch(error => {console.error(error); process.exitCode = 1;});
'''
        result = subprocess.run(["node", "--input-type=commonjs"], input=script, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
