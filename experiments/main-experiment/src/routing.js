import { conditionFromId, randomCondition } from "./stimuli.js";

export function previewAssignmentFromLocation(location) {
  const query = new URLSearchParams(location.search);
  const forcedCondition = conditionFromId(query.get("condition"));

  return {
    selectedCondition: forcedCondition ?? randomCondition(),
    assignmentSource: forcedCondition ? "url-forced-preview" : "local-random-preview",
  };
}
