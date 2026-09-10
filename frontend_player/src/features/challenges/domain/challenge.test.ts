/**
 * The pair rule, read from the client's side — **the naming a refusal refuses to do.**
 *
 * What is asserted is the set of claims a build session could quietly undo: an ended challenge
 * releases the pair, a seat that declined or lapsed releases one person out of a challenge
 * that still stands, and the organiser is never the answer to *who are you already playing*.
 */

import type { Challenge, ChallengeSeat } from './challenge';
import { challengeStands, pairAlreadyPlaying, playersStillIn, standingFactsFor } from './challenge';
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
  it('counts the three live standings and none of the three endings', () => {
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
  const named = (playerId: string, nickname: string, answer?: SeatAnswer): ChallengeSeat => ({
    playerId,
    nickname,
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

  it('names the first person in court order to have given the answer that ended it', () => {
    const declined = challenge('DECLINED', [
      named(ME, 'me.p', 'ACCEPTED'),
      named(BEA, 'bea.k', 'DECLINED'),
    ]);

    expect(standingFactsFor(declined, ME)).toMatchObject({
      standing: 'DECLINED',
      player: { kind: 'player', nickname: 'bea.k' },
    });
  });

  it('names the organiser on a withdrawal, and nobody at all when users has lost them', () => {
    const withdrawn = challenge('WITHDRAWN', [named(ME, 'me.p'), named(BEA, 'bea.k')]);

    expect(standingFactsFor(withdrawn, BEA)).toMatchObject({
      player: { kind: 'player', nickname: 'me.p' },
    });

    const nameless: Challenge = { ...withdrawn, seats: [{ playerId: ME }, { playerId: BEA }] };
    expect(standingFactsFor(nameless, BEA)).toMatchObject({ player: { kind: 'unknown' } });
  });

  it('folds to nothing on a standing it has no words for, so the row draws the gap', () => {
    const unreadable: Challenge = { ...halfBuilt, standing: undefined };

    expect(standingFactsFor(unreadable, ME)).toBeUndefined();
  });
});
