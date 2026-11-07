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

  // #663: each step at the court opens the booked game's result screen.
  it('reads a step at the court, which opens the result screen', () => {
    expect(parsePushNotice({ ...PAYLOAD, kind: 'IS_THAT_RIGHT', opens: 'RESULT' })).toMatchObject({
      kind: 'IS_THAT_RIGHT',
      opens: 'RESULT',
      gameId: PAYLOAD.game_id,
    });
  });

  // #727, #731: *Get your level* is about no game — the backend pushes its id, kind and Home alone.
  it('reads a notice about no game, which opens Home and names nothing more', () => {
    const level = { notice_id: PAYLOAD.notice_id, kind: 'GET_YOUR_LEVEL', opens: 'HOME' };

    expect(parsePushNotice(level)).toEqual({
      noticeId: PAYLOAD.notice_id,
      kind: 'GET_YOUR_LEVEL',
      opens: 'HOME',
      gameId: null,
      poolId: null,
      sport: null,
      gameKind: null,
    });
  });

  it('never reads a game’s facts off a push that opens Home', () => {
    expect(parsePushNotice({ ...PAYLOAD, kind: 'GET_YOUR_LEVEL', opens: 'HOME' })).toMatchObject({
      opens: 'HOME',
      gameId: null,
      poolId: null,
    });
  });

  // #753: *You're friends* opens the friend's record, named by `player_id` (#745's push data).
  it('reads a friend’s notice, which opens their record by the person it names', () => {
    const PERSON = '3f2b8c1e-0000-4000-8000-000000000102';
    expect(
      parsePushNotice({
        notice_id: PAYLOAD.notice_id,
        kind: 'FRIENDS_MADE',
        opens: 'RECORD',
        player_id: PERSON,
      }),
    ).toEqual({
      noticeId: PAYLOAD.notice_id,
      kind: 'FRIENDS_MADE',
      opens: 'RECORD',
      gameId: null,
      poolId: null,
      sport: null,
      gameKind: null,
      playerId: PERSON,
    });
  });

  it('is nothing to open when a record’s push names nobody, or not by an id', () => {
    const record = { notice_id: PAYLOAD.notice_id, kind: 'FRIENDS_MADE', opens: 'RECORD' };
    expect(parsePushNotice(record)).toBeUndefined();
    expect(parsePushNotice({ ...record, player_id: '../../me' })).toBeUndefined();
  });

  // A friend request names its requester too, and opens Home, where its card is.
  it('reads a friend request as a notice that opens Home', () => {
    expect(
      parsePushNotice({
        notice_id: PAYLOAD.notice_id,
        kind: 'FRIEND_REQUEST',
        opens: 'HOME',
        player_id: '3f2b8c1e-0000-4000-8000-000000000102',
      }),
    ).toMatchObject({ kind: 'FRIEND_REQUEST', opens: 'HOME', gameId: null });
  });

  // #749, #758: an ask for a level pushes the sport it names — and the group, for the picker.
  it('reads Level asked, which opens the sport’s questionnaire by the sport it names', () => {
    expect(
      parsePushNotice({
        notice_id: PAYLOAD.notice_id,
        kind: 'LEVEL_ASKED',
        opens: 'QUESTIONNAIRE',
        player_id: '3f2b8c1e-0000-4000-8000-000000000102',
        sport: 'PADEL',
      }),
    ).toEqual({
      noticeId: PAYLOAD.notice_id,
      kind: 'LEVEL_ASKED',
      opens: 'QUESTIONNAIRE',
      gameId: null,
      poolId: null,
      sport: 'PADEL',
      gameKind: null,
    });
  });

  it('reads Level got, which opens the picker of the group it names, in the sport', () => {
    expect(
      parsePushNotice({
        notice_id: PAYLOAD.notice_id,
        kind: 'LEVEL_GOT',
        opens: 'PICKER',
        player_id: '3f2b8c1e-0000-4000-8000-000000000102',
        pool_id: PAYLOAD.pool_id,
        sport: 'PADEL',
      }),
    ).toEqual({
      noticeId: PAYLOAD.notice_id,
      kind: 'LEVEL_GOT',
      opens: 'PICKER',
      gameId: null,
      poolId: PAYLOAD.pool_id,
      sport: 'PADEL',
      gameKind: null,
    });
  });

  it('is nothing to open when an ask’s push names no sport, or the picker’s no group', () => {
    const asked = { notice_id: PAYLOAD.notice_id, kind: 'LEVEL_ASKED', opens: 'QUESTIONNAIRE' };
    const got = { notice_id: PAYLOAD.notice_id, kind: 'LEVEL_GOT', opens: 'PICKER' };
    expect(parsePushNotice(asked)).toBeUndefined();
    expect(parsePushNotice({ ...got, sport: 'PADEL' })).toBeUndefined();
    expect(parsePushNotice({ ...got, sport: 'PADEL', pool_id: '../../admin' })).toBeUndefined();
  });

  it('is nothing to open when a game’s push names no game', () => {
    expect(
      parsePushNotice({ notice_id: PAYLOAD.notice_id, kind: 'GAME_BOOKED', opens: 'BOOKING' }),
    ).toBeUndefined();
  });

  it('is nothing to open when a key is missing or is not what it says', () => {
    expect(parsePushNotice({ ...PAYLOAD, opens: 'SOMEWHERE' })).toBeUndefined();
    expect(parsePushNotice({ ...PAYLOAD, opens: 'result' })).toBeUndefined();
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
