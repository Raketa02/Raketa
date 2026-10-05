/**
 * **A push's payload is untrusted input** (#559; `docs/architecture.md` Part 13): what it carried is
 * checked before anything is opened — the backend's seven keys (`pushing.py`) — and anything that is
 * not one is nothing to open.
 */

import { parsePushNotice } from './pushNotice';

const PAYLOAD = {
  notice_id: '0f1e2d3c-4b5a-4968-8776-655443322110',
  kind: 'GAME_BOOKED',
  opens: 'BOOKING',
  game_id: '7a1c2f0e-3b4d-4e5f-8a9b-0c1d2e3f4a5b',
  pool_id: '9b8a7c6d-5e4f-4a3b-8c2d-1e0f9a8b7c6d',
  sport: 'PADEL',
  game_kind: 'COMPETITIVE',
};

describe('a push’s payload', () => {
  it('is read into the facts a tap opens by', () => {
    expect(parsePushNotice(PAYLOAD)).toEqual({
      noticeId: PAYLOAD.notice_id,
      kind: 'GAME_BOOKED',
      opens: 'BOOKING',
      gameId: PAYLOAD.game_id,
      poolId: PAYLOAD.pool_id,
      sport: 'PADEL',
      gameKind: 'COMPETITIVE',
    });
  });

  it('is nothing to open when a key is missing or is not what it says', () => {
    expect(parsePushNotice({ ...PAYLOAD, opens: 'SOMEWHERE' })).toBeUndefined();
    expect(parsePushNotice({ ...PAYLOAD, notice_id: 'not-an-id' })).toBeUndefined();
    expect(parsePushNotice({ ...PAYLOAD, game_id: '../../admin' })).toBeUndefined();
    expect(parsePushNotice({ ...PAYLOAD, pool_id: undefined })).toBeUndefined();
  });

  it('is nothing to open when it is not an object at all', () => {
    expect(parsePushNotice(undefined)).toBeUndefined();
    expect(parsePushNotice('BOOKING')).toBeUndefined();
    expect(parsePushNotice(null)).toBeUndefined();
  });

  it('keeps nothing it does not open by', () => {
    expect(parsePushNotice({ ...PAYLOAD, token: 'ExponentPushToken[x]' })).not.toHaveProperty(
      'token',
    );
  });
});
