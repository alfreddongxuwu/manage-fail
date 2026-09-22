import test from "node:test";
import assert from "node:assert/strict";
import {
  CONDITIONS,
  QUESTION_TYPES,
  combinedRatingStimulus,
  conditionFromId,
  questionFor,
} from "../src/stimuli.js";

test("the design contains four unique item-by-prior conditions", () => {
  assert.equal(CONDITIONS.length, 4);
  assert.deepEqual(
    CONDITIONS.map(({ item, prior }) => `${item}:${prior}`).sort(),
    ["package:high", "package:low", "photo:high", "photo:low"],
  );
  assert.equal(new Set(CONDITIONS.map(({ id }) => id)).size, 4);
});

test("condition lookup only returns valid conditions", () => {
  assert.equal(conditionFromId("0")?.item, "photo");
  assert.equal(conditionFromId("3")?.prior, "low");
  assert.equal(conditionFromId(null), undefined);
  assert.equal(conditionFromId(""), undefined);
  assert.equal(conditionFromId("4"), undefined);
  assert.equal(conditionFromId("not-a-number"), undefined);
});

test("every condition has both planned rating questions", () => {
  for (const condition of CONDITIONS) {
    for (const questionType of QUESTION_TYPES) {
      assert.match(questionFor(condition, questionType), /\?$/);
    }
  }
});

test("rating questions are regular weight except for every occurrence of try to", () => {
  for (const condition of CONDITIONS) {
    const stimulus = combinedRatingStimulus(condition, ["try", "completion"]);
    assert.doesNotMatch(stimulus, /<p class="question-text"><strong>Given/);
    assert.match(stimulus, /<strong>try to<\/strong>/i);
  }
});

test("the completion question contains no bold text", () => {
  const stimulus = combinedRatingStimulus(CONDITIONS[0], ["completion", "try"]);
  const completionControl = stimulus.match(
    /<div class="rating-control" data-question-type="completion">([\s\S]*?)<\/div>/,
  )?.[1];
  assert.doesNotMatch(completionControl, /<strong>/);
});

test("both unnumbered questions appear on the same page in the supplied order", () => {
  const stimulus = combinedRatingStimulus(CONDITIONS[0], ["try", "completion"]);
  assert.equal((stimulus.match(/class="rating-control"/g) ?? []).length, 2);
  assert.ok(stimulus.indexOf('data-question-type="try"') < stimulus.indexOf('data-question-type="completion"'));
  assert.doesNotMatch(stimulus, />\s*[12][.)]\s/);
});

test("scenario prose preserves explicit try to emphasis", () => {
  const condition = {
    ...CONDITIONS[0],
    context: "Alfred planned to try to hang the photo.",
  };
  const stimulus = combinedRatingStimulus(condition, ["completion", "try"]);
  const scenario = stimulus.match(/<p class="scenario-text">([\s\S]*?)<\/p>/)?.[1];
  assert.equal(scenario, "Alfred planned to <strong>try to</strong> hang the photo.");
});

test("the regular-weight reading instruction appears immediately before the scenario", () => {
  const stimulus = combinedRatingStimulus(CONDITIONS[0], ["completion", "try"]);
  assert.match(
    stimulus,
    /<p class="reading-instruction">Please read the following text\.<\/p>\s*<p class="scenario-text">/,
  );
});
