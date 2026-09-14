/**
 * The inbox's three rules, held to the claims a build session could quietly undo.
 *
 * **One predicate read three ways** is the thing worth a suite: the badge counts what
 * `yoursToClear` says, the sort puts what `yoursToClear` says at the top, and the row asks
 * `yoursToClear` which of two sentences to print. If those ever stop being one function, the
 * badge says 1 and the list shows the waiting row fourth.
 *
 * The shelf life is asserted against **the instant the wire now serves**
 * ([#388](https://github.com/Raketa02/Raketa/issues/388)), and the row that proves the
 * difference is the withdrawal: undated, it was kept for ever, and here it leaves. What is
 * still pinned is the direction — a row is never dropped early, and one the app cannot date is
 * never dropped at all.
 */

import type { Challenge, ChallengeSeat } from './challenge';
import {
  ENDED_ROW_SHELF_LIFE_MS,
  belongsOnTheInbox,
  challengeInbox,
  challengesWaiting,
  othersOn,
  stoppedBeingArrangedAt,
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

describe('when a challenge stopped being arranged', () => {
  it('takes the instant the wire serves, on all three of the endings it dates', () => {
    for (const standing of ['DECLINED', 'LAPSED', 'WITHDRAWN'] as const) {
      const ended = challenge({ standing, openedAt: at(-78), endedAt: at(-30) }, [
        { playerId: EWA, answer: 'ACCEPTED' },
        // A deadline the old approximation would have taken instead, and later than the
        // ending — so reading the court rather than the field is visible here.
        { playerId: ME, answer: 'LAPSED', answerBy: at(-2) },
      ]);

      expect(stoppedBeingArrangedAt(ended)).toBe(at(-30));
    }
  });

  it('dates a completed line-up off the court, because the contract does not call it an ending', () => {
    const completed = challenge({ standing: 'ON', openedAt: at(-78) }, [
      { playerId: EWA, answer: 'ACCEPTED' },
      { playerId: ME, answer: 'ACCEPTED', answerBy: at(-30) },
    ]);

    expect(completed.endedAt).toBeUndefined();
    expect(stoppedBeingArrangedAt(completed)).toBe(at(-30));
  });

  it('falls back to the moment it opened on a completed court where nobody was asked', () => {
    const mutual = challenge({ standing: 'ON' }, [
      { playerId: EWA, answer: 'ACCEPTED' },
      { playerId: ME, answer: 'ACCEPTED' },
    ]);

    expect(stoppedBeingArrangedAt(mutual)).toBe(mutual.openedAt);
  });

  it('says nothing where the contract claimed an ending and dated none', () => {
    const undated = challenge({ standing: 'DECLINED' }, [
      { playerId: EWA, answer: 'ACCEPTED' },
      { playerId: ME, answer: 'DECLINED', answerBy: at(-2) },
    ]);

    expect(stoppedBeingArrangedAt(undated)).toBeUndefined();
  });
});

describe('what the inbox still holds', () => {
  it('keeps everything that is still being arranged, mine and theirs', () => {
    expect(belongsOnTheInbox(askedMe(), ME)).toBe(true);
    expect(
      belongsOnTheInbox(askedMe({ organiserId: ME, standing: 'LINE_UP_INCOMPLETE' }), ME),
    ).toBe(true);
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

    expect(belongsOnTheInbox(justCompleted, ME)).toBe(true);
    expect(belongsOnTheInbox(longCompleted, ME)).toBe(false);
  });

  it('keeps an ending inside the shelf life', () => {
    const justLapsed = challenge({ standing: 'LAPSED', openedAt: at(-49), endedAt: at(-1) }, [
      { playerId: ME, answer: 'LAPSED', answerBy: at(-1) },
    ]);

    expect(belongsOnTheInbox(justLapsed, ME)).toBe(true);
  });

  it('lets it go once the shelf life has passed, so an inbox is not an archive', () => {
    const hours = ENDED_ROW_SHELF_LIFE_MS / HOUR;
    const old = challenge(
      { standing: 'DECLINED', openedAt: at(-hours - 2), endedAt: at(-hours - 1) },
      [{ playerId: ME, answer: 'DECLINED', answerBy: at(-hours - 1) }],
    );

    expect(belongsOnTheInbox(old, ME)).toBe(false);
  });

  /**
   * **The row this ticket existed for.** Nothing dated a withdrawal, so it was kept — one
   * opened five hundred hours ago among this week's news — and over time that row was the
   * archive §1.1 exists to prevent. [#388](https://github.com/Raketa02/Raketa/issues/388) put
   * the instant on the wire, and the whole of the fix on this side is subtracting it.
   */
  it('lets a withdrawal go, which is what #388 made possible', () => {
    const withdrawn = challenge({ standing: 'WITHDRAWN', openedAt: at(-500), endedAt: at(-499) }, [
      { playerId: ME, answer: 'ACCEPTED', answerBy: at(-490) },
    ]);

    expect(belongsOnTheInbox(withdrawn, ME)).toBe(false);
  });

  it('keeps a withdrawal that has just happened, in its place among the rest', () => {
    const justWithdrawn = challenge(
      { standing: 'WITHDRAWN', openedAt: at(-500), endedAt: at(-2) },
      [{ playerId: ME, answer: 'ACCEPTED', answerBy: at(-490) }],
    );

    expect(belongsOnTheInbox(justWithdrawn, ME)).toBe(true);
  });

  it('keeps a standing it cannot read, because it may not decide an unnamed thing is over', () => {
    expect(belongsOnTheInbox(challenge({ standing: undefined, openedAt: at(-500) }), ME)).toBe(
      true,
    );
  });

  /**
   * The `undefined` branch's remaining purpose, and it is a narrower one than it had. It used
   * to cover a withdrawal, which was undatable by design; now it covers only a contract that
   * claimed an ending and dated none — a broken promise rather than a gap in the wire. The row
   * stays for the same reason an unreadable standing does: **a row the app cannot date is not a
   * row it may decide is finished.**
   */
  it('keeps an ending the wire failed to date, however long ago it opened', () => {
    const undated = challenge({ standing: 'LAPSED', openedAt: at(-500) }, [
      { playerId: ME, answer: 'LAPSED', answerBy: at(-490) },
    ]);

    expect(undated.endedAt).toBeUndefined();
    expect(belongsOnTheInbox(undated, ME)).toBe(true);
  });
});

describe('a no of my own', () => {
  /**
   * The shelf life keeps a row a day so the reader learns something they did not do. A decline is
   * the reader's own act, so there is nothing on *You said no* to be told — and the row goes with
   * the tap, whether the no ended a singles court or left a doubles court to carry on without them.
   */
  it('leaves at once, on a court it ended', () => {
    const iSaidNo = challenge({ standing: 'DECLINED', openedAt: at(-4), endedAt: at(-1) }, [
      { playerId: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
      { playerId: ME, answer: 'DECLINED', answerBy: at(20) },
    ]);

    expect(belongsOnTheInbox(iSaidNo, ME)).toBe(false);
  });

  it('leaves at once, on a court that carries on filling without me', () => {
    const stillFilling = challenge({ standing: 'LINE_UP_INCOMPLETE', sport: 'padel' }, [
      { playerId: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
      { playerId: ME, answer: 'DECLINED', answerBy: at(20) },
      {},
      {},
    ]);

    expect(belongsOnTheInbox(stillFilling, ME)).toBe(false);
    expect(challengeInbox([stillFilling], ME)).toEqual([]);
  });

  /** To the organiser the same no is news, and it keeps its day. */
  it('is news to the organiser, whose row stays its day', () => {
    const theirNo = challenge(
      { organiserId: ME, standing: 'DECLINED', openedAt: at(-4), endedAt: at(-1) },
      [
        { playerId: ME, answer: 'ACCEPTED' },
        { playerId: EWA, answer: 'DECLINED', answerBy: at(20), nickname: 'ewa.m' },
      ],
    );

    expect(belongsOnTheInbox(theirNo, ME)).toBe(true);
  });

  /** A lapse is not a decline: nobody chose it, and *Your day ran out* is kept to be read. */
  it('is not a lapse, which keeps its row to be read', () => {
    const myDayRanOut = challenge({ standing: 'LAPSED', openedAt: at(-49), endedAt: at(-1) }, [
      { playerId: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
      { playerId: ME, answer: 'LAPSED', answerBy: at(-1) },
    ]);

    expect(belongsOnTheInbox(myDayRanOut, ME)).toBe(true);
  });
});

describe('a departure of my own', () => {
  /**
   * An own *left* is the reader's own act in the same sense as an own *no*
   * ([ADR-0165](../../../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
   * §6): there is nothing on *You left* they have to be told, and a court they walked out of
   * going on filling without them is not their news.
   */
  it('leaves at once, on a court that carries on filling without me', () => {
    const iLeft = challenge({ standing: 'LINE_UP_INCOMPLETE', sport: 'padel' }, [
      { playerId: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
      { playerId: 'ola', answer: 'ACCEPTED', nickname: 'ola.k' },
      { playerId: ME, answer: 'LEFT' },
      {},
    ]);

    expect(belongsOnTheInbox(iLeft, ME)).toBe(false);
    expect(challengeInbox([iLeft], ME)).toEqual([]);
  });

  /** And on the court it ended — one left, nobody deciding, and a departure is a no. */
  it('leaves at once, on a court my leaving ended', () => {
    const iEndedIt = challenge({ standing: 'DECLINED', openedAt: at(-4), endedAt: at(-1) }, [
      { playerId: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
      { playerId: ME, answer: 'LEFT' },
    ]);

    expect(belongsOnTheInbox(iEndedIt, ME)).toBe(false);
  });

  /** To the people still on the court the same departure is news, and their row keeps its day. */
  it('is news to the others, whose row stays while the court fills', () => {
    const theyLeft = challenge({ organiserId: ME, standing: 'LINE_UP_INCOMPLETE' }, [
      { playerId: ME, answer: 'ACCEPTED' },
      { playerId: EWA, answer: 'LEFT', nickname: 'ewa.m' },
    ]);

    expect(belongsOnTheInbox(theyLeft, ME)).toBe(true);
  });
});

describe('a removal of my own', () => {
  /**
   * **A removed challenge is the organiser's own act, by construction** — nobody else may remove
   * one, and only while nobody besides them holds an accepted seat (ADR-0165 §4,
   * [#428](https://github.com/Raketa02/Raketa/issues/428)) — so *You withdrew this* tells them
   * nothing, and the row goes with the tap as an own *no* and an own *left* do.
   */
  it('leaves at once, whatever seats were still deciding when it was removed', () => {
    const iRemovedIt = challenge(
      { organiserId: ME, standing: 'WITHDRAWN', sport: 'padel', openedAt: at(-4), endedAt: at(-1) },
      [
        { playerId: ME, answer: 'ACCEPTED' },
        { playerId: EWA, answerBy: at(20), nickname: 'ewa.m' },
        { playerId: 'ola', answer: 'DECLINED', answerBy: at(20), nickname: 'ola.k' },
        {},
      ],
    );

    expect(belongsOnTheInbox(iRemovedIt, ME)).toBe(false);
    expect(challengeInbox([iRemovedIt], ME)).toEqual([]);
  });

  /** To the people asked, the same removal is news — §13's sixth row — and their row keeps its day. */
  it('is news to an invitee, whose row stays its day', () => {
    const theyRemovedIt = challenge({ standing: 'WITHDRAWN', openedAt: at(-4), endedAt: at(-1) }, [
      { playerId: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
      { playerId: ME, answerBy: at(20) },
    ]);

    expect(belongsOnTheInbox(theyRemovedIt, ME)).toBe(true);
  });

  /**
   * **A game called off is not a removal**, though the standing is the same word: others had
   * joined, and since anybody on the court may call it off the organiser did not necessarily act.
   * Their row keeps its day, as it does for a departure.
   */
  it('is not a court called off with others on it, whose row keeps its day for the organiser', () => {
    const calledOff = challenge(
      {
        organiserId: ME,
        standing: 'WITHDRAWN',
        sport: 'padel',
        openedAt: at(-30),
        endedAt: at(-1),
      },
      [
        { playerId: ME, answer: 'ACCEPTED' },
        { playerId: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
        { playerId: 'ola', answer: 'ACCEPTED', nickname: 'ola.k' },
        { playerId: 'tomek', answer: 'LEFT', nickname: 'tomek.p' },
      ],
    );

    expect(belongsOnTheInbox(calledOff, ME)).toBe(true);
  });
});

describe('a court that ended on somebody leaving it, with me the one left', () => {
  /**
   * B said yes, C and D said no, and B took the yes back: the organiser is alone with nobody
   * deciding, so the court is over — `DECLINED`, because a departure is a no (ADR-0165 §3) —
   * and the seat that was taken back reads `LEFT`. The room the first yes opened is where the
   * departure was told, and what is left is a court with nobody committed to it but the reader:
   * nothing to fill and nobody to ask again about, so the row goes with the room rather than
   * keeping a day as news ([#429](https://github.com/Raketa02/Raketa/issues/429)).
   */
  it('leaves at once, for the reader left on it', () => {
    const theyAllWent = challenge(
      { organiserId: ME, standing: 'DECLINED', sport: 'padel', endedAt: at(-1) },
      [
        { playerId: ME, answer: 'ACCEPTED' },
        { playerId: EWA, answer: 'LEFT', nickname: 'ewa.m' },
        { playerId: 'ola', answer: 'DECLINED', nickname: 'ola.k' },
        { playerId: 'tomek', answer: 'DECLINED', nickname: 'tomek.p' },
      ],
    );

    expect(belongsOnTheInbox(theyAllWent, ME)).toBe(false);
    expect(challengeInbox([theyAllWent], ME)).toEqual([]);
  });

  /** The ending rule is organiser-blind, and so is this: an invitee left alone reads the same. */
  it('leaves at once for an invitee the organiser walked out on', () => {
    const organiserLeft = challenge({ standing: 'DECLINED', endedAt: at(-1) }, [
      { playerId: EWA, answer: 'LEFT', nickname: 'ewa.m' },
      { playerId: ME, answer: 'ACCEPTED' },
    ]);

    expect(belongsOnTheInbox(organiserLeft, ME)).toBe(false);
  });

  /**
   * A court everybody merely **declined** is not this: nobody was ever in it with the reader,
   * and *{name} said no — that seat is open again* is the news #388 keeps a day.
   */
  it('is not a court everybody declined, whose row keeps its day', () => {
    const allSaidNo = challenge(
      { organiserId: ME, standing: 'DECLINED', sport: 'padel', endedAt: at(-1) },
      [
        { playerId: ME, answer: 'ACCEPTED' },
        { playerId: EWA, answer: 'DECLINED', nickname: 'ewa.m' },
        { playerId: 'ola', answer: 'DECLINED', nickname: 'ola.k' },
        { playerId: 'tomek', answer: 'DECLINED', nickname: 'tomek.p' },
      ],
    );

    expect(belongsOnTheInbox(allSaidNo, ME)).toBe(true);
  });

  /** And not a reader whose own seat was never accepted — their day ran out, and that is theirs to read. */
  it('is not a court the reader lapsed on, whose row keeps its day', () => {
    const myDayRanOut = challenge({ standing: 'DECLINED', endedAt: at(-1) }, [
      { playerId: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
      { playerId: 'ola', answer: 'LEFT', nickname: 'ola.k' },
      { playerId: ME, answer: 'LAPSED', answerBy: at(-2) },
      {},
    ]);

    expect(belongsOnTheInbox(myDayRanOut, ME)).toBe(true);
  });
});

describe('who a row names', () => {
  /**
   * A court still being filled names the people still on it: a seat given up — a no, a day run
   * out, a yes taken back — keeps its occupant on the wire, and drew two faces of people who said
   * no under *2 in, 2 seats open* ([#429](https://github.com/Raketa02/Raketa/issues/429)). A
   * seat still deciding stays: they were asked and have not said no.
   */
  it('drops the seats that were given up while the court is still being filled', () => {
    const filling = challenge({ organiserId: ME, standing: 'LINE_UP_INCOMPLETE', sport: 'padel' }, [
      { playerId: ME, answer: 'ACCEPTED' },
      { playerId: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
      { playerId: 'ola', answer: 'DECLINED', nickname: 'ola.k' },
      { playerId: 'tomek', answer: 'LAPSED', nickname: 'tomek.p' },
    ]);
    const awaiting = challenge({ organiserId: ME, standing: 'AWAITING_ANSWERS', sport: 'padel' }, [
      { playerId: ME, answer: 'ACCEPTED' },
      { playerId: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
      { playerId: 'ola', answer: 'DECLINED', nickname: 'ola.k' },
      { playerId: 'tomek', answerBy: at(20), nickname: 'tomek.p' },
      { playerId: 'kuba', answer: 'LEFT', nickname: 'kuba.z' },
    ]);

    expect(othersOn(filling, ME).map((seat) => seat.playerId)).toEqual([EWA]);
    expect(othersOn(awaiting, ME).map((seat) => seat.playerId)).toEqual([EWA, 'tomek']);
  });

  /** An ended court is history rather than a line-up, and names everybody it asked. */
  it('names everybody asked once the court has ended, so a singles no still has a face', () => {
    const declined = challenge({ organiserId: ME, standing: 'DECLINED', endedAt: at(-1) }, [
      { playerId: ME, answer: 'ACCEPTED' },
      { playerId: EWA, answer: 'DECLINED', nickname: 'ewa.m' },
    ]);
    const on = challenge({ organiserId: ME, standing: 'ON' }, [
      { playerId: ME, answer: 'ACCEPTED' },
      { playerId: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
    ]);

    expect(othersOn(declined, ME).map((seat) => seat.playerId)).toEqual([EWA]);
    expect(othersOn(on, ME).map((seat) => seat.playerId)).toEqual([EWA]);
  });

  it('never names the reader, and never an empty seat', () => {
    const court = challenge({ organiserId: ME, standing: 'LINE_UP_INCOMPLETE', sport: 'padel' }, [
      { playerId: ME, answer: 'ACCEPTED' },
      { playerId: EWA, answer: 'ACCEPTED', nickname: 'ewa.m' },
      {},
      {},
    ]);

    expect(othersOn(court, ME).map((seat) => seat.playerId)).toEqual([EWA]);
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
