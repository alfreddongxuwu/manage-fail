import { ParameterType } from "jspsych";

export default class ThreeSliderResponsePlugin {
  static info = {
    name: "three-slider-response",
    version: "1.0.0",
    parameters: {
      stimulus: {
        type: ParameterType.HTML_STRING,
        default: undefined,
      },
      questions: {
        type: ParameterType.COMPLEX,
        array: true,
        default: undefined,
      },
      button_label: {
        type: ParameterType.STRING,
        default: "Continue",
      },
    },
    data: {
      rt: { type: ParameterType.INT },
      completion_rating: { type: ParameterType.INT },
      try_rating: { type: ParameterType.INT },
      naturalness_rating: { type: ParameterType.INT },
      rating_order: { type: ParameterType.STRING, array: true },
    },
  };

  constructor(jsPsych) {
    this.jsPsych = jsPsych;
  }

  trial(displayElement, trial) {
    displayElement.innerHTML = `
      ${trial.stimulus}
      <div class="rating-questions">
        ${trial.questions.map((question) => this.renderQuestion(question)).join("")}
      </div>
      <button id="three-slider-next" class="jspsych-btn" disabled>${trial.button_label}</button>
    `;

    const inputs = [...displayElement.querySelectorAll(".rating-slider")];
    const nextButton = displayElement.querySelector("#three-slider-next");
    const moved = new Set();
    const startTime = performance.now();

    for (const input of inputs) {
      input.addEventListener("input", () => {
        const ratingType = input.dataset.ratingType;
        moved.add(ratingType);
        input.closest(".rating-control").classList.add("has-response");

        if (moved.size === inputs.length) {
          nextButton.disabled = false;
        }
      });
    }

    nextButton.addEventListener("click", () => {
      const values = Object.fromEntries(
        inputs.map((input) => [input.dataset.ratingType, Number(input.value)]),
      );

      this.jsPsych.finishTrial({
        rt: Math.round(performance.now() - startTime),
        completion_rating: values["P?"],
        try_rating: values["TRY?"],
        naturalness_rating: values.NAT,
        rating_order: inputs.map((input) => input.dataset.ratingType),
      });
    });
  }

  renderQuestion(question) {
    return `
      <div class="rating-control" data-rating-type="${question.type}">
        <p class="question-text">${question.prompt}</p>
        <input
          class="rating-slider"
          type="range"
          min="0"
          max="100"
          step="1"
          value="50"
          data-rating-type="${question.type}"
          aria-label="${question.plainPrompt}"
        />
        <div class="slider-end-labels" aria-hidden="true">
          <span>${question.endpoints[0]}</span>
          <span>${question.endpoints[1]}</span>
        </div>
      </div>
    `;
  }
}
