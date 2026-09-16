/**
 * A ranked row and the envelope over it, as the three cards and the why-fit sheet hold them.
 *
 * The **first** mapper in this feature to cross a candidate. `searchMappers` crosses the *ask*
 * and the questions a search raised; this crosses the answer, and it arrives with the deck
 * ([#270](https://github.com/Raketa02/Raketa/issues/270)) because the deck is the first
 * surface that draws a person.
 *
 * ## Every narrowing, and §3 decides each one separately
 *
 * The generated unions say a served code is always one this build knows. That is true of the
 * document these types were generated from and false of a phone that has not been updated in
 * eight months, which is the state
 * [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §3 legislates for — so
 * every closed vocabulary is a **membership test**, exactly as `toSocialTagId` is, and the
 * placement decides what an unknown value costs:
 *
 * | | |
 * | --- | --- |
 * | a **social tag** | dropped — §3's own ruling, and a chip with no words is nothing |
 * | a **liveness reason**, an **inclusion reason**, a **concern** | dropped — each is a
 *   selection out of a longer list, and no screen states a total one belongs to |
 * | a **scored term** and its **evidence** | **kept**, with `null` where the code is unknown |
 * | a **stood-down term** and its **reason** | **kept**, the same way |
 * | a **photo verdict** | dropped — and the drop is the point, not a cost |
 *
 * **The verdict's row is the one where a drop is the safe answer rather than the lossy one.**
 * Every other narrowing here trades a fact for silence and the placement decides what that
 * costs; this one trades an unreadable code for *nobody looked*, which is a state the contract
 * already has and the card already draws — as nothing. A verdict minted after this build
 * shipped could be anything, including a refusal, so reading it as a pass is the one reading
 * that could put a mark on a photograph the platform had doubts about. It is
 * `player_profile`'s fold turned round: an upload with no readable verdict warns about
 * nothing, and a card with no readable verdict **marks** nothing.
 *
 * The two term rows are the ones that matter, and neither is a drop. The why-fit sheet
 * prints **totals these rows belong to** — a sub-total the column must sum to, a derived
 * `applied`, and a count of live terms in its own header — so a row dropped here does not go
 * missing quietly: its contribution reappears as an adjustment nobody made, which is #233 §4's
 * own objection, *"a wrong number that looks like a plausible one"*. So the row is kept and
 * the gap lands **in place**, exactly as §3 and ADR-0106 §6 specify: *"an unrenderable
 * evidence variant leaves its row's weight, value and contribution standing — those are
 * numbers, not codes"*, and an unknown `Term` takes the whole row's label
 * (`domain/evidence`).
 *
 * ## What is not carried, and why each absence is a decision
 *
 * **`photo_id`.** The URL is the only address a stranger's photograph has —
 * `GET /photos/{id}` refuses somebody else's on purpose — so an id here would be a field with
 * no reader and an invitation to store one.
 *
 * **`would_be_forecast` and `strands`.** No surface draws either; a DTO with fields nobody
 * reads is a contract nobody is checking. `at_stake`, `counted_games` and `last_five` were on
 * that list until the blocks that print them were built
 * ([#312](https://github.com/Raketa02/Raketa/issues/312)), and they cross now for the same
 * reason `player_score` started to.
 *
 * ## `last_five` is the one narrowing that takes the whole field with it
 *
 * A fifth row for the table above, and it is neither of the two answers in it. Every other
 * closed vocabulary here is narrowed **per value** — a tag is dropped, a term keeps its row
 * with a `null` in it — because the surface either states no total the value belongs to or
 * states one the gap can stand in.
 *
 * The run of form is neither. **Its length is itself a statement**: five squares means five
 * counted results and three means three, *"and the client draws the gap rather than filling
 * it"*. So an outcome this build cannot read has nowhere to go. Dropping it would shorten the
 * run and claim a game fewer than the platform counted; keeping it as a `null` would ask the
 * card to draw a third kind of square, which is a design nobody has taken and a state the
 * spoken reading (*three of the last five won*) cannot count either way.
 *
 * So the **field** is omitted, and the block is hidden rather than drawn wrong — which is what
 * every absence on this card already does. Nothing about the record disappears with it:
 * `counted_games` is a separate figure and goes on printing, so *the honesty figure* survives a
 * run this build can only half read. It is `toRelaxedAsk`'s answer one register over — *a
 * `RADIUS` rung with no radius has no sentence left at all* — rather than `matchedInFull`'s,
 * because there is no second thing here for a bit to switch between.
 *
 * **`withheld` rows carry no person**, so they cannot become a candidate. They are dropped
 * here and are **not** counted as unreadable: a withheld row is a row this build read
 * perfectly and the product has since agreed not to show. Drawing the fact is the *court's*
 * job and it derives it as a set difference against the seats a line-up holds
 * ([#271](https://github.com/Raketa02/Raketa/issues/271)); a fresh deal never carries one.
 */

import type { components } from '@/generated/schema';
import { SOCIAL_TAG_IDS, type SocialTagId } from '@/shared/vocabulary/socialTags';
import type { WeekCell } from '@/shared/vocabulary/week';
import { toWeekCells } from '@/features/player_profile/types';

import type {
  Candidate,
  DegradedTerm,
  Modifier,
  RelaxedAsk,
  RungOffer,
  SearchEnvelope,
} from '../domain/candidate';
import type { Evidence, ScoredTerm, TagPair } from '../domain/evidence';
import {
  DEGRADED_REASONS,
  GAME_RESULTS,
  INCLUSION_REASONS,
  LEVEL_DIRECTIONS,
  LIVENESS_REASONS,
  MODIFIER_CODES,
  OPTIMISED_FOR,
  PHOTO_REVIEWS,
  PLAY_INTENTS,
  RELAXATION_ASKS,
  RUNGS,
  SEARCH_MODES,
  SORT_OPTIONS,
  TERMS,
  WINDOWS,
  type DegradedReason,
  type GameResult,
  type InclusionReason,
  type LevelDirection,
  type LivenessReason,
  type ModifierCode,
  type OptimisedFor,
  type PhotoReview,
  type PlayIntent,
  type RelaxationAsk,
  type Rung,
  type SearchMode,
  type SortOption,
  type Term,
  type Window,
} from '../domain/vocabulary';

type ShortlistResponse = components['schemas']['ShortlistResponse'];
type CandidateSchema = components['schemas']['CandidateSchema'];
type ScoredTermSchema = components['schemas']['ScoredTermSchema'];
type WireEvidence = ScoredTermSchema['evidence'];
type WireTagPair = components['schemas']['TagPair'];
type WireDegradedTerm = components['schemas']['DegradedTermSchema'];
type WireModifier = components['schemas']['ModifierSchema'];
type WireRungOffer = components['schemas']['RungOfferSchema'];

/**
 * One answer, as the screens over it hold it: the envelope, and the rows that survived.
 *
 * Named for the record rather than for the surface, because three routes mint one and the
 * shape is identical across them — `POST /searches`, `POST /lineups` and `POST /deck`.
 */
export interface RankedList {
  readonly envelope: SearchEnvelope;
  readonly candidates: readonly Candidate[];
}

export function toRankedList(response: ShortlistResponse): RankedList {
  return {
    envelope: toSearchEnvelope(response),
    candidates: response.candidates.flatMap((row) =>
      row.withheld === true ? [] : [toCandidate(row as CandidateSchema)],
    ),
  };
}

/**
 * The facts about the search itself.
 *
 * `myAreaCode` is folded on **exactly when the wire carries one**, and that is the whole of
 * what this function decides beyond a renaming. The envelope's code is the searcher's area
 * *as the search ran on it*, and a search recorded before the backend kept one omits it
 * ([#279](https://github.com/Raketa02/Raketa/issues/279)) — so the key is left off rather
 * than set to a sentinel, because an empty string compares unequal to every real code and
 * would quietly mean *never in your area* (`domain/candidate`).
 *
 * A `mode` outside this build's two becomes `null`, which is the deck's own value and reads
 * as *this answer names no mode* — the honest reading, and the one place where guessing would
 * put a weight vector's name on a sheet that was priced under another.
 */
export function toSearchEnvelope(response: ShortlistResponse): SearchEnvelope {
  const mode = response.search.mode;
  const pool = response.search.pool;

  return {
    searchId: response.search.search_id,
    mode: mode == null || !KNOWN_MODES.has(mode) ? null : mode,
    ...(response.search.my_area_code === undefined
      ? {}
      : { myAreaCode: response.search.my_area_code }),
    pool: {
      radiusKmUsed: pool.radius_km_used,
      playersInRange: pool.players_in_range,
      window: toWindow(pool.window) ?? null,
      // The deal's two counts, kept omitted where the answer is not a deal: a nought is a
      // measured nought and crosses, and an absence is *this surface has no such number*.
      ...(pool.remaining === undefined ? {} : { remaining: pool.remaining }),
      ...(pool.want_to_play_you === undefined ? {} : { wantToPlayYou: pool.want_to_play_you }),
    },
    radiusClamp: response.search.radius_clamp,
    optimisedFor: toOptimisedFor(response.search.optimised_for) ?? null,
    // A sort this build has no words for is **dropped**: the row is a selection out of a
    // longer vocabulary and states no total, so a chip nobody could read is nothing to draw.
    sortsAvailable: response.search.sorts_available.flatMap((sort) => toSortOption(sort) ?? []),
    rungOffers: toRungOffers(response.search.rung_offers),
    rulesetVersion: response.search.ruleset_version,
    engineVersion: response.search.engine_version,
  };
}

/**
 * The ladder, with **`null` kept as `null`**.
 *
 * That is the whole of what this function has to be careful about: `null` is *the offers were
 * never computed, because the list cleared five* and `[]` is *they were computed and there is
 * nothing left to offer*. The falsifier is one against the other, so `?? []` here would delete
 * the difference between a long list and a terminal one and hand the screen one empty state
 * where the contract has two.
 */
function toRungOffers(offers: WireRungOffer[] | null): readonly RungOffer[] | null {
  return offers == null ? null : offers.flatMap((offer) => toRungOffer(offer) ?? []);
}

/**
 * One priced rung, or nothing.
 *
 * Three narrowings and each is §3's **drop**, because an offer is a control rather than a row
 * in a total: an unreadable rung has nothing to cite when it is taken, an unreadable ask has
 * no label, and a `RADIUS` rung with no radius has no sentence at all — its label *is* that
 * number. The **window** is the one that stays, as a `null`: it is a clause on a control whose
 * count and label are both still true without it.
 */
function toRungOffer(offer: WireRungOffer): RungOffer | undefined {
  const rung = KNOWN_RUNGS.has(offer.rung) ? (offer.rung as Rung) : undefined;
  const ask = KNOWN_ASKS.has(offer.ask) ? (offer.ask as RelaxationAsk) : undefined;
  if (rung === undefined || ask === undefined) return undefined;

  const relaxed = toRelaxedAsk(ask, offer.radius_km);
  if (relaxed === undefined) return undefined;

  return {
    rung,
    candidatesAboveFloor: offer.candidates_above_floor,
    window: toWindow(offer.window) ?? null,
    slot: toAddedCell(offer.slot),
    ...relaxed,
  };
}

/** The pair the label is written from — and `undefined` where half of it is missing. */
function toRelaxedAsk(ask: RelaxationAsk, radiusKm: number | undefined): RelaxedAsk | undefined {
  if (ask === 'TIMES') return { ask };
  return radiusKm === undefined ? undefined : { ask, radiusKm };
}

/**
 * The cell a times rung would add — **kept as a `null`, never as a dropped offer.**
 *
 * That is the opposite of the radius one line up, and the difference is what each half is for.
 * A radius rung's whole label *is* its number, so a missing one leaves no sentence to draw. A
 * cell is in no sentence at all: it is the tick the grid draws two screens back
 * ([#283](https://github.com/Raketa02/Raketa/issues/283)), and the control's label and count
 * are both true without it. So an absent or unreadable cell costs the tick and nothing else —
 * `window`'s own answer one field over.
 */
function toAddedCell(slot: WireRungOffer['slot']): WeekCell | null {
  const [cell] = slot === undefined ? [] : toWeekCells([slot]);
  return cell ?? null;
}

export function toCandidate(row: CandidateSchema): Candidate {
  return {
    playerId: row.player_id,
    fit: row.fit,
    // Omitted rather than zero when the distance term stood down — the two spellings of
    // absence, and what lets *Closest* sort a stood-down row last instead of first.
    ...(row.distance_km === undefined ? {} : { distanceKm: row.distance_km }),
    card: {
      name: row.player_card.name,
      ...(row.player_card.photo_url === undefined ? {} : { photoUrl: row.player_card.photo_url }),
      // Omitted where nobody looked, and omitted again where the verdict is a word this
      // build has never seen — the two collapse, because both are *this card cannot say a
      // check passed* and only a pass draws anything.
      ...photoReview(row.player_card.review),
      areaCode: row.player_card.area_code,
      socialTags: row.player_card.social_tags.flatMap((tag) => toSocialTagId(tag) ?? []),
      level: row.player_card.level,
      band: row.player_card.band,
      range: { low: row.player_card.range.low, high: row.player_card.range.high },
      // The one line they wrote, verbatim, and omitted where they wrote none — the contract
      // never sends an empty string, and the card closes the gap rather than quoting one.
      ...(row.player_card.intro === undefined ? {} : { intro: row.player_card.intro }),
      // Omitted rather than zero where the platform has watched nothing — the same two
      // spellings of absence as `distance_km`, and what lets *Most reliable* sort a player
      // with no record last instead of first.
      ...(row.player_card.player_score === undefined
        ? {}
        : { playerScore: row.player_card.player_score }),
      // The other two thirds of the record block, on the same spelling: omitted where the
      // platform watched nothing, and never a nought it would have to be told not to print.
      ...(row.player_card.counted_games === undefined
        ? {}
        : { countedGames: row.player_card.counted_games }),
      ...lastFive(row.player_card.last_five),
    },
    terms: row.terms.map(toScoredTerm),
    // A concern is joined back to a row by its term, so one this build cannot name could not
    // be marked in place even if it were kept — and the sheet states no total it belongs to.
    concerns: row.concerns.flatMap((concern) => toTerm(concern.term) ?? []),
    livenessReasons: row.liveness_reasons.flatMap((reason) => toLivenessReason(reason) ?? []),
    ...inclusion(row.inclusion_reason),
    degradedTerms: row.degraded_terms.map(toDegradedTerm),
    // A modifier row prints a sentence and a figure, and **nothing sums the list** — so an
    // unknown code has no total to distort, and a row with no words is nothing to draw.
    modifiers: row.modifiers.flatMap((modifier) => toModifier(modifier) ?? []),
    // Two figures, carried as served. The client never derives one from the other and never
    // supplies the loss's minus — `win_delta > 0 > loss_delta` is the server's invariant.
    ...(row.at_stake === undefined
      ? {}
      : { atStake: { winDelta: row.at_stake.win_delta, lossDelta: row.at_stake.loss_delta } }),
  };
}

/**
 * The run of form, **whole or not at all** — see the module note.
 *
 * **Absence gets one spelling here and nowhere after it.** The contract omits the field for
 * *nothing of theirs has been counted and agreed* and never sends an empty list, but an empty
 * one would otherwise arrive downstream as a run with no squares in it — a second absence for
 * every reader to remember. So it is collapsed at the boundary, and the block and the spoken
 * clause both ask the one question the rest of this card asks: is the field there.
 */
function lastFive(served: readonly string[] | undefined): {
  readonly lastFive?: readonly GameResult[];
} {
  if (served === undefined || served.length === 0) return {};
  const read = served.flatMap((result) => toGameResult(result) ?? []);
  return read.length === served.length ? { lastFive: read } : {};
}

/**
 * The verdict, **kept omitted** — the second field on this card that is absent rather than
 * null, and the one whose absence is a design rather than a spelling.
 *
 * `inclusion`'s shape one function down, and a different argument under it. An inclusion
 * reason this build cannot read is dropped because no screen states a total it belongs to; a
 * verdict this build cannot read is dropped because **the absence is already a state**, and
 * it is the state that draws nothing. There is no gap to keep in place here: the mark is not a
 * row in any total, and *nobody looked* and *nobody here can read what they concluded* are the
 * same sentence for a card that will say nothing either way.
 */
function photoReview(served: CandidateSchema['player_card']['review']): {
  readonly photoReview?: PhotoReview;
} {
  if (served === undefined) return {};
  const known = KNOWN_PHOTO_REVIEWS.has(served) ? (served as PhotoReview) : undefined;
  return known === undefined ? {} : { photoReview: known };
}

/** The one field that is omitted rather than nulled, kept omitted. */
function inclusion(reason: CandidateSchema['inclusion_reason']): {
  readonly inclusionReason?: InclusionReason;
} {
  if (reason === undefined) return {};
  const known = KNOWN_INCLUSION.has(reason) ? (reason as InclusionReason) : undefined;
  return known === undefined ? {} : { inclusionReason: known };
}

/**
 * One row of the arithmetic, **always**.
 *
 * The three numbers cross whatever the codes beside them say, because they are numbers rather
 * than codes: the column has to sum to the sub-total printed under it, and dropping a row here
 * would move its contribution into the derived `applied` where it would read as an adjustment
 * the engine never made.
 */
function toScoredTerm(row: ScoredTermSchema): ScoredTerm {
  return {
    term: toTerm(row.term) ?? null,
    weight: row.weight,
    value: row.value,
    contribution: row.contribution,
    evidence: toEvidence(row.evidence) ?? null,
  };
}

/**
 * The eight variants, by `kind` — the discriminator the wire and this app spell identically.
 *
 * A `switch` rather than a table, because each arm renames different fields: this is the
 * ordinary mapper boundary, and `shared_count` becoming `sharedCount` is the whole of it.
 */
function toEvidence(evidence: WireEvidence): Evidence | undefined {
  switch (evidence.kind) {
    case 'level_fit': {
      const direction = toLevelDirection(evidence.direction);
      return direction === undefined
        ? undefined
        : {
            kind: 'level_fit',
            myMu: evidence.my_mu,
            theirMu: evidence.their_mu,
            delta: evidence.delta,
            direction,
          };
    }
    case 'predicted_balance':
      return {
        kind: 'predicted_balance',
        pct: evidence.pct,
        mySigma: evidence.my_sigma,
        theirSigma: evidence.their_sigma,
        confidence: evidence.confidence,
      };
    case 'intent_alignment': {
      const myMode: SearchMode | undefined = KNOWN_MODES.has(evidence.my_mode)
        ? evidence.my_mode
        : undefined;
      const theirIntent: PlayIntent | undefined = KNOWN_INTENTS.has(evidence.their_intent)
        ? evidence.their_intent
        : undefined;
      return myMode === undefined || theirIntent === undefined
        ? undefined
        : { kind: 'intent_alignment', myMode, theirIntent, aligned: evidence.aligned };
    }
    case 'reliability':
      // `strands` stops here: the sheet draws the published score and the floor breach, and
      // the six strands behind it are the engine's working rather than the pair's facts.
      return {
        kind: 'reliability',
        score: evidence.score,
        floorBreached: evidence.floor_breached,
      };
    case 'availability_overlap': {
      const [next] = evidence.next_slot == null ? [] : toWeekCells([evidence.next_slot]);
      return {
        kind: 'availability_overlap',
        sharedCount: evidence.shared_count,
        // A cell naming a day outside 1–7 is dropped by `toWeekCells`, which leaves the same
        // `null` the wire uses for *there is no shared cell*: both mean the line says a count
        // and no next slot, and neither invents a Tuesday.
        nextSlot: next ?? null,
      };
    }
    case 'playing_style':
      return { kind: 'playing_style', ...tagRelationships(evidence) };
    case 'social_vibe':
      return { kind: 'social_vibe', ...tagRelationships(evidence) };
    case 'distance':
      return {
        kind: 'distance',
        km: evidence.km,
        areaCode: evidence.area_code,
        outsideTheirRadius: evidence.outside_their_radius,
      };
    // A ninth variant. The row it belongs to is counted rather than drawn — see the module
    // note, and `EVIDENCE_KINDS_AGREE`, which is what makes this unreachable from a build
    // generated against the current document.
    default:
      return undefined;
  }
}

/**
 * The three sets a tag term carries, narrowed together — **and one bit saying whether the
 * narrowing took anything.**
 *
 * A pair is dropped when **either** id is one this build has no words for: a sentence naming
 * one half of a relationship is a claim about a pairing the reader cannot check.
 *
 * `matchedInFull` is the one place that drop is not free, and `TagRelationships` carries the
 * argument: the competitive card says *No tags in common* off an empty `matched`, so a build
 * that narrowed a real match to nothing would turn §3's silent drop into a false claim. The
 * two pair lists need no such bit — nothing counts them and nothing states their absence.
 */
function tagRelationships(evidence: {
  readonly matched: readonly string[];
  readonly complementary: readonly WireTagPair[];
  readonly clashing: readonly WireTagPair[];
}) {
  const matched = evidence.matched.flatMap((tag) => toSocialTagId(tag) ?? []);
  return {
    matched,
    matchedInFull: matched.length === evidence.matched.length,
    complementary: evidence.complementary.flatMap((pair) => toTagPair(pair) ?? []),
    clashing: evidence.clashing.flatMap((pair) => toTagPair(pair) ?? []),
  };
}

function toTagPair(pair: WireTagPair): TagPair | undefined {
  const a = toSocialTagId(pair.a);
  const b = toSocialTagId(pair.b);
  return a === undefined || b === undefined ? undefined : { a, b };
}

/**
 * A stood-down term, **always** — either half may be the gap.
 *
 * The not-counted block *is* the renormalisation basis a reader is owed, so a line that
 * vanished would make the sheet's own account of what did not count shorter than the answer
 * it describes.
 */
function toDegradedTerm(degraded: WireDegradedTerm): DegradedTerm {
  return {
    term: toTerm(degraded.term) ?? null,
    reason: toDegradedReason(degraded.reason) ?? null,
  };
}

function toModifier(modifier: WireModifier): Modifier | undefined {
  const code = KNOWN_MODIFIERS.has(modifier.code) ? (modifier.code as ModifierCode) : undefined;
  return code === undefined ? undefined : { code, points: modifier.points };
}

const KNOWN_TERMS = new Set<string>(TERMS);
const KNOWN_MODES = new Set<string>(SEARCH_MODES);
const KNOWN_INTENTS = new Set<string>(PLAY_INTENTS);
const KNOWN_LIVENESS = new Set<string>(LIVENESS_REASONS);
const KNOWN_INCLUSION = new Set<string>(INCLUSION_REASONS);
const KNOWN_DEGRADED = new Set<string>(DEGRADED_REASONS);
const KNOWN_MODIFIERS = new Set<string>(MODIFIER_CODES);
const KNOWN_TAGS = new Set<string>(SOCIAL_TAG_IDS);
const KNOWN_DIRECTIONS = new Set<string>(LEVEL_DIRECTIONS);
const KNOWN_WINDOWS = new Set<string>(WINDOWS);
const KNOWN_OPTIMISED_FOR = new Set<string>(OPTIMISED_FOR);
const KNOWN_SORTS = new Set<string>(SORT_OPTIONS);
const KNOWN_RUNGS = new Set<string>(RUNGS);
const KNOWN_ASKS = new Set<string>(RELAXATION_ASKS);
const KNOWN_RESULTS = new Set<string>(GAME_RESULTS);
const KNOWN_PHOTO_REVIEWS = new Set<string>(PHOTO_REVIEWS);

function toTerm(term: string): Term | undefined {
  return KNOWN_TERMS.has(term) ? (term as Term) : undefined;
}

function toLivenessReason(reason: string): LivenessReason | undefined {
  return KNOWN_LIVENESS.has(reason) ? (reason as LivenessReason) : undefined;
}

function toOptimisedFor(optimised: string): OptimisedFor | undefined {
  return KNOWN_OPTIMISED_FOR.has(optimised) ? (optimised as OptimisedFor) : undefined;
}

function toSortOption(sort: string): SortOption | undefined {
  return KNOWN_SORTS.has(sort) ? (sort as SortOption) : undefined;
}

function toWindow(window: string): Window | undefined {
  return KNOWN_WINDOWS.has(window) ? (window as Window) : undefined;
}

function toDegradedReason(reason: string): DegradedReason | undefined {
  return KNOWN_DEGRADED.has(reason) ? (reason as DegradedReason) : undefined;
}

function toSocialTagId(tag: string): SocialTagId | undefined {
  return KNOWN_TAGS.has(tag) ? (tag as SocialTagId) : undefined;
}

function toLevelDirection(direction: string): LevelDirection | undefined {
  return KNOWN_DIRECTIONS.has(direction) ? (direction as LevelDirection) : undefined;
}

function toGameResult(result: string): GameResult | undefined {
  return KNOWN_RESULTS.has(result) ? (result as GameResult) : undefined;
}
