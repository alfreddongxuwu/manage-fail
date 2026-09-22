import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const mainSource = await readFile(new URL("../src/main.js", import.meta.url), "utf8");
let normingSource = null;

try {
  normingSource = await readFile(new URL("../../norming/src/main.js", import.meta.url), "utf8");
} catch (error) {
  if (error.code !== "ENOENT") {
    throw error;
  }
}

function consentStimulus(source) {
  return source.match(/const consent = \{[\s\S]*?stimulus: `([\s\S]*?)`,\s*choices:/)?.[1];
}

function instructionsStimulus(source) {
  return source.match(/const instructions = \{[\s\S]*?stimulus: `([\s\S]*?)`,\s*choices:/)?.[1];
}

function demographicsPreamble(source) {
  return source.match(/const demographics = \{[\s\S]*?preamble: `([\s\S]*?)`,\s*html:/)?.[1];
}

function demographicsHtml(source) {
  return source.match(/const demographics = \{[\s\S]*?html: `([\s\S]*?)`,\s*button_label:/)?.[1];
}

function demographicsButtonLabel(source) {
  return source.match(/const demographics = \{[\s\S]*?button_label: "([^"]+)"/)?.[1];
}

function asciiQuotes(value) {
  return value
    .replaceAll("\u201c", '"')
    .replaceAll("\u201d", '"')
    .replaceAll("\u2018", "'")
    .replaceAll("\u2019", "'");
}

function normalizedHtml(value) {
  return asciiQuotes(value)
    .trim()
    .split("\n")
    .map((line) => line.trim())
    .join("\n");
}

test("main experiment source uses ASCII quotes on non-rating pages", () => {
  assert.doesNotMatch(mainSource, /[\u2018\u2019\u201c\u201d]/);
});

test("consent text matches the norming consent text except for quote style", () => {
  if (!normingSource) {
    assert.match(consentStimulus(mainSource), /Consent to Participate in Research/);
    assert.match(
      consentStimulus(mainSource),
      /selecting <strong>"Yes, I agree to participate"<\/strong> and continuing/,
    );
    return;
  }

  assert.equal(normalizedHtml(consentStimulus(mainSource)), normalizedHtml(consentStimulus(normingSource)));
});

test("instructions text matches norming except for the three-question wording", () => {
  const mainInstructions = normalizedHtml(instructionsStimulus(mainSource));

  assert.match(mainInstructions, /three questions using sliders/);

  if (!normingSource) {
    assert.match(mainInstructions, /You will read one short description/);
    assert.match(mainInstructions, /respond based <strong>only<\/strong>/);
    return;
  }

  assert.equal(
    mainInstructions.replace("three questions using sliders", "two questions using sliders"),
    normalizedHtml(instructionsStimulus(normingSource)),
  );
});

test("demographics page matches the norming demographics page except for quote style", () => {
  if (!normingSource) {
    assert.match(demographicsPreamble(mainSource), /Your answers on this page will <strong>not<\/strong>/);
    assert.match(demographicsHtml(mainSource), /Bachelor's degree/);
    assert.match(demographicsHtml(mainSource), /Master's degree/);
    assert.equal(demographicsButtonLabel(mainSource), "Submit responses");
    return;
  }

  assert.equal(
    normalizedHtml(demographicsPreamble(mainSource)),
    normalizedHtml(demographicsPreamble(normingSource)),
  );
  assert.equal(
    normalizedHtml(demographicsHtml(mainSource)),
    normalizedHtml(demographicsHtml(normingSource)),
  );
  assert.equal(demographicsButtonLabel(mainSource), demographicsButtonLabel(normingSource));
});

test("demographics validation follows the norming required-field behavior", () => {
  assert.match(mainSource, /const fields = \[\.\.\.form\.querySelectorAll\("\[required\]"\)\]/);
  assert.match(mainSource, /form\.noValidate = true/);
  assert.match(mainSource, /field\.value\.trim\(\) === ""/);
  assert.match(mainSource, /Please enter your age in years\./);
  assert.match(mainSource, /Please enter an age between 18 and 120\./);
  assert.match(mainSource, /Please select an option\./);
  assert.match(mainSource, /field\.toggleAttribute\("aria-invalid", message !== ""\)/);
  assert.match(mainSource, /field\.addEventListener\(eventName, \(\) => renderValidation\(field\)\)/);
  assert.match(mainSource, /event\.stopImmediatePropagation\(\)/);
  assert.match(mainSource, /invalidFields\[0\]\.focus\(\)/);
});
