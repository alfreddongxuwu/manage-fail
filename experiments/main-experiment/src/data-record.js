export const DATA_SCHEMA_VERSION = "main-exp-1.0.0";

export function buildParticipantRecord(trials) {
  const consent = trials.find((trial) => trial.trial_kind === "consent");
  const instructions = trials.find((trial) => trial.trial_kind === "instructions");
  const rating = trials.find((trial) => trial.trial_kind === "rating");
  const demographics = trials.find((trial) => trial.trial_kind === "demographics");
  const metadata = rating ?? demographics ?? consent ?? {};
  const demographicResponse = demographics?.response ?? {};
  const age = Number(demographicResponse.age);

  return {
    data_schema_version: DATA_SCHEMA_VERSION,
    participant_uuid: metadata.participant_uuid ?? null,
    study: metadata.study ?? null,
    study_version: metadata.study_version ?? null,
    collection_mode: metadata.collection_mode ?? null,
    prolific_pid: metadata.prolific_pid ?? null,
    prolific_study_id: metadata.prolific_study_id ?? null,
    prolific_session_id: metadata.prolific_session_id ?? null,
    assignment_source: metadata.assignment_source ?? null,
    item_route: metadata.item_route ?? null,
    local_condition_id: metadata.local_condition_id ?? null,
    global_condition_id: metadata.global_condition_id ?? null,
    item: metadata.item ?? null,
    prior: metadata.prior ?? null,
    qud: metadata.qud ?? null,
    utterance_id: metadata.utterance_id ?? null,
    utterance_family: metadata.utterance_family ?? null,
    utterance_polarity: metadata.utterance_polarity ?? null,
    is_implicative: metadata.is_implicative ?? null,
    consent_given: consent?.consent_given ?? null,
    consent_rt_ms: consent?.rt ?? null,
    instructions_rt_ms: instructions?.rt ?? null,
    ratings_rt_ms: rating?.rt ?? null,
    rating_order: rating?.rating_order ?? null,
    try_rating: rating?.try_rating ?? null,
    completion_rating: rating?.completion_rating ?? null,
    naturalness_rating: rating?.naturalness_rating ?? null,
    demographics_rt_ms: demographics?.rt ?? null,
    age: Number.isFinite(age) ? age : null,
    gender: demographicResponse.gender ?? null,
    education: demographicResponse.education ?? null,
    native_language: demographicResponse.native_language ?? null,
    country: demographicResponse.country ?? null,
  };
}
