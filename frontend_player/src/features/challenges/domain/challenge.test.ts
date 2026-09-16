/**
 * The pair rule, read from the client's side — **the naming a refusal refuses to do.**
 *
 * What is asserted is the set of claims a build session could quietly undo: an ended challenge
 * releases the pair, a seat that declined or lapsed releases one person out of a challenge
 * that still stands, and the organiser is never the answer to *who are you already playing*.
 */

import type { Challenge, ChallengeSeat } from './challenge';
import {
  challengeStands,
  holdsTheExit,
  leavingWouldEnd,
  mayDismiss,
  mayRemove,
  pairAlreadyPlaying,
  playersStillIn,
  standingFactsFor,
} from './challenge';
import { STANDINGS, type SeatAnswer, type Standing } from './standing';

const ME = 'me';
const BEA = 'bea';
const CYRYL = 'cyryl';

function challenge(standing: Standing, seats: readonly ChallengeSeat[]): Challenge {
  return {
    challengeId: 'c1',
    organiserId: ME,
    standing,
    sport: 'padel',
    openedAt: '2026-09-05T09:00:00Z',
    readAt: '2026-09-05T12:00:00Z',
    seats,
  };
}

/** A live singles game between the two of us: my seat accepted from birth, theirs waiting. */
const WAITING_ON_BEA = challenge('AWAITING_ANSWERS', [
  { playerId: ME, answer: 'ACCEPTED' },
  { playerId: BEA },
]);

describe('which challenges still hold a pair', () => {
  it('counts the three live standings and none of the four endings', () => {
    const stands = STANDINGS.filter((standing) => challengeStands(challenge(standing, [])));

    expect(stands).toEqual(['AWAITING_ANSWERS', 'ON', 'LINE_UP_INCOMPLETE']);
  });

  it('empties an ended challenge, so the pair releases with it', () => {
    const declined = challenge('DECLINED', [
      { playerId: ME, answer: 'ACCEPTED' },
      { playerId: BEA, answer: 'DECLINED' },
    ]);

    expect(playersStillIn(declined)).toEqual([]);
  });

  /**
   * A decline and a lapse both open the seat, and **the challenge can stand without them**: a
   * padel four where one person said no is `LINE_UP_INCOMPLETE`, and that one person is a
   * stranger again while the other two are not.
   */
  it('drops the seat that said no from a challenge that still stands', () => {
    const short = challenge('LINE_UP_INCOMPLETE', [
      { playerId: ME, answer: 'ACCEPTED' },
      { playerId: BEA, answer: 'ACCEPTED' },
      { playerId: CYRYL, answer: 'DECLINED' },
      {},
    ]);

    expect(playersStillIn(short)).toEqual([ME, BEA]);
  });

  it('drops the seat whose day ran out for the same reason, and it is not a decline', () => {
    const lapsed = challenge('LINE_UP_INCOMPLETE', [
      { playerId: ME, answer: 'ACCEPTED' },
      { playerId: BEA, answer: 'ACCEPTED' },
      { playerId: CYRYL, answer: 'LAPSED' },
      {},
    ]);

    expect(playersStillIn(lapsed)).toEqual([ME, BEA]);
  });

  /**
   * The third way a seat opens (ADR-0162): somebody leaving a game they had agreed to. It is
   * neither a no nor silence, and the pair releases the moment they go — a seat kept in the game
   * here would be somebody uninvitable by the person they just walked out on.
   */
  it('drops the seat that left the game, which is neither a no nor silence', () => {
    const left = challenge('LINE_UP_INCOMPLETE', [
      { playerId: ME, answer: 'ACCEPTED' },
      { playerId: BEA, answer: 'ACCEPTED' },
      { playerId: CYRYL, answer: 'LEFT' },
      {},
    ]);

    expect(playersStillIn(left)).toEqual([ME, BEA]);
  });
});

/**
 * **Who may call a game off** — any player on the court
 * ([ADR-0165](../../../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
 * §5, [#428](https://github.com/Raketa02/Raketa/issues/428)): the reader holds an accepted seat,
 * and nothing about who organised it. The organiser-first rule and its fallback are gone.
 */
describe('who holds the exit', () => {
  /** A padel four that became a game and lost Cyryl; Bea organised it. */
  const reopened = (organiserAnswer: SeatAnswer = 'ACCEPTED') =>
    ({
      ...challenge('LINE_UP_INCOMPLETE', [
        { playerId: BEA, answer: organiserAnswer },
        { playerId: ME, answer: 'ACCEPTED' },
        { playerId: CYRYL, answer: 'LEFT' },
        { playerId: 'dorota', answer: 'ACCEPTED' },
      ]),
      organiserId: BEA,
    }) satisfies Challenge;

  it('is any player’s on the court, the organiser or not', () => {
    expect(holdsTheExit(reopened(), BEA)).toBe(true);
    expect(holdsTheExit(reopened(), ME)).toBe(true);
    expect(holdsTheExit(reopened(), 'dorota')).toBe(true);
  });

  it('is nobody’s who has left, the organiser included', () => {
    expect(holdsTheExit(reopened('LEFT'), BEA)).toBe(false);
    expect(holdsTheExit(reopened('LEFT'), CYRYL)).toBe(false);
  });

  it('is nobody’s who holds no seat on it, or a seat still deciding', () => {
    expect(holdsTheExit(reopened(), 'stranger')).toBe(false);
    expect(
      holdsTheExit(
        {
          ...reopened(),
          seats: [...reopened().seats.slice(0, 3), { playerId: 'newcomer' }],
        },
        'newcomer',
      ),
    ).toBe(false);
  });
});

/**
 * **Who may remove a challenge** — the organiser, exactly while nobody besides them holds an
 * accepted seat, whatever seats are still deciding (ADR-0165 §4, #428). Pinned across organiser /
 * invitee / joined / not joined, which is the row's reveal decision and the arranging arm's.
 */
describe('who may remove the challenge', () => {
  /** My padel four, just sent: three people asked, nobody has answered. */
  const justSent = challenge('AWAITING_ANSWERS', [
    { playerId: ME, answer: 'ACCEPTED' },
    { playerId: BEA, answerBy: '2026-09-06T09:00:00Z' },
    { playerId: CYRYL, answerBy: '2026-09-06T09:00:00Z' },
    { playerId: 'dorota', answerBy: '2026-09-06T09:00:00Z' },
  ]);

  it('is the organiser’s while nobody has answered', () => {
    expect(mayRemove(justSent, ME)).toBe(true);
  });

  it('is never an invitee’s, answered or not', () => {
    expect(mayRemove(justSent, BEA)).toBe(false);
    expect(mayRemove({ ...justSent, organiserId: BEA }, ME)).toBe(false);
  });

  it('is nobody’s once somebody has joined, however many are still deciding', () => {
    const joined: Challenge = {
      ...justSent,
      seats: [
        { playerId: ME, answer: 'ACCEPTED' },
        { playerId: BEA, answer: 'ACCEPTED' },
        { playerId: CYRYL, answerBy: '2026-09-06T09:00:00Z' },
        { playerId: 'dorota', answerBy: '2026-09-06T09:00:00Z' },
      ],
    };

    expect(mayRemove(joined, ME)).toBe(false);
    expect(mayRemove(joined, BEA)).toBe(false);
  });

  /** A yes taken back leaves the organiser alone again, and the act comes back with it. */
  it('is the organiser’s again once everybody who joined has left, with others still deciding', () => {
    const aloneAgain: Challenge = {
      ...justSent,
      seats: [
        { playerId: ME, answer: 'ACCEPTED' },
        { playerId: BEA, answer: 'LEFT' },
        { playerId: CYRYL, answer: 'DECLINED' },
        { playerId: 'dorota', answerBy: '2026-09-06T09:00:00Z' },
      ],
    };

    expect(mayRemove(aloneAgain, ME)).toBe(true);
  });

  it('is nobody’s once the challenge has ended, or on a standing this build cannot read', () => {
    for (const standing of ['DECLINED', 'LAPSED', 'WITHDRAWN'] as const) {
      expect(mayRemove({ ...justSent, standing }, ME)).toBe(false);
    }
    const { standing: _unread, ...unreadable } = justSent;
    expect(mayRemove(unreadable, ME)).toBe(false);
  });
});

/**
 * **Who may clear a called-off court** — anybody still seated on it, on `CALLED_OFF` and nothing
 * else (ADR-0173). The row's reveal decision for the one ending that moves.
 */
describe('who may clear a called-off court', () => {
  const GAME = 'g1';

  /** The court both readings fit: my four, everybody accepted, and the three of them left. */
  const leftAloneOn = {
    ...challenge('CALLED_OFF', [
      { playerId: ME, answer: 'ACCEPTED' },
      { playerId: BEA, answer: 'LEFT' },
      { playerId: CYRYL, answer: 'LEFT' },
      { playerId: 'dorota', answer: 'LEFT' },
    ]),
    gameId: GAME,
    endedBy: 'dorota',
  };

  it('is the one left behind’s, and not a leaver’s', () => {
    expect(mayDismiss(leftAloneOn, ME)).toBe(true);
    expect(mayDismiss(leftAloneOn, BEA)).toBe(false);
    expect(mayDismiss(leftAloneOn, 'dorota')).toBe(false);
  });

  it('is everybody still seated’s when somebody pressed Call it off, the presser included', () => {
    const pressed = {
      ...challenge('CALLED_OFF', [
        { playerId: ME, answer: 'ACCEPTED' },
        { playerId: BEA, answer: 'ACCEPTED' },
        { playerId: CYRYL, answer: 'LEFT' },
        { playerId: 'dorota', answer: 'ACCEPTED' },
      ]),
      gameId: GAME,
      endedBy: BEA,
    };

    expect(mayDismiss(pressed, ME)).toBe(true);
    expect(mayDismiss(pressed, BEA)).toBe(true);
    expect(mayDismiss(pressed, CYRYL)).toBe(false);
    expect(mayDismiss(pressed, 'stranger')).toBe(false);
  });

  it('is nobody’s on any other standing, or on a court with no game behind it', () => {
    for (const standing of STANDINGS) {
      if (standing === 'CALLED_OFF') continue;
      expect(mayDismiss({ ...leftAloneOn, standing }, ME)).toBe(false);
    }
    const { standing: _unread, ...unreadable } = leftAloneOn;
    expect(mayDismiss(unreadable, ME)).toBe(false);
    const { gameId: _none, ...neverAGame } = leftAloneOn;
    expect(mayDismiss(neverAGame, ME)).toBe(false);
  });
});

describe('who on this court you already have a game with', () => {
  it('names the invitee an open challenge of yours still holds', () => {
    expect(pairAlreadyPlaying([WAITING_ON_BEA], [BEA, CYRYL])).toBe(BEA);
  });

  /** In seat order, because §21's sentence names one person and the court has an order. */
  it('names the first of them in seat order', () => {
    const withCyryl = challenge('ON', [
      { playerId: ME, answer: 'ACCEPTED' },
      { playerId: CYRYL, answer: 'ACCEPTED' },
    ]);

    expect(pairAlreadyPlaying([WAITING_ON_BEA, withCyryl], [CYRYL, BEA])).toBe(CYRYL);
  });

  /** The organiser holds a seat in every challenge of their own, so they are never the answer. */
  it('is asked without the organiser, so their own seat names nobody', () => {
    expect(pairAlreadyPlaying([WAITING_ON_BEA], [CYRYL])).toBeUndefined();
  });

  /**
   * The refusal is about **any** pair on the court, so the game in the way can be between two
   * invitees — and that one is not the organiser's to read. Nothing is named, and the screen
   * says the nameless thing rather than guessing.
   */
  it('names nobody when the game in the way is not one of yours', () => {
    expect(pairAlreadyPlaying([], [BEA, CYRYL])).toBeUndefined();
  });

  it('names nobody out of a challenge that has ended', () => {
    const over = challenge('LAPSED', [
      { playerId: ME, answer: 'ACCEPTED' },
      { playerId: BEA, answer: 'LAPSED' },
    ]);

    expect(pairAlreadyPlaying([over], [BEA])).toBeUndefined();
  });
});

/**
 * The fold every sentence is keyed on. Three claims, each of which has been wrong somewhere:
 * the count is of **open seats**, an invitee who has left reads their own seat rather than
 * their side, and a standing this build cannot read folds to nothing so the row can draw the
 * gap instead of a sentence about a code nobody here understands.
 */
describe('what a standing says to a reader', () => {
  const named = (playerId: string, name: string, answer?: SeatAnswer): ChallengeSeat => ({
    playerId,
    name,
    ...(answer === undefined ? {} : { answer }),
  });

  /** A padel four of mine: Bea accepted, Cyryl declined, one seat was never filled. */
  const halfBuilt = challenge('LINE_UP_INCOMPLETE', [
    named(ME, 'me.p', 'ACCEPTED'),
    named(BEA, 'bea.k', 'ACCEPTED'),
    named(CYRYL, 'cyryl.w', 'DECLINED'),
    {},
  ]);

  it('reads the side off the organiser seat and never off a field', () => {
    expect(standingFactsFor(halfBuilt, ME)?.side).toBe('organiser');
    expect(standingFactsFor(halfBuilt, BEA)?.side).toBe('invitee');
  });

  it('counts seats nobody has accepted, never seats still to answer', () => {
    const facts = standingFactsFor(halfBuilt, BEA);

    // Cyryl's, which a decline reopened, and the one nobody was ever put in.
    expect(facts).toMatchObject({ standing: 'LINE_UP_INCOMPLETE', accepted: 2, open: 2 });
  });

  it('carries the reader\u2019s own seat, which is the third reading of an invitee', () => {
    expect(standingFactsFor(halfBuilt, CYRYL)).toMatchObject({
      side: 'invitee',
      ownAnswer: 'DECLINED',
    });
    expect(standingFactsFor(halfBuilt, BEA)).toMatchObject({ ownAnswer: 'ACCEPTED' });
  });

  /**
   * #389. The same third reading is owed one row up: `standing_of` returns `AWAITING_ANSWERS`
   * while **any** seat is awaiting, so a padel four can be in it with the reader's own answer
   * already given — accepted, or given and then released.
   */
  it('carries the reader’s own seat while somebody else is still deciding', () => {
    // Ola has not answered, which is what keeps this in `AWAITING_ANSWERS`.
    const stillDeciding = (mine?: SeatAnswer) =>
      challenge('AWAITING_ANSWERS', [
        named(ME, 'me.p', 'ACCEPTED'),
        named(BEA, 'bea.k', mine),
        named(CYRYL, 'cyryl.w'),
      ]);

    expect(standingFactsFor(stillDeciding('ACCEPTED'), BEA)).toMatchObject({
      standing: 'AWAITING_ANSWERS',
      side: 'invitee',
      ownAnswer: 'ACCEPTED',
    });
    expect(standingFactsFor(stillDeciding('DECLINED'), BEA)).toMatchObject({
      ownAnswer: 'DECLINED',
    });
    expect(standingFactsFor(stillDeciding('LAPSED'), BEA)).toMatchObject({ ownAnswer: 'LAPSED' });
  });

  /**
   * **Absence means the opposite thing here**, and the field is the same one: on
   * `LINE_UP_INCOMPLETE` an absent answer is a reader who is in, and here it is a reader who
   * has not spoken. What is the same is the rule — absent draws the sentence that shipped.
   */
  it('leaves the reader’s own seat off entirely when they have not answered', () => {
    const asked = challenge('AWAITING_ANSWERS', [
      named(ME, 'me.p', 'ACCEPTED'),
      named(BEA, 'bea.k'),
      named(CYRYL, 'cyryl.w'),
    ]);

    expect(standingFactsFor(asked, BEA)).not.toHaveProperty('ownAnswer');
  });

  /**
   * **An ending names whose act ended it, and the wire says who** — `ended_by`, never a walk
   * over the seats ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
   * §3, §7): the name and the date come from the same fold on the server, and a seat that
   * `LEFT` reads as a departure wherever it is named.
   */
  it('names ended_by on a decline, and says whether their seat was a departure', () => {
    const declined = challenge('DECLINED', [
      named(ME, 'me.p', 'ACCEPTED'),
      named(BEA, 'bea.k', 'DECLINED'),
    ]);

    expect(standingFactsFor({ ...declined, endedBy: BEA }, ME)).toMatchObject({
      standing: 'DECLINED',
      endedBy: { kind: 'player', name: 'bea.k' },
      byADeparture: false,
    });

    // B took the yes back after C said no: the wire names B, whose seat reads `LEFT`.
    const deserted = challenge('DECLINED', [
      named(ME, 'me.p', 'ACCEPTED'),
      named(BEA, 'bea.k', 'LEFT'),
      named(CYRYL, 'cyryl.w', 'DECLINED'),
      {},
    ]);

    expect(standingFactsFor({ ...deserted, endedBy: BEA }, ME)).toMatchObject({
      standing: 'DECLINED',
      endedBy: { kind: 'player', name: 'bea.k' },
      byADeparture: true,
    });
  });

  it('names the reader as *you* where their own act ended it, and carries their own seat', () => {
    const iSaidNo: Challenge = {
      ...challenge('DECLINED', [named(BEA, 'bea.k', 'ACCEPTED'), named(ME, 'me.p', 'DECLINED')]),
      organiserId: BEA,
      endedBy: ME,
    };

    expect(standingFactsFor(iSaidNo, ME)).toMatchObject({
      standing: 'DECLINED',
      endedBy: { kind: 'you' },
      byADeparture: false,
      ownAnswer: 'DECLINED',
    });
  });

  /**
   * The seventh standing, keyed the same way: the last leaver's seat reads `LEFT`, the presser's
   * still reads `ACCEPTED`, and which of the two it was is the whole difference between
   * *{name} left* and *{name} called the game off*.
   */
  it('tells a call-off by a departure from one by the button off ended_by’s seat', () => {
    const beaLeft = challenge('CALLED_OFF', [
      named(ME, 'me.p', 'ACCEPTED'),
      named(BEA, 'bea.k', 'LEFT'),
    ]);
    const beaPressed = challenge('CALLED_OFF', [
      named(ME, 'me.p', 'ACCEPTED'),
      named(BEA, 'bea.k', 'ACCEPTED'),
      named(CYRYL, 'cyryl.w', 'LEFT'),
      {},
    ]);

    expect(standingFactsFor({ ...beaLeft, endedBy: BEA }, ME)).toMatchObject({
      standing: 'CALLED_OFF',
      endedBy: { kind: 'player', name: 'bea.k' },
      byADeparture: true,
    });
    expect(standingFactsFor({ ...beaPressed, endedBy: BEA }, ME)).toMatchObject({
      standing: 'CALLED_OFF',
      endedBy: { kind: 'player', name: 'bea.k' },
      byADeparture: false,
    });
    expect(standingFactsFor({ ...beaPressed, endedBy: ME }, ME)).toMatchObject({
      endedBy: { kind: 'you' },
      byADeparture: false,
    });
  });

  it('names the organiser on a withdrawal, and nobody at all when users has lost them', () => {
    const withdrawn: Challenge = {
      ...challenge('WITHDRAWN', [named(ME, 'me.p'), named(BEA, 'bea.k')]),
      endedBy: ME,
    };

    expect(standingFactsFor(withdrawn, BEA)).toMatchObject({
      endedBy: { kind: 'player', name: 'me.p' },
    });
    expect(standingFactsFor(withdrawn, ME)).toMatchObject({ endedBy: { kind: 'you' } });

    const nameless: Challenge = { ...withdrawn, seats: [{ playerId: ME }, { playerId: BEA }] };
    expect(standingFactsFor(nameless, BEA)).toMatchObject({ endedBy: { kind: 'unknown' } });
  });

  /** The wire broke its promise: an ending with nobody named draws `?`, and never a guess. */
  it('names nobody where the contract claimed an ending and named nobody', () => {
    const declined = challenge('DECLINED', [
      named(ME, 'me.p', 'ACCEPTED'),
      named(BEA, 'bea.k', 'DECLINED'),
    ]);

    expect(standingFactsFor(declined, ME)).toMatchObject({
      endedBy: { kind: 'unknown' },
      byADeparture: false,
    });
  });

  it('folds to nothing on a standing it has no words for, so the row draws the gap', () => {
    const unreadable: Challenge = { ...halfBuilt, standing: undefined };

    expect(standingFactsFor(unreadable, ME)).toBeUndefined();
  });
});

/**
 * **What the reader's leaving would do to the court** — the sheet's rule
 * ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
 * §9): the reader is the only other accepted seat and no seat is awaiting an answer, read off
 * the row the list holds, and `game_id` says whether that ends a game or closes a court.
 */
describe('what leaving would end', () => {
  const named = (playerId: string, name: string, answer?: SeatAnswer): ChallengeSeat => ({
    playerId,
    name,
    ...(answer === undefined ? {} : { answer }),
  });

  it('calls the game off for the one person left, on a court that has been a game', () => {
    const singles: Challenge = {
      ...challenge('ON', [named(BEA, 'bea.k', 'ACCEPTED'), named(ME, 'me.p', 'ACCEPTED')]),
      organiserId: BEA,
      gameId: 'g1',
    };

    expect(leavingWouldEnd(singles, ME)).toEqual({
      court: 'a-game',
      theOneLeft: { kind: 'player', name: 'bea.k' },
    });
  });

  it('closes the court for the one person left, on a court that was never a game', () => {
    const halfBuilt = challenge('LINE_UP_INCOMPLETE', [
      named(ME, 'me.p', 'ACCEPTED'),
      named(BEA, 'bea.k', 'ACCEPTED'),
      named(CYRYL, 'cyryl.w', 'DECLINED'),
      {},
    ]);

    expect(leavingWouldEnd(halfBuilt, BEA)).toEqual({
      court: 'never-a-game',
      theOneLeft: { kind: 'player', name: 'me.p' },
    });
  });

  it('ends nothing while somebody is still deciding, or while two others are in', () => {
    const deciding = challenge('AWAITING_ANSWERS', [
      named(ME, 'me.p', 'ACCEPTED'),
      named(BEA, 'bea.k', 'ACCEPTED'),
      { playerId: CYRYL, name: 'cyryl.w', answerBy: '2026-09-06T09:00:00Z' },
      {},
    ]);
    const three: Challenge = {
      ...challenge('LINE_UP_INCOMPLETE', [
        named(ME, 'me.p', 'ACCEPTED'),
        named(BEA, 'bea.k', 'ACCEPTED'),
        named(CYRYL, 'cyryl.w', 'ACCEPTED'),
        { playerId: 'dana', name: 'dana.s', answer: 'LEFT' },
      ]),
      gameId: 'g1',
    };

    expect(leavingWouldEnd(deciding, BEA)).toBeUndefined();
    expect(leavingWouldEnd(three, BEA)).toBeUndefined();
  });

  it('ends nothing for a reader who holds no accepted seat, or on a court already over', () => {
    const iLeftAlready = challenge('LINE_UP_INCOMPLETE', [
      named(ME, 'me.p', 'LEFT'),
      named(BEA, 'bea.k', 'ACCEPTED'),
      named(CYRYL, 'cyryl.w', 'ACCEPTED'),
      {},
    ]);
    const over: Challenge = {
      ...challenge('CALLED_OFF', [named(ME, 'me.p', 'ACCEPTED'), named(BEA, 'bea.k', 'LEFT')]),
      endedBy: BEA,
      gameId: 'g1',
    };

    expect(leavingWouldEnd(iLeftAlready, ME)).toBeUndefined();
    expect(leavingWouldEnd(over, ME)).toBeUndefined();
  });

  it('names the one left as ? where users has lost them, and still says what ends', () => {
    const nameless: Challenge = {
      ...challenge('ON', [{ playerId: BEA, answer: 'ACCEPTED' }, named(ME, 'me.p', 'ACCEPTED')]),
      gameId: 'g1',
    };

    expect(leavingWouldEnd(nameless, ME)).toEqual({
      court: 'a-game',
      theOneLeft: { kind: 'unknown' },
    });
  });
});
