import test from "node:test";
import assert from "node:assert/strict";
import { previewAssignmentFromLocation } from "../src/routing.js";
import { CONDITIONS } from "../src/stimuli.js";

test("the main entry supports all 64 conditions across both items", () => {
  for (const expected of CONDITIONS) {
    const assignment = previewAssignmentFromLocation({
      pathname: "/manage-fail/main-experiment/",
      search: `?condition=${expected.global_condition_id}`,
    });
    assert.equal(assignment.selectedCondition, expected);
    assert.equal(assignment.assignmentSource, "url-forced-preview");
  }
});

test("the ordinary main entry selects a condition from the complete design", () => {
  for (const value of [0, 0.5, 0.999999]) {
    const originalRandom = Math.random;
    try {
      Math.random = () => value;
      const assignment = previewAssignmentFromLocation({ search: "" });
      assert.equal(assignment.selectedCondition, CONDITIONS[Math.floor(value * CONDITIONS.length)]);
      assert.equal(assignment.assignmentSource, "local-random-preview");
    } finally {
      Math.random = originalRandom;
    }
  }
});

test("invalid condition values fall back to random assignment", () => {
  for (const search of ["?condition=-1", "?condition=64", "?condition=invalid"]) {
    const assignment = previewAssignmentFromLocation({ search });
    assert.ok(CONDITIONS.includes(assignment.selectedCondition));
    assert.equal(assignment.assignmentSource, "local-random-preview");
  }
});
