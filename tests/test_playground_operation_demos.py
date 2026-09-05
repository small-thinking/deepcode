"""Execute teaching scripts and compare their toy math with a vectorized oracle."""
import json
import re
import shutil
import subprocess
import unittest
import xml.etree.ElementTree as ET
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
        for number, expected_states in ((389, 48), (390, 96)):
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

    def test_portrait_attention_forward_and_stage_controls(self):
        path = Path("problems/388-pytorch-projected-multihead-attention/assets/operation-theater.html")
        script = re.search(r"<script>(.*?)</script>", path.read_text(), re.S).group(1)
        stub = DOM_STUB + """
document.createElement = () => {const e=new Element(); e.dataset={}; return e};
Element.prototype.replaceChildren=function(){this.children=[]};
Element.prototype.append=function(e){this.children.push(e)};
const buttons=Array.from({length:5},(_,i)=>{const b=new Element();b.tagName='BUTTON';b.dataset={stage:String(i)};return b});
document.querySelectorAll=()=>buttons;
"""
        exercise = """
for(const causal of [false,true]) for(let head=0;head<2;head++) for(let token=0;token<4;token++) {
 Object.assign(state,{causal,head,token});
 for(const mode of ['forward','backward']) {
  setMode(mode);
  for(const button of buttons) {
   button.focus();button.onclick();
   assert.equal(document.activeElement,button);
   assert.equal(button['aria-pressed'],'true');
   assert.ok(el('scene').innerHTML.includes('<title'));
  }
 }
 console.log(JSON.stringify({causal,x:X,...compute()}));
}
el('reset').onclick();assert.equal(state.stage,0);assert.equal(state.token,2);assert.equal(state.mode,'forward');
"""
        subprocess.run(["node", "--check", "-"], input=script, text=True, check=True, capture_output=True)
        result = subprocess.run(["node", "-e", stub + script + exercise], text=True, check=True, capture_output=True)
        rows = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(len(rows), 16)
        for data in rows:
            x = np.array(data["x"])
            # Independently execute the documented packed nn.Linear projection.
            weight = np.concatenate([np.eye(4), .5 * np.eye(4), np.eye(4)])
            q, k, v = (x @ weight.T).reshape(4, 3, 2, 2).transpose(1, 2, 0, 3)
            scores = q @ k.transpose(0, 2, 1) / np.sqrt(2)
            allowed = np.tril(np.ones((4, 4), dtype=bool)) if data["causal"] else np.ones((4, 4), dtype=bool)
            masked = np.where(allowed, scores, -np.inf)
            p = np.exp(masked - masked.max(axis=-1, keepdims=True))
            p /= p.sum(axis=-1, keepdims=True)
            output = p @ v
            h = data["head"]
            for name, expected in dict(q=q[h], k=k[h], v=v[h], scores=scores[h], p=p[h], outputs=output[h]).items():
                np.testing.assert_allclose(data[name], expected, atol=1e-12)
            np.testing.assert_array_equal(data["allowed"], allowed)

    def test_network_forward_values_and_step_focus(self):
        rows = self.run_demo(391, """
for (let input=-4; input<=4; input+=.25) {
  el('input').value=String(input); render();
  const data=calculate(input);
  console.log(JSON.stringify({input, data,
    contractions:[false,true].map(second=>[0,1].map(j=>contraction(data,second,j))),
    sigmoid:el('sigmoid').innerHTML, relu:el('relu').innerHTML}));
}
""")
        self.assertEqual(len(rows), 33)
        for data in rows:
            x = np.array([data["input"], -1])
            weights = [np.array([[1, -1], [.5, 1]]), np.array([[1, -1], [2, .5]])]
            biases = [np.array([0, .5]), np.array([-.5, .25])]
            z1 = x @ weights[0] + biases[0]
            hidden = 1 / (1 + np.exp(-z1))
            z2 = hidden @ weights[1] + biases[1]
            output = np.maximum(z2, 0)
            for name, expected in dict(x=x, z1=z1, h=hidden, z2=z2, y=output).items():
                np.testing.assert_allclose(data["data"][name], expected, atol=1e-12)
            for layer, inputs in enumerate([x, hidden]):
                for column in range(2):
                    detail = data["contractions"][layer][column]
                    expected_products = inputs * weights[layer][:, column]
                    np.testing.assert_allclose(detail["products"], expected_products, atol=1e-12)
                    self.assertAlmostEqual(detail["bias"], biases[layer][column])
                    self.assertAlmostEqual(detail["result"], expected_products.sum() + biases[layer][column])

            # Check the drawn markers, not only helper outputs. In SVG, coordinate
            # zero is the circle and coordinate one is the square's center.
            for name, before, after, xlim, ylim in [
                ("sigmoid", z1, hidden, (-5, 5), (0, 1)),
                ("relu", z2, output, (-1, 2), (-.12, 2)),
            ]:
                svg = ET.fromstring(data[name])
                ns = "{http://www.w3.org/2000/svg}"
                circle = svg.find(f"{ns}circle")
                square = svg.find(f"{ns}rect")
                actual = [[float(circle.attrib["cx"]), float(circle.attrib["cy"])],
                          [float(square.attrib["x"]) + 4, float(square.attrib["y"]) + 4]]
                expected_x = 34 + (before - xlim[0]) / (xlim[1] - xlim[0]) * (195 - 34)
                expected_y = 163 - (after - ylim[0]) / (ylim[1] - ylim[0]) * (163 - 30)
                np.testing.assert_allclose(actual, np.column_stack([expected_x, expected_y]), atol=1e-9)

    def test_network_coordinate_steps_and_reset_preserve_focus(self):
        self.run_demo(391, """
el('coord1').focus(); el('coord1').onclick();
assert.equal(document.activeElement, el('coord1'));
assert.equal(coordinate, 1);
assert.equal(el('coord1')['aria-pressed'], 'true');
el('input').value='-4'; el('input').oninput();
stage=3; render();
assert.ok(el('equation').innerHTML.includes('z₂[0, 1]'));
assert.ok(el('matmul').innerHTML.includes('column 1'));
el('reset').onclick();
assert.equal(coordinate, 0); assert.equal(stage, 0);
assert.equal(el('input').value, '1');
assert.equal(el('prev').disabled, true);
el('prev').onclick(); assert.equal(stage, 0);
for(let i=0;i<8;i++) el('next').onclick();
assert.equal(stage, 4); assert.equal(el('next').disabled, true);
assert.equal(stableSigmoid(-1000), 0); assert.equal(stableSigmoid(1000), 1);
""")
