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
 * | `reliability.strands[].strand` | that row is dropped | a metered row with no label is a bar with a fraction beside it and nothing saying what was counted |
 * | `sportsmanship_band` | the **whole block** goes | a band is three words wide and the word *is* the answer; there is nothing else in that block to keep |
 * | `review` | folded to *no mark* | the absence is already a state, and it is the one that draws nothing |
 *
 * A dropped strand row is a **shorter card and not a wrong one**, which is the opposite answer
 * to the run of five's above it and for the reason stated there: a run's length is itself the
 * claim, where a card states one row per thing the platform has watched and has never promised
 * how many. The figure over it is the server's own blend and is not recomputed from what
 * survived, so the pill goes on being right about a row this build could not name.
 *
 * ## Whose record it is decides which opinion crosses, and the figure never reaches its subject
 *
 * The contract sends `sportsmanship` and `sportsmanship_band` as two fields and states that
 * they never appear together. `Opinion` is **one value with two arms**, and the arm is chosen
 * here from `is_self` rather than from which field happened to arrive: a published average
 * beside a published count lets the subject subtract each new rating out and name it, and they
 * know who they played, so a response carrying both must draw the band. Folding it here is what
 * makes *your own record drew the figure* unrepresentable rather than merely unlikely — the
 * same argument the verdict's fold below makes about a different disclosure.
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
 * Every optional on the response is *the platform has nothing to say*, and the four absences
 * ask four different questions. A `?? 0` anywhere below would turn *nobody has been due
 * anywhere* into *they never turn up*, which is the one confusion this whole sheet is built to
 * avoid.
 */

import type { components } from '@/generated/schema';
import { toSport } from '@/features/onboarding/types';
import { GAME_RESULTS, type GameResult } from '@/shared/vocabulary/gameResult';
import { SOCIAL_TAG_IDS, type SocialTagId } from '@/shared/vocabulary/socialTags';

import {
  OPINION_BANDS,
  RELIABILITY_STRANDS,
  type Opinion,
  type OpinionBand,
  type OpponentVariety,
  type PlayerRecord,
  type RatedSport,
  type Reliability,
  type ReliabilityStrand,
  type SkillPanel,
  type StrandRow,
} from '../domain/playerRecord';

type PlayerRecordResponse = components['schemas']['PlayerRecordResponse'];
type SkillPanelSchema = components['schemas']['SkillPanelSchema'];
type ReliabilitySchema = components['schemas']['ReliabilitySchema'];
type OpponentVarietySchema = components['schemas']['OpponentVarietySchema'];

export function toPlayerRecord(response: PlayerRecordResponse): PlayerRecord {
  return {
    isSelf: response.is_self,
    nickname: response.nickname,
    ...(response.photo_url === undefined ? {} : { photoUrl: response.photo_url }),
    // The mark is a fact about **a photograph**: a player with none is drawn the generated
    // poster, which has nothing to have passed. The pair is read together and once.
    onCourt: response.photo_url !== undefined && response.review === 'allowed',
    areaCode: response.area_code,
    socialTags: response.social_tags.flatMap((tag) => toSocialTagId(tag) ?? []),
    sports: response.sports.flatMap(toRatedSport),
    ...skillPanel(response.skill),
    ...(response.reliability === undefined
      ? {}
      : { reliability: reliability(response.reliability) }),
    ...(response.variety === undefined ? {} : { variety: variety(response.variety) }),
    ...opinion(response),
  };
}

/**
 * **What other players said — the band about yourself, the figure about anybody else.**
 *
 * Read off `is_self` and never off which field arrived, for the reason in the module note. The
 * figure is carried whole; the band is narrowed, and a band with no words takes the block with
 * it rather than drawing a code where a word about somebody belongs.
 */
function opinion(response: PlayerRecordResponse): { readonly opinion?: Opinion } {
  if (response.is_self) {
    const band = toOpinionBand(response.sportsmanship_band);
    return band === undefined ? {} : { opinion: { kind: 'band', band } };
  }

  const said = response.sportsmanship;
  return said === undefined
    ? {}
    : { opinion: { kind: 'figure', average: said.average, raters: said.raters } };
}

/**
 * The pill and its rows, as one fact.
 *
 * They are carried together because they are **one absence** — nothing has ever fallen due —
 * and splitting them here is how a build ends up drawing a figure over an empty card.
 */
function reliability(served: ReliabilitySchema): Reliability {
  return {
    playerScore: served.player_score,
    strands: served.strands.flatMap(toStrandRow),
  };
}

/** One row, or none — see the narrowing table above. The order is the server's and is kept. */
function toStrandRow(served: ReliabilitySchema['strands'][number]): readonly StrandRow[] {
  const strand = toStrand(served.strand);
  return strand === undefined
    ? []
    : [
        {
          strand,
          good: served.good,
          opportunities: served.opportunities,
          // Served rather than divided here: `good / opportunities` on this side would be the
          // fourth rounding of one record, and the two disagree by a point on exactly the
          // values a player notices.
          pct: served.pct,
        },
      ];
}

/** The raw pair, whole. The share it is drawn as is `varietyShare`'s one division. */
function variety(served: OpponentVarietySchema): OpponentVariety {
  return {
    distinctOpponents: served.distinct_opponents,
    gamesPlayed: served.games_played,
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
const KNOWN_STRANDS = new Set<string>(RELIABILITY_STRANDS);
const KNOWN_BANDS = new Set<string>(OPINION_BANDS);

function toGameResult(served: string): GameResult | undefined {
  return KNOWN_RESULTS.has(served) ? (served as GameResult) : undefined;
}

function toSocialTagId(served: string): SocialTagId | undefined {
  return KNOWN_TAGS.has(served) ? (served as SocialTagId) : undefined;
}

function toStrand(served: string): ReliabilityStrand | undefined {
  return KNOWN_STRANDS.has(served) ? (served as ReliabilityStrand) : undefined;
}

/** The one narrowing that takes an absence as well, because the field is optional on the wire. */
function toOpinionBand(served: string | undefined): OpinionBand | undefined {
  return served !== undefined && KNOWN_BANDS.has(served) ? (served as OpinionBand) : undefined;
}
