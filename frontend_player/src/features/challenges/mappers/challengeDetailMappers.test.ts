/**
 * The detail read crossing the wire — **the three codes that are narrowed three different ways**,
 * and the cards that ride a reply that has none.
 *
 * The field renaming is not asserted: a mapper that dropped `area_code` fails `pnpm typecheck` in
 * the file that reads it. What is asserted is every place this file makes a **decision** — which
 * absence a code collapses to, which record survives one it cannot read, and what an answer's
 * reply is allowed to carry away with it.
 */

import type { Wire } from '@/test-support/transport';

import { toAnsweredChallenge, toChallengeDetail } from './challengeDetailMappers';

const ME = 'me';
const EWA = 'ewa';

const A_CARD: Wire['SeatCardSchema'] = {
  person: {
    name: 'ewa.m',
    area_code: 'WAW-C',
    level: 2.71,
    band: 'Established',
    range: { low: 2.55, high: 2.87 },
  },
  pairing: { fit: 78, terms: [], degraded_terms: [], concerns: [] },
};

function response(
  over: Partial<Wire['ChallengeDetailResponse']> = {},
): Wire['ChallengeDetailResponse'] {
  return {
    read_at: '2026-09-08T12:00:00Z',
    challenge_id: 'c1',
    sport: 'SQUASH',
    organiser_id: EWA,
    standing: 'AWAITING_ANSWERS',
    opened_at: '2026-09-08T08:00:00Z',
    seats: [
      { side: 'A', player_id: EWA, answer: 'ACCEPTED', name: 'ewa.m', card: A_CARD },
      { side: 'B', player_id: ME, answer: null, answer_by: '2026-09-10T08:00:00Z' },
    ],
    ...over,
  };
}

describe('the three codes, narrowed three ways', () => {
  /** The code *is* the whole sentence, so the row draws §3's named gap and the record stays. */
  it('keeps a challenge whose standing this build cannot read', () => {
    const detail = toChallengeDetail(
      response({ standing: 'SOMETHING_NEW' as Wire['ChallengeDetailResponse']['standing'] }),
    );

    expect(detail?.standing).toBeUndefined();
    expect(detail?.seats).toHaveLength(2);
  });

  /** The sport is what the screen calls the challenge: a record it cannot name has a hole
   * where the identifying fact goes, so the whole read goes with it. */
  it('drops a challenge whose sport it cannot name', () => {
    expect(
      toChallengeDetail(response({ sport: 'CURLING' as Wire['ChallengeDetailResponse']['sport'] })),
    ).toBeUndefined();
  });

  /**
   * The safe direction, and the only one: this field explains an emptiness the reader can
   * already see, so a sentence written from a code we cannot read would be this app guessing
   * whose gap it was.
   */
  it('reports no absence at all for an absence code it cannot read', () => {
    const detail = toChallengeDetail(
      response({
        pairing_absence: 'SOMETHING_NEW' as Wire['ChallengeDetailResponse']['pairing_absence'],
      }),
    );

    expect(detail?.pairingAbsence).toBeUndefined();
  });

  it('carries an absence it can read', () => {
    expect(
      toChallengeDetail(response({ pairing_absence: 'COULD_NOT_BE_READ' }))?.pairingAbsence,
    ).toBe('COULD_NOT_BE_READ');
  });
});

describe('null is *this response said nothing*', () => {
  it('collapses every optional to absent, so no screen has two spellings of one gap', () => {
    const detail = toChallengeDetail(
      response({
        seats: [{ side: 'A', player_id: null, answer: null, answer_by: null, name: null }],
      }),
    );

    expect(detail?.seats[0]).toEqual({});
  });
});

describe('the card is per seat', () => {
  it('keeps it where the wire drew one and invents none where it did not', () => {
    const detail = toChallengeDetail(response());

    expect(detail?.seats[0]?.card?.person.name).toBe('ewa.m');
    expect(detail?.seats[1]?.card).toBeUndefined();
  });

  /** ADR-0140: omitted where the platform has watched nothing, and never read as a nought. */
  it('leaves a Player Score absent rather than zero', () => {
    expect(toChallengeDetail(response())?.seats[0]?.card?.person.playerScore).toBeUndefined();
  });
});

describe("what an answer's reply carries", () => {
  /**
   * `ChallengeSchema` is the list's shape and has no cards in it — which is not a loss, because
   * `redrawnFrom` keeps the ones the screen is holding and the arm drops them when the standing
   * moves past the two that draw a block.
   */
  it('is the standing and the court, and nothing the screen already holds', () => {
    const answered = toAnsweredChallenge({
      challenge_id: 'c1',
      sport: 'SQUASH',
      organiser_id: EWA,
      standing: 'LINE_UP_INCOMPLETE',
      opened_at: '2026-09-08T08:00:00Z',
      seats: [
        { side: 'A', player_id: EWA, answer: 'ACCEPTED', name: 'ewa.m' },
        { side: 'B', player_id: ME, answer: 'DECLINED' },
      ],
    });

    expect(answered).toEqual({
      standing: 'LINE_UP_INCOMPLETE',
      seats: [
        { playerId: EWA, answer: 'ACCEPTED', name: 'ewa.m' },
        { playerId: ME, answer: 'DECLINED' },
      ],
    });
  });
});
