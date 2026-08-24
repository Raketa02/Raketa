/**
 * The instrument: five rows of two cells, one of them live.
 *
 * `ADR-0060` §5's constraint is *"a score typed standing on a court, one-handed, in
 * the dark"*, which is why the pad is a pad rather than the system keyboard or a
 * stepper. What is here is the pad's **state** and nothing about a match: which
 * cell a key lands in, where the cursor goes next, and which rows are finished
 * enough to send. There is no rule about scores in this file — the server owns
 * that, permissively, and this app holds none (`ADR-0053`).
 *
 * ## One pad for every sport, and the sport is the reason
 *
 * `ADR-0060` specifies the pad **per sport** — *"padel and tennis get 0–7, squash
 * 0–11, badminton 0–21 over four rows"* — and that cannot be built from this
 * contract: **the sport is not on the wire.** Neither the card's spine nor the
 * result screen carries it, so a phone opening this route knows the club, the
 * price, the situation and the score, and not what was played.
 *
 * So one pad ships, and it is **badminton's** — the widest of the four `ADR-0060`
 * names, which makes every score the other three can produce reachable. The cost is
 * real and is stated rather than hidden: a padel player is shown fourteen keys she
 * will never press. Filed as `Raketa02/Raketa#120`, so the per-sport pad arrives
 * with the sport rather than with a guess.
 *
 * ## Rows are finished or empty, and only finished rows are sent
 *
 * A row nobody scored in is refused by the server as impossible, so an untouched
 * row and a `0-0` are the same thing and an untouched row is simply not sent. A
 * row with **one** cell filled is neither, and it is the one thing this pad will
 * not send: `sendable` is false while one exists, because sending it would mean
 * choosing a number she did not type.
 */

import type { ScoreLine } from '@/features/now/types';

/**
 * How many rows the pad offers.
 *
 * Five, which is what an evening holds in any of the four sports — and the same
 * number the server's own validator refuses a sixth above. It is the
 * **instrument's** shape rather than a rule the phone applies: nothing here refuses
 * anything, and a score with six sets in it is rejected by the server whatever this
 * number is. The cost of the two agreeing by coincidence is that a server that one
 * day allows six would need this raised too, which is a diff somebody makes rather
 * than a silent divergence.
 */
export const PAD_ROWS = 5;

/**
 * The highest key on the pad — badminton's, and therefore everybody's.
 *
 * See the module docstring: the sport is not on the wire, so the pad is the widest
 * of `ADR-0060`'s four rather than the right one.
 */
export const PAD_MAX = 21;

/** Which cell the next key lands in. `side` is `0` for hers and `1` for theirs. */
export interface PadCell {
  readonly row: number;
  readonly side: number;
}

/** One row of the pad: her games and theirs, either of which may be untyped. */
export type PadRow = readonly [number | undefined, number | undefined];

export interface ScorePad {
  readonly rows: readonly PadRow[];
  readonly active: PadCell;
}

const EMPTY_ROW: PadRow = [undefined, undefined];

const FIRST_CELL: PadCell = { row: 0, side: 0 };

/** A pad with nothing typed into it, live on the first cell. */
export function emptyPad(): ScorePad {
  return { rows: Array.from({ length: PAD_ROWS }, () => EMPTY_ROW), active: FIRST_CELL };
}

/**
 * A pad already holding what is on the table.
 *
 * **Only ever used for a correction**, which is her own side's score, and never for
 * a counter. A counter that opened pre-filled with the score it is countering is
 * one tap from being identical to it — which consumes her side's one proposal on a
 * statement she did not mean to make, and then lets silence uncount the match. The
 * two acts differ in exactly that: correcting is editing her own sentence, and
 * countering is writing a different one.
 *
 * The score arrives viewer-first, so `first` is already her side's and no flip
 * happens here.
 */
export function padFrom(score: ScoreLine): ScorePad {
  const typed: readonly PadRow[] = score.sets
    .slice(0, PAD_ROWS)
    .map((set): PadRow => [set.first, set.second]);

  return {
    rows: [...typed, ...Array.from({ length: PAD_ROWS - typed.length }, () => EMPTY_ROW)],
    active: FIRST_CELL,
  };
}

/**
 * Type a number into the live cell, and move on.
 *
 * The cursor walks her side then theirs then the next row, which is the order a
 * scoreline is read in and the order it will be sent in. It **stops** on the last
 * cell rather than wrapping to the first: wrapping would silently overwrite the
 * score's opening set on the next key press.
 */
export function typeInPad(pad: ScorePad, value: number): ScorePad {
  return {
    rows: pad.rows.map((row, index) =>
      index === pad.active.row ? written(row, pad.active.side, value) : row,
    ),
    active: nextCell(pad.active, pad.rows.length),
  };
}

/** Move the cursor, so a cell already typed can be typed again. */
export function selectInPad(pad: ScorePad, cell: PadCell): ScorePad {
  return { ...pad, rows: pad.rows, active: cell };
}

/**
 * Empty the live row, both cells.
 *
 * The **row** and not the cell, because the row is what gets sent: clearing one
 * cell of a finished row would leave the pad holding the one shape it refuses to
 * send, which is a control that creates the problem it exists to fix. It is also
 * how a score gets *shorter* — there is no other way to un-type a set.
 */
export function clearRowInPad(pad: ScorePad): ScorePad {
  return {
    rows: pad.rows.map((row, index) => (index === pad.active.row ? EMPTY_ROW : row)),
    active: { row: pad.active.row, side: 0 },
  };
}

/** The finished rows, in the order they were typed. This is what the write sends. */
export function padSets(pad: ScorePad): readonly (readonly [number, number])[] {
  const sets: (readonly [number, number])[] = [];

  for (const [mine, theirs] of pad.rows) {
    if (mine === undefined || theirs === undefined) continue;
    sets.push([mine, theirs]);
  }

  return sets;
}

/** Whether a row is holding one number and waiting for the other. */
export function padHasUnfinishedRow(pad: ScorePad): boolean {
  return pad.rows.some(([mine, theirs]) => (mine === undefined) !== (theirs === undefined));
}

/**
 * Whether there is a score here to send.
 *
 * At least one finished row and no half-typed one. That is a fact about the
 * **instrument** — *she has finished typing* — rather than about the score: whether
 * `21-19, 3-6` is a match anybody played is the server's permissive validator's,
 * and this app does not hold a second opinion about it.
 */
export function padIsSendable(pad: ScorePad): boolean {
  return padSets(pad).length > 0 && !padHasUnfinishedRow(pad);
}

function written(row: PadRow, side: number, value: number): PadRow {
  return side === 0 ? [value, row[1]] : [row[0], value];
}

function nextCell(from: PadCell, rows: number): PadCell {
  if (from.side === 0) return { row: from.row, side: 1 };
  return from.row + 1 < rows ? { row: from.row + 1, side: 0 } : from;
}
