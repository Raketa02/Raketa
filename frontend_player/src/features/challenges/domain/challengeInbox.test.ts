/**
 * The inbox's three rules, held to the claims a build session could quietly undo.
 *
 * **One predicate read three ways** is the thing worth a suite: the badge counts what
 * `yoursToClear` says, the sort puts what `yoursToClear` says at the top, and the row asks
 * `yoursToClear` which of two sentences to print. If those ever stop being one function, the
 * badge says 1 and the list shows the waiting row fourth.
 *
 * The shelf life is asserted against what the wire actually dates, which is not the ending —
 * see the module note. What is pinned here is the direction of the approximation: a row is
 * never dropped early, and a withdrawal, which nothing dates, is never dropped at all.
 */

import type { Challenge, ChallengeSeat } from './challenge';
import {
  ENDED_ROW_SHELF_LIFE_MS,
  belongsOnTheInbox,
  challengeInbox,
  challengesWaiting,
  endedNoEarlierThan,
  yoursToClear,
} from './challengeInbox';
import type { Standing } from './standing';

const ME = 'me';
const EWA = 'ewa';

const READ_AT = '2026-09-08T12:00:00Z';
const HOUR = 60 * 60 * 1000;

function at(offsetHours: number): string {
  return new Date(Date.parse(READ_AT) + offsetHours * HOUR).toISOString();
}

function challenge(
  overrides: Partial<Challenge> & { readonly standing?: Standing },
  seats: readonly ChallengeSeat[] = [],
): Challenge {
  return {
    challengeId: 'c1',
    organiserId: EWA,
    standing: 'AWAITING_ANSWERS',
    sport: 'squash',
    openedAt: at(-4),
    readAt: READ_AT,
    seats,
    ...overrides,
  };
}

/** Somebody asked me, and I have not answered — the one shape the badge counts. */
const askedMe = (overrides: Partial<Challenge> = {}) =>
  challenge(overrides, [
    { playerId: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
    { playerId: ME, answerBy: at(20) },
  ]);

describe('is this one mine to clear', () => {
  it('counts a live challenge somebody else opened that my own seat has not answered', () => {
    expect(yoursToClear(askedMe(), ME)).toBe(true);
    expect(yoursToClear(askedMe({ standing: 'LINE_UP_INCOMPLETE' }), ME)).toBe(true);
  });

  it('never counts my own send, however live it is', () => {
    expect(yoursToClear(askedMe({ organiserId: ME }), ME)).toBe(false);
  });

  it('never counts a seat I have already answered', () => {
    const answered = challenge({}, [
      { playerId: EWA, answer: 'ACCEPTED' },
      { playerId: ME, answer: 'ACCEPTED', answerBy: at(20) },
    ]);

    expect(yoursToClear(answered, ME)).toBe(false);
  });

  it('never counts a standing that has ended, or one it cannot read', () => {
    for (const standing of ['ON', 'DECLINED', 'LAPSED', 'WITHDRAWN'] as const) {
      expect(yoursToClear(askedMe({ standing }), ME)).toBe(false);
    }
    expect(yoursToClear(askedMe({ standing: undefined }), ME)).toBe(false);
  });

  it('is the badge, so the badge is the number of rows it answers yes to', () => {
    const list = [askedMe(), askedMe({ organiserId: ME }), askedMe({ standing: 'ON' })];

    expect(challengesWaiting(list, ME)).toBe(list.filter((one) => yoursToClear(one, ME)).length);
    expect(challengesWaiting(list, ME)).toBe(1);
  });
});

describe('what the wire dates about an ending', () => {
  it('takes the latest deadline on the court, which is exactly when a lapse happened', () => {
    const lapsed = challenge({ standing: 'LAPSED', openedAt: at(-78) }, [
      { playerId: EWA, answer: 'ACCEPTED' },
      { playerId: ME, answer: 'LAPSED', answerBy: at(-30) },
    ]);

    expect(endedNoEarlierThan(lapsed)).toBe(at(-30));
  });

  it('falls back to the moment it opened on a court where nobody was asked', () => {
    const mutual = challenge({ standing: 'DECLINED' }, [
      { playerId: EWA, answer: 'ACCEPTED' },
      { playerId: ME, answer: 'DECLINED' },
    ]);

    expect(endedNoEarlierThan(mutual)).toBe(mutual.openedAt);
  });

  it('dates a withdrawal by nothing, because every clock on that court had stopped', () => {
    const withdrawn = challenge({ standing: 'WITHDRAWN' }, [
      { playerId: EWA, answer: 'ACCEPTED' },
      { playerId: ME, answer: 'ACCEPTED', answerBy: at(-40) },
    ]);

    expect(endedNoEarlierThan(withdrawn)).toBeUndefined();
  });
});

describe('what the inbox still holds', () => {
  it('keeps everything that is still being arranged, mine and theirs', () => {
    expect(belongsOnTheInbox(askedMe())).toBe(true);
    expect(belongsOnTheInbox(askedMe({ organiserId: ME, standing: 'LINE_UP_INCOMPLETE' }))).toBe(
      true,
    );
  });

  /**
   * The one place the inbox's question and the pair rule's disagree. `challengeStands` answers
   * **yes** for `ON` and is right — a completed line-up is exactly when two people have a game —
   * but nothing about the arrangement can change again, so the row is news and not work.
   */
  it('treats a completed line-up as news rather than as work still being arranged', () => {
    const justCompleted = challenge({ standing: 'ON' }, [
      { playerId: EWA, answer: 'ACCEPTED' },
      { playerId: ME, answer: 'ACCEPTED', answerBy: at(-2) },
    ]);
    const longCompleted = challenge({ standing: 'ON', openedAt: at(-200) }, [
      { playerId: EWA, answer: 'ACCEPTED' },
      { playerId: ME, answer: 'ACCEPTED', answerBy: at(-199) },
    ]);

    expect(belongsOnTheInbox(justCompleted)).toBe(true);
    expect(belongsOnTheInbox(longCompleted)).toBe(false);
  });

  it('keeps an ending the wire dates inside the shelf life', () => {
    const justLapsed = challenge({ standing: 'LAPSED', openedAt: at(-49) }, [
      { playerId: ME, answer: 'LAPSED', answerBy: at(-1) },
    ]);

    expect(belongsOnTheInbox(justLapsed)).toBe(true);
  });

  it('lets it go once the shelf life has passed, so an inbox is not an archive', () => {
    const hours = ENDED_ROW_SHELF_LIFE_MS / HOUR;
    const old = challenge({ standing: 'DECLINED', openedAt: at(-hours - 1) }, [
      { playerId: ME, answer: 'DECLINED', answerBy: at(-hours - 1) },
    ]);

    expect(belongsOnTheInbox(old)).toBe(false);
  });

  it('keeps a withdrawal, because dropping it would call news old on no evidence', () => {
    const withdrawn = challenge({ standing: 'WITHDRAWN', openedAt: at(-500) }, [
      { playerId: ME, answer: 'ACCEPTED', answerBy: at(-490) },
    ]);

    expect(belongsOnTheInbox(withdrawn)).toBe(true);
  });

  it('keeps a standing it cannot read, because it may not decide an unnamed thing is over', () => {
    expect(belongsOnTheInbox(challenge({ standing: undefined, openedAt: at(-500) }))).toBe(true);
  });
});

describe('the order', () => {
  const soon = askedMe({ challengeId: 'soon' });
  const later = challenge({ challengeId: 'later' }, [
    { playerId: EWA, answer: 'ACCEPTED' },
    { playerId: ME, answerBy: at(40) },
  ]);
  const mySendYesterday = challenge({
    challengeId: 'mine-old',
    organiserId: ME,
    openedAt: at(-30),
  });
  const mySendToday = challenge({ challengeId: 'mine-new', organiserId: ME, openedAt: at(-2) });

  it('puts what I can clear first, least time remaining first', () => {
    const rows = challengeInbox([later, mySendToday, soon], ME);

    expect(rows.map((one) => one.challengeId)).toEqual(['soon', 'later', 'mine-new']);
  });

  it('orders everything else newest first, and never shelves an ended row separately', () => {
    const endedJustNow = challenge(
      { challengeId: 'ended', organiserId: ME, standing: 'DECLINED', openedAt: at(-10) },
      [{ playerId: EWA, answer: 'DECLINED', answerBy: at(-1) }],
    );

    const rows = challengeInbox([mySendYesterday, endedJustNow, mySendToday], ME);

    expect(rows.map((one) => one.challengeId)).toEqual(['mine-new', 'ended', 'mine-old']);
  });
});
