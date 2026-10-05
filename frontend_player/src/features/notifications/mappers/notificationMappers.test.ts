/**
 * The notices off the wire and back (#559): the three choices both ways, a listed notice into the
 * domain's, and where a tap goes from the facts a notice names — the list's row and a push's
 * payload alike.
 */

import type { Wire } from '@/test-support/transport';

import { toChoices, toChoicesRequest, toNotice, toTarget } from './notificationMappers';

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
      target: {
        opens: 'deck',
        groupId: POOL,
        proposalId: GAME,
        sport: 'padel',
        kind: 'forFun',
      },
    });
  });

  it('opens nowhere for a sport this build cannot name — and is still listed', () => {
    const notice = toNotice({ ...NOTICE, sport: 'PICKLEBALL' as Wire['Sport'] });
    expect(notice.title).toBe('You complete it');
    expect(notice.target).toBeUndefined();
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
});
