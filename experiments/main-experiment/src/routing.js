import { ITEMS, conditionFromId, randomCondition } from "./stimuli.js";

const BASE_PATH = "/manage-fail/main-experiment/";
const ITEM_IDS = new Set(ITEMS.map((item) => item.id));

export function itemFromPath(pathname) {
  const relativePath = pathname.startsWith(BASE_PATH)
    ? pathname.slice(BASE_PATH.length)
    : pathname.replace(/^\/+/, "");
  const [firstSegment] = relativePath.split("/").filter(Boolean);

  return ITEM_IDS.has(firstSegment) ? firstSegment : undefined;
}

export function previewAssignmentFromLocation(location) {
  const itemRoute = itemFromPath(location.pathname);
  const query = new URLSearchParams(location.search);
  const forcedCondition = conditionFromId(query.get("condition"), itemRoute);
  const selectedCondition = forcedCondition ?? randomCondition(itemRoute);

  return {
    selectedCondition,
    itemRoute: itemRoute ?? null,
    assignmentSource: forcedCondition
      ? itemRoute
        ? `url-forced-${itemRoute}-preview`
        : "url-forced-preview"
      : itemRoute
        ? `local-random-${itemRoute}-preview`
        : "local-random-preview",
  };
}
