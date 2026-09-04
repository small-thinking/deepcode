"""Execute teaching scripts and compare their toy math with a vectorized oracle."""
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

import numpy as np


DOM_STUB = r"""
const assert = require('node:assert/strict');
const nodes = new Map();
class Element {
  constructor(id) {
    this.value = ({head:'0', token:'0', kvheads:'2', cachemode:'prefill', input:'1'})[id] || '';
    this.checked = true;
    this.children = [];
    this.html = '';
  }
  set innerHTML(html) {
    if (this.children.includes(document.activeElement)) document.activeElement = null;
    this.html = html;
    this.children = [...html.matchAll(/data-step="(\d+)"/g)].map(match => {
      const button = new Element('button');
      button.dataset = {step: match[1]};
      return button;
    });
  }
  get innerHTML() { return this.html; }
  querySelectorAll() { return this.children; }
  setAttribute(name, value) { this[name] = value; }
  addEventListener() {}
  focus() { document.activeElement = this; }
}
const document = {
  activeElement: null,
  getElementById(id) {
    if (!nodes.has(id)) nodes.set(id, new Element(id));
    return nodes.get(id);
  },
  querySelector: () => ({getBoundingClientRect: () => ({height: 700})}),
  documentElement: {style: {setProperty() {}}},
};
const parent = {postMessage() {}};
const window = {addEventListener() {}};
const ResizeObserver = class {observe() {}};
"""

FOCUS_CHECK = """
const originalSteps = [...el('steps').children];
for (const button of originalSteps) {
  button.focus();
  button.onclick();
  assert.equal(document.activeElement, button);
  assert.equal(button['aria-pressed'], 'true');
  assert.deepEqual(el('steps').children, originalSteps);
}
"""


@unittest.skipUnless(shutil.which("node"), "Node is required to exercise operation demos")
class PlaygroundOperationDemosTest(unittest.TestCase):
    def run_demo(self, number, exercise):
        paths = list(Path("problems").glob(f"{number}-*/assets/operation-theater.html"))
        self.assertEqual(len(paths), 1)
        script = re.search(r"<script>(.*?)</script>", paths[0].read_text(), re.S).group(1)
        subprocess.run(["node", "--check", "-"], input=script, text=True, check=True, capture_output=True)
        result = subprocess.run(
            ["node", "-e", DOM_STUB + script + FOCUS_CHECK + exercise],
            text=True, check=True, capture_output=True,
        )
        return [json.loads(line) for line in result.stdout.splitlines()]

    def test_attention_probabilities_outputs_and_step_focus(self):
        exercise = """
for (const mode of (isCache ? ['prefill','decode','chunk'] : ['full']))
for (const kv of (isGroup ? [1,2,4] : [4]))
for (const causal of [false,true])
for (let head=0; head<4; head++) {
  el('cachemode').value=mode; el('kvheads').value=String(kv);
  el('causal').checked=causal; el('head').value=String(head);
  const count = ({prefill:3, decode:1, chunk:2, full:4})[mode];
  for (let token=0; token<count; token++) {
    el('token').value=String(token);
    render();
    console.log(JSON.stringify(calculate()));
  }
}
"""
        for number, expected_states in ((388, 32), (389, 48), (390, 96)):
            with self.subTest(problem=number):
                rows = self.run_demo(number, exercise)
                self.assertEqual(len(rows), expected_states)
                for data in rows:
                    # Independent all-head matrix calculation: never use the demo's
                    # selected q/k/v or mapped head to compute the expected result.
                    x = np.array(data["x"])
                    position = data["past"] + data["token"]
                    kv_heads = data["kvHeads"]
                    query = x[position].reshape(4, 2)
                    keys = (x[:, :kv_heads * 2] * .5).reshape(-1, kv_heads, 2)
                    values = x[:, :kv_heads * 2].reshape(-1, kv_heads, 2)
                    keys = np.repeat(keys, 4 // kv_heads, axis=1)
                    values = np.repeat(values, 4 // kv_heads, axis=1)
                    scores = np.einsum("hd,thd->ht", query, keys) / np.sqrt(2)
                    if data["mask"]:
                        scores[:, position + 1:] = -np.inf
                    probabilities = np.exp(scores - scores.max(axis=1, keepdims=True))
                    probabilities /= probabilities.sum(axis=1, keepdims=True)
                    output = np.einsum("ht,thd->hd", probabilities, values)
                    np.testing.assert_allclose(output[data["head"]], data["out"], atol=1e-12)
                    np.testing.assert_allclose(probabilities[data["head"]], data["p"], atol=1e-12)

    def test_network_forward_values_and_step_focus(self):
        rows = self.run_demo(391, """
for (const input of [-4,0,1,4]) {
  el('input').value=String(input); render();
  console.log(JSON.stringify({input, table:el('allvalues').innerHTML}));
}
""")
        for data in rows:
            x = np.array([data["input"], -1])
            hidden = 1 / (1 + np.exp(-(x @ np.array([[1, -1], [.5, 1]]) + [0, .5])))
            output = np.maximum(hidden @ np.array([[1, -1], [2, .5]]) + [-.5, .25], 0)
            expected_cells = ''.join(f'<td class="num">{value:.3f}</td>' for value in output)
            self.assertIn(expected_cells, data["table"])
