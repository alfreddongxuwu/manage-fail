export const ITEMS = Object.freeze([
  {
    id: "photo",
    globalOffset: 0,
    protagonist: "Alfred",
    object: "photo",
    action: "put up the photo",
    completedAction: "put up the photo",
    prior: Object.freeze({
      high:
        "Alfred recently took and printed a group photo of himself and his two roommates. He told his roommates that he was planning to put it up soon, and he mentioned several times that putting it up was part of his current plan.",
      low:
        "Alfred recently took and printed a group photo of himself and his two roommates. He told his roommates that he was not planning to put it up soon, and he mentioned several times that putting it up was not part of his current plan.",
    }),
    qud: Object.freeze({
      "P?":
        "Later, Alfred's roommate Catherine happened to think of the photo and wondered whether Alfred put it up. She asked their other roommate, who was reliable and knew what actually happened, whether Alfred put up the photo.",
      "TRY?":
        "Later, Alfred's roommate Catherine happened to think of the photo and wondered whether Alfred TRIED TO put it up. She asked their other roommate, who was reliable and knew what actually happened, whether Alfred TRIED TO put up the photo.",
    }),
  },
  {
    id: "package",
    globalOffset: 32,
    protagonist: "Catherine",
    object: "package",
    action: "pick up the package",
    completedAction: "picked up the package",
    prior: Object.freeze({
      high:
        "Catherine recently received a message saying that a package was waiting for her at the front desk. She told her two roommates that she was planning to pick it up soon, and she mentioned several times that picking it up was part of her current plan.",
      low:
        "Catherine recently received a message saying that a package was waiting for her at the front desk. She told her two roommates that she was not planning to pick it up soon, and she mentioned several times that picking it up was not part of her current plan.",
    }),
    qud: Object.freeze({
      "P?":
        "Later, Catherine's roommate Alfred happened to think of the package and wondered whether Catherine picked it up. He asked their other roommate, who was reliable and knew what actually happened, whether Catherine picked up the package.",
      "TRY?":
        "Later, Catherine's roommate Alfred happened to think of the package and wondered whether Catherine TRIED TO pick it up. He asked their other roommate, who was reliable and knew what actually happened, whether Catherine TRIED TO pick up the package.",
    }),
  },
]);

export const PRIORS = Object.freeze(["high", "low"]);
export const QUDS = Object.freeze(["P?", "TRY?"]);

export const UTTERANCE_TYPES = Object.freeze([
  {
    id: "managed",
    family: "manage",
    polarity: "positive",
    isImplicative: true,
    text: ({ protagonist, action }) => `${protagonist} managed to ${action}.`,
  },
  {
    id: "didnt_manage",
    family: "manage",
    polarity: "negative",
    isImplicative: true,
    text: ({ protagonist, action }) => `${protagonist} didn't manage to ${action}.`,
  },
  {
    id: "failed",
    family: "fail",
    polarity: "positive",
    isImplicative: true,
    text: ({ protagonist, action }) => `${protagonist} failed to ${action}.`,
  },
  {
    id: "didnt_fail",
    family: "fail",
    polarity: "negative",
    isImplicative: true,
    text: ({ protagonist, action }) => `${protagonist} didn't fail to ${action}.`,
  },
  {
    id: "did",
    family: "simple",
    polarity: "positive",
    isImplicative: false,
    text: ({ protagonist, completedAction }) => `${protagonist} ${completedAction}.`,
  },
  {
    id: "didnt",
    family: "simple",
    polarity: "negative",
    isImplicative: false,
    text: ({ protagonist, action }) => `${protagonist} didn't ${action}.`,
  },
  {
    id: "tried",
    family: "try",
    polarity: "positive",
    isImplicative: false,
    text: ({ protagonist, action }) => protagonist + " tried to " + action + ".",
  },
  {
    id: "didnt_try",
    family: "try",
    polarity: "negative",
    isImplicative: false,
    text: ({ protagonist, action }) => protagonist + " didn" + String.fromCharCode(39) + "t try to " + action + ".",
  },
]);

export const RATING_TYPES = Object.freeze(["P?", "TRY?", "NAT"]);

export const CONDITIONS = Object.freeze(
  ITEMS.flatMap((item) =>
    PRIORS.flatMap((prior) =>
      QUDS.flatMap((qud) =>
        UTTERANCE_TYPES.map((utterance, utteranceIndex) => {
          const localConditionId =
            PRIORS.indexOf(prior) * QUDS.length * UTTERANCE_TYPES.length
            + QUDS.indexOf(qud) * UTTERANCE_TYPES.length
            + utteranceIndex;

          return Object.freeze({
            local_condition_id: localConditionId,
            global_condition_id: item.globalOffset + localConditionId,
            item: item.id,
            prior,
            qud,
            protagonist: item.protagonist,
            action: item.action,
            completed_action: item.completedAction,
            prior_text: item.prior[prior],
            qud_text: item.qud[qud],
            utterance_id: utterance.id,
            utterance_family: utterance.family,
            utterance_polarity: utterance.polarity,
            is_implicative: utterance.isImplicative,
            target_utterance: utterance.text(item),
          });
        }),
      ),
    ),
  ),
);

export function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

export function emphasizeTryTo(value) {
  return escapeHtml(value).replace(/\b(?:try|tried) to\b/gi, (match) => `<strong>${match}</strong>`);
}

export function conditionsForItem(itemId) {
  return CONDITIONS.filter((condition) => condition.item === itemId);
}

export function randomCondition(itemId) {
  const pool = itemId ? conditionsForItem(itemId) : CONDITIONS;
  return pool[Math.floor(Math.random() * pool.length)];
}

export function conditionFromId(rawId, itemId) {
  if (rawId === null || rawId === undefined || rawId === "") {
    return undefined;
  }

  const id = Number(rawId);
  const pool = itemId ? conditionsForItem(itemId) : CONDITIONS;
  const idKey = itemId ? "local_condition_id" : "global_condition_id";

  return Number.isInteger(id)
    ? pool.find((condition) => condition[idKey] === id)
    : undefined;
}

export function ratingQuestion(condition, ratingType) {
  if (ratingType === "P?") {
    return `Given what you have read, how likely is it that ${condition.protagonist} ${condition.completed_action}?`;
  }

  if (ratingType === "TRY?") {
    return `Given what you have read, how likely is it that ${condition.protagonist} tried to ${condition.action}?`;
  }

  if (ratingType === "NAT") {
    return "How natural does the roommate's answer sound in this context?";
  }

  throw new Error(`Unknown rating type: ${ratingType}`);
}

export function ratingEndpoints(ratingType) {
  return ratingType === "NAT"
    ? ["very unnatural", "very natural"]
    : ["very unlikely", "very likely"];
}

export function orderedRatingTypes(shuffle) {
  return [...shuffle(["P?", "TRY?"]), "NAT"];
}

export function ratingStimulus(condition) {
  return `
    <section class="rating-screen">
      <p class="reading-instruction">Please read the following text.</p>
      <div class="scenario-text">
        <p>${escapeHtml(condition.prior_text)}</p>
        <p>${escapeHtml(condition.qud_text)}</p>
        <p>The roommate answered: <em>&quot;${escapeHtml(condition.target_utterance)}&quot;</em></p>
      </div>
    </section>
  `;
}
