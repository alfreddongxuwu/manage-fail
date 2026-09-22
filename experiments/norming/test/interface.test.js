import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const [mainSource, stylesSource, pluginSource] = await Promise.all([
  readFile(new URL("../src/main.js", import.meta.url), "utf8"),
  readFile(new URL("../src/styles.css", import.meta.url), "utf8"),
  readFile(new URL("../src/plugins/two-slider-response.js", import.meta.url), "utf8"),
]);

test("the slider uses the endpoint labels", () => {
  assert.match(stylesSource, /justify-content:\s*space-between/);
  const labelRule = stylesSource.match(/\.slider-end-labels\s*\{([^}]*)\}/)?.[1];
  assert.match(labelRule, /font-weight:\s*700/);
});

test("the experiment column is centered in the middle third and text is left aligned", () => {
  assert.match(stylesSource, /width:\s*min\(33\.333vw,\s*42rem\)/);
  assert.match(stylesSource, /text-align:\s*left/);
  assert.match(stylesSource, /align-items:\s*center/);
  assert.match(stylesSource, /justify-content:\s*center/);
});

test("both sliders must be moved before submission", () => {
  assert.match(pluginSource, /disabled/);
  assert.match(pluginSource, /moved\.size === inputs\.length/);
});

test("the rating page records one total response time", () => {
  assert.match(pluginSource, /rt: Math\.round\(performance\.now\(\) - startTime\)/);
  assert.doesNotMatch(pluginSource, /completion_rt|try_rt|firstMovementRt/);
});

test("the two rating questions are randomized once and shown in one trial", () => {
  assert.match(mainSource, /randomization\.shuffle/);
  assert.match(mainSource, /combinedRatingStimulus\(selectedCondition, questionOrder\)/);
  assert.doesNotMatch(mainSource, /ratingTrials/);
});

test("rating and demographic submit buttons have added space above them", () => {
  assert.match(stylesSource, /#two-slider-next,\s*#jspsych-survey-html-form-next\s*\{\s*margin-top:\s*2rem/);
});

test("demographic validation uses experiment-controlled English messages", () => {
  assert.match(mainSource, /form\.noValidate = true/);
  assert.match(mainSource, /Please enter your age in years\./);
  assert.match(mainSource, /Please enter an age between 18 and 120\./);
  assert.match(mainSource, /Please select an option\./);
});

test("the demographics payment reassurance emphasizes not", () => {
  assert.match(
    mainSource,
    /Your answers on this page will <strong>not<\/strong> affect your payment/,
  );
});

test("ordinary study text uses the question font size", () => {
  assert.match(stylesSource, /--study-font-size:\s*1\.08rem/);
  assert.match(stylesSource, /\.scenario-text\s*\{[\s\S]*?font-size:\s*var\(--study-font-size\)/);
  assert.match(stylesSource, /\.consent-screen p\s*\{[\s\S]*?font-size:\s*var\(--study-font-size\)/);
  assert.match(stylesSource, /\.slider-end-labels\s*\{[\s\S]*?font-size:\s*var\(--study-font-size\)/);
});

test("the reading instruction is regular while the scenario text is bold", () => {
  const readingInstructionRule = stylesSource.match(
    /\.reading-instruction\s*\{([^}]*)\}/,
  )?.[1];
  assert.match(stylesSource, /\.scenario-text\s*\{[\s\S]*?font-weight:\s*700/);
  assert.doesNotMatch(readingInstructionRule, /font-weight:\s*700/);
});

test("the instructions page emphasizes only", () => {
  assert.match(
    mainSource,
    /Please respond based <strong>only<\/strong> on the information in the description\./,
  );
  assert.doesNotMatch(
    mainSource,
    /Please respond based only on the information in the description\./,
  );
});

test("consent emphasizes the duration number and the quoted affirmative choice", () => {
  assert.match(mainSource, /about <strong>5 minutes<\/strong>/);
  assert.match(
    mainSource,
    /selecting <strong>"Yes, I agree to participate"<\/strong> and continuing/,
  );
});

test("consent response choices have visible space between them", () => {
  assert.match(
    stylesSource,
    /#jspsych-html-button-response-btngroup\s*\{[^}]*column-gap:\s*1\.25rem/s,
  );
});

test("the experiment ends on one static completion screen without a redundant Finish step", () => {
  assert.doesNotMatch(mainSource, /const completion =|choices: \["Finish"\]/);
  assert.doesNotMatch(mainSource, /<h1>Thank you<\/h1>/);
  assert.equal(
    mainSource.match(
      /Thank you for completing this demo\. No responses were uploaded\./g,
    )?.length,
    1,
  );
  assert.doesNotMatch(mainSource, /Preview complete\. No responses were saved\./);
  assert.doesNotMatch(mainSource, /You may now close this window\./);
  assert.match(mainSource, /You should be redirected to Prolific automatically\./);
  assert.match(stylesSource, /\.completion-screen p,[\s\S]*?font-size:\s*1\.35rem/);
});
