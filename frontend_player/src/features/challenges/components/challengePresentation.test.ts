/**
 * What a challenge says.
 *
 * Five things are asserted rather than the wording. One code reads as **two sentences**, one
 * per side; `LINE_UP_INCOMPLETE` never reads as a waiting room, because the chat is already
 * open; that same line counts **open seats** and not answers, because at that rung there are
 * none outstanding and the figure it used to quote could only ever be zero; **a lapse is
 * not a decline**, because the `answers challenges` strand needs the denominator and copy that
 * blurred them would restate one fact as another; and on the two live standings the invitee's
 * sentence reads **the reader's own seat and not only their side** (§13.1, §13.2) — the claim
 * most easily undone, because the side is the obvious key and it is wrong in doubles.
 */

import type { NamedPlayer } from '@/shared/formatting/playerName';

import {
  STANDINGS,
  type ChallengeSide,
  type SeatAnswer,
  type StandingFacts,
} from '../domain/standing';

import {
  CHALLENGES_HEADING,
  CHALLENGE_SCREEN_TITLE,
  MUTUAL_YES,
  NOBODY_IS_CONTACTED_YET,
  answerWindowLine,
  proposeClosing,
  standingLine,
  yourAnswerWindowLine,
} from './challengePresentation';

/** The other player, as a person rather than as a string — ADR-0107's rule, held by a type. */
const SOMEBODY: NamedPlayer = { kind: 'player', name: 'niepokonany' };

/** One of each standing, with whatever its sentence quotes. */
function facts(side: ChallengeSide): readonly StandingFacts[] {
  return [
    { side, standing: 'AWAITING_ANSWERS', awaiting: 3 },
    { side, standing: 'ON' },
    { side, standing: 'LINE_UP_INCOMPLETE', accepted: 2, open: 1 },
    { side, standing: 'DECLINED', player: SOMEBODY },
    { side, standing: 'LAPSED', player: SOMEBODY },
    { side, standing: 'WITHDRAWN', player: SOMEBODY },
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

/**
 * §13.2 — one row, **four readings, three of them new** (#389).
 *
 * `They're waiting on you` assumes the reader has not answered, and in doubles one has:
 * `standing_of` returns `AWAITING_ANSWERS` while **any** seat is awaiting, so an invitee who
 * accepted, declined or lapsed sits in this standing being told they are the holdup. Singles
 * cannot reach it — the only invitee accepting takes the challenge to `ON`.
 */
describe('an invitee who has already answered is not the wait', () => {
  const invitee = (ownAnswer?: SeatAnswer): StandingFacts => ({
    side: 'invitee',
    standing: 'AWAITING_ANSWERS',
    awaiting: 2,
    ...(ownAnswer === undefined ? {} : { ownAnswer }),
  });

  it('still tells the one who has not answered that they are the wait', () => {
    expect(standingLine(invitee())).toBe("They're waiting on you");
  });

  /**
   * The shape is §13's `LINE_UP_INCOMPLETE` invitee sentence with one clause swapped, and the
   * clause is the organiser's own sentence: both sides print the same `awaiting`, so the two
   * cannot disagree about the number. **The chat clause is #221's refusal** — the room opened
   * on the first acceptance, so an accepted reader told only *waiting* is the waiting room it
   * forbids.
   */
  it('tells the one who is in that they are in, what is left, and that the room is open', () => {
    expect(standingLine(invitee('ACCEPTED'))).toBe(
      "You're in. Waiting on 2 answers, and the chat is already open",
    );
  });

  it('keeps its own first clause for each of the three who have left', () => {
    expect(standingLine(invitee('DECLINED'))).toBe(
      'You said no. They are still waiting on answers.',
    );
    expect(standingLine(invitee('LAPSED'))).toBe(
      'Your day ran out. They are still waiting on answers.',
    );
    // A re-seated court asking its newcomer: the one who left reads what they did (ADR-0162).
    expect(standingLine(invitee('LEFT'))).toBe('You left. They are still waiting on answers.');
  });

  /**
   * §13.1's rule, transferred: *they have left, so who is on that court is no longer theirs to
   * be told.* A count of outstanding answers is not a count of who is in, and it still leaks
   * the court's shape to somebody off it.
   */
  it('tells neither of them how many answers are outstanding', () => {
    for (const answer of ['DECLINED', 'LAPSED'] as const) {
      expect(standingLine(invitee(answer))).not.toMatch(/\d/);
    }
  });

  /** The organiser's seat is accepted from birth, so there is no split to make on their side. */
  it('says one thing to the organiser however the reader’s seat reads', () => {
    for (const answer of [undefined, 'ACCEPTED', 'DECLINED', 'LAPSED'] as const) {
      const facts: StandingFacts = {
        side: 'organiser',
        standing: 'AWAITING_ANSWERS',
        awaiting: 2,
        ...(answer === undefined ? {} : { ownAnswer: answer }),
      };

      expect(standingLine(facts)).toBe('Waiting on 2 answers');
    }
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
      player: { kind: 'player', name: 'niepokonanywojownik42' },
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

describe('an invitee who has left a challenge that has not', () => {
  // §13.1. A padel four where one declines and two accept is `LINE_UP_INCOMPLETE` for the
  // player who declined too, and the sentence keyed on `(standing, side)` alone is false in
  // both of its clauses for them.
  it('tells them what they did, and that the court is still being filled', () => {
    expect(
      standingLine({
        side: 'invitee',
        standing: 'LINE_UP_INCOMPLETE',
        accepted: 2,
        open: 2,
        ownAnswer: 'DECLINED',
      }),
    ).toBe('You said no. They are still filling the court.');

    expect(
      standingLine({
        side: 'invitee',
        standing: 'LINE_UP_INCOMPLETE',
        accepted: 2,
        open: 2,
        ownAnswer: 'LAPSED',
      }),
    ).toBe('Your day ran out. They are still filling the court.');

    // The third way out (ADR-0162): they left the game the court had become, and the court is
    // half built again. The same second clause, because it is the same news.
    expect(
      standingLine({
        side: 'invitee',
        standing: 'LINE_UP_INCOMPLETE',
        accepted: 2,
        open: 2,
        ownAnswer: 'LEFT',
      }),
    ).toBe('You left. They are still filling the court.');
  });

  it('never tells them how many are in, because that court is no longer theirs to be told', () => {
    for (const ownAnswer of ['DECLINED', 'LAPSED', 'LEFT'] as const) {
      const line = standingLine({
        side: 'invitee',
        standing: 'LINE_UP_INCOMPLETE',
        accepted: 2,
        open: 2,
        ownAnswer,
      });

      expect(line).not.toMatch(/\d/);
      expect(line).not.toMatch(/you're in/i);
    }
  });

  it('still says *You’re in* to the invitee who is', () => {
    expect(
      standingLine({
        side: 'invitee',
        standing: 'LINE_UP_INCOMPLETE',
        accepted: 2,
        open: 1,
        ownAnswer: 'ACCEPTED',
      }),
    ).toBe("You're in. 1 seat open, and the chat is already open");
  });
});

describe('a withdrawal is neither a decline nor a lapse', () => {
  it('names the act with the record’s own word, and says what it closed', () => {
    expect(standingLine({ side: 'organiser', standing: 'WITHDRAWN', player: SOMEBODY })).toBe(
      'You withdrew this',
    );
    expect(standingLine({ side: 'invitee', standing: 'WITHDRAWN', player: SOMEBODY })).toBe(
      'niepokonany withdrew this — that court is closed',
    );
  });

  it('borrows neither the plan’s word nor the platform’s', () => {
    for (const side of ['organiser', 'invitee'] as const) {
      const line = standingLine({ side, standing: 'WITHDRAWN', player: SOMEBODY });
      expect(line).not.toMatch(/cancel|called? off|stood down|stand down/i);
    }
  });

  it('tells an invitee who never answered the same as one who accepted', () => {
    // Separating them would say who else was on the court.
    expect(standingLine({ side: 'invitee', standing: 'WITHDRAWN', player: SOMEBODY })).toBe(
      standingLine({ side: 'invitee', standing: 'WITHDRAWN', player: SOMEBODY }),
    );
  });
});

describe('your own seat, on your own row', () => {
  // §14's fourth sentence. `{name} · {duration} left` is the organiser's, listing each seat and
  // its own clock; naming yourself on your own row would be the app telling you who you are.
  it('states the time left and names nobody', () => {
    expect(yourAnswerWindowLine('21 hours')).toBe('21 hours left to answer');
  });

  it('is not the sentence that names a seat', () => {
    expect(yourAnswerWindowLine('21 hours')).not.toBe(
      answerWindowLine({ player: SOMEBODY, duration: '21 hours' }),
    );
    expect(yourAnswerWindowLine('21 hours')).not.toMatch(/·/);
  });
});

/**
 * The lines this feature names a surface with, held to the test every line in the app is.
 *
 * `shellCopy.test.ts` makes the same two refusals of the tab's own sentences; these are here
 * because the vocabulary is the challenge's rather than the tab's, and a line that escaped both
 * files would be the one place *coming soon* could land.
 */
describe('what this feature refuses to say', () => {
  const LINES = [CHALLENGES_HEADING, CHALLENGE_SCREEN_TITLE];

  it('never says nothing is happening', () => {
    for (const line of LINES) {
      expect(line).not.toMatch(/nothing/i);
      expect(line).not.toMatch(/empty/i);
    }
  });

  it('never promises a date, and never apologises', () => {
    for (const line of LINES) {
      expect(line).not.toMatch(/coming soon|soon|sorry|under construction/i);
    }
  });
});
