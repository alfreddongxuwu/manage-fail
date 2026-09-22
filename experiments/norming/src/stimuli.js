export const CONDITIONS = Object.freeze([
  {
    id: 0,
    item: "photo",
    prior: "high",
    protagonist: "Alfred",
    action: "put up the photo",
    context:
      "Alfred recently took and printed a group photo of himself and his two roommates. He told his roommates that he was planning to put it up soon, and he mentioned several times that putting it up was part of his current plan.",
  },
  {
    id: 1,
    item: "photo",
    prior: "low",
    protagonist: "Alfred",
    action: "put up the photo",
    context:
      "Alfred recently took and printed a group photo of himself and his two roommates. He told his roommates that he was not planning to put it up soon, and he mentioned several times that putting it up was not part of his current plan.",
  },
  {
    id: 2,
    item: "package",
    prior: "high",
    protagonist: "Catherine",
    action: "pick up the package",
    context:
      "Catherine recently received a message saying that a package was waiting for her at the front desk. She told her roommates that she was planning to pick it up soon, and she mentioned several times that picking it up was part of her current plan.",
  },
  {
    id: 3,
    item: "package",
    prior: "low",
    protagonist: "Catherine",
    action: "pick up the package",
    context:
      "Catherine recently received a message saying that a package was waiting for her at the front desk. She told her roommates that she was not planning to pick it up soon, and she mentioned several times that picking it up was not part of her current plan.",
  },
]);

export const QUESTION_TYPES = Object.freeze(["completion", "try"]);

export function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

export function emphasizeTryTo(value) {
  return escapeHtml(value).replace(/\btry to\b/gi, (match) => `<strong>${match}</strong>`);
}

export function questionFor(condition, questionType) {
  if (questionType === "completion") {
    return `Given what you have read, how likely is it that ${condition.protagonist} would ${condition.action}?`;
  }

  if (questionType === "try") {
    return `Given what you have read, how likely is it that ${condition.protagonist} would try to ${condition.action}?`;
  }

  throw new Error(`Unknown question type: ${questionType}`);
}

function ratingControl(condition, questionType) {
  const plainQuestion = questionFor(condition, questionType);
  const formattedQuestion = emphasizeTryTo(plainQuestion);

  return `
    <div class="rating-control" data-question-type="${questionType}">
      <p class="question-text">${formattedQuestion}</p>
      <input
        class="rating-slider"
        type="range"
        min="0"
        max="100"
        step="1"
        value="50"
        data-question-type="${questionType}"
        aria-label="${escapeHtml(plainQuestion)}"
      />
      <div class="slider-end-labels" aria-hidden="true">
        <span>very unlikely</span>
        <span>very likely</span>
      </div>
    </div>
  `;
}

export function combinedRatingStimulus(condition, questionOrder) {
  return `
    <section class="rating-screen">
      <p class="reading-instruction">Please read the following text.</p>
      <p class="scenario-text">${emphasizeTryTo(condition.context)}</p>
      <div class="rating-questions">
        ${questionOrder.map((questionType) => ratingControl(condition, questionType)).join("")}
      </div>
    </section>
  `;
}

export function conditionFromId(rawId) {
  if (rawId === null || rawId === undefined || rawId === "") {
    return undefined;
  }

  const id = Number(rawId);
  return Number.isInteger(id) ? CONDITIONS.find((condition) => condition.id === id) : undefined;
}
