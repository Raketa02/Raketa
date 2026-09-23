/**
 * Reading a pairing — **and which of the route's answers is a pairing, which is none, and
 * which is a failure.** Driven through the real HTTP layer with only the socket faked.
 */

import { AppError } from '@/shared/errors';
import {
  errorResponse,
  installTransport,
  json,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { readPairing } from './readPairing';

const GAME = 'aaaaaaaa-0000-4000-8000-000000000009';
const PAIRING_PATH = `/api/v1/games/${GAME}/pairing`;

const SERVED: Wire['GamePairingResponse'] = {
  read_at: '2026-09-12T09:00:00Z',
  forecast: { pct: 90, sigma_group: 0.4, provisional: false, assumption: null },
  split: { your_side: 2.7, their_side: 2.71, gap: -0.01 },
  at_stake: { win_delta: 0.08, loss_delta: -0.08 },
  seats: [],
};

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
});

afterEach(() => transport.restore());

describe('readPairing', () => {
  it('reads the pairing beside the game, and never the game list', async () => {
    transport.on('GET', PAIRING_PATH, () => json(SERVED));

    const pairing = await readPairing(GAME);

    expect(pairing?.forecast).toEqual({ pct: 90 });
    expect(transport.requestsTo('GET', '/api/v1/games')).toHaveLength(0);
  });

  /**
   * The three refusals are **answers**, folded to *no pairing* by name: a game that has
   * happened, a game that is not yours, a held account. None is retried and none is an outage.
   */
  it.each([
    [404, 'game_not_found'],
    [409, 'pairing_is_history'],
    [403, 'account_held'],
  ])('resolves to no pairing on %s %s', async (status, code) => {
    transport.on('GET', PAIRING_PATH, () => errorResponse(status, code));

    await expect(readPairing(GAME)).resolves.toBeNull();
  });

  /** Anything else is the failure it is, and reaches the hook as one. */
  it('fails on a refusal it has no name for', async () => {
    transport.on('GET', PAIRING_PATH, () => errorResponse(500, 'internal_error'));

    await expect(readPairing(GAME)).rejects.toBeInstanceOf(AppError);
  });
});
