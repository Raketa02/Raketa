/**
 * **Who's here, at a booked game's court** ([#658](https://github.com/Raketa02/Raketa/issues/658);
 * ADR-0195 §3; the backend's #657). In the first half hour a player at the club taps *isn't here
 * yet* about anybody else on the court, an awaited player says *I'm here*, and anybody says *they're
 * here* about somebody awaited. Afterwards a player who Didn't come may say *I was there* within a
 * day, and somebody else on the court confirms it.
 *
 * What is asserted here is the fold the block is drawn from: which taps a reader is offered, about
 * whom, and what is said of each player — never the outcome itself, which is the backend's.
 */

import { attendanceBlock, isRoughFix, tapsAreOpen, type BookedHour } from './attendance';
import type { Attendance, Game } from './game';

const ME = 'me-1111-4444-8888-000000000001';
const PARTNER = 'partner-11-4444-8888-000000002';
const KUBA = 'kuba-11111-4444-8888-00000003';
const INES = 'ines-11111-4444-8888-00000004';

/** Wednesday 14 October, 17:00 in Warsaw — the hour the story is told on. */
const STARTS_AT = '2026-10-14T15:00:00Z';
const HOUR: BookedHour = { startsAt: STARTS_AT };
/** 17:10 — inside the first half hour. */
const AT_THE_COURT = '2026-10-14T15:10:00Z';
/** 17:30, the half hour's end, and the day after it. */
const ARRIVE_BY = '2026-10-14T15:30:00Z';
const CLAIM_BY = '2026-10-15T15:30:00Z';
/** The next morning, inside the late claim's day. */
const NEXT_MORNING = '2026-10-15T07:00:00Z';

function game(over: Partial<Game> = {}): Game {
  return {
    gameId: 'game-1111-4444-8888-00000000001',
    sport: 'tennis',
    kind: 'COUNTED',
    standing: 'AWAITING_ENTRY',
    seats: [
      { side: 'A', playerId: ME, name: 'Ivan Petrov' },
      { side: 'A', playerId: PARTNER, name: 'Piotr Sowa' },
      { side: 'B', playerId: KUBA, name: 'Oscar Nowak' },
      { side: 'B', playerId: INES },
    ],
    plannedAt: '2026-10-10T18:00:00Z',
    entryClosesAt: '2026-10-15T16:00:00Z',
    proposals: [],
    attendance: [],
    readAt: AT_THE_COURT,
    ...over,
  };
}

function row(playerId: string, over: Partial<Attendance> = {}): Attendance {
  return {
    playerId,
    state: 'WAITING',
    notedAt: '2026-10-14T15:05:00Z',
    arriveBy: ARRIVE_BY,
    claimBy: CLAIM_BY,
    ...over,
  };
}

describe('the first half hour', () => {
  it('is open from the start until half an hour after it, and never outside', () => {
    expect(tapsAreOpen(STARTS_AT, '2026-10-14T14:59:59Z')).toBe(false);
    expect(tapsAreOpen(STARTS_AT, STARTS_AT)).toBe(true);
    expect(tapsAreOpen(STARTS_AT, '2026-10-14T15:29:59Z')).toBe(true);
    // Half-open, as the backend's: a tap at exactly 17:30 is refused.
    expect(tapsAreOpen(STARTS_AT, ARRIVE_BY)).toBe(false);
  });

  it('is never open on an hour this build cannot read', () => {
    expect(tapsAreOpen('not an instant', AT_THE_COURT)).toBe(false);
  });
});

describe('isn’t here yet', () => {
  it('is one tap per other player on the court, in its order, named whole, and never about you', () => {
    const block = attendanceBlock(game(), ME, HOUR);

    expect(block.phase).toBe('at-the-court');
    expect(block.rows).toStrictEqual([
      { playerId: PARTNER, who: { kind: 'player', name: 'Piotr Sowa' }, tap: 'not-here-yet' },
      { playerId: KUBA, who: { kind: 'player', name: 'Oscar Nowak' }, tap: 'not-here-yet' },
      { playerId: INES, who: { kind: 'unknown' }, tap: 'not-here-yet' },
    ]);
    expect(block.own).toBeUndefined();
  });

  it('is offered while a score waits for its answer — a waiting score stops no tap', () => {
    const block = attendanceBlock(game({ standing: 'AWAITING_ANSWER' }), ME, HOUR);

    expect(block.rows.filter((one) => one.tap === 'not-here-yet')).toHaveLength(3);
  });

  it('is not offered before the hour, after its first half, or on a game with no hour', () => {
    expect(attendanceBlock(game({ readAt: '2026-10-14T14:50:00Z' }), ME, HOUR).rows).toEqual([]);
    expect(attendanceBlock(game({ readAt: ARRIVE_BY }), ME, HOUR).rows).toEqual([]);
    expect(attendanceBlock(game(), ME, undefined).rows).toEqual([]);
  });

  it('is not offered on a game that is settled, called off or started short', () => {
    for (const standing of ['CONFIRMED', 'CALLED_OFF', 'STARTED_SHORT'] as const) {
      expect(attendanceBlock(game({ standing }), ME, HOUR).rows).toEqual([]);
    }
    // A standing this build cannot read offers nothing either.
    expect(attendanceBlock(game({ standing: undefined }), ME, HOUR).rows).toEqual([]);
  });

  it('skips an open seat — nobody is in it to wait for', () => {
    const block = attendanceBlock(
      game({
        seats: [{ side: 'A', playerId: ME, name: 'Ivan Petrov' }, { side: 'B' }],
      }),
      ME,
      HOUR,
    );

    expect(block.rows).toEqual([]);
  });
});

describe('while somebody is awaited', () => {
  const oscarAwaited = (over: Partial<Game> = {}) =>
    game({ standing: 'NOT_HERE_YET', attendance: [row(KUBA)], ...over });

  it('offers they’re here about them, and isn’t here yet about everybody else still', () => {
    const block = attendanceBlock(oscarAwaited(), ME, HOUR);

    expect(block.rows).toStrictEqual([
      { playerId: PARTNER, who: { kind: 'player', name: 'Piotr Sowa' }, tap: 'not-here-yet' },
      { playerId: KUBA, who: { kind: 'player', name: 'Oscar Nowak' }, tap: 'here' },
      { playerId: INES, who: { kind: 'unknown' }, tap: 'not-here-yet' },
    ]);
  });

  it('offers the awaited player I’m here, and no tap about anybody else', () => {
    const block = attendanceBlock(oscarAwaited(), KUBA, HOUR);

    expect(block.own).toBe('im-here');
    expect(block.rows).toEqual([]);
  });

  it('tells an awaited player about the other one awaited, with nothing to press', () => {
    const block = attendanceBlock(oscarAwaited({ attendance: [row(KUBA), row(INES)] }), KUBA, HOUR);

    expect(block.own).toBe('im-here');
    expect(block.rows).toStrictEqual([
      { playerId: INES, who: { kind: 'unknown' }, said: 'not-here-yet' },
    ]);
  });
});

describe('an arrival', () => {
  it('on time vanishes: nothing is said and nothing is offered about them', () => {
    const block = attendanceBlock(
      game({
        attendance: [row(KUBA, { state: 'ON_TIME', arrivedAt: '2026-10-14T15:08:00Z' })],
      }),
      ME,
      HOUR,
    );

    expect(block.rows.find((one) => one.playerId === KUBA)).toBeUndefined();
  });

  it('late is said — to everybody, the late player too — and offers nothing more', () => {
    const late = game({
      attendance: [row(KUBA, { state: 'CAME_LATE', arrivedAt: '2026-10-14T15:22:00Z' })],
    });

    expect(attendanceBlock(late, ME, HOUR).rows).toContainEqual({
      playerId: KUBA,
      who: { kind: 'player', name: 'Oscar Nowak' },
      said: 'came-late',
    });
    expect(attendanceBlock(late, KUBA, HOUR).rows).toContainEqual({
      playerId: KUBA,
      who: { kind: 'you' },
      said: 'came-late',
    });
  });

  it('late lets the late player tap anybody else still to come', () => {
    const late = game({
      attendance: [row(KUBA, { state: 'CAME_LATE', arrivedAt: '2026-10-14T15:22:00Z' })],
    });

    expect(
      attendanceBlock(late, KUBA, HOUR).rows.filter((one) => one.tap === 'not-here-yet'),
    ).toHaveLength(3);
  });
});

describe('after the first half hour', () => {
  const didntCome = (over: Partial<Attendance> = {}) =>
    game({
      standing: 'DIDNT_COME',
      entryClosesAt: undefined,
      readAt: NEXT_MORNING,
      attendance: [row(KUBA, { state: 'DIDNT_COME', ...over })],
    });

  it('offers the player who Didn’t come I was there, inside their day', () => {
    const block = attendanceBlock(didntCome(), KUBA, HOUR);

    expect(block.phase).toBe('afterwards');
    expect(block.own).toBe('i-was-there');
  });

  it('offers nothing once their day is over — Didn’t come is final', () => {
    const block = attendanceBlock(didntCome(), KUBA, HOUR);
    const late = attendanceBlock({ ...didntCome(), readAt: CLAIM_BY }, KUBA, HOUR);

    expect(block.own).toBe('i-was-there');
    expect(late.own).toBeUndefined();
  });

  it('says nothing about a Didn’t come the standing line already names, and offers no tap', () => {
    expect(attendanceBlock(didntCome(), ME, HOUR).rows).toEqual([]);
  });

  it('offers everybody else Yes, they were here once they have said it', () => {
    const claimed = didntCome({ state: 'CLAIMED', claimedAt: '2026-10-15T06:30:00Z' });

    expect(attendanceBlock(claimed, ME, HOUR).rows).toStrictEqual([
      {
        playerId: KUBA,
        who: { kind: 'player', name: 'Oscar Nowak' },
        said: 'says-they-were-there',
        tap: 'was-here',
      },
    ]);
    // Said: it waits on somebody else now.
    expect(attendanceBlock(claimed, KUBA, HOUR).own).toBeUndefined();
  });

  it('offers no confirmation once the day is over, nor to a player who didn’t come themselves', () => {
    const claimed = (over: Partial<Game> = {}) => ({
      ...didntCome({ state: 'CLAIMED', claimedAt: '2026-10-15T06:30:00Z' }),
      ...over,
    });

    expect(attendanceBlock(claimed({ readAt: CLAIM_BY }), ME, HOUR).rows).toStrictEqual([
      {
        playerId: KUBA,
        who: { kind: 'player', name: 'Oscar Nowak' },
        said: 'says-they-were-there',
      },
    ]);

    const bothAway = claimed({
      attendance: [
        row(KUBA, { state: 'CLAIMED', claimedAt: '2026-10-15T06:30:00Z' }),
        row(INES, { state: 'DIDNT_COME' }),
      ],
    });
    expect(attendanceBlock(bothAway, INES, HOUR).rows).toStrictEqual([
      {
        playerId: KUBA,
        who: { kind: 'player', name: 'Oscar Nowak' },
        said: 'says-they-were-there',
      },
    ]);
  });

  it('says a confirmed claim as Came late', () => {
    const confirmed = game({
      readAt: NEXT_MORNING,
      attendance: [
        row(KUBA, {
          state: 'CONFIRMED',
          claimedAt: '2026-10-15T06:30:00Z',
          confirmedAt: '2026-10-15T06:45:00Z',
        }),
      ],
    });

    expect(attendanceBlock(confirmed, ME, HOUR).rows).toStrictEqual([
      { playerId: KUBA, who: { kind: 'player', name: 'Oscar Nowak' }, said: 'came-late' },
    ]);
  });

  it('says nothing about a row whose state this build cannot read', () => {
    const unreadable = game({ attendance: [row(KUBA, { state: undefined })] });

    expect(attendanceBlock(unreadable, ME, HOUR).rows.find((one) => one.playerId === KUBA)).toBe(
      undefined,
    );
  });
});

/**
 * **A fix too rough for the club's check** — wider than the backend allows for. Said as such when the
 * backend answers *not at the club*, because a phone sharing only an approximate position (iOS with
 * Precise Location off, Android's approximate) is the likeliest reason a player at the club hears it.
 */
describe('a rough fix', () => {
  const at = (accuracyMetres: number | null) => ({ latitude: 50, longitude: 20, accuracyMetres });

  it('is one whose stated accuracy is wider than the 200 m the check allows for', () => {
    expect(isRoughFix(at(200))).toBe(false);
    expect(isRoughFix(at(201))).toBe(true);
    expect(isRoughFix(at(3000))).toBe(true);
  });

  it('is never one that states no accuracy — nothing is known to be rough about it', () => {
    expect(isRoughFix(at(null))).toBe(false);
  });
});
