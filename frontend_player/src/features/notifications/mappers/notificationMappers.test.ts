/**
 * The notices off the wire and back (#559): the three choices both ways, a listed notice into the
 * domain's, and where a tap goes from the facts a notice names — the list's row and a push's
 * payload alike.
 */

import type { Wire } from '@/test-support/transport';

import {
  toChoices,
  toChoicesRequest,
  toNotice,
  toRecentNotices,
  toTarget,
} from './notificationMappers';

const GAME = '7a1c2f0e-3b4d-4e5f-8a9b-0c1d2e3f4a5b';
const POOL = '9b8a7c6d-5e4f-4a3b-8c2d-1e0f9a8b7c6d';

const NOTICE: Wire['NoticeSchema'] = {
  notice_id: '0f1e2d3c-4b5a-4968-8776-655443322110',
  kind: 'YOU_COMPLETE_IT',
  title: 'You complete it',
  body: 'Padel · Sat 16:00 at Bonarka needs only you.',
  given_at: '2026-10-02T12:05:00Z',
  opens: 'DECK',
  game_id: GAME,
  pool_id: POOL,
  sport: 'PADEL',
  game_kind: 'FOR_FUN',
  gathered: 0,
  new: true,
  your_own: false,
  player_id: null,
};

describe('the three choices', () => {
  it('are read in the domain’s names', () => {
    expect(
      toChoices({ you_complete_it: true, challenges_for_you: false, fill_in_alerts: true }),
    ).toEqual({ youCompleteIt: true, challengesForYou: false, fillInAlerts: true });
  });

  it('are sent all three, every time — the route replaces them', () => {
    expect(
      toChoicesRequest({ youCompleteIt: false, challengesForYou: true, fillInAlerts: false }),
    ).toEqual({ you_complete_it: false, challenges_for_you: true, fill_in_alerts: false });
  });
});

describe('a listed notice', () => {
  it('keeps the words it was pushed in, when it was given, and where it opens', () => {
    expect(toNotice(NOTICE)).toEqual({
      id: NOTICE.notice_id,
      kind: 'YOU_COMPLETE_IT',
      title: 'You complete it',
      body: 'Padel · Sat 16:00 at Bonarka needs only you.',
      givenAt: '2026-10-02T12:05:00Z',
      isNew: true,
      yourOwn: false,
      target: {
        opens: 'deck',
        groupId: POOL,
        proposalId: GAME,
        sport: 'padel',
        kind: 'forFun',
      },
    });
  });

  it('keeps whether it is the player’s own — born seen, never new (Q102)', () => {
    const own = toNotice({ ...NOTICE, kind: 'GAME_BOOKED', new: false, your_own: true });
    expect(own.isNew).toBe(false);
    expect(own.yourOwn).toBe(true);
  });

  it('opens nowhere for a sport this build cannot name — and is still listed', () => {
    const notice = toNotice({ ...NOTICE, sport: 'PICKLEBALL' as Wire['Sport'] });
    expect(notice.title).toBe('You complete it');
    expect(notice.target).toBeUndefined();
  });
});

describe('the list behind the bell', () => {
  it('carries the bell’s number beside the rows, exact past 99 (Q101)', () => {
    const read = toRecentNotices({
      notices: [NOTICE],
      new_count: 120,
      last_opened_at: '2026-10-01T08:00:00Z',
    });
    expect(read.newCount).toBe(120);
    expect(read.notices.map((notice) => notice.id)).toEqual([NOTICE.notice_id]);
  });
});

describe('where a tap goes', () => {
  it('a booked game, by its booking — the game’s own id', () => {
    expect(
      toTarget({
        kind: 'GAME_BOOKED',
        opens: 'BOOKING',
        gameId: GAME,
        poolId: POOL,
        sport: 'TENNIS',
        gameKind: 'COMPETITIVE',
      }),
    ).toEqual({ opens: 'booking', bookingId: GAME });
  });

  // Q122 (#671): the contract's new kind is spelled so it opens where it is sent — the booked game.
  it('Game moved, to the booked game it moved', () => {
    expect(
      toTarget({
        kind: 'GAME_MOVED',
        opens: 'BOOKING',
        gameId: GAME,
        poolId: POOL,
        sport: 'PADEL',
        gameKind: 'COMPETITIVE',
      }),
    ).toEqual({ opens: 'booking', bookingId: GAME });
  });

  // Q110: the four matched with one payment missing — the game is still the proposal's, waiting.
  it('It’s a game! · waiting for one payment, to the game’s details in its group', () => {
    expect(
      toTarget({
        kind: 'WAITING_FOR_A_PAYMENT',
        opens: 'PROPOSAL',
        gameId: GAME,
        poolId: POOL,
        sport: 'PADEL',
        gameKind: 'COMPETITIVE',
      }),
    ).toEqual({
      opens: 'game',
      groupId: POOL,
      proposalId: GAME,
      sport: 'padel',
      kind: 'competitive',
    });
  });

  // Q107: the card first a club's cancel promised, on top of the deck it was dealt in.
  it('Your new game, to the group’s deck with the card on top', () => {
    expect(
      toTarget({
        kind: 'NEW_GAME',
        opens: 'DECK',
        gameId: GAME,
        poolId: POOL,
        sport: 'PADEL',
        gameKind: 'FOR_FUN',
      }),
    ).toEqual({
      opens: 'deck',
      groupId: POOL,
      proposalId: GAME,
      sport: 'padel',
      kind: 'forFun',
    });
  });

  it('a Fill in alert, to the open seat seen from outside', () => {
    expect(
      toTarget({
        kind: 'FILL_IN_ALERT',
        opens: 'BOOKING',
        gameId: GAME,
        poolId: POOL,
        sport: 'TENNIS',
        gameKind: 'COMPETITIVE',
      }),
    ).toEqual({ opens: 'rescue', groupId: POOL, bookingId: GAME });
  });

  // #663: each step at the court, named by this build, to the booked game's result screen.
  it.each(['NOT_HERE_YET', 'AT_THE_CLUB', 'HOW_DID_IT_GO', 'IS_THAT_RIGHT', 'WERE_THEY_THERE'])(
    '%s, to the booked game’s result screen, by its booking',
    (kind) => {
      expect(
        toTarget({
          kind,
          opens: 'RESULT',
          gameId: GAME,
          poolId: POOL,
          sport: 'PADEL',
          gameKind: 'COMPETITIVE',
        }),
      ).toEqual({ opens: 'result', bookingId: GAME });
    },
  );

  it('nowhere for a notice this build cannot name', () => {
    expect(
      toTarget({
        kind: 'SOMETHING_NEW',
        opens: 'BOOKING',
        gameId: GAME,
        poolId: POOL,
        sport: 'TENNIS',
        gameKind: 'COMPETITIVE',
      }),
    ).toBeUndefined();
  });

  it('nowhere for a kind this build cannot name', () => {
    expect(
      toTarget({
        kind: 'POST_DID_NOT_FILL',
        opens: 'PROPOSAL',
        gameId: GAME,
        poolId: POOL,
        sport: 'TENNIS',
        gameKind: 'CASUAL',
      }),
    ).toBeUndefined();
  });

  /**
   * **A notice about no game** (#727): *Get your level* names no game and opens Home (#731), where
   * its card is.
   */
  it('Home for a notice that opens Home', () => {
    expect(
      toTarget({
        kind: 'GET_YOUR_LEVEL',
        opens: 'HOME',
        gameId: null,
        poolId: null,
        sport: null,
        gameKind: null,
      }),
    ).toEqual({ opens: 'home' });
  });

  it('Home whatever the notice, for one that says it opens Home — there is nothing to name', () => {
    expect(
      toTarget({
        kind: 'A_NOTICE_FROM_A_LATER_RELEASE',
        opens: 'HOME',
        gameId: null,
        poolId: null,
        sport: null,
        gameKind: null,
      }),
    ).toEqual({ opens: 'home' });
  });

  /** **You're friends** (#753, #745) opens the new friend's record, by the person it names. */
  it('the record of the person a friend’s notice names', () => {
    expect(
      toTarget({
        kind: 'FRIENDS_MADE',
        opens: 'RECORD',
        gameId: null,
        poolId: null,
        sport: null,
        gameKind: null,
        playerId: 'p-kuba',
      }),
    ).toEqual({ opens: 'record', playerId: 'p-kuba' });
  });

  it('nowhere for a record’s notice that names nobody', () => {
    expect(
      toTarget({
        kind: 'FRIENDS_MADE',
        opens: 'RECORD',
        gameId: null,
        poolId: null,
        sport: null,
        gameKind: null,
        playerId: null,
      }),
    ).toBeUndefined();
  });

  it('nowhere for a notice that names no game, wherever it says it opens', () => {
    expect(
      toTarget({
        kind: 'GAME_BOOKED',
        opens: 'BOOKING',
        gameId: null,
        poolId: null,
        sport: null,
        gameKind: null,
      }),
    ).toBeUndefined();
  });
});

describe('a listed friend’s notice (#753)', () => {
  it('a request opens Home, where its card is', () => {
    expect(
      toNotice({
        ...NOTICE,
        kind: 'FRIEND_REQUEST',
        opens: 'HOME',
        game_id: null,
        pool_id: 'group-1',
        sport: null,
        game_kind: null,
        player_id: 'p-ines',
      }).target,
    ).toEqual({ opens: 'home' });
  });

  it('You’re friends opens the friend’s record', () => {
    expect(
      toNotice({
        ...NOTICE,
        kind: 'FRIENDS_MADE',
        opens: 'RECORD',
        game_id: null,
        pool_id: null,
        sport: null,
        game_kind: null,
        player_id: 'p-kuba',
      }).target,
    ).toEqual({ opens: 'record', playerId: 'p-kuba' });
  });
});

describe('a listed notice about no game', () => {
  it('is listed in the backend’s words, opening Home', () => {
    const served: Wire['NoticeSchema'] = {
      ...NOTICE,
      kind: 'GET_YOUR_LEVEL',
      title: 'Get your level so your groups can deal you games.',
      body: 'Pick the sports you play — a few questions each.',
      opens: 'HOME',
      game_id: null,
      pool_id: null,
      sport: null,
      game_kind: null,
    };

    const notice = toNotice(served);

    expect(notice).toMatchObject({
      kind: 'GET_YOUR_LEVEL',
      title: 'Get your level so your groups can deal you games.',
      body: 'Pick the sports you play — a few questions each.',
      target: { opens: 'home' },
    });
  });
});
