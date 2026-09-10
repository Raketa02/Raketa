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
export { WITHHELD_SEAT_LINE, unfilledSeatLine } from './components/courtPresentation';
export {
  PROMPT_CLOSER,
  REFRESH_YOUR_TIMES_BODY,
  promptCopy,
  promptSuppression,
  type PromptCopy,
} from './components/promptPresentation';
export type { RaisedPrompt } from './domain/raisedPrompt';
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
export { CourtMini, type CourtMiniProps } from './components/court/CourtMini';
export {
  CourtSeat,
  type CourtSeatOccupant,
  type CourtSeatProps,
} from './components/court/CourtSeat';
export {
  SeatFace,
  seatBox,
  type CourtFaceOccupant,
  type SeatFaceProps,
} from './components/court/seatFace';
export { seatWho, type SeatWho } from './components/court/seatWho';

export {
  SEAT_PLACES,
  seatIsClearable,
  seatIsLocked,
  seatPlaces,
  tapSeat,
  type BuildSeat,
  type SeatPlace,
  type SeatTap,
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

/**
 * **Find a game** — the screen behind ⚡, and the first Play surface that is not only words.
 *
 * Named by `src/app/(app)/(tabs)/play/index.tsx` and by nothing else. It replaced the shell's
 * stub, which is why the title moved out of `shellCopy` with it: a placeholder holds a tab's
 * words only for as long as the tab has no screen
 * ([#268](https://github.com/Raketa02/Raketa/issues/268)).
 */
export { FindAGameScreen } from './components/FindAGameScreen';

/**
 * **Match me** — the deck, and the second Play screen.
 *
 * Named by `src/app/(app)/(tabs)/play/deck.tsx` and by nothing else. One person at a time, two
 * named buttons and no swipe, and a long press that opens `SH.whyfit`
 * ([#270](https://github.com/Raketa02/Raketa/issues/270)).
 */
export { DeckScreen } from './components/DeckScreen';

/**
 * The whole Fit calculation, in a sheet — and the one surface allowed to draw a term row.
 *
 * Exported because three surfaces open it: the deck's long press, and each of the pool's two
 * cards on a plain press ([#273](https://github.com/Raketa02/Raketa/issues/273)). It takes
 * `(candidate, envelope)` and reads no global state, which is what lets it name no mode on the
 * deck — `SearchEnvelope.mode` is null exactly there.
 */
export { WhyFitSheet, type WhyFitSheetProps } from './components/whyfit/WhyFitSheet';

/**
 * **The builder** — the court, and the three ways to fill it.
 *
 * Named by `src/app/(app)/(tabs)/play/builder.tsx` and by nothing else. The route validates its
 * one param before this screen reads it, because an origin `search_id` becomes a request body
 * and a Query key ([#271](https://github.com/Raketa02/Raketa/issues/271)).
 */
export { BuilderScreen, type BuilderScreenProps } from './components/BuilderScreen';
export {
  parseBuilderRouteParams,
  parsePoolRouteParams,
  type BuilderRouteParams,
  type PoolRouteParams,
} from './schemas/routeParams';

/**
 * **The pool** — an honest placeholder until
 * [#272](https://github.com/Raketa02/Raketa/issues/272) fills it in.
 *
 * Named by `src/app/(app)/(tabs)/play/pool.tsx`. It exists now because the builder routes
 * every remedy here, and a court naming a remedy with nowhere to go is worse than one that
 * said nothing.
 */
export { PoolScreen, type PoolScreenProps } from './components/PoolScreen';

/**
 * The forecast, as the builder holds it — **every way round, each with its own number**, and
 * the rule that turns a swap into a selection rather than a request.
 *
 * Exported for the suites that drive the court, and for the pool
 * ([#272](https://github.com/Raketa02/Raketa/issues/272)), whose *Evenest* sort reads a
 * forecast and whose header draws one. Nothing here computes a forecast number; a check on
 * that is a check for arithmetic, and there is none.
 */
export {
  arrangementFor,
  courtSeating,
  courtWithYou,
  currentArrangement,
  evenestArrangement,
  partnerOf,
  seatedIds,
  seatingOf,
  seatsFilled,
  shortfallBySeat,
  swapSeats,
  type Arrangement,
  type ArrangementSeat,
  type Forecast,
  type Seating,
  type SeatedCourt,
  type SeatOccupancy,
  type SeatedSeat,
} from './domain/forecast';

export {
  lineupStanding,
  withheldSeats,
  type Lineup,
  type LineupStanding,
  type OriginSearch,
  type PlayOrigin,
  type SearchRecord,
} from './domain/lineup';

export { optimisedForLine } from './components/courtPresentation';

/**
 * The builder's own words, exported for its suite for `findAGamePresentation`'s reason: an
 * assertion spelling *Even it out* as a string literal is a red build for the ticket that
 * rewords it. Nothing in `src/` outside this feature reads any of them.
 */
export {
  ALREADY_EVENEST,
  EVEN_IT_OUT_LABEL,
  PICK_PLAYERS_LABEL,
  PROVISIONAL_WORD,
  START_OVER_LABEL,
  SWAP_HINT,
  builderTitle,
  fillSeatsLabel,
  forecastHeading,
} from './components/builderPresentation';

/**
 * Play's two ways through the tab, as one control.
 *
 * Both screens draw it, and it is **not** the shell's: the count on it is filtered by the
 * sport on screen, and the sport is a Play screen's own fact — which is also why the tab bar
 * carries no badge (`TabBar`).
 */
export { PlaySegment, type PlaySegmentProps, type PlaySurface } from './components/PlaySegment';

/**
 * What stands between a player and a search, and the words the screen says about it.
 *
 * Exported for the suites that drive the screen through the real route tree: an assertion
 * spelling *Search* or *Find a game* as a string literal is a red build for the ticket that
 * rewords it, which is the concession `shellCopy`'s `PLACEHOLDER_COPY` already makes and for
 * the same reason. No screen outside this feature reads any of them.
 *
 * `modeControlLabel` joined them for the **shell's** suite, which is the one place a rule
 * spanning two tabs can be checked: *a declaration changed on You does not move the mode Play
 * opens in* ([#296](https://github.com/Raketa02/Raketa/issues/296)) is a fact about Play and
 * `player_profile` together, and neither of those two features may import the other.
 */
export {
  FIND_A_GAME_TITLE,
  WEEK_CHANGED_FROM_PROFILE,
  declarationTitle,
  intentLabel,
  modeControlLabel,
  modeLabel,
  searchControlLabel,
} from './components/findAGamePresentation';
export { findAGameStanding, type FindAGameStanding } from './domain/findAGame';

/**
 * The deck's own words, exported for its suite for the reason above — and for one more: three
 * of them are what a **rule** looks like on screen. *There is no `Show them again`* is only
 * checkable against the sentences that replaced it, and the empty states' split is only
 * checkable by asking which title was drawn.
 */
export {
  DEAL_AGAIN_LABEL,
  DECK_FOOTER,
  MATCH_ME_TITLE,
  NOBODY_IN_RANGE_TITLE,
  SEEN_EVERYBODY_TITLE,
  WIDEN_IN_YOU,
  interestToast,
  mutualToast,
  outgoingYeses,
  passedToast,
} from './components/deckPresentation';
export { poolDescription } from './components/searchPresentation';
export { deckStanding, type DeckDeal, type DeckStanding } from './domain/deckHand';
export { whyFitColumn, type WhyFitColumn, type WhyFitRow } from './domain/whyFitColumn';
