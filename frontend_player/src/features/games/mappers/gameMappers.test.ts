/**
 * The wire boundary, and the one asymmetry it holds: **vocabulary degrades in place, structure
 * is refused whole.**
 *
 * The list is *"your games, newest arrangement first"*, and a client that dropped a row because
 * a code on it had grown a fifth value would be the same class of lie as a read-back that got
 * shorter. So a standing this build cannot read leaves a game in the list with a named gap, and
 * only a sport with no score shape or a side with no place on a court takes one out.
 */

import type { Wire } from '@/test-support/transport';

import { toGame, toGames, toStateResultRequest } from './gameMappers';

const READ_AT = '2026-09-05T09:00:00Z';

function wireGame(over: Partial<Wire['GameSchema']> = {}): Wire['GameSchema'] {
  return {
    game_id: 'game-1',
    booking_id: 'booking-1',
    sport: 'PADEL',
    kind: 'COUNTED',
    standing: 'AWAITING_ENTRY',
    planned_at: '2026-09-01T18:00:00Z',
    seats: [
      { side: 'A', player_id: 'me' },
      { side: 'B', player_id: 'them' },
    ],
    proposals: [],
    no_shows: [],
    ...over,
  };
}

/** One side's score on the table, with the deadline the screens read off it. */
function wireProposal(side: 'A' | 'B'): Wire['StandingProposalSchema'] {
  return {
    side,
    proposed_by: side === 'A' ? 'me' : 'them',
    score: { sets: [{ a: 4, b: 6 }] },
    proposed_at: '2026-09-04T20:12:00Z',
    answer_by: '2026-09-05T20:12:00Z',
  };
}

describe('one game off the wire', () => {
  it('carries the instant the list was folded against, so a countdown cannot disagree', () => {
    expect(toGame(wireGame(), READ_AT)?.readAt).toBe(READ_AT);
  });

  it('collapses every null to absent, so no screen has two spellings of nothing', () => {
    const game = toGame(
      wireGame({ played_at: null, entry_closes_at: null, score: null, outcome: null }),
      READ_AT,
    );

    expect(game).toMatchObject({ playedAt: undefined, score: undefined, outcome: undefined });
  });

  it('reads the scores on the table whole, with when silence makes each the result', () => {
    const game = toGame(
      wireGame({
        standing: 'AWAITING_ANSWER',
        played_at: '2026-09-04T20:12:00Z',
        proposals: [wireProposal('B')],
      }),
      READ_AT,
    );

    expect(game?.proposals).toEqual([
      {
        side: 'B',
        proposedBy: 'them',
        score: { sets: [{ a: 4, b: 6 }] },
        answerBy: '2026-09-05T20:12:00Z',
      },
    ]);
  });

  /**
   * Both of them, in the server's order — *side A's first and never in the order they arrived*,
   * because the order of the two acts is a fact about who reached their phone first.
   */
  it('keeps both scores of a disagreement, in the order they were served', () => {
    const game = toGame(
      wireGame({
        standing: 'AWAITING_ANSWER',
        played_at: '2026-09-04T20:12:00Z',
        proposals: [wireProposal('A'), wireProposal('B')],
      }),
      READ_AT,
    );

    expect(game?.proposals.map((one) => one.side)).toEqual(['A', 'B']);
  });

  /**
   * **The two ends #654 and #655 added** (ADR-0195 §2, §5): a full game nobody recorded is played,
   * and two scores naming different winners are disputed. An agreement is never pending any more —
   * *That's right* settles at once — so nothing on a game says somebody agreed.
   */
  it.each(['PLAYED_NO_SCORE', 'DISPUTED'] as const)(
    'reads %s as the standing it is',
    (standing) => {
      const game = toGame(wireGame({ standing, entry_closes_at: null }), READ_AT);

      expect(game?.standing).toBe(standing);
      expect(game).not.toHaveProperty('acceptance');
    },
  );
});

describe('a code this build has never seen', () => {
  it('leaves a standing absent and the game in the list', () => {
    const games = toGames({
      read_at: READ_AT,
      // @ts-expect-error — a sixth standing is exactly what an old build meets on a real phone.
      games: [wireGame({ standing: 'ABANDONED' })],
    });

    expect(games).toHaveLength(1);
    expect(games[0]?.standing).toBeUndefined();
  });

  it('leaves a kind absent and every other sentence on the screen standing', () => {
    // @ts-expect-error — same case, one vocabulary over.
    const game = toGame(wireGame({ kind: 'LADDER' }), READ_AT);

    expect(game?.kind).toBeUndefined();
    expect(game?.sport).toBe('padel');
  });

  it('drops a game whose sport has no score shape, because there is no instrument to draw', () => {
    // @ts-expect-error — a fifth sport is a release, and this build is the one before it.
    expect(toGames({ read_at: READ_AT, games: [wireGame({ sport: 'PICKLEBALL' })] })).toEqual([]);
  });

  it('reads the handle on a seat, which is the whole of what a seat says about a person', () => {
    const [game] = toGames({
      read_at: READ_AT,
      games: [
        wireGame({
          seats: [
            { side: 'A', player_id: 'me', name: 'me_' },
            { side: 'B', player_id: 'them', name: 'tomek.p' },
          ],
        }),
      ],
    });

    expect(game?.seats).toEqual([
      { side: 'A', playerId: 'me', name: 'me_' },
      { side: 'B', playerId: 'them', name: 'tomek.p' },
    ]);
  });

  /**
   * **A missing handle is not a missing seat**, which is the one place this mapper's *structure
   * is refused whole* rule deliberately does not apply: dropping the seat would draw a
   * three-person doubles game, and `users` no longer having an account is not a court changing
   * shape (`docs/adr/0141`).
   */
  it('keeps a seat whose handle the response could not answer for', () => {
    const [game] = toGames({
      read_at: READ_AT,
      games: [
        wireGame({
          seats: [
            { side: 'A', player_id: 'me', name: 'me_' },
            { side: 'B', player_id: 'them', name: null },
          ],
        }),
      ],
    });

    expect(game?.seats).toEqual([
      { side: 'A', playerId: 'me', name: 'me_' },
      { side: 'B', playerId: 'them' },
    ]);
  });

  /**
   * **An open seat is a seat** (ADR-0162): somebody left the game and nobody has filled it, so
   * `player_id` is `null` and the seat keeps its place and its side. Dropping it would publish a
   * three-person doubles game; dropping the game would take a live court off the rail.
   */
  it('keeps a seat somebody has left, with nobody in it', () => {
    const [game] = toGames({
      read_at: READ_AT,
      games: [
        wireGame({
          seats: [
            { side: 'A', player_id: 'me', name: 'me_' },
            { side: 'B', player_id: null, name: null },
          ],
        }),
      ],
    });

    expect(game?.seats).toEqual([{ side: 'A', playerId: 'me', name: 'me_' }, { side: 'B' }]);
  });

  /**
   * **The fourth end is dated by the act** (ADR-0163): `called_off_at` is the instant somebody
   * called it off, and it is what the ending card is shelved from — `entry_closes_at` is `null`
   * on it, so a card that read the window would stay eight days.
   */
  it('reads when a game was called off, and leaves it absent on every other standing', () => {
    const calledOff = toGame(
      wireGame({
        standing: 'CALLED_OFF',
        entry_closes_at: null,
        called_off_at: '2026-09-04T20:00:00Z',
      }),
      READ_AT,
    );

    expect(calledOff).toMatchObject({
      standing: 'CALLED_OFF',
      calledOffAt: '2026-09-04T20:00:00Z',
    });
    expect(toGame(wireGame({ called_off_at: null }), READ_AT)?.calledOffAt).toBeUndefined();
  });

  /**
   * **And who called it off, with their name** ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
   * §4): the leaver's seat is vacated on the game, so the court cannot supply the name and the
   * field carries it — `null` where `users` no longer has the account, which draws `?`.
   */
  it('reads who called it off and their name, and leaves a lost name absent', () => {
    const named = toGame(
      wireGame({
        standing: 'CALLED_OFF',
        entry_closes_at: null,
        called_off_at: '2026-09-04T20:00:00Z',
        called_off_by: { player_id: 'tomek', name: 'tomek.p' },
      }),
      READ_AT,
    );
    const nameless = toGame(
      wireGame({
        standing: 'CALLED_OFF',
        entry_closes_at: null,
        called_off_at: '2026-09-04T20:00:00Z',
        called_off_by: { player_id: 'tomek', name: null },
      }),
      READ_AT,
    );

    expect(named?.calledOffBy).toEqual({ playerId: 'tomek', name: 'tomek.p' });
    expect(nameless?.calledOffBy).toEqual({ playerId: 'tomek' });
    expect(toGame(wireGame({ called_off_by: null }), READ_AT)).not.toHaveProperty('calledOffBy');
  });

  /**
   * **A no-show report, and what became of it** (#560; the backend's #547) — who, by id and whole
   * name, when it was made, the end of their day to dispute it, and when they did. Who reported
   * them is on no wire: the report is the game's.
   */
  it('reads every no-show report — a lost name and an undisputed report left absent', () => {
    const game = toGame(
      wireGame({
        standing: 'NO_SHOW_REPORTED',
        entry_closes_at: null,
        no_shows: [
          {
            player_id: 'them',
            name: 'Kuba Nowak',
            reported_at: '2026-09-04T20:00:00Z',
            dispute_by: '2026-09-05T20:00:00Z',
            disputed_at: '2026-09-05T08:00:00Z',
          },
          {
            player_id: 'gone',
            name: null,
            reported_at: '2026-09-04T20:05:00Z',
            dispute_by: '2026-09-05T20:05:00Z',
            disputed_at: null,
          },
        ],
      }),
      READ_AT,
    );

    expect(game?.standing).toBe('NO_SHOW_REPORTED');
    expect(game?.noShows).toEqual([
      {
        playerId: 'them',
        name: 'Kuba Nowak',
        reportedAt: '2026-09-04T20:00:00Z',
        disputeBy: '2026-09-05T20:00:00Z',
        disputedAt: '2026-09-05T08:00:00Z',
      },
      {
        playerId: 'gone',
        reportedAt: '2026-09-04T20:05:00Z',
        disputeBy: '2026-09-05T20:05:00Z',
      },
    ]);
    expect(toGame(wireGame(), READ_AT)?.noShows).toEqual([]);
  });

  it('drops a game whose court it cannot place somebody on', () => {
    const games = toGames({
      read_at: READ_AT,
      // @ts-expect-error — a third side would be a different court, not a wider one.
      games: [wireGame({ seats: [{ side: 'C', player_id: 'me' }] })],
    });

    expect(games).toEqual([]);
  });

  /**
   * Structure again, and for a sharper reason than the seat's: dropping one score of two would
   * leave a lone proposal on screen — a different story about the same game, told confidently.
   */
  it('drops a game carrying a score it cannot attribute to a side', () => {
    const games = toGames({
      read_at: READ_AT,
      games: [
        wireGame({
          standing: 'AWAITING_ANSWER',
          played_at: '2026-09-04T20:12:00Z',
          // @ts-expect-error — a third side is the same redesign, one field over.
          proposals: [wireProposal('A'), { ...wireProposal('B'), side: 'C' }],
        }),
      ],
    });

    expect(games).toEqual([]);
  });
});

describe('the score going back', () => {
  it('is the sets and nothing else — no act name, because the record decides which', () => {
    expect(
      toStateResultRequest({
        sets: [
          { a: 6, b: 4 },
          { a: 6, b: 2 },
        ],
      }),
    ).toEqual({
      score: {
        sets: [
          { a: 6, b: 4 },
          { a: 6, b: 2 },
        ],
      },
    });
  });
});
