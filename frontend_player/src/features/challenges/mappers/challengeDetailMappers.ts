/**
 * `GET /challenges/{id}` coming back — **the arrangement, the people on it, and the pairing
 * recomputed for the reader.**
 *
 * One of the two layers allowed to read generated types, and the only place this shape is
 * turned into words this app owns.
 *
 * ## It is a second spelling of the evidence, and that is the decision rather than the debt
 *
 * `challenges` spells its own schema and it is **narrower than the card**
 * ([ADR-0143](../../../../../docs/adr/0143-the-challenge-is-the-gate-and-the-card-is-recomputed-for-the-reader.md)
 * §5): `matchmaking` owns `PlayerCardSchema`, `challenges` may not import it, and *"the
 * alternative to two spellings is the matcher owning the vocabulary of the context that was
 * built to take it off him."* The wire therefore carries `Court…` schemas beside Play's, and a
 * client that mapped them through `candidateMappers` would be reading a contract it was not
 * sent — the two are free to diverge, which is the whole point of the second spelling, and the
 * day one does the shared mapper would silently map the wrong one.
 *
 * **What is not duplicated is the vocabulary and the words.** The eight evidence variants,
 * the terms and the reasons written over them are ADR-0106's *contract*, and they have one
 * home: `features/play/types`. So this file narrows against Play's own lists and produces
 * Play's own domain objects — a code added, removed or renamed reaches both features at once,
 * and the only thing spelled twice is the field renaming, which is what a mapper is.
 *
 * ## Four fields this read does not carry, each refused for its own reason
 *
 * `liveness_reasons` answers *why did this person move* and `inclusion_reason* answers *why are
 * they in the list at all* — **neither question exists when somebody asked you directly**, and
 * there is no list. `modifiers` is engine internals, and the card furniture a search draws —
 * social tags, the run of form, counted games, the photo verdict — is not drawn here.
 *
 * ## `null` is *this response said nothing*, and it collapses to absent
 *
 * `challengeMappers`' rule, unchanged: every optional arrives as `T | null | undefined` and
 * every one becomes `undefined`, so no screen has two spellings of one absence to branch on.
 *
 * ## Three codes are narrowed, and they are narrowed three different ways
 *
 * A **standing** this build cannot read becomes `undefined` and the challenge stays, because the
 * code *is* the whole sentence. A **sport** it cannot read takes the whole read with it, for
 * `challengeMappers`' reason: the sport is the identifying fact. And a **pairing absence** it
 * cannot read collapses to *no absence reported*, which is the safe direction — the cards are
 * either on the seats or they are not, and inventing a sentence about whose gap it was would be
 * a claim this build cannot support.
 */

import type { components } from '@/generated/schema';
import { toSport } from '@/features/onboarding/types';
import { toWeekCells } from '@/features/player_profile/types';
import {
  DEGRADED_REASONS,
  FORECAST_ASSUMPTIONS,
  LEVEL_DIRECTIONS,
  SEARCH_MODES,
  TERMS,
  type Evidence,
  type Forecast,
  type ForecastAssumption,
  type LevelDirection,
  type PlayIntent,
  type ScoredTerm,
  type SearchMode,
  type TagPair,
  type Term,
} from '@/features/play/types';
import { PLAY_INTENTS } from '@/shared/vocabulary/playIntent';
import { SOCIAL_TAG_IDS, type SocialTagId } from '@/shared/vocabulary/socialTags';

import type {
  AnsweredChallenge,
  ChallengeDetail,
  CourtPairing,
  CourtPerson,
  DegradedReason,
  DegradedTerm,
  DetailSeat,
  PairingAbsence,
  SeatCard,
} from '../domain/challengeDetail';
import { PAIRING_ABSENCES } from '../domain/challengeDetail';
import { STANDINGS, type Standing } from '../domain/standing';

type ChallengeDetailResponse = components['schemas']['ChallengeDetailResponse'];
type ChallengeSchema = components['schemas']['ChallengeSchema'];
type WireListSeat = components['schemas']['SeatSchema'];
type WireSeat = components['schemas']['DetailSeatSchema'];
type WireCard = components['schemas']['SeatCardSchema'];
type WirePerson = components['schemas']['CourtPersonSchema'];
type WirePairing = components['schemas']['CourtPairingSchema'];
type WireScoredTerm = components['schemas']['CourtScoredTermSchema'];
type WireEvidence = WireScoredTerm['evidence'];
type WireDegradedTerm = components['schemas']['CourtDegradedTermSchema'];
type WireForecast = components['schemas']['CourtForecastSchema'];
type WireTagPair = components['schemas']['CourtTagPair'];

/**
 * The whole read, or nothing where the sport is a code this build cannot name.
 *
 * `undefined` rather than a partial challenge: the screen's own *no challenge of yours has this
 * address* answer is the honest one for a record it cannot describe, and it already exists for
 * the `404`.
 */
export function toChallengeDetail(response: ChallengeDetailResponse): ChallengeDetail | undefined {
  const sport = toSport(response.sport);
  if (sport === undefined) return undefined;

  const standing = toStanding(response.standing);
  const absence = toPairingAbsence(response.pairing_absence);

  return {
    challengeId: response.challenge_id,
    organiserId: response.organiser_id,
    ...(standing === undefined ? {} : { standing }),
    sport,
    openedAt: response.opened_at,
    readAt: response.read_at,
    seats: response.seats.map(toDetailSeat),
    ...(absence === undefined ? {} : { pairingAbsence: absence }),
  };
}

/** A standing, or nothing where the server sent a code this build has no words for. */
function toStanding(wire: Standing): Standing | undefined {
  return STANDINGS.some((known) => known === wire) ? wire : undefined;
}

/**
 * Whose gap the pairing was, or nothing.
 *
 * A code this build cannot read draws **the same as no absence at all**, which is the safe
 * direction and the only one: the seats either carry cards or they do not, and this field only
 * ever explains an emptiness the reader can already see. A sentence written from a code we
 * cannot read would be this app guessing whose gap it was.
 */
function toPairingAbsence(wire: PairingAbsence | null | undefined): PairingAbsence | undefined {
  if (wire == null) return undefined;
  return PAIRING_ABSENCES.some((known) => known === wire) ? wire : undefined;
}

function toDetailSeat(seat: WireSeat): DetailSeat {
  const card = seat.card === undefined ? undefined : toSeatCard(seat.card);

  return {
    ...(seat.player_id == null ? {} : { playerId: seat.player_id }),
    ...(seat.answer == null ? {} : { answer: seat.answer }),
    ...(seat.nickname == null ? {} : { nickname: seat.nickname }),
    ...(seat.answer_by == null ? {} : { answerBy: seat.answer_by }),
    ...(card === undefined ? {} : { card }),
  };
}

function toSeatCard(card: WireCard): SeatCard {
  return { person: toCourtPerson(card.person), pairing: toCourtPairing(card.pairing) };
}

/**
 * **`photo_id` and `photo_url` are present exactly together**, and only the URL is kept.
 *
 * The id is what the *record* keeps and `GET /photos/{id}` refuses another player's on purpose,
 * so the link is the only address this photograph has. Neither means the client draws the
 * generated court poster, which chooses by hash and needs nothing from the wire.
 */
function toCourtPerson(person: WirePerson): CourtPerson {
  return {
    nickname: person.nickname,
    ...(person.photo_url === undefined ? {} : { photoUrl: person.photo_url }),
    areaCode: person.area_code,
    level: person.level,
    band: person.band,
    range: { low: person.range.low, high: person.range.high },
    ...(person.player_score === undefined ? {} : { playerScore: person.player_score }),
  };
}

function toCourtPairing(pairing: WirePairing): CourtPairing {
  const forecast = pairing.forecast === undefined ? undefined : toForecast(pairing.forecast);

  return {
    fit: pairing.fit,
    ...(pairing.distance_km === undefined ? {} : { distanceKm: pairing.distance_km }),
    terms: pairing.terms.map(toScoredTerm),
    degradedTerms: pairing.degraded_terms.map(toDegradedTerm),
    // A concern is a term and nothing else; the card joins it back to the row it already holds.
    // One this build cannot name is dropped, because nothing totals this list and a concern
    // with no term is not a sentence anybody can write.
    concerns: pairing.concerns.flatMap((concern) => toTerm(concern.term) ?? []),
    ...(forecast === undefined ? {} : { forecast }),
    ...(pairing.at_stake === undefined
      ? {}
      : {
          atStake: {
            winDelta: pairing.at_stake.win_delta,
            lossDelta: pairing.at_stake.loss_delta,
          },
        }),
  };
}

/**
 * One row of the arithmetic, **always**.
 *
 * The three numbers cross whatever the codes beside them say, because they are numbers rather
 * than codes — and a row dropped here would move its contribution into a gap nobody could
 * account for.
 */
function toScoredTerm(row: WireScoredTerm): ScoredTerm {
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
      const myMode = toSearchMode(evidence.my_mode);
      const theirIntent = toPlayIntent(evidence.their_intent);
      return myMode === undefined || theirIntent === undefined
        ? undefined
        : { kind: 'intent_alignment', myMode, theirIntent, aligned: evidence.aligned };
    }
    case 'reliability':
      // `strands` stops here, as it does on a search: the six strands behind the score are the
      // engine's working rather than the pair's facts, and nothing on this screen draws them.
      return { kind: 'reliability', score: evidence.score, floorBreached: evidence.floor_breached };
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
    // A ninth variant this build has never seen. Its row is still counted — the numbers crossed
    // — and it renders no reason line, which `selectReasons` already treats as a term that
    // declines rather than as a blank row.
    default:
      return undefined;
  }
}

/**
 * The three sets a tag term carries, narrowed together — **and one bit saying whether the
 * narrowing took anything.**
 *
 * A pair is dropped when **either** id is one this build has no words for: a sentence naming one
 * half of a relationship is a claim about a pairing the reader cannot check. `matchedInFull` is
 * the one place that drop is not free, because a card states *No tags in common* off an empty
 * `matched` and a build that narrowed a real match to nothing would turn a silent drop into a
 * false claim.
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
 * The not-counted block *is* the renormalisation basis the Fit is read against, so a line that
 * vanished would make this read's own account of what did not count shorter than the number it
 * describes.
 */
function toDegradedTerm(degraded: WireDegradedTerm): DegradedTerm {
  return { term: toTerm(degraded.term) ?? null, reason: toDegradedReason(degraded.reason) ?? null };
}

/**
 * The forecast, with the caveat it may not be able to state.
 *
 * `assumption` is `null` for *nothing was assumed* and `null` again for a code this build has no
 * words for, and the two are deliberately not told apart: `provisional` is the field that says
 * whether there was one, and a caveat we cannot state is not a caveat we may drop.
 */
function toForecast(forecast: WireForecast): Forecast {
  return {
    pct: forecast.pct,
    sigmaGroup: forecast.sigma_group,
    provisional: forecast.provisional,
    assumption: forecast.assumption == null ? null : (toAssumption(forecast.assumption) ?? null),
  };
}

const KNOWN_TERMS = new Set<string>(TERMS);
const KNOWN_MODES = new Set<string>(SEARCH_MODES);
const KNOWN_INTENTS = new Set<string>(PLAY_INTENTS);
const KNOWN_DEGRADED = new Set<string>(DEGRADED_REASONS);
const KNOWN_DIRECTIONS = new Set<string>(LEVEL_DIRECTIONS);
const KNOWN_ASSUMPTIONS = new Set<string>(FORECAST_ASSUMPTIONS);
const KNOWN_TAGS = new Set<string>(SOCIAL_TAG_IDS);

function toTerm(term: string): Term | undefined {
  return KNOWN_TERMS.has(term) ? (term as Term) : undefined;
}

function toSearchMode(mode: string): SearchMode | undefined {
  return KNOWN_MODES.has(mode) ? (mode as SearchMode) : undefined;
}

function toPlayIntent(intent: string): PlayIntent | undefined {
  return KNOWN_INTENTS.has(intent) ? (intent as PlayIntent) : undefined;
}

function toDegradedReason(reason: string): DegradedReason | undefined {
  return KNOWN_DEGRADED.has(reason) ? (reason as DegradedReason) : undefined;
}

function toLevelDirection(direction: string): LevelDirection | undefined {
  return KNOWN_DIRECTIONS.has(direction) ? (direction as LevelDirection) : undefined;
}

function toAssumption(assumption: string): ForecastAssumption | undefined {
  return KNOWN_ASSUMPTIONS.has(assumption) ? (assumption as ForecastAssumption) : undefined;
}

function toSocialTagId(tag: string): SocialTagId | undefined {
  return KNOWN_TAGS.has(tag) ? (tag as SocialTagId) : undefined;
}

/**
 * **What an answer route said back** — the standing and the court, and nothing this screen
 * already holds.
 *
 * `ChallengeSchema` is the *list's* shape, so it carries no cards; that is not a loss, because
 * `redrawnFrom` keeps the ones the screen is holding and the rule drops them when the standing
 * moves past the two that draw a block (ADR-0143 §8).
 *
 * The sport is **not** re-read. A challenge whose sport this build cannot name never reached the
 * screen at all — `toChallengeDetail` refused it — so narrowing it a second time here could only
 * ever invent a way for an answer to fail on a challenge that is already on screen.
 */
export function toAnsweredChallenge(answered: ChallengeSchema): AnsweredChallenge {
  const standing = toStanding(answered.standing);

  return {
    ...(standing === undefined ? {} : { standing }),
    seats: answered.seats.map(toListSeat),
  };
}

function toListSeat(seat: WireListSeat) {
  return {
    ...(seat.player_id == null ? {} : { playerId: seat.player_id }),
    ...(seat.answer == null ? {} : { answer: seat.answer }),
    ...(seat.nickname == null ? {} : { nickname: seat.nickname }),
    ...(seat.answer_by == null ? {} : { answerBy: seat.answer_by }),
  };
}
