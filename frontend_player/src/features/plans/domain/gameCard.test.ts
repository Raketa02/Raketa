/**
 * **The card's name, its door, and how long an ending keeps a card.**
 *
 * The four rungs are `ladder.test.ts`'s and are not re-asserted here; what is asserted is the
 * seam — that a standing other than `AWAITING_ENTRY` never reaches the ladder at all, that every
 * name has exactly the door §5.2's table gives it, that the game screen's entry arm lands where
 * that door promises, and that an ending leaves after a day.
 */

import type { Game } from '@/features/games/types';

import { GAME_CARD_NAMES, belongsOnTheRail, doorOf, entryLeadOf, gameCardName } from './gameCard';
import type { Plan } from './slots';

const GAME_ID = '11111111-0000-4000-8000-000000000001';
const READ_AT = '2026-09-12T09:00:00Z';

function game(over: Partial<Game> = {}): Game {
  return {
    gameId: GAME_ID,
    challengeId: '22222222-0000-4000-8000-000000000002',
    sport: 'padel',
    standing: 'AWAITING_ENTRY',
    seats: [
      { side: 'A', playerId: 'me', nickname: 'me' },
      { side: 'B', playerId: 'them', nickname: 'tomek.p' },
    ],
    plannedAt: '2026-09-08T09:00:00Z',
    entryClosesAt: '2026-09-19T09:00:00Z',
    proposals: [],
    readAt: READ_AT,
    ...over,
  };
}

function plan(over: Partial<Plan> = {}): Plan {
  return { gameId: GAME_ID, ...over };
}

/** The same court after the opponent left: their seat open, nobody in it. */
const SHORT: Game['seats'] = [{ side: 'A', playerId: 'me', nickname: 'me' }, { side: 'B' }];

describe('which card a game draws', () => {
  it('reads the ladder only while an entry is still awaited', () => {
    expect(gameCardName(game(), plan({ day: '2026-09-12' }))).toBe('today');
  });

  /**
   * **The open seat outranks the clock** (#411 rule 5): a court somebody left is *Needs a
   * player* on the agreed day and after the agreed point alike — and the server's own ending
   * still wins, because a window that closed on a short court closed all the same.
   */
  it('is Needs a player while a seat is open, whatever the plan and the clock say', () => {
    expect(gameCardName(game({ seats: SHORT }), undefined)).toBe('needs-a-player');
    expect(gameCardName(game({ seats: SHORT }), plan({ day: '2026-09-12' }))).toBe(
      'needs-a-player',
    );
    expect(
      gameCardName(game({ seats: SHORT }), plan({ agreedPoint: '2026-09-11T18:00:00Z' })),
    ).toBe('needs-a-player');
  });

  it('still lets the server’s Never played win over an open seat', () => {
    expect(gameCardName(game({ seats: SHORT, standing: 'NEVER_PLAYED' }), undefined)).toBe(
      'never-played',
    );
  });

  it('names each of the endings and never asks the plan about them', () => {
    const today = plan({ day: '2026-09-12' });

    expect(gameCardName(game({ standing: 'AWAITING_ANSWER' }), today)).toBe('confirm');
    expect(gameCardName(game({ standing: 'CONFIRMED' }), today)).toBe('counted');
    expect(gameCardName(game({ standing: 'UNSCORED' }), today)).toBe('uncounted');
    expect(gameCardName(game({ standing: 'NEVER_PLAYED' }), today)).toBe('never-played');
    expect(gameCardName(game({ standing: 'CALLED_OFF' }), today)).toBe('called-off');
  });

  /** An app that cannot say what a game is may not name a card after one of the states it knows. */
  it('draws the named gap for a standing this build cannot read', () => {
    const { standing: _dropped, ...rest } = game();

    expect(gameCardName(rest, plan({ day: '2026-09-12' }))).toBe('unreadable');
  });
});

describe('the door each card carries', () => {
  it('is §5.2’s table, and every name is in it', () => {
    expect(GAME_CARD_NAMES.map(doorOf)).toEqual([
      'open',
      'we-played',
      'we-played',
      'open',
      'open',
      'confirm',
      undefined,
      undefined,
      undefined,
      undefined,
      undefined,
    ]);
  });

  it('offers nothing on the four endings and on the gap', () => {
    for (const name of [
      'counted',
      'uncounted',
      'never-played',
      'called-off',
      'unreadable',
    ] as const) {
      expect(doorOf(name)).toBeUndefined();
    }
  });
});

describe('how long an ending keeps a card', () => {
  it('keeps every game that is still live, however old', () => {
    expect(belongsOnTheRail(game({ plannedAt: '2025-01-01T09:00:00Z' }))).toBe(true);
    expect(belongsOnTheRail(game({ standing: 'AWAITING_ANSWER' }))).toBe(true);
  });

  it('keeps a game that never happened for a day after its window closed', () => {
    const closed = (at: string) =>
      game({ standing: 'NEVER_PLAYED', entryClosesAt: at, playedAt: undefined });

    expect(belongsOnTheRail(closed('2026-09-11T10:00:00Z'))).toBe(true);
    expect(belongsOnTheRail(closed('2026-09-11T08:00:00Z'))).toBe(false);
  });

  it('keeps a played game for a day after somebody said so', () => {
    const played = (at: string) =>
      game({ standing: 'CONFIRMED', playedAt: at, entryClosesAt: undefined });

    expect(belongsOnTheRail(played('2026-09-11T10:00:00Z'))).toBe(true);
    expect(belongsOnTheRail(played('2026-09-11T08:00:00Z'))).toBe(false);
  });

  /**
   * **The consequence the shelf's anchor has, pinned so it is a decision rather than a surprise.**
   *
   * `played_at` *is* the entry and silence confirms a score one answer window after it, so a game
   * counted by silence reaches `CONFIRMED` at almost exactly the moment its card leaves. A
   * *Counted* card is therefore drawn for a score somebody **agreed with** — which settles after a
   * grace shorter than the window — and barely or not at all for one confirmed by silence.
   */
  it('has all but run out on a game counted by a full day of silence', () => {
    const window = 24 * 60 * 60 * 1000;
    const played = new Date(Date.parse(READ_AT) - window).toISOString();

    expect(
      belongsOnTheRail(game({ standing: 'CONFIRMED', playedAt: played, entryClosesAt: undefined })),
    ).toBe(false);
  });

  /** A card the app cannot name is not a card it may decide is finished. */
  it('keeps an ending it cannot date, and a standing it cannot read', () => {
    const { standing: _dropped, ...unreadable } = game({ plannedAt: '2025-01-01T09:00:00Z' });

    expect(belongsOnTheRail(unreadable)).toBe(true);
    expect(
      belongsOnTheRail(
        game({ standing: 'UNSCORED', playedAt: undefined, entryClosesAt: undefined }),
      ),
    ).toBe(true);
  });
});

describe('what the game screen’s entry arm leads with', () => {
  /**
   * §5.2 lands *Planning* and *Game on* on the plan and *Today* and *Needs result* on the score
   * grid — and *the verb names what you arrive at*, so this is read off the card's own door rather
   * than written beside it. Two tables would be two opinions about where one button goes.
   */
  it('is the plan while the moment is still ahead', () => {
    expect(entryLeadOf(game(), undefined)).toBe('the-plan');
    expect(
      entryLeadOf(game(), plan({ place: 'Zabłocie Sport', day: '2026-09-19', hour: '18:00' })),
    ).toBe('the-plan');
  });

  it('is the score on the agreed day, and once the agreed point has passed', () => {
    expect(entryLeadOf(game(), plan({ day: '2026-09-12' }))).toBe('the-score');
    expect(entryLeadOf(game(), plan({ agreedPoint: '2026-09-11T18:00:00Z' }))).toBe('the-score');
  });

  /** A seat open is not a score to enter: the plan leads, even past the agreed point. */
  it('is the plan while a seat is open, whatever the clock says', () => {
    expect(entryLeadOf(game({ seats: SHORT }), plan({ day: '2026-09-12' }))).toBe('the-plan');
    expect(entryLeadOf(game({ seats: SHORT }), plan({ agreedPoint: '2026-09-11T18:00:00Z' }))).toBe(
      'the-plan',
    );
  });

  /** It cannot disagree with the card, because it is derived from it. */
  it('agrees with the door the card carries, on every rung', () => {
    const rungs = [
      undefined,
      plan({ place: 'Zabłocie Sport', day: '2026-09-19', hour: '18:00' }),
      plan({ day: '2026-09-12' }),
      plan({ agreedPoint: '2026-09-11T18:00:00Z' }),
    ];

    for (const court of [game(), game({ seats: SHORT })]) {
      for (const one of rungs) {
        const expected =
          doorOf(gameCardName(court, one)) === 'we-played' ? 'the-score' : 'the-plan';

        expect(entryLeadOf(court, one)).toBe(expected);
      }
    }
  });
});
