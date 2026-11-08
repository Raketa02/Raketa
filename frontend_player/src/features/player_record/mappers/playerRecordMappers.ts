/**
 * The record, from the wire's spelling into this app's.
 *
 * One of the two layers allowed to read generated types, and the only place the response's
 * shape is known. Everything above this file reads `PlayerRecord`.
 *
 * ## Every closed vocabulary is narrowed, and each narrowing has its own answer
 *
 * The generated unions say a served value is always one this build knows. A phone that has not
 * been updated in eight months says otherwise, so each is a **membership test** and what
 * happens to an unreadable value is decided per field rather than once:
 *
 * | Field | An unreadable value | Why |
 * | --- | --- | --- |
 * | `sports[].sport` | that pill is dropped | a pill with no name on it is a coloured dot claiming a sport |
 * | `social_tags[]` | that tag is dropped | a chip with no words on it |
 * | `skill.sport` | the **whole panel** goes | the sport is printed on the panel and on the poster beside it; a card that could not say which sport it was about would be a Level with no subject |
 * | `skill.last_five` | the **whole run** goes | its length is a claim: dropping one entry says a counted game fewer than the platform counted, and a third kind of square is a drawing nobody has designed |
 * | `reliability.band` | the **word** goes, the figure stays | the points are the server's and still true; a word this phone guessed from them would be the thresholds it gave up |
 * | `reliability.filter.minimum` | the **switch** goes, with its line | a switch drawn standing at Off over a filter that is on would say the opposite of the truth, and *Off* is the one position it could stand at |
 * | `reliability.filter.back_with_everyone.band` | that **sentence** goes | it names the band — *play only with High reliability or above* — and a sentence with a blank where the band goes is no sentence |
 * | `review` | folded to *no mark* | the absence is already a state, and it is the one that draws nothing |
 *
 * The band's answer is the opposite of the skill panel's sport and for the reason stated there:
 * a sport is what the panel is **about**, where a band is a word **under** a figure that means
 * the same without it — so the figure is drawn alone rather than taken off the sheet.
 *
 * ## The opinion is one figure for every reader, and the band no longer crosses
 *
 * The contract served `sportsmanship_band` to a record's subject and `sportsmanship` to anybody
 * else until [#468](https://github.com/Raketa02/Raketa/issues/468) retired the band (ADR-0179
 * §5): the figure and its count now cross to the subject as to any reader, and the wire has one
 * field. So the mapper reads that one field whoever is asking, and `Opinion` is that one shape
 * ([#473](https://github.com/Raketa02/Raketa/issues/473)) — `is_self` retitles the sheet and
 * decides nothing here.
 *
 * ## The verdict is folded to a boolean here and is never carried further
 *
 * *Checked and flagged* and *nobody looked* draw **identically**
 * ([ADR-0138](../../../../../docs/adr/0138-the-verdict-crosses-on-a-card-and-never-checked-is-its-own-answer.md)),
 * and a component holding the code could branch on it a second way — the second way being the
 * one that publishes a moderation outcome about somebody who is not looking at this screen. So
 * only the positive survives the boundary, which makes the second reading unrepresentable
 * rather than merely undone.
 *
 * ## Nothing is defaulted to a nought
 *
 * Every optional on the response is *the platform has nothing to say*, and the three absences
 * ask three different questions. A `?? 0` anywhere below would turn *nobody has rated them* into
 * *they rate badly*, which is the one confusion this whole sheet is built to avoid. Player
 * reliability is not optional at all since ADR-0195 §1 — everyone starts at 100 — so its
 * noughts are the server's counts and are carried as they came.
 */

import type { components } from '@/generated/schema';
import { toSport } from '@/features/onboarding/types';
import { GAME_RESULTS, type GameResult } from '@/shared/vocabulary/gameResult';
import { SOCIAL_TAG_IDS, type SocialTagId } from '@/shared/vocabulary/socialTags';

import {
  RELIABILITY_BANDS,
  RELIABILITY_MINIMUMS,
  type BackWithEveryone,
  type Opinion,
  type OpponentVariety,
  type PlayerRecord,
  type RatedSport,
  type Reliability,
  type ReliabilityBand,
  type ReliabilityFilter,
  type ReliabilityMinimum,
  type SkillPanel,
} from '../domain/playerRecord';

type PlayerRecordResponse = components['schemas']['PlayerRecordResponse'];
type SkillPanelSchema = components['schemas']['SkillPanelSchema'];
type ReliabilitySchema = components['schemas']['ReliabilitySchema'];
type ReliabilityFilterSchema = components['schemas']['ReliabilityFilterSchema'];
type OpponentVarietySchema = components['schemas']['OpponentVarietySchema'];

export function toPlayerRecord(response: PlayerRecordResponse): PlayerRecord {
  return {
    isSelf: response.is_self,
    nickname: response.nickname,
    // Verbatim, and absent where absent. Nothing trims, shortens or defaults it: what
    // crosses is what they wrote, fenced on the way in and never on the way out.
    ...(response.intro === undefined ? {} : { intro: response.intro }),
    ...(response.photo_url === undefined ? {} : { photoUrl: response.photo_url }),
    // The mark is a fact about **a photograph**: a player with none is drawn the generated
    // poster, which has nothing to have passed. The pair is read together and once.
    onCourt: response.photo_url !== undefined && response.review === 'allowed',
    areaCode: response.area_code,
    socialTags: response.social_tags.flatMap((tag) => toSocialTagId(tag) ?? []),
    sports: response.sports.flatMap(toRatedSport),
    ...skillPanel(response.skill),
    reliability: reliability(response.reliability),
    ...(response.variety === undefined ? {} : { variety: variety(response.variety) }),
    ...opinion(response),
    // Spelled as the wire spells it — `friends`' vocabulary holds the two equal.
    relation: response.relation,
    canAddFriend: response.can_add_friend,
  };
}

/**
 * **What other players said — the figure and its count, for every reader** (#468, ADR-0179 §5).
 *
 * Carried whole, and absent where nobody has said anything: the block is never drawn at nought.
 */
function opinion(response: PlayerRecordResponse): { readonly opinion?: Opinion } {
  const said = response.sportsmanship;
  return said === undefined ? {} : { opinion: { average: said.average, raters: said.raters } };
}

/**
 * **Player reliability, field for field** (#660) — the points, the band where this build can name
 * it, *New*, and the four counts. Nothing is computed here: the band is the server's and the
 * counts are the server's, and a phone that worked either out would be a second opinion.
 */
function reliability(served: ReliabilitySchema): Reliability {
  const band = toReliabilityBand(served.band);
  return {
    playerScore: served.player_score,
    ...(band === undefined ? {} : { band }),
    isNew: served.is_new,
    counts: {
      turnedUp: served.turned_up,
      turnedUpOf: served.turned_up_of,
      late: served.late,
      kept: served.kept,
      keptOf: served.kept_of,
      leftInDispute: served.left_in_dispute,
    },
    ...filterFacts(served.filter),
  };
}

/**
 * **The filter's two facts, off one wire object** (#662, ADR-0195 §6) — the player's own switch
 * with what it hides, and the figure that deals them with everyone again. Served on your own
 * record only, so both are absent on anybody else's; each is narrowed on its own, per the table
 * above, because each is drawn on its own.
 */
function filterFacts(served: ReliabilityFilterSchema | undefined): {
  readonly filter?: ReliabilityFilter;
  readonly backWithEveryone?: BackWithEveryone;
} {
  if (served === undefined) return {};
  return { ...ownSwitch(served), ...backWithEveryone(served.back_with_everyone) };
}

/** The switch and its line, or neither — see the narrowing table. Off is *no minimum*. */
function ownSwitch(served: ReliabilityFilterSchema): { readonly filter?: ReliabilityFilter } {
  if (served.minimum === undefined) return { filter: { hides: served.hides, of: served.of } };
  const minimum = toReliabilityMinimum(served.minimum);
  return minimum === undefined ? {} : { filter: { minimum, hides: served.hides, of: served.of } };
}

/** The figure back, whole or not at all: the sentence names the band. */
function backWithEveryone(served: ReliabilityFilterSchema['back_with_everyone']): {
  readonly backWithEveryone?: BackWithEveryone;
} {
  if (served === undefined) return {};
  const band = toReliabilityBand(served.band);
  return band === undefined ? {} : { backWithEveryone: { band, points: served.points } };
}

/** The raw pair, whole. The share it is drawn as is `varietyShare`'s one division. */
function variety(served: OpponentVarietySchema): OpponentVariety {
  return {
    distinctOpponents: served.distinct_opponents,
    timesOnCourt: served.times_on_court,
  };
}

/** One pill, or none — see the narrowing table above. The order is the server's and is kept. */
function toRatedSport(served: PlayerRecordResponse['sports'][number]): readonly RatedSport[] {
  const sport = toSport(served.sport);
  return sport === undefined ? [] : [{ sport, level: served.level }];
}

/**
 * The skill card, **whole or not at all**.
 *
 * The panel prints the sport it resolved to, so a sport this build cannot name takes the card
 * with it rather than drawing a Level with no subject. That is the same answer the run of five
 * gets one field down and for a related reason: what is missing is not a detail of the claim,
 * it is what the claim is about.
 */
function skillPanel(served: SkillPanelSchema | undefined): { readonly skill?: SkillPanel } {
  if (served === undefined) return {};
  const sport = toSport(served.sport);
  if (sport === undefined) return {};

  return {
    skill: {
      sport,
      level: served.level,
      band: served.band,
      confidence: served.confidence,
      countedGames: served.counted_games,
      likelyRange: served.likely_range,
      ...lastFive(served.last_five),
    },
  };
}

/**
 * The run, or **no run at all** — never a shorter one.
 *
 * An empty list is a real answer and stays one: it says none of theirs has been counted, which
 * the drawing renders as no squares. What cannot survive is a run this build read only part
 * of, because the row's length is itself the statement.
 */
function lastFive(served: readonly string[]): { readonly lastFive?: readonly GameResult[] } {
  const read = served.flatMap((result) => toGameResult(result) ?? []);
  return read.length === served.length ? { lastFive: read } : {};
}

const KNOWN_RESULTS = new Set<string>(GAME_RESULTS);
const KNOWN_TAGS = new Set<string>(SOCIAL_TAG_IDS);
const KNOWN_BANDS = new Set<string>(RELIABILITY_BANDS);
const KNOWN_MINIMUMS = new Set<string>(RELIABILITY_MINIMUMS);

function toGameResult(served: string): GameResult | undefined {
  return KNOWN_RESULTS.has(served) ? (served as GameResult) : undefined;
}

function toSocialTagId(served: string): SocialTagId | undefined {
  return KNOWN_TAGS.has(served) ? (served as SocialTagId) : undefined;
}

/**
 * **A served band, or nothing** — see the narrowing table above. Exported through `types.ts` for
 * the one other reader of the code, `groups`' Members rows, so one list cannot read a band two
 * ways.
 */
export function toReliabilityBand(served: string): ReliabilityBand | undefined {
  return KNOWN_BANDS.has(served) ? (served as ReliabilityBand) : undefined;
}

/** A served minimum this build can offer on its switch, or nothing — see the narrowing table. */
function toReliabilityMinimum(served: string): ReliabilityMinimum | undefined {
  return KNOWN_MINIMUMS.has(served) ? (served as ReliabilityMinimum) : undefined;
}
