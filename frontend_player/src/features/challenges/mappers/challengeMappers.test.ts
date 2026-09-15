/**
 * The court going out, and the list coming back.
 *
 * The claim worth a test is the one the compiler cannot make: **the side is derived from the
 * position**, so the request is *every A, then every B* whoever is standing where — including
 * an organiser who moved themselves across the net, and including a hole nobody filled.
 */

import type { Wire } from '@/test-support/transport';

import { toChallenges, toSendChallengeRequest } from './challengeMappers';

const SEARCH = 'search-1';
/** The instant the whole list was folded against — every duration on a row is read from it. */
const READ_AT = '2026-09-01T12:00:00Z';

const ME = 'me';
const BEA = 'bea';
const CYRYL = 'cyryl';
const DOROTA = 'dorota';

describe('the court a send carries', () => {
  it('is every A seat then every B, in the order the court draws them', () => {
    const request = toSendChallengeRequest({
      searchId: SEARCH,
      court: [ME, BEA, CYRYL, DOROTA],
    });

    expect(request.search_id).toBe(SEARCH);
    expect(request.court).toEqual([
      { side: 'A', player_id: ME },
      { side: 'A', player_id: BEA },
      { side: 'B', player_id: CYRYL },
      { side: 'B', player_id: DOROTA },
    ]);
  });

  /** Swap mode is *change sides, never seats*, and a side follows you. */
  it('puts the organiser on B when that is the half they are standing in', () => {
    const request = toSendChallengeRequest({ searchId: SEARCH, court: [BEA, ME] });

    expect(request.court).toEqual([
      { side: 'A', player_id: BEA },
      { side: 'B', player_id: ME },
    ]);
  });

  /** An empty seat is a seat: it keeps its place, because which side is short is a fact. */
  it('keeps a hole in the list, carrying nobody', () => {
    const request = toSendChallengeRequest({
      searchId: SEARCH,
      court: [ME, BEA, undefined, DOROTA],
    });

    expect(request.court).toEqual([
      { side: 'A', player_id: ME },
      { side: 'A', player_id: BEA },
      { side: 'B' },
      { side: 'B', player_id: DOROTA },
    ]);
  });
});

describe('the challenges coming back', () => {
  it('reads a seat’s occupant and answer, and leaves an empty seat empty', () => {
    const response: Wire['ChallengeListResponse'] = {
      read_at: READ_AT,
      challenges: [
        {
          challenge_id: 'c1',
          sport: 'PADEL',
          organiser_id: ME,
          standing: 'LINE_UP_INCOMPLETE',
          opened_at: '2026-09-01T10:00:00Z',
          seats: [
            { side: 'A', player_id: ME, answer: 'ACCEPTED' },
            { side: 'A', player_id: BEA, answer: 'ACCEPTED' },
            { side: 'B', player_id: CYRYL, answer: 'DECLINED', name: 'cyryl.k' },
            { side: 'B', player_id: null, answer: null, answer_by: null, name: null },
          ],
        },
      ],
    };

    expect(toChallenges(response)).toEqual([
      {
        challengeId: 'c1',
        organiserId: ME,
        standing: 'LINE_UP_INCOMPLETE',
        sport: 'padel',
        openedAt: '2026-09-01T10:00:00Z',
        readAt: READ_AT,
        seats: [
          { playerId: ME, answer: 'ACCEPTED' },
          { playerId: BEA, answer: 'ACCEPTED' },
          { playerId: CYRYL, answer: 'DECLINED', name: 'cyryl.k' },
          {},
        ],
      },
    ]);
  });

  /** A seat nobody has answered carries no answer at all — *awaiting* is the absence of one. */
  it('leaves an unanswered seat without an answer', () => {
    const response: Wire['ChallengeListResponse'] = {
      read_at: READ_AT,
      challenges: [
        {
          challenge_id: 'c2',
          sport: 'TENNIS',
          organiser_id: ME,
          standing: 'AWAITING_ANSWERS',
          opened_at: '2026-09-01T10:00:00Z',
          seats: [
            { side: 'A', player_id: ME, answer: 'ACCEPTED' },
            { side: 'B', player_id: BEA, answer_by: '2026-09-02T10:00:00Z' },
          ],
        },
      ],
    };

    expect(toChallenges(response)[0]?.seats[1]).toEqual({
      playerId: BEA,
      answerBy: '2026-09-02T10:00:00Z',
    });
  });

  /**
   * A standing the app has no words for keeps its challenge, because the code **is** the whole
   * line: `the-words.md` §3 owes it a named gap on the row rather than a shorter list.
   */
  it('drops a standing it cannot read and keeps the challenge', () => {
    const response = {
      read_at: READ_AT,
      challenges: [
        {
          challenge_id: 'c3',
          sport: 'SQUASH',
          organiser_id: ME,
          standing: 'ABANDONED_BY_THE_MOON',
          opened_at: '2026-09-01T10:00:00Z',
          seats: [{ side: 'A', player_id: ME, answer: 'ACCEPTED' }],
        },
      ],
    } as unknown as Wire['ChallengeListResponse'];

    const [challenge] = toChallenges(response);

    expect(challenge?.challengeId).toBe('c3');
    expect(challenge?.standing).toBeUndefined();
  });

  /**
   * `null` and a missing key are the same absence to this mapper, which is every nullable field
   * on this list's own rule — and the domain field is absent either way, so no reader can
   * subtract a nothing from a clock.
   */
  it('carries an ending’s instant, and carries no field where nothing ended', () => {
    const response: Wire['ChallengeListResponse'] = {
      read_at: READ_AT,
      challenges: [
        {
          challenge_id: 'c5',
          sport: 'TENNIS',
          organiser_id: ME,
          standing: 'WITHDRAWN',
          opened_at: '2026-09-01T10:00:00Z',
          ended_at: '2026-09-03T09:00:00Z',
          seats: [{ side: 'A', player_id: ME, answer: 'ACCEPTED' }],
        },
        {
          challenge_id: 'c6',
          sport: 'TENNIS',
          organiser_id: ME,
          standing: 'AWAITING_ANSWERS',
          opened_at: '2026-09-01T10:00:00Z',
          ended_at: null,
          seats: [{ side: 'A', player_id: ME, answer: 'ACCEPTED' }],
        },
      ],
    };

    const [withdrawn, standing] = toChallenges(response);

    expect(withdrawn?.endedAt).toBe('2026-09-03T09:00:00Z');
    expect(standing).not.toHaveProperty('endedAt');
  });

  /** A sport takes the whole row with it: it is what the row calls the game. */
  it('drops a challenge whose sport it cannot read', () => {
    const response = {
      read_at: READ_AT,
      challenges: [
        {
          challenge_id: 'c4',
          sport: 'PICKLEBALL',
          organiser_id: ME,
          standing: 'ON',
          opened_at: '2026-09-01T10:00:00Z',
          seats: [{ side: 'A', player_id: ME, answer: 'ACCEPTED' }],
        },
      ],
    } as unknown as Wire['ChallengeListResponse'];

    expect(toChallenges(response)).toEqual([]);
  });
});
