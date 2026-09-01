/**
 * Every closed vocabulary the Play screens draw, as **this build** knows it.
 *
 * Nothing the matcher sends is prose. What crosses is a code — a `Term`, a `LivenessReason`,
 * an `UnfilledReason`, a `Prompt` — and the app writes the words for all of them
 * ([ADR-0022](../../../../../docs/adr/0022-kernel-negative-space-and-constant-homes.md),
 * [ADR-0106](../../../../../docs/adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md)).
 * The words themselves are in `components/*Presentation.ts`, one module per vocabulary; what
 * is here is only **which values this build can render**.
 *
 * ## Why the lists are written down at all
 *
 * They are `SOCIAL_TAG_IDS`' shape and exist for its reason: a membership test wearing an
 * array, and the array is what makes the type beside it. Two things then follow that a raw
 * wire union would not give:
 *
 * - **A code with no words does not compile.** Every table below is a
 *   `Readonly<Record<Code, string>>` keyed by one of these unions, so a value added to the
 *   vocabulary and not to the copy fails `pnpm typecheck` rather than rendering blank —
 *   ADR-0106's *"a compiler says so"*.
 * - **A code this build has never seen is representable.** Old app versions live on real
 *   phones for months, so the day the platform adds a ninth term, an eight-month-old build
 *   is holding a string none of these lists contain. That is the state
 *   [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §3 legislates for,
 *   and a type that claimed it could not happen would delete the branch that handles it.
 *
 * **These lists are held to the generated unions by a compiler, in
 * [`mappers/wireVocabulary.ts`](../mappers/wireVocabulary.ts).** The wire boundary keeps
 * `generated/` out of `domain/` and `components/`, so the agreement is asserted at the one
 * layer allowed to read both — a value added, removed or renamed on the contract fails the
 * build there, naming the vocabulary that moved.
 *
 * **No order here is a ranking.** The candidate's terms arrive *ranked by contribution* and
 * the client renders them in the order it was given; these arrays are the vocabulary's own
 * order, which is documentation.
 */

/**
 * The eight terms of Fit.
 *
 * Eight, not seven, and `FAMILIARITY` is **not** among them — it is a modifier. The split
 * between playing style and social vibe is by *relationship* rather than by tag group, which
 * is why they are two terms carrying two different weights.
 */
export const TERMS = [
  'LEVEL_FIT',
  'PREDICTED_BALANCE',
  'INTENT_ALIGNMENT',
  'RELIABILITY',
  'AVAILABILITY_OVERLAP',
  'PLAYING_STYLE',
  'DISTANCE',
  'SOCIAL_VIBE',
] as const;

export type Term = (typeof TERMS)[number];

/** Which side of the searcher a candidate's level sits. */
export const LEVEL_DIRECTIONS = ['ABOVE', 'LEVEL', 'BELOW'] as const;

export type LevelDirection = (typeof LEVEL_DIRECTIONS)[number];

/**
 * The kind of evening a **search** was run for.
 *
 * Two values and never three: `NO_PREFERENCE` is a thing a player may *declare*, not a thing
 * a search may be. The deck has no mode at all, which is a null envelope rather than a third
 * value ([#233](https://github.com/Raketa02/Raketa/issues/233) §6).
 */
export const SEARCH_MODES = ['COMPETITIVE', 'FOR_FUN'] as const;

export type SearchMode = (typeof SEARCH_MODES)[number];

/**
 * The kind of evening a **player** has declared for a sport — **`shared/vocabulary`'s**, and
 * re-exported here so Play still reads its whole vocabulary from one file.
 *
 * It moved out when `player_profile` became the second feature to hold one: it serves the
 * declaration on the profile surface and writes it on `PUT /play-intents/{sport}`, and a Play
 * intent is a root-glossary term rather than this feature's reading of one — `sport.ts`'s
 * argument exactly. What stayed here is what Play does with one: `domain/playMode` maps a
 * declaration to the `SearchMode` a search opens in.
 */
export { PLAY_INTENTS, type PlayIntent } from '@/shared/vocabulary/playIntent';

/**
 * Whose gap made a term stand down: nobody's, yours, or theirs.
 *
 * `NOTHING_FROM_THEM` deliberately covers every reason a record could not be read, because
 * separating them would publish activity recency (ADR-0106 §5).
 */
export const DEGRADED_REASONS = [
  'NOT_YET_ON_THIS_PLATFORM',
  'NOTHING_FROM_YOU',
  'NOTHING_FROM_THEM',
] as const;

export type DegradedReason = (typeof DEGRADED_REASONS)[number];

/** The four adjustments the engine may make after the eight terms are summed. */
export const MODIFIER_CODES = [
  'CALIBRATION_VALUE',
  'FAMILIARITY',
  'WELCOMING_RECORD',
  'RELIABILITY_FLOOR_BREACH',
] as const;

export type ModifierCode = (typeof MODIFIER_CODES)[number];

/**
 * Why this person moved up the list — ten codes, and **no number**.
 *
 * The two silent signals are not here and must never be: a silent move carries points and no
 * code, so there is no name on the value to print.
 */
export const LIVENESS_REASONS = [
  'INTEREST_RECEIVED',
  'PREVIOUS_ACCEPT',
  'ANSWER_RATE_AND_SPEED',
  'RECENT_ACTIVITY',
  'OVERLAP_PROXIMITY',
  'RECIPROCAL_ASYMMETRY',
  'NEWCOMER_LIFT',
  'CHALLENGE_LOAD_SOME',
  'CHALLENGE_LOAD_BUSY',
  'CHALLENGE_LOAD_FULL',
] as const;

export type LivenessReason = (typeof LIVENESS_REASONS)[number];

/**
 * Why this person is in the list **at all** — a union of one.
 *
 * Only an interest lift *admits* anybody. The two reasons that merely reorder stay in the
 * store, so this list is one code long by design and not by accident.
 */
export const INCLUSION_REASONS = ['INTEREST_LIFT'] as const;

export type InclusionReason = (typeof INCLUSION_REASONS)[number];

/** Why a seat on the court could not be filled — the court's own statement of its shortfall. */
export const UNFILLED_REASONS = [
  'NO_CANDIDATE_ABOVE_FLOOR',
  'NO_ADMISSIBLE_COMBINATION',
  'POOL_EXHAUSTED',
  'NO_SHARED_SLOTS',
] as const;

export type UnfilledReason = (typeof UNFILLED_REASONS)[number];

/** Why this four beat the runner-up — one closed code, never a number. */
export const GROUP_REASONS = [
  'EVENEST_ARRANGEMENT',
  'STRONGEST_WEAKEST_SEAT',
  'BEST_AVERAGE_FIT',
  'MOST_SHARED_SLOTS',
  'GROUP_RAPPORT',
] as const;

export type GroupReason = (typeof GROUP_REASONS)[number];

/** The four questions a search may raise. It never blocks: each rides on a response. */
export const PROMPTS = [
  'KEEP_THESE_TIMES',
  'KEEP_THIS_RADIUS',
  'UPDATE_PLAY_INTENT',
  'REFRESH_YOUR_TIMES',
] as const;

export type Prompt = (typeof PROMPTS)[number];

/** How soon a search is asking about. A code, never a sentence — *tonight* is the client's word. */
export const WINDOWS = ['TODAY', 'TOMORROW', 'WEEKEND', 'THIS_WEEK', 'ANY'] as const;

export type Window = (typeof WINDOWS)[number];

/**
 * The re-sorts a client may offer over rows it already holds.
 *
 * The row draws `sorts_available` and vanishes when it is empty, so two of these have words
 * and no reachable surface today. They keep them anyway: the table is exhaustive by type,
 * which is what makes a sort that becomes offerable a copy change of nothing.
 */
export const SORT_OPTIONS = ['BEST_FIT', 'CLOSEST', 'EVENEST', 'MOST_RELIABLE'] as const;

export type SortOption = (typeof SORT_OPTIONS)[number];

/** What a rung of the relaxation ladder asks the player to give up. */
export const RELAXATION_ASKS = ['TIMES', 'RADIUS'] as const;

export type RelaxationAsk = (typeof RELAXATION_ASKS)[number];

/**
 * Which rung of the ladder an offer is.
 *
 * **Letters are never printed.** They are letters rather than numbers precisely so nobody
 * lines them up against a struck rung, and printing either spelling would publish an
 * engine-internal ordering.
 */
export const RUNGS = ['A', 'B', 'C'] as const;

export type Rung = (typeof RUNGS)[number];

/**
 * What a provisional forecast assumed.
 *
 * **The wire spells this an open string**, so unlike every other list here there is no union
 * to be held to — this build renders the assumptions it knows and treats the rest as §3's
 * gap, which is the same answer it would give a ninth term.
 */
export const FORECAST_ASSUMPTIONS = ['EMPTY_SEAT_MATCHES_ITS_PARTNER'] as const;

export type ForecastAssumption = (typeof FORECAST_ASSUMPTIONS)[number];

/**
 * Whom an answer was optimised for — and the reason the builder has to be able to say it.
 *
 * `SEARCHER` is every shortlist and every deal. `GROUP` arrives the moment the searcher
 * hand-seats somebody: from there the engine fills the seats **around** them, and the four it
 * finds may be a worse individual match than an empty court would have given — *"and the
 * screen has to say so rather than leave it to be discovered."*
 *
 * It is on the envelope rather than implied by the request, which is what lets a read-back a
 * month later still say what it was.
 */
export const OPTIMISED_FOR = ['SEARCHER', 'GROUP'] as const;

export type OptimisedFor = (typeof OPTIMISED_FOR)[number];

/**
 * What a seat is **to the searcher** — stated by the engine and never inferred from the side.
 *
 * *"The whole partner/opponent asymmetry hangs on it… and a client deriving it from which half
 * of the court somebody sits on would be a second implementation of a domain rule."* It is
 * also how a court knows **which seat** is yours: `SELF` is the answer, where an index would
 * be an assumption — *seat 0 is you* is a rule the engine states, and a swap moves you across
 * the net. Who you are is a different question and a different source (`GET /users/me`).
 */
export const RELATIONSHIPS = ['SELF', 'PARTNER', 'OPPONENT'] as const;

export type Relationship = (typeof RELATIONSHIPS)[number];
