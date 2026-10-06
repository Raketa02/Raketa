/**
 * **The two rules the court's pairing carries into `domain/`**: whose row is drawn first, and
 * which of the route's refusals is an answer rather than a failure.
 *
 * The shapes themselves are types and carry no rule — the figures are the server's, and
 * a client never computes a gap, a range or a band from them.
 */

import { AppError } from '@/shared/errors';

import type { GameSeat } from './game';
import { pairingRefusedByName, sidesForReader } from './pairing';

const ME = 'me-1111-4444-8888-000000000001';
const PARTNER = 'partner-11-4444-8888-000000002';
const OPPONENT = 'opp-111111-4444-8888-00000003';

const seat = (playerId: string, side: 'A' | 'B'): GameSeat => ({ playerId, side });

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
