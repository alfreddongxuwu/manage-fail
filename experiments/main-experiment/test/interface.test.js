import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [stylesSource, pluginSource] = await Promise.all([
  readFile(new URL("../src/styles.css", import.meta.url), "utf8"),
  readFile(new URL("../src/plugins/three-slider-response.js", import.meta.url), "utf8"),
]);

test("the preview layout follows the norming centered column", () => {
  assert.match(stylesSource, /width:\s*min\(33\.333vw,\s*42rem\)/);
  assert.match(stylesSource, /text-align:\s*left/);
  assert.match(stylesSource, /align-items:\s*center/);
  assert.match(stylesSource, /justify-content:\s*center/);
});

test("the rating page makes the text bold but leaves question text regular", () => {
  assert.match(stylesSource, /\.scenario-text\s*\{[\s\S]*?font-weight:\s*700/);
  assert.match(stylesSource, /\.question-text\s*\{[\s\S]*?font-weight:\s*400/);
  assert.match(stylesSource, /\.question-text strong\s*\{[\s\S]*?font-weight:\s*700/);
  assert.match(stylesSource, /\.scenario-text em\s*\{[\s\S]*?font-style:\s*italic/);
});

test("slider endpoint labels are bold", () => {
  const labelRule = stylesSource.match(/\.slider-end-labels\s*\{([^}]*)\}/)?.[1];

  assert.match(labelRule, /font-weight:\s*700/);
});

test("all three sliders must be moved before submission", () => {
  assert.match(pluginSource, /disabled/);
  assert.match(pluginSource, /moved\.size === inputs\.length/);
  assert.match(pluginSource, /naturalness_rating/);
});
