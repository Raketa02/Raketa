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

/**
 * **The evidence vocabulary's own lists**, widened for the second feature that narrows a code
 * against them.
 *
 * ADR-0106 holds that this vocabulary is *contract* — the codes cross and the client writes the
 * words — and `challenges` now reads the same eight evidence variants off its own narrower
 * schema (ADR-0143 §5). Narrowing a served code needs the list at **runtime**, so the types
 * below are not enough on their own.
 *
 * They are widened rather than copied, and rather than moved to `shared/`: a second `TERMS`
 * beside this one is the way an eighth term reaches one feature and not the other, while a move
 * is a refactor of every file in this feature that [#361](https://github.com/Raketa02/Raketa/issues/361)
 * did not ask for and `CLAUDE.md` warns against making on a second caller alone. The day a third
 * feature reads them is the day that move is owed.
 */
export {
  DEGRADED_REASONS,
  FORECAST_ASSUMPTIONS,
  LEVEL_DIRECTIONS,
  SEARCH_MODES,
  TERMS,
} from './domain/vocabulary';

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
  /**
   * **The Player Score's name and the stake's two clauses**, widened for the challenge screen.
   *
   * That screen draws the same figure under the same rule — the published one, omitted where the
   * platform has watched nothing, never `0` — and speaks the same two stake clauses under
   * `stakeOnACard`'s. Re-spelling either would put the denominator and the signed format in two
   * places, and a listener would eventually hear one card's figure out of a hundred and
   * another's out of nothing.
   */
  PLAYER_SCORE_BLOCK,
  balanceRowValue,
  levelRow,
  metaLine,
  overlapRowValue,
  stakeClauses,
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
export {
  balanceLabel,
  balanceReading,
  balanceTone,
  balanceWord,
} from './components/balancePresentation';
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
  SEAT_NAME_LETTERS,
  SeatCaption,
  SeatFace,
  seatBox,
  seatCaptionName,
  type CourtFaceOccupant,
  type SeatCaptionProps,
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

export type {
  AtStake,
  Candidate,
  LikelyRange,
  PlayerCard,
  SearchEnvelope,
} from './domain/candidate';

/**
 * **What a counted game would move, and the rule about when a card may print it** — widened to
 * this surface's second reader.
 *
 * `AtStake` above and these two below cross for the challenge screen, which draws the same pair
 * of figures under the same rule: *a win against one named person isn't a thing that exists
 * until the other three seats are known*, so a doubles court draws neither box
 * ([ADR-0143](../../../docs/adr/0143-the-challenge-is-the-gate-and-the-card-is-recomputed-for-the-reader.md)
 * §5, which ships `at_stake` on `challenges`' own narrower schema and cites *the card's own rule
 * unchanged*).
 *
 * They are widened rather than re-spelled on the third-caller rule `recoveryMessage` already
 * states: a second `seats === 2` beside this one is the third answer to a question that has one,
 * and the figures' format is `formatSignedLevel`'s either way. What `challenges` **does** spell
 * for itself is its wire schema, because the backend spelled a second one there and a client
 * mapping a narrower contract through a wider feature's mapper would be reading a shape it was
 * not sent.
 */
export { stakeOnACard } from './domain/atStake';
export { StakeBoxes, type StakeBoxesProps } from './components/candidate/StakeBoxes';

/**
 * **The two joins between a selection and its sentences**, widened to their second caller.
 *
 * `selectReasons` and `selectConcern` already cross this seam as rules, and they answer in
 * `ScoredTerm`s rather than in words — so a second surface reading them either re-spells the
 * `switch` that turns a selection into lines, or shares this. The arm a copy forgets is `hidden`,
 * whose whole job is not printing the blank row the selection exists to prevent.
 *
 * `concernLines` takes the two lists rather than a `Candidate`, because the challenge screen's
 * card holds a narrower pairing and no candidate at all.
 */
export { concernLines, reasonLines } from './components/candidate/candidateFacts';

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
 * **Players** — the deck, and the whole of the second tab.
 *
 * Named by `src/app/(app)/(tabs)/players.tsx` and by nothing else. It was *Match me*, the second
 * Play screen, until [ADR-0169](../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §1 gave it a column of its own. One person at a time, two named buttons and no swipe, and a
 * long press that opens `SH.whyfit` ([#270](https://github.com/Raketa02/Raketa/issues/270)).
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

/**
 * **⚡ Fill the seats, pressed on a challenge** — the act, where `features/challenges/` owns the
 * control ([`the-loop-components.md`](../../../../docs/specs/the-loop/the-loop-components.md)
 * §4.2).
 *
 * It is this feature's because a fill is a search: it mints one, records it, and binds a line-up
 * to it. It borrows `playSession` rather than handing back a line-up of its own, so there is one
 * store and one definition of a line-up and **no fork of `domain/lineup.ts`** — which is the
 * whole reason the builder it pushes needs nothing passed to it.
 *
 * `CompletingChallenge` crosses with it because the challenge screen is the only surface that can
 * state one: who has already said yes is a fact about a court, and the fill's own answer returns
 * those people as ordinary candidate rows that say nothing about a challenge.
 */
export { useFillChallengeSeats } from './hooks/useBuilder';
export type { CompletingChallenge } from './domain/lineup';

/**
 * **Whom the reader has said yes to** — the deck's read, and the rule that asks it one person at
 * a time — widened to the challenge screen
 * ([ADR-0169](../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §8).
 *
 * The invitee's line — *You said yes to Karol on Players* — is drawn when the organiser is in the
 * reader's outgoing list for the challenge's sport, and that list is this feature's: a deck yes
 * is `POST /interest`, its read is `GET /interest`, and `challenges` holding a second query over
 * the same route would be two cache entries for one answer. The hook crosses rather than the
 * map, so the one entry is shared with the pool and moves on a tap's own reply; the rule
 * crosses with it so `sport` and `playerId` are compared in one place.
 */
export { useOutgoingInterest } from './hooks/useInterest';
export { saidYesTo } from './domain/outgoingInterest';
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
  USE_MATCHMAKING_LABEL,
  builderTitle,
  forecastHeading,
} from './components/builderPresentation';

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
 * The deck's own words, exported for its suite for the reason above — and for one more: several
 * of them are what a **rule** looks like on screen. *Show them again* on one ending and not the
 * other is only checkable by asking which title was drawn beside which button; the counter's
 * arithmetic and the chip's presence rule are only checkable against the sentences they print.
 */
export {
  DEAL_AGAIN_LABEL,
  NOBODY_IN_RANGE_TITLE,
  PANE_LABEL,
  RADAR_LINE,
  SEEN_EVERYBODY_TITLE,
  SHOW_THEM_AGAIN_LABEL,
  STAMP_WORDS,
  TRY_THE_RADAR_LABEL,
  WIDEN_IN_YOU,
  deckCounter,
  interestAnnouncement,
  mutualToast,
  passedAnnouncement,
  seenEverybodyLine,
  wantToPlayYouChip,
} from './components/deckPresentation';
export {
  ACCEPT_GLYPH,
  DECK_HINT_LINE,
  deckMetaLine,
  deckTiles,
  quotedIntro,
} from './components/deckCardPresentation';
export { poolDescription } from './components/searchPresentation';
export {
  cardsLeft,
  deckStanding,
  type DealtCard,
  type DeckDeal,
  type DeckStanding,
} from './domain/deckHand';
export { whyFitColumn, type WhyFitColumn, type WhyFitRow } from './domain/whyFitColumn';
