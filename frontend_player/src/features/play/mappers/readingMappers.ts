/**
 * A reading, as the Radar pane holds it — the deal's mapper over the deal's shape, plus the
 * two fields a reading's row carries and no other surface's does.
 *
 * `candidateMappers` crosses the candidate and the envelope, and every narrowing it decides
 * stands here unchanged: this reads **on top of** `toCandidate` rather than beside it, so a
 * field added to the card arrives on the radar the day it arrives on the deck. What is decided
 * here is two things.
 *
 * ## A row with no spot is dropped, and the drop is stated
 *
 * `distance_km` is optional on the contract because the distance term may stand down on a
 * search, and `bearing_deg` is optional because it is served on a reading only. A radar row
 * needs both to be drawn anywhere, and the reading's own rows always carry both — so a row
 * without either is a state this build cannot draw rather than one it can half draw, and it is
 * **dropped** here in [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §3's
 * sense: a selection out of a population, with the footer counting what was drawn. It is not a
 * gap kept in place, because there is no place to keep it in.
 *
 * ## A rating in a sport this build cannot name is dropped, and the row stays
 *
 * `ratings[]` is *every sport the player is rated in*, and the card draws one row per entry.
 * A sport outside `SPORTS` has no name and no dot to draw — `sportLabel` would have nothing to
 * say — so that entry is dropped and the others stand, exactly as a social tag this build has no
 * words for is (`toSocialTagId`). The card is shorter by a row it could not have drawn, and
 * `card.level` — the reading's own sport, always one this build knows, because the reading was
 * asked for in it — is untouched.
 */

import type { components } from '@/generated/schema';
import { toSport } from '@/features/onboarding/types';

import type { RadarRow, RatedSport, Reading } from '../domain/reading';

import { toCandidate, toSearchEnvelope } from './candidateMappers';

type ShortlistResponse = components['schemas']['ShortlistResponse'];
type CandidateSchema = components['schemas']['CandidateSchema'];
type WireRatedSport = components['schemas']['RatedSportSchema'];

export function toReading(response: ShortlistResponse): Reading {
  return {
    envelope: toSearchEnvelope(response),
    rows: response.candidates.flatMap((row) =>
      row.withheld === true ? [] : (toRadarRow(row as CandidateSchema) ?? []),
    ),
  };
}

/** One row, or nothing where the wire gave it no spot to be drawn at — see the module note. */
export function toRadarRow(row: CandidateSchema): RadarRow | undefined {
  if (row.distance_km === undefined || row.bearing_deg === undefined) return undefined;
  return {
    ...toCandidate(row),
    distanceKm: row.distance_km,
    bearingDeg: row.bearing_deg,
    ratings: (row.ratings ?? []).flatMap((rated) => toRatedSport(rated) ?? []),
  };
}

function toRatedSport(rated: WireRatedSport): RatedSport | undefined {
  const sport = toSport(rated.sport);
  return sport === undefined ? undefined : { sport, level: rated.level };
}
