/**
 * **A reading** — what `POST /radar` answers, as the Radar pane holds it: every player the
 * radar may draw for the viewer in one sport, each at a distance and a bearing
 * ([ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §1–§3, [`the-radar.md`](../../../../../docs/specs/matchmaking/the-radar.md) §2).
 *
 * ## A row is a candidate with a position, and the position is required
 *
 * The wire's row is `CandidateSchema` — the deck's own shape — plus two fields that arrive on a
 * reading and on no other surface: `bearing_deg`, and `ratings[]` for every sport the player is
 * rated in. `distanceKm` is optional on a {@link Candidate}, because the distance term may
 * stand down on a search; on a radar row it is **required**, together with the bearing, because
 * a row with no spot has nowhere to be drawn. The mapper drops a row the contract could send
 * without either rather than inventing a place for it, and the footer counts what was drawn.
 *
 * ## The reading is not a deal
 *
 * It enters no dealt memory and notes no exposure (ADR-0174 §4 as amended); the client holds it
 * under a five-minute stale time and never appends to it (`hooks/useReading`). A row answered
 * from the record sheet stays a row — the radar hides nobody for a pass (§4) — which is #464's
 * to draw on the card's last line.
 */

import { SPORTS, type Sport } from '@/shared/vocabulary/sport';

import type { Candidate, SearchEnvelope } from './candidate';

/** One sport a player is rated in, with the Level held there — the card's sport rows. */
export interface RatedSport {
  readonly sport: Sport;
  readonly level: number;
}

/** One row of a reading: the candidate shape, and where they are drawn. */
export interface RadarRow extends Candidate {
  /** Kilometres to one decimal, spot to spot, never below 0,1. Required here — see the module note. */
  readonly distanceKm: number;
  /** 0–359, north 0, clockwise, spot to spot. On a reading's row only, never inside the card. */
  readonly bearingDeg: number;
  /** Every sport they are rated in, the registry's order. `card.level` is the reading's sport's. */
  readonly ratings: readonly RatedSport[];
}

/** One answer to `POST /radar`: the envelope every card is drawn with, and the rows drawn. */
export interface Reading {
  readonly envelope: SearchEnvelope;
  /** Ordered by drawn distance then player id, as served. Nothing on this side sorts for display. */
  readonly rows: readonly RadarRow[];
}

/**
 * The order the tiles are **painted** in: farther first, so nearer players are drawn above
 * farther ones, and the selected player last of all — above everybody (§7.4, §7.5).
 *
 * A stable sort over the served order, so two rows at one printed distance keep the id order
 * the server gave them.
 */
export function drawOrder(
  rows: readonly RadarRow[],
  selectedId: string | undefined,
): readonly RadarRow[] {
  const others = rows.filter((row) => row.playerId !== selectedId);
  const byDistanceDescending = [...others].sort((a, b) => b.distanceKm - a.distanceKm);
  const selected = rows.find((row) => row.playerId === selectedId);
  return selected === undefined ? byDistanceDescending : [...byDistanceDescending, selected];
}

/**
 * The card's sport rows: **the reading's sport first, the rest in registry order** (§7.4).
 *
 * Every sport they are rated in and not only the ones the viewer shares — the card is about
 * them. The registry order is `SPORTS`', which is the order the server serves `ratings[]` in;
 * the one move this makes is lifting the reading's sport to the top.
 */
export function sportRows(row: RadarRow, readingSport: Sport): readonly RatedSport[] {
  const rank = (sport: Sport) => (sport === readingSport ? -1 : SPORTS.indexOf(sport));
  return [...row.ratings].sort((a, b) => rank(a.sport) - rank(b.sport));
}

/**
 * Whether the selected player is still on the reading — *a selected player who is not in the
 * next reading is deselected silently* (§7.5). `undefined` is nobody selected, which is kept.
 */
export function selectionOn(
  rows: readonly RadarRow[],
  selectedId: string | undefined,
): string | undefined {
  if (selectedId === undefined) return undefined;
  return rows.some((row) => row.playerId === selectedId) ? selectedId : undefined;
}
