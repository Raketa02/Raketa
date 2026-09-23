/**
 * **The two rules the court's pairing carries into `domain/`**: whose row is drawn first, and
 * which of the route's refusals is an answer rather than a failure.
 *
 * The shapes themselves are types and carry no rule — the figures are the server's, and
 * `the-play-screens.md` §5 forbids a client computing a gap, a range or a band from them.
 */

import { AppError } from '@/shared/errors';

import type { GameSeat } from './game';
import { courtForReader, pairingRefusedByName, sidesForReader } from './pairing';

const ME = 'me-1111-4444-8888-000000000001';
const PARTNER = 'partner-11-4444-8888-000000002';
const OPPONENT = 'opp-111111-4444-8888-00000003';
const OTHER_OPPONENT = 'opp-222222-4444-8888-00000004';

const seat = (playerId: string, side: 'A' | 'B'): GameSeat => ({ playerId, side });

describe('courtForReader', () => {
  /**
   * §5.5's row order: **your side first — you, then your partner — then the other side.** The
   * court arrives in the challenge's own order, which is whoever seated whom, and a reader who
   * is on side B is still the first row.
   */
  it('puts your side first and you at the head of it, whichever side you sit on', () => {
    const court = [
      seat(OPPONENT, 'A'),
      seat(OTHER_OPPONENT, 'A'),
      seat(PARTNER, 'B'),
      seat(ME, 'B'),
    ];

    expect(courtForReader(court, ME).map((one) => one.playerId)).toEqual([
      ME,
      PARTNER,
      OPPONENT,
      OTHER_OPPONENT,
    ]);
  });

  /** Inside a side the court's own order is kept: the other side is not re-sorted either. */
  it('keeps the court’s order inside each side', () => {
    const court = [seat(OTHER_OPPONENT, 'B'), seat(ME, 'A'), seat(OPPONENT, 'B')];

    expect(courtForReader(court, ME).map((one) => one.playerId)).toEqual([
      ME,
      OTHER_OPPONENT,
      OPPONENT,
    ]);
  });

  /** A singles court is two rows, you first. */
  it('is you then them on a singles court', () => {
    const court = [seat(OPPONENT, 'A'), seat(ME, 'B')];

    expect(courtForReader(court, ME).map((one) => one.playerId)).toEqual([ME, OPPONENT]);
  });

  /**
   * A reader holding no seat is a stale link, and the screen around this has already said so.
   * The court is handed back as it came rather than invented an order for.
   */
  it('hands the court back unchanged when no seat is the reader’s', () => {
    const court = [seat(OPPONENT, 'A'), seat(PARTNER, 'B')];

    expect(courtForReader(court, ME)).toEqual(court);
  });
});

describe('pairingRefusedByName', () => {
  const refused = (status: number, code: string) =>
    new AppError('not-found', 'terminal', 'refused', { status, code });

  /**
   * The route's three refusals are **answers**: no game of yours has that id, the game has
   * happened, or the account is held. Each is *no pairing to draw* rather than a failure to
   * retry, and the block draws nothing either way — what the name buys is that a refusal is
   * never reported or retried as an outage.
   */
  it.each([
    [404, 'game_not_found'],
    [409, 'pairing_is_history'],
    [403, 'account_held'],
  ])('is true for %s %s', (status, code) => {
    expect(pairingRefusedByName(refused(status, code))).toBe(true);
  });

  /** Branch on the code, never on the status: a 409 with another name is not this refusal. */
  it('is false for a status without one of the three names', () => {
    expect(pairingRefusedByName(refused(409, 'something_else'))).toBe(false);
    expect(
      pairingRefusedByName(new AppError('network-unavailable', 'retryable-automatically', 'x')),
    ).toBe(false);
  });
});

describe('sidesForReader', () => {
  /** The same order as two halves — one split, read by the bar's labels and the row's names. */
  it('splits the court into yours and theirs, you first on yours', () => {
    const court = [seat(OPPONENT, 'A'), seat(PARTNER, 'B'), seat(ME, 'B')];

    expect(sidesForReader(court, ME)).toEqual({
      yours: [seat(ME, 'B'), seat(PARTNER, 'B')],
      theirs: [seat(OPPONENT, 'A')],
    });
  });

  it('has no halves for a reader holding no seat', () => {
    expect(sidesForReader([seat(OPPONENT, 'A')], ME)).toBeUndefined();
  });
});
