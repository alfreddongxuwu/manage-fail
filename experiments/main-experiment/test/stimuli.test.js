import test from "node:test";
import assert from "node:assert/strict";
import {
  CONDITIONS,
  ITEMS,
  QUDS,
  RATING_TYPES,
  UTTERANCE_TYPES,
  conditionFromId,
  conditionsForItem,
  emphasizeTryTo,
  orderedRatingTypes,
  ratingQuestion,
  ratingEndpoints,
  escapeHtml,
  ratingStimulus,
} from "../src/stimuli.js";

test("the design has two items and 64 total preview conditions", () => {
  assert.deepEqual(ITEMS.map((item) => item.id), ["photo", "package"]);
  assert.equal(CONDITIONS.length, 64);
  assert.equal(CONDITIONS.filter((condition) => condition.item === "photo").length, 32);
  assert.equal(CONDITIONS.filter((condition) => condition.item === "package").length, 32);
});

test("condition ids are local within item and global across both items", () => {
  assert.equal(conditionsForItem("photo").length, 32);
  assert.equal(conditionsForItem("package").length, 32);

  assert.deepEqual(
    CONDITIONS.filter((condition) => condition.item === "photo").map(
      (condition) => condition.local_condition_id,
    ),
    [...Array(32).keys()],
  );
  assert.deepEqual(
    CONDITIONS.filter((condition) => condition.item === "package").map(
      (condition) => condition.local_condition_id,
    ),
    [...Array(32).keys()],
  );
  assert.deepEqual(
    CONDITIONS.map((condition) => condition.global_condition_id),
    [...Array(64).keys()],
  );
});

test("condition query ids can lock the 32 photo preview conditions", () => {
  for (let id = 0; id < 32; id += 1) {
    const condition = conditionFromId(String(id), "photo");

    assert.equal(condition.global_condition_id, id);
    assert.equal(condition.item, "photo");
  }

  assert.equal(conditionFromId("not-a-number"), undefined);
  assert.equal(conditionFromId(""), undefined);
});

test("item routes scope condition query ids locally", () => {
  for (let id = 0; id < 32; id += 1) {
    const condition = conditionFromId(String(id), "package");

    assert.equal(condition.local_condition_id, id);
    assert.equal(condition.global_condition_id, id + 32);
    assert.equal(condition.item, "package");
  }

  assert.equal(conditionFromId("32", "photo"), undefined);
  assert.equal(conditionFromId("32", "package"), undefined);
  assert.equal(conditionFromId("32").item, "package");
});

test("the QUD values use the design labels", () => {
  assert.deepEqual(QUDS, ["P?", "TRY?"]);
});

test("the utterance set includes try and not-try controls", () => {
  assert.deepEqual(
    UTTERANCE_TYPES.map((utterance) => utterance.id),
    ["managed", "didnt_manage", "failed", "didnt_fail", "did", "didnt", "tried", "didnt_try"],
  );
});

test("only manage and fail utterances are marked implicative", () => {
  const implicativeById = Object.fromEntries(
    UTTERANCE_TYPES.map((utterance) => [utterance.id, utterance.isImplicative]),
  );

  assert.deepEqual(implicativeById, {
    managed: true,
    didnt_manage: true,
    failed: true,
    didnt_fail: true,
    did: false,
    didnt: false,
    tried: false,
    didnt_try: false,
  });
});

test("rating order randomizes the first two questions and fixes naturalness last", () => {
  assert.deepEqual(RATING_TYPES, ["P?", "TRY?", "NAT"]);
  assert.deepEqual(orderedRatingTypes((values) => [...values].reverse()), ["TRY?", "P?", "NAT"]);
});

test("slider endpoints use lowercase labels", () => {
  assert.deepEqual(ratingEndpoints("P?"), ["very unlikely", "very likely"]);
  assert.deepEqual(ratingEndpoints("TRY?"), ["very unlikely", "very likely"]);
  assert.deepEqual(ratingEndpoints("NAT"), ["very unnatural", "very natural"]);
});

test("the TRY question is the only rating question with tried to emphasis", () => {
  const condition = CONDITIONS.find(
    (candidate) => candidate.item === "photo" && candidate.qud === "TRY?",
  );

  assert.match(emphasizeTryTo(ratingQuestion(condition, "TRY?")), /<strong>tried to<\/strong>/);
  assert.doesNotMatch(ratingQuestion(condition, "P?"), /<strong>|tried to|try to/);
  assert.doesNotMatch(ratingQuestion(condition, "NAT"), /<strong>|tried to|try to/);
});

test("the rating text contains prior paragraph, QUD paragraph, and target answer", () => {
  const condition = CONDITIONS.find(
    (candidate) =>
      candidate.item === "package" &&
      candidate.prior === "low" &&
      candidate.qud === "TRY?" &&
      candidate.utterance_id === "didnt_fail",
  );
  const stimulus = ratingStimulus(condition);

  assert.match(stimulus, /Catherine recently received a message/);
  assert.match(stimulus, /She told her two roommates that she was not planning/);
  assert.match(stimulus, /wondered whether Catherine TRIED TO pick it up/);
  assert.match(stimulus, /He asked their other roommate, who was reliable and knew what actually happened, whether Catherine TRIED TO pick up the package/);
  assert.match(
    stimulus,
    /The roommate answered: <em>&quot;Catherine didn&#039;t fail to pick up the package\.&quot;<\/em>/,
  );
  assert.doesNotMatch(stimulus, /\* Assume/);
});

test("prior and QUD paragraphs are independently recombined from the stimuli files", () => {
  const highTryPhoto = CONDITIONS.find(
    (condition) =>
      condition.item === "photo" &&
      condition.prior === "high" &&
      condition.qud === "TRY?" &&
      condition.utterance_id === "managed",
  );
  const lowPPhoto = CONDITIONS.find(
    (condition) =>
      condition.item === "photo" &&
      condition.prior === "low" &&
      condition.qud === "P?" &&
      condition.utterance_id === "managed",
  );

  assert.match(highTryPhoto.prior_text, /he was planning to put it up soon/);
  assert.match(highTryPhoto.qud_text, /wondered whether Alfred TRIED TO put it up/);
  assert.match(lowPPhoto.prior_text, /he was not planning to put it up soon/);
  assert.match(lowPPhoto.qud_text, /wondered whether Alfred put it up/);
});
