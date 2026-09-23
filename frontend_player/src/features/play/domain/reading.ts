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
 * under a five-minute stale time and never appends to it (`hooks/useReading`).
 *
 * ## A row answered stays a row, and remembers what was said
 *
 * *Let's play* and *Not today* from the record sheet are the deck's own answers with the
 * reading's id as their origin (§4); the person **stays on the radar** — the radar hides nobody
 * for a pass — and their card's last line reads *You said yes ›* or *Not today ›* in place of
 * the door. So the answer is written onto the row ({@link withAnswer}) rather than the row being
 * removed, by the mutation that made it and never by a refetch: a reading that comes back after
 * the window is the whole reach again, and is allowed to have forgotten. **By person, not by
 * search**: an answer names the reading it came off for the ledger's sake, and the mark is about
 * whom the reader answered, which a fresh reading of the same reach may well draw again.
 */

import { SPORTS, type Sport } from '@/shared/vocabulary/sport';

import type { Candidate, SearchEnvelope } from './candidate';
import { isLiker } from './yesBudget';

/** What the reader said about a row from the sheet — the two answers, and nothing else. */
export type RadarAnswer = 'yes' | 'no';

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
  /**
   * What the reader said about them from the sheet, on this held reading. Absent until they
   * have, and absent again on a refused write — see the module note.
   */
  readonly answered?: RadarAnswer;
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

/**
 * The reading with one row marked as answered — or unmarked, when the write was refused and the
 * mark is taken back. The same reading where it does not hold the person, so a patch of an
 * entry the answer is not about leaves the entry alone.
 */
export function withAnswer(
  reading: Reading,
  playerId: string,
  answered: RadarAnswer | undefined,
): Reading {
  if (!reading.rows.some((row) => row.playerId === playerId)) return reading;
  return {
    ...reading,
    rows: reading.rows.map((row) => {
      if (row.playerId !== playerId) return row;
      const { answered: _was, ...rest } = row;
      return answered === undefined ? rest : { ...rest, answered };
    }),
  };
}

/**
 * The reading with one fewer person waiting — **only where the row answered was a liker's**,
 * the deck's own rule read on the reading's envelope (`deckHand`'s `oneFewerWaiting`,
 * ADR-0169 §4; ADR-0174 §5).
 *
 * The chip on the radar is the deck's number on the reading's envelope, so a liker's yes come
 * back mutual counts one of the people it counted as answered, here as there. A stranger's
 * mutual was never counted; a reading that carried no count, or nought, has nothing to drop.
 */
export function oneFewerWaitingOnReading(reading: Reading, playerId: string): Reading {
  const row = reading.rows.find((one) => one.playerId === playerId);
  const waiting = reading.envelope.pool.wantToPlayYou;
  if (row === undefined || !isLiker(row) || waiting === undefined || waiting === 0) {
    return reading;
  }
  return {
    ...reading,
    envelope: {
      ...reading.envelope,
      pool: { ...reading.envelope.pool, wantToPlayYou: waiting - 1 },
    },
  };
}
