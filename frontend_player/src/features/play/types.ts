/**
 * The Play feature's only public surface.
 *
 * It begins as a **copy deck and the rules over it**: every sentence the Play screens write
 * from a closed code, plus the one rule that decides which of them a surface says
 * ([#262](https://github.com/Raketa02/Raketa/issues/262),
 * [`the-words.md`](../../../../docs/specs/matchmaking/the-words.md)). The screens that draw
 * them arrive after it, which is the order the prefactor exists to make possible: a card is
 * assembled from sentences that already have one home, rather than from templates inlined in
 * six components.
 *
 * Nothing outside this folder reads anything not re-exported here — ESLint blocks the deep
 * paths.
 */

export {
  COMPETITIVE_CARD_DRAWS,
  DECK_CARD_DRAWS,
  REASON_CAP,
  SOCIAL_CARD_DRAWS,
  WHYFIT_DRAWS,
  selectReasons,
  type ReasonInput,
  type ReasonSelection,
} from './domain/reasonSelection';

export type {
  AvailabilityOverlapEvidence,
  DistanceEvidence,
  Evidence,
  IntentAlignmentEvidence,
  LevelFitEvidence,
  PlayingStyleEvidence,
  PredictedBalanceEvidence,
  ReliabilityEvidence,
  ScoredTerm,
  SocialVibeEvidence,
  TagPair,
} from './domain/evidence';

export type {
  DegradedReason,
  ForecastAssumption,
  GroupReason,
  InclusionReason,
  LevelDirection,
  LivenessReason,
  ModifierCode,
  PlayIntent,
  Prompt,
  RelaxationAsk,
  Rung,
  SearchMode,
  SortOption,
  Term,
  UnfilledReason,
  Window,
} from './domain/vocabulary';

export { termLabel } from './components/termPresentation';
export { reasonLine } from './components/reasonPresentation';
export { concernLine } from './components/concernPresentation';
export {
  levelRow,
  metaLine,
  type LevelRowFacts,
  type MetaLineFacts,
} from './components/playerCardPresentation';
export { NOT_ON_THIS_PLATFORM_FOOTER, degradedLine } from './components/degradedPresentation';
export {
  MODIFIERS_HEADING,
  TERM_SUBTOTAL_LABEL,
  adjustmentsTotal,
  modifierLine,
} from './components/modifierPresentation';
export {
  WHAT_ELSE_MOVED_YOU_HERE,
  inclusionLine,
  livenessLine,
} from './components/livenessPresentation';
export { groupReasonLine, unfilledSeatLine } from './components/courtPresentation';
export {
  PROMPT_CLOSER,
  REFRESH_YOUR_TIMES_BODY,
  promptCopy,
  promptSuppression,
  type PromptCopy,
  type RaisedPrompt,
} from './components/promptPresentation';
export {
  forecastAssumption,
  modeWord,
  relaxationOffer,
  sortLabel,
  windowLabel,
} from './components/searchPresentation';
export {
  CANDIDATE_ACTIONS,
  PLAY_LIVE_REGIONS,
  SEAT_PLACES,
  SWAP_TOGGLE_LABEL,
  availabilityDiffCellLabel,
  candidateActionLabel,
  candidateCardLabel,
  clearSeatLabel,
  courtSummaryLabel,
  deckAnswerLabels,
  fitSentence,
  provisionalForecastAnnouncement,
  seatLabel,
  whyFitRowLabel,
  whyFitSheetLabel,
  type CandidateAction,
  type CandidateCardFacts,
  type DeckAnswerLabels,
  type PlayLiveRegion,
  type SeatOccupant,
  type SeatPlace,
} from './components/accessibilityPresentation';
export { balanceLabel, balanceTone, balanceWord } from './components/balancePresentation';
export {
  engineFillStatus,
  poolRankingStatus,
  whyFitHeader,
  type SearchingStatus,
} from './components/searchingPresentation';
