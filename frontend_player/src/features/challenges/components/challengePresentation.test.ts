/**
 * What a challenge says.
 *
 * Four things are asserted rather than the wording. One code reads as **two sentences**, one
 * per side; `LINE_UP_INCOMPLETE` never reads as a waiting room, because the chat is already
 * open; that same line counts **open seats** and not answers, because at that rung there are
 * none outstanding and the figure it used to quote could only ever be zero; and **a lapse is
 * not a decline**, because the `answers challenges` strand needs the denominator and copy that
 * blurred them would restate one fact as another.
 */

import type { NamedPlayer } from '@/shared/formatting/playerName';

import { STANDINGS, type ChallengeSide } from '../domain/standing';

import {
  MUTUAL_YES,
  NOBODY_IS_CONTACTED_YET,
  answerWindowLine,
  proposeClosing,
  standingLine,
  type StandingFacts,
} from './challengePresentation';

/** The other player, as a person rather than as a string — ADR-0107's rule, held by a type. */
const SOMEBODY: NamedPlayer = { kind: 'player', nickname: 'niepokonany' };

/** One of each standing, with whatever its sentence quotes. */
function facts(side: ChallengeSide): readonly StandingFacts[] {
  return [
    { side, standing: 'AWAITING_ANSWERS', awaiting: 3 },
    { side, standing: 'ON' },
    { side, standing: 'LINE_UP_INCOMPLETE', accepted: 2, open: 1 },
    { side, standing: 'DECLINED', player: SOMEBODY },
    { side, standing: 'LAPSED', player: SOMEBODY },
  ];
}

describe('one standing, two sides', () => {
  it('says something different to each of them, for every code', () => {
    const organiser = facts('organiser').map(standingLine);
    const invitee = facts('invitee').map(standingLine);

    expect(organiser).toHaveLength(STANDINGS.length);
    for (const [index, line] of organiser.entries()) expect(line).not.toBe(invitee[index]);
  });

  it('asks the organiser to wait and tells an invitee they are the wait', () => {
    expect(standingLine({ side: 'organiser', standing: 'AWAITING_ANSWERS', awaiting: 3 })).toBe(
      'Waiting on 3 answers',
    );
    expect(standingLine({ side: 'invitee', standing: 'AWAITING_ANSWERS', awaiting: 3 })).toBe(
      "They're waiting on you",
    );
  });

  it('hardcodes no plural', () => {
    expect(standingLine({ side: 'organiser', standing: 'AWAITING_ANSWERS', awaiting: 1 })).toBe(
      'Waiting on 1 answer',
    );
  });
});

describe('a half-answered line-up is not a waiting room', () => {
  it('says the chat is already open, on both sides', () => {
    // #221: the chat opens on the first acceptance and grows with each one, so *waiting for
    // the rest* is the obvious phrasing and the false one.
    for (const side of ['organiser', 'invitee'] as const) {
      const line = standingLine({ side, standing: 'LINE_UP_INCOMPLETE', accepted: 2, open: 1 });

      expect(line).toMatch(/the chat is already open/);
      expect(line).not.toMatch(/waiting for the rest|once everybody/i);
    }
  });

  it('counts the seats that are open, and never the answers that cannot be outstanding', () => {
    // `standing_of` returns `AWAITING_ANSWERS` while **any** seat is still awaiting, so at the
    // rung that yields this standing nothing is. The figure this line used to quote could only
    // ever be zero, and the sentence it built read *"2 in, 0 still to answer"*.
    const organiser = standingLine({
      side: 'organiser',
      standing: 'LINE_UP_INCOMPLETE',
      accepted: 2,
      open: 1,
    });
    const invitee = standingLine({
      side: 'invitee',
      standing: 'LINE_UP_INCOMPLETE',
      accepted: 2,
      open: 1,
    });

    expect(organiser).toBe('2 in, 1 seat open — the chat is already open');
    expect(invitee).toBe("You're in. 1 seat open, and the chat is already open");
    for (const line of [organiser, invitee]) expect(line).not.toMatch(/still to answer/i);
  });

  it('hardcodes no plural here either', () => {
    expect(
      standingLine({ side: 'organiser', standing: 'LINE_UP_INCOMPLETE', accepted: 1, open: 2 }),
    ).toBe('1 in, 2 seats open — the chat is already open');
  });
});

describe('a lapse is not a decline', () => {
  it('says a day ran out and that nobody said no', () => {
    expect(standingLine({ side: 'organiser', standing: 'LAPSED', player: SOMEBODY })).toBe(
      "niepokonany's day ran out — that seat is open again",
    );
    expect(standingLine({ side: 'invitee', standing: 'LAPSED', player: SOMEBODY })).toBe(
      'Your day ran out',
    );
  });

  it('keeps the two words apart', () => {
    const lapsed = [
      standingLine({ side: 'organiser', standing: 'LAPSED', player: SOMEBODY }),
      standingLine({ side: 'invitee', standing: 'LAPSED', player: SOMEBODY }),
    ];

    for (const line of lapsed) expect(line).not.toMatch(/said no|declin|refus/i);
  });

  it('names the whole handle and never a familiar form of it', () => {
    const line = standingLine({
      side: 'organiser',
      standing: 'DECLINED',
      player: { kind: 'player', nickname: 'niepokonanywojownik42' },
    });

    expect(line).toMatch(/^niepokonanywojownik42 said no/);
  });
});

describe('the three sentences that stood behind one constant', () => {
  it('promises irreversibility before the send, and names no duration', () => {
    // "24 h" is not a string: a seat carries its own `answer_by`, and #241 took the branch
    // where the pre-send sheet names no duration at all.
    expect(NOBODY_IS_CONTACTED_YET).toBe('Nobody is contacted until you send it.');
    expect(NOBODY_IS_CONTACTED_YET).not.toMatch(/24|hour|h\b/i);
  });

  it('states the real deadline per seat, from a duration it was given', () => {
    expect(answerWindowLine({ player: SOMEBODY, duration: '21 h' })).toBe(
      'niepokonany · 21 h left',
    );
  });

  it('gives a mutual yes no deadline clause at all', () => {
    // `ChallengeOpenedFromMutualInterest` carries *no deadline* as a distinct event, because a
    // nullable `answer_by` is how a later reader invents one that never existed.
    expect(MUTUAL_YES).toBe("You both said yes — this one's already on.");
    expect(MUTUAL_YES).not.toMatch(/\d|answer by|left/i);
  });
});

describe('what the pre-send sheet closes with', () => {
  it('promises nothing opens, for singles', () => {
    expect(proposeClosing({ kind: 'singles' })).toBe('Nothing opens until they accept.');
  });

  it('says the opposite for doubles, because the first yes opens the chat', () => {
    expect(proposeClosing({ kind: 'doubles', sportName: 'Padel', stillNeeded: 2 })).toBe(
      'Padel is doubles — you need 2 more. The first person to say yes is in, and you can start talking then.',
    );
  });
});
