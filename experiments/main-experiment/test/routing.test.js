import test from "node:test";
import assert from "node:assert/strict";
import { itemFromPath, previewAssignmentFromLocation } from "../src/routing.js";

test("preview links expose item routes in the path", () => {
  assert.equal(itemFromPath("/manage-fail/main-experiment/photo/"), "photo");
  assert.equal(itemFromPath("/manage-fail/main-experiment/package/"), "package");
  assert.equal(itemFromPath("/manage-fail/main-experiment/"), undefined);
});

test("condition query ids are local inside item routes", () => {
  const photo = previewAssignmentFromLocation({
    pathname: "/manage-fail/main-experiment/photo/",
    search: "?condition=0",
  });
  const packageItem = previewAssignmentFromLocation({
    pathname: "/manage-fail/main-experiment/package/",
    search: "?condition=0",
  });

  assert.equal(photo.selectedCondition.item, "photo");
  assert.equal(photo.selectedCondition.local_condition_id, 0);
  assert.equal(photo.selectedCondition.global_condition_id, 0);
  assert.equal(photo.itemRoute, "photo");
  assert.equal(photo.assignmentSource, "url-forced-photo-preview");

  assert.equal(packageItem.selectedCondition.item, "package");
  assert.equal(packageItem.selectedCondition.local_condition_id, 0);
  assert.equal(packageItem.selectedCondition.global_condition_id, 32);
  assert.equal(packageItem.itemRoute, "package");
  assert.equal(packageItem.assignmentSource, "url-forced-package-preview");
});
