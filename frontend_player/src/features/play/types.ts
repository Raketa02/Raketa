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
 *
 * **What the rest of the app may reach in Play's state is a Play session, and only that.**
 * `endPlaySession` is what the shell's reset calls, and `usePlaySession` beside it is how that
 * ending is *observed* ([#264](https://github.com/Raketa02/Raketa/issues/264)). `playPreferences`
 * is not here at all, and neither is the origin guard: what a player last searched for and when
 * a line-up is worth a confirmation are Play's own business, and a second feature reading either
 * is the coupling the origin key exists to make unnecessary.
 */

export {
  CONCERN_CAP,
  REASON_CAP,
  WHYFIT_DRAWS,
  selectConcern,
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
  BALANCE_ROW_LABEL,
  CANDIDATE_ACTION_WORD,
  CANDIDATE_POSTER_LABEL,
  DECK_ANSWER_WORDS,
  OVERLAP_ROW_LABEL,
  balanceRowValue,
  levelRow,
  metaLine,
  overlapRowValue,
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
export {
  WITHHELD_SEAT_LINE,
  groupReasonLine,
  seatGuardLine,
  unfilledSeatLine,
} from './components/courtPresentation';
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
} from './components/accessibilityPresentation';
export { balanceLabel, balanceTone, balanceWord } from './components/balancePresentation';
export {
  engineFillStatus,
  poolRankingStatus,
  whyFitHeader,
  type SearchingStatus,
} from './components/searchingPresentation';

/**
 * The three cards, and the parts kit under them.
 *
 * **Three components, not one with a `surface` prop** — after Decision 3 the shapes genuinely
 * differ, and one component would carry `surface === …` at nine sites, which is §G3 #1's own
 * complaint in a new spelling
 * ([`the-play-components.md`](../../../../docs/specs/matchmaking/the-play-components.md) §3).
 * Each takes `(candidate, envelope)` and reads no global state, and **each exports the set of
 * terms it draws**, because that set is a statement about that component and is the one thing
 * that could go stale silently anywhere else.
 *
 * The parts are exported beside them because the court's seat draws a face and the pool's
 * header states a fact, and neither is a card.
 */
export {
  COMPETITIVE_CARD_DRAWS,
  CandidateCard,
  type CandidateCardProps,
} from './components/candidate/CandidateCard';
export {
  CandidateCardSocial,
  SOCIAL_CARD_DRAWS,
  type CandidateCardSocialProps,
} from './components/candidate/CandidateCardSocial';
export { DECK_CARD_DRAWS, DeckCard, type DeckCardProps } from './components/candidate/DeckCard';
export {
  CandidatePhoto,
  type CandidatePhotoBox,
  type CandidatePhotoProps,
} from './components/candidate/CandidatePhoto';
export { CardHead, type CardHeadProps } from './components/candidate/CardHead';

export { FactRow, type FactRowProps } from './components/candidate/FactRow';
export {
  ReasonLine,
  type ReasonLineProps,
  type ReasonLineVariant,
} from './components/candidate/ReasonLine';

/**
 * The two courts, over one drawn object.
 *
 * `Court` is the design system's — a Sport and a box in, the ground, the chrome and the seat
 * **positions** out. These two are the feature's, and they are **two components rather than a
 * flag on one**: they share every number and no behaviour, so read-only faces and pressable
 * seats are different children
 * ([`the-play-components.md`](../../../../docs/specs/matchmaking/the-play-components.md) §4).
 * The rules under them — a side that follows you across the net, a seat nobody may vacate, and
 * what a tap means — are `domain/lineup`'s, exported below.
 */
export { CourtBuild, type CourtBuildProps } from './components/court/CourtBuild';
export {
  CourtMini,
  type CourtFaceOccupant,
  type CourtMiniProps,
} from './components/court/CourtMini';
export {
  CourtSeat,
  type CourtSeatOccupant,
  type CourtSeatProps,
} from './components/court/CourtSeat';
export { seatName } from './components/court/seatName';

export {
  SEAT_PLACES,
  seatIsClearable,
  seatIsLocked,
  seatPlaces,
  tapSeat,
  type BuildSeat,
  type SeatGuard,
  type SeatPlace,
  type SeatTap,
  type SwapState,
} from './domain/lineup';

export type { Candidate, LikelyRange, PlayerCard, SearchEnvelope } from './domain/candidate';

/**
 * A Play session: the working copy of the week and the line-up on it, and the one function
 * that ends both.
 *
 * `endPlaySession` is called by `resetShellStack` and by nothing else, which is what makes the
 * shell's one navigation move the **definition** of a session ending rather than a line
 * somebody must remember on every exit.
 *
 * **`usePlaySession` is exported because that definition lives in another feature.** The rule
 * is stated here and enforced by the shell, so the shell's own suite is where it has to be
 * checked — and a rule nothing can observe is a rule that stops being true without a symptom,
 * which is the failure the shell was built to avoid in the first place. It is the same
 * concession `features/shell/types.ts` already makes for `PLACEHOLDER_COPY`, *"read outside
 * this feature by one thing: the test harness."*
 *
 * The honest cost is that the store's writers — `enter`, `seat`, `toggleWeekCell` — are
 * reachable from outside too. Nothing calls them from outside and nothing should: seating
 * somebody is an act on the pool, and a second feature doing it would be building a line-up
 * against an origin it cannot see. If a caller ever appears, the answer is a narrower export,
 * not a wider one.
 */
export { endPlaySession, usePlaySession } from './store/playSession.store';
