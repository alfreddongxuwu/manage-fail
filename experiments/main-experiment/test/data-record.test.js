import test from "node:test";
import assert from "node:assert/strict";
import { buildParticipantRecord } from "../src/data-record.js";

test("raw jsPsych trials are reduced to one main-experiment participant record", () => {
  const shared = {
    participant_uuid: "123e4567-e89b-12d3-a456-426614174000",
    study: "main-experiment",
    study_version: "main-experiment-photo-1.0.0",
    collection_mode: "main",
    prolific_pid: "participant-1",
    prolific_study_id: "study-2",
    prolific_session_id: "session-3",
    assignment_source: "datapipe-sequential-photo",
    item_route: "photo",
    local_condition_id: 7,
    global_condition_id: 7,
    item: "photo",
    prior: "high",
    qud: "P?",
    utterance_id: "didnt_manage",
    utterance_family: "manage",
    utterance_polarity: "negative",
    is_implicative: true,
  };

  const record = buildParticipantRecord([
    { ...shared, trial_kind: "consent", consent_given: true, rt: 4100 },
    { ...shared, trial_kind: "instructions", rt: 1800 },
    {
      ...shared,
      trial_kind: "rating",
      rt: 11200,
      completion_rating: 28,
      try_rating: 76,
      naturalness_rating: 82,
      rating_order: ["P?", "TRY?", "NAT"],
    },
    {
      ...shared,
      trial_kind: "demographics",
      rt: 13700,
      response: {
        age: "25",
        gender: "woman",
        education: "bachelor",
        native_language: "english-only",
        country: "united-states",
      },
    },
  ]);

  assert.deepEqual(record, {
    data_schema_version: "main-exp-1.0.0",
    ...shared,
    consent_given: true,
    consent_rt_ms: 4100,
    instructions_rt_ms: 1800,
    ratings_rt_ms: 11200,
    rating_order: ["P?", "TRY?", "NAT"],
    try_rating: 76,
    completion_rating: 28,
    naturalness_rating: 82,
    demographics_rt_ms: 13700,
    age: 25,
    gender: "woman",
    education: "bachelor",
    native_language: "english-only",
    country: "united-states",
  });
  assert.equal("submission_id" in record, false);
  assert.equal("target_utterance" in record, false);
  assert.equal("prior_text" in record, false);
  assert.equal("qud_text" in record, false);
  assert.equal("completion_question" in record, false);
  assert.equal("try_question" in record, false);
  assert.equal("naturalness_question" in record, false);
  assert.equal("stimulus" in record, false);
});
