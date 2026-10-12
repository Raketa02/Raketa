/**
 * Where a notice opens (#559; the screens A9: *tapping a notice opens the game it is about — the
 * deck opens with the card on top for You complete it and Challenges*), when it was given, as the
 * list says it, and what a read of the list brings (#627; the mechanics Q101, Q102).
 */

import {
  JUST_OPENED,
  afterTheVisit,
  arrivalsOf,
  givenWhen,
  readOnTheOpenList,
  standingOut,
  targetOf,
  type Notice,
} from './notice';

const FACTS = {
  gameId: '7a1c2f0e-3b4d-4e5f-8a9b-0c1d2e3f4a5b',
  poolId: '9b8a7c6d-5e4f-4a3b-8c2d-1e0f9a8b7c6d',
  sport: 'padel',
  kind: 'competitive',
} as const;

describe('where a notice opens', () => {
  it('a booked game opens its details, by the booking — which is the game’s own id', () => {
    expect(targetOf('SOMEONE_LEFT', 'BOOKING', FACTS)).toEqual({
      opens: 'booking',
      bookingId: FACTS.gameId,
    });
  });

  // The backend sends a Fill in alert as `BOOKING` — the booked game — to a reader who is not in it,
  // so its details are the ones a Seats to fill row opens: a rescue seen from outside (A4.3).
  it('a Fill in alert opens the booked game’s open seat, seen from outside, in its group', () => {
    expect(targetOf('FILL_IN_ALERT', 'BOOKING', FACTS)).toEqual({
      opens: 'rescue',
      groupId: FACTS.poolId,
      bookingId: FACTS.gameId,
    });
  });

  it('a game still filling — or one that did not fill — opens its details in its group', () => {
    expect(targetOf('POST_DID_NOT_FILL', 'PROPOSAL', FACTS)).toEqual({
      opens: 'game',
      groupId: FACTS.poolId,
      proposalId: FACTS.gameId,
      sport: 'padel',
      kind: 'competitive',
    });
  });

  // #663: isn't here yet, they're at the club, How did it go?, Is that right? and Were they there?
  it.each([
    'NOT_HERE_YET',
    'AT_THE_CLUB',
    'HOW_DID_IT_GO',
    'IS_THAT_RIGHT',
    'WERE_THEY_THERE',
  ] as const)('%s opens the booked game’s result screen, by the booking', (kind) => {
    expect(targetOf(kind, 'RESULT', FACTS)).toEqual({ opens: 'result', bookingId: FACTS.gameId });
  });

  it('a card waiting for you opens the group’s deck, in its sport and kind, with it on top', () => {
    expect(targetOf('CHALLENGE', 'DECK', FACTS)).toEqual({
      opens: 'deck',
      groupId: FACTS.poolId,
      proposalId: FACTS.gameId,
      sport: 'padel',
      kind: 'competitive',
    });
  });
});

describe('when a notice was given', () => {
  // 2026-10-02 18:30 in Warsaw (CEST, UTC+2).
  const NOW = '2026-10-02T16:30:00Z';

  it('today is only its clock, in the platform zone', () => {
    expect(givenWhen('2026-10-02T12:05:00Z', NOW)).toEqual({ day: 'today', clock: '14:05' });
  });

  it('yesterday is said so, with its clock', () => {
    expect(givenWhen('2026-10-01T20:00:00Z', NOW)).toEqual({ day: 'yesterday', clock: '22:00' });
  });

  it('is yesterday by the Warsaw calendar, not by the hours since', () => {
    // 23:30 in Warsaw on the 1st — nineteen hours ago, and still yesterday.
    expect(givenWhen('2026-10-01T21:30:00Z', NOW)?.day).toBe('yesterday');
    // 00:30 in Warsaw on the 2nd — sixteen hours ago, and today.
    expect(givenWhen('2026-10-01T22:30:00Z', NOW)?.day).toBe('today');
  });

  it('within the week is its weekday', () => {
    expect(givenWhen('2026-09-28T07:00:00Z', NOW)).toEqual({
      day: 'weekday',
      weekday: 1,
      clock: '09:00',
    });
  });

  it('older is its date', () => {
    expect(givenWhen('2026-09-20T07:00:00Z', NOW)).toEqual({
      day: 'date',
      date: '2026-09-20',
      clock: '09:00',
    });
  });

  it('a time it cannot read is nothing said', () => {
    expect(givenWhen('not a time', NOW)).toBeUndefined();
  });
});

/** A listed notice — news, not the player's own, unless told otherwise. */
function listed(id: string, extra: Partial<Notice> = {}): Notice {
  return {
    id,
    kind: 'SOMEONE_LEFT',
    title: 'Someone left your game',
    body: 'Padel · Tue 19:00',
    givenAt: '2026-10-06T21:00:00Z',
    isNew: true,
    yourOwn: false,
    ...extra,
  };
}

describe('what a read of the list brings the session', () => {
  it('nothing, when every notice on it was seen before — Home is not read again', () => {
    expect(arrivalsOf(new Set(['a', 'b']), [listed('a'), listed('b')])).toEqual({
      arrived: false,
    });
  });

  it('the newest it had not seen, as the banner — the list is newest first', () => {
    const read = [listed('c'), listed('b'), listed('a')];
    expect(arrivalsOf(new Set(['a']), read)).toEqual({ arrived: true, banner: read[0] });
  });

  it('never the player’s own as the banner — the newest that is somebody else’s act', () => {
    const read = [listed('c', { yourOwn: true, isNew: false }), listed('b'), listed('a')];
    expect(arrivalsOf(new Set(['a']), read)).toEqual({ arrived: true, banner: read[1] });
  });

  it('an arrival and no banner, when the only one it brings is the player’s own', () => {
    const read = [listed('b', { yourOwn: true, isNew: false }), listed('a')];
    expect(arrivalsOf(new Set(['a']), read)).toEqual({ arrived: true });
  });

  it('nothing for a notice the day bundled another into — it keeps its id and moves up', () => {
    const read = [listed('a', { givenAt: '2026-10-06T22:00:00Z' }), listed('b')];
    expect(arrivalsOf(new Set(['a', 'b']), read)).toEqual({ arrived: false });
  });
});

describe('the rows that stand out on a visit to the list', () => {
  it('are the ones a read says are new', () => {
    const read = [listed('c'), listed('b', { isNew: false }), listed('a', { isNew: false })];
    expect(standingOut(new Set(), read)).toEqual(new Set(['c']));
  });

  it('stay standing out once a later read says they are seen — for as long as the list is open', () => {
    const after = [listed('c', { isNew: false }), listed('b', { isNew: false })];
    expect(standingOut(new Set(['c']), after)).toEqual(new Set(['c']));
  });

  it('gain one that arrives while the list is open', () => {
    const later = [listed('d'), listed('c', { isNew: false })];
    expect(standingOut(new Set(['c']), later)).toEqual(new Set(['c', 'd']));
  });

  it('keep the same set when a read adds nothing, so the screen need not draw again', () => {
    const held = new Set(['c']);
    expect(standingOut(held, [listed('c', { isNew: false })])).toBe(held);
    expect(standingOut(held, [listed('c')])).toBe(held);
  });
});

describe('when the open list sends the visit', () => {
  const CACHED = { sinceOpening: false } as const;
  const FRESH = { sinceOpening: true } as const;

  it('not on the read it opens on — that one is from before it was opened', () => {
    const { list, visit } = readOnTheOpenList(JUST_OPENED, [listed('a')], CACHED);
    expect(visit).toBe(false);
    expect(list.standOut).toEqual(new Set(['a']));
  });

  it('after the first read since opening, even with nothing new — opening is the visit', () => {
    const read = [listed('a', { isNew: false })];
    expect(readOnTheOpenList(JUST_OPENED, read, FRESH).visit).toBe(true);
  });

  it('not again for a read that brings nothing new', () => {
    const first = readOnTheOpenList(JUST_OPENED, [listed('a')], FRESH).list;
    expect(readOnTheOpenList(first, [listed('a', { isNew: false })], FRESH).visit).toBe(false);
  });

  // A visit the server declines to move — opened at the same moment on another phone — leaves the
  // rows new; sending again for them would be a loop.
  it('not again for the rows a visit already covered, though the server still calls them new', () => {
    const first = readOnTheOpenList(JUST_OPENED, [listed('a')], FRESH).list;
    expect(readOnTheOpenList(first, [listed('a')], FRESH).visit).toBe(false);
  });

  it('again for a notice that reaches the open list', () => {
    const first = readOnTheOpenList(JUST_OPENED, [listed('a')], FRESH).list;
    const { list, visit } = readOnTheOpenList(
      first,
      [listed('b'), listed('a', { isNew: false })],
      FRESH,
    );
    expect(visit).toBe(true);
    expect(list.standOut).toEqual(new Set(['a', 'b']));
  });

  it('again for a notice the day bundled into a row already standing out — it reached the list again', () => {
    const first = readOnTheOpenList(JUST_OPENED, [listed('a')], FRESH).list;
    const bundled = [listed('a', { givenAt: '2026-10-06T22:00:00Z' })];
    expect(readOnTheOpenList(first, bundled, FRESH).visit).toBe(true);
  });
});

describe('the list once the visit is recorded', () => {
  it('counts nothing and holds no new row — everything listed by then is seen', () => {
    const read = { notices: [listed('b'), listed('a', { isNew: false })], newCount: 1 };
    expect(afterTheVisit(read)).toEqual({
      notices: [listed('b', { isNew: false }), listed('a', { isNew: false })],
      newCount: 0,
    });
  });
});
