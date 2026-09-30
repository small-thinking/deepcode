import shutil
import subprocess
import unittest
from pathlib import Path


class ProblemTimerTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node is required to exercise the timer")
    def test_completed_runs_pause_only_after_full_suite_success(self):
        source = Path("frontend/app.js").read_text(encoding="utf-8")
        timers = source[source.index("function loadProblemTimers() {"):source.index("function mainNavigation() {")]
        run = source[source.index("async function runPayload("):source.index("async function runTestsWithStream(")]
        script = r'''
const assert = require('node:assert/strict');
const PROBLEM_TIMERS_KEY = 'deepcode-problem-timers';
const storage = new Map();
const localStorage = {
  getItem: key => storage.get(key) ?? null,
  setItem: (key, value) => storage.set(key, value),
};
let now = 10000;
Date.now = () => now;
let problemTimer = null;
let intervalCleared = false;
const setInterval = () => 1;
const clearInterval = () => { intervalCleared = true; };
const button = {textContent: '', setAttribute: (key, value) => { button[key] = value; }};
const display = {textContent: ''};
const document = {querySelector: selector => selector === '#problem-timer-toggle' ? button : display};
const state = {selected: {slug: 'example'}, running: false};
const saveSubmittedCodeVersion = () => {};
const startRunTimer = () => {};
const stopRunTimer = () => {};
const updateRunElapsed = () => {};
const syncProblemStatus = () => {};
const render = () => {
  syncProblemTimer();
  updateProblemTimerDisplay();
  const timer = problemTimerFor(state.selected.slug);
  button.textContent = problemTimerIsRunning(timer) ? 'Pause' : timer.elapsedMs ? 'Resume' : 'Start';
};
let result;
let useStream;
let error;
const runTestsWithStream = async () => {
  if (error) throw new Error(error);
  if (useStream) state.runResult = result;
  return useStream;
};
const api = async () => result;
''' + timers + run + r'''
(async () => {
  for (useStream of [true, false]) {
    for (const scenario of [
      {payload: {}, status: 'passed', paused: true},
      {payload: {}, status: 'failed', paused: false},
      {payload: {}, status: 'error', paused: false},
      {payload: {test_index: 0}, status: 'passed', paused: false},
      {payload: {custom_only: true, custom_tests: [{}]}, status: 'passed', paused: false},
      {payload: {custom_tests: [{}]}, status: 'passed', paused: false},
      {payload: {}, status: 'passed', error: 'Network failure', paused: false},
    ]) {
      now = 10000;
      saveProblemTimer('example', {elapsedMs: 2000, startedAt: 5000});
      saveProblemTimer('other', {elapsedMs: 3000, startedAt: 6000});
      result = {status: scenario.status};
      error = scenario.error;
      intervalCleared = false;
      await runPayload({code: 'solution', ...scenario.payload});
      assert.equal(problemTimerIsRunning(problemTimerFor('example')), !scenario.paused);
      assert.deepEqual(problemTimerFor('other'), {elapsedMs: 3000, startedAt: 6000});
      if (scenario.paused) {
        assert.deepEqual(problemTimerFor('example'), {elapsedMs: 7000, startedAt: null});
        assert.equal(button.textContent, 'Resume');
        assert.equal(display.textContent, '00:00:07');
        assert.equal(intervalCleared, true);
        now += 5000;
        assert.equal(problemTimerElapsedMs(problemTimerFor('example')), 7000);
        toggleProblemTimer();
        assert.equal(button.textContent, 'Pause');
        now += 1000;
        assert.equal(problemTimerElapsedMs(problemTimerFor('example')), 8000);
      }
    }
    error = null;
    result = {status: 'passed'};
    for (const elapsedMs of [0, 2500]) {
      saveProblemTimer('example', {elapsedMs, startedAt: null});
      await runPayload({code: 'solution'});
      assert.deepEqual(problemTimerFor('example'), {elapsedMs, startedAt: null});
    }
  }
})().catch(error => { console.error(error); process.exit(1); });
'''
        subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True)
