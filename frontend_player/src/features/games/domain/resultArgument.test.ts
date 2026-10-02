/**
 * **The one rule that says what a player may do about a result**, and it is derived from the
 * record rather than asked for.
 *
 * The wire has one route for three acts on purpose — *"a client that named which would be a
 * client that could name it wrongly, and a mislabelled correction is a proposal nobody may
 * make"* — so what this decides is not *which act to send* but **what to draw**: a correction
 * and a counter are the same request and a completely different screen, and a player who spent
 * their side's one turn fixing a typo is the failure the ticket names first.
 *
 * Two of these describe acts the **aggregate refuses**, and they are here rather than left to a
 * red note after the tap: a correction once the other side has answered, and a second agreement
 * from a side that has already made one.
 */

import type { Acceptance, Game, NoShowReport, StandingProposal } from './game';
import { actsOffered, awaitsYourAgreement, editingAct, resultArgument } from './resultArgument';

const ME = 'me-1111-4444-8888-000000000001';
const PARTNER = 'partner-11-4444-8888-000000002';
const OPPONENT = 'opp-111111-4444-8888-00000003';

const PROPOSAL: StandingProposal = {
  side: 'A',
  proposedBy: ME,
  score: {
    sets: [
      { a: 6, b: 4 },
      { a: 6, b: 2 },
    ],
  },
  answerBy: '2026-09-06T20:12:00Z',
  settlesAt: '2026-09-06T02:12:00Z',
};

/** The other side's answer to it — one digit apart, which is what a real disagreement is. */
const COUNTER: StandingProposal = {
  side: 'B',
  proposedBy: OPPONENT,
  score: {
    sets: [
      { a: 6, b: 4 },
      { a: 4, b: 6 },
    ],
  },
  answerBy: '2026-09-06T22:00:00Z',
  settlesAt: '2026-09-06T04:00:00Z',
};

/** An agreement with one side's score. The accepter is always the other side. */
function agreed(withSide: 'A' | 'B', by: string = OPPONENT): Acceptance {
  return { agreedBy: by, ofSide: withSide, settlesAt: '2026-09-06T02:12:00Z' };
}

function game(over: Partial<Game> = {}): Game {
  return {
    gameId: 'game-1111-4444-8888-00000000001',
    challengeId: 'ask-11111-4444-8888-000000001',
    sport: 'padel',
    kind: 'COUNTED',
    standing: 'AWAITING_ENTRY',
    seats: [
      { side: 'A', playerId: ME, name: 'me_' },
      { side: 'A', playerId: PARTNER, name: 'kasia_w' },
      { side: 'B', playerId: OPPONENT, name: 'tomek.p' },
      { side: 'B', playerId: 'opp2-1111-4444-8888-00000004', name: 'marekb' },
    ],
    plannedAt: '2026-09-01T18:00:00Z',
    entryClosesAt: '2026-09-09T18:00:00Z',
    proposals: [],
    noShows: [],
    readAt: '2026-09-05T09:00:00Z',
    ...over,
  };
}

describe('before anybody has said it happened', () => {
  it('offers the entry, and says when saying so stops being possible', () => {
    const argument = resultArgument(game(), ME);

    expect(argument).toEqual({
      kind: 'awaiting-entry',
      entryClosesAt: '2026-09-09T18:00:00Z',
      seatOpen: false,
    });
    expect(actsOffered(argument)).toEqual(['enter']);
  });

  /**
   * **We played is withheld while a seat is open** (#411 rule 5): the server refuses a result on
   * a short court, and a game with a gap in it is not one anybody could have played.
   */
  it('offers no entry while a seat somebody left is still open', () => {
    const short = game({
      seats: [
        { side: 'A', playerId: ME, name: 'me_' },
        { side: 'A', playerId: PARTNER, name: 'kasia_w' },
        { side: 'B', playerId: OPPONENT, name: 'tomek.p' },
        { side: 'B' },
      ],
    });
    const argument = resultArgument(short, ME);

    expect(argument).toEqual({
      kind: 'awaiting-entry',
      entryClosesAt: '2026-09-09T18:00:00Z',
      seatOpen: true,
    });
    expect(actsOffered(argument)).toEqual([]);
  });

  it('offers it to anybody who held a seat, which is all four of them', () => {
    expect(actsOffered(resultArgument(game(), OPPONENT))).toEqual(['enter']);
  });

  it('offers nothing once the window has closed — the game is a ghost and stays one', () => {
    const argument = resultArgument(game({ standing: 'NEVER_PLAYED' }), ME);

    expect(argument).toEqual({ kind: 'never-played' });
    expect(actsOffered(argument)).toEqual([]);
  });

  /** The fourth end (ADR-0163): somebody ended it, and nothing anybody is measured on moves. */
  /**
   * **The hour's call-off names nobody by design** ([ADR-0175](../../../../../docs/adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md)
   * §3): `called_off_by` null is the platform's act, and the court's shape still travels.
   */
  it('offers nothing once the game has been called off, and reads a nameless one as the hour’s', () => {
    const argument = resultArgument(game({ standing: 'CALLED_OFF' }), ME);

    expect(argument).toEqual({
      kind: 'called-off',
      ending: { how: 'the-hour', format: 'doubles' },
    });
    expect(actsOffered(argument)).toEqual([]);
  });

  /**
   * **A named call-off is a departure** (ADR-0172 §4, ADR-0175 §1): nobody presses one any more,
   * so whoever `called_off_by` names left — the record written while somebody could press
   * folds the same way, by the person it names, *you* for the reader's own.
   */
  it('says who left, singles or doubles, and You for the reader’s own', () => {
    const leaverGone = game({
      standing: 'CALLED_OFF',
      seats: [{ side: 'A', playerId: ME, name: 'me_' }, { side: 'B' }],
      calledOffBy: { playerId: OPPONENT, name: 'tomek.p' },
    });
    const doubles = game({
      standing: 'CALLED_OFF',
      seats: [
        { side: 'A', playerId: ME, name: 'me_' },
        { side: 'A', playerId: PARTNER, name: 'kasia_w' },
        { side: 'B', playerId: OPPONENT, name: 'tomek.p' },
        { side: 'B' },
      ],
      calledOffBy: { playerId: OPPONENT, name: 'tomek.p' },
    });

    expect(resultArgument(leaverGone, ME)).toEqual({
      kind: 'called-off',
      ending: { by: { kind: 'player', name: 'tomek.p' }, how: 'departure', format: 'singles' },
    });
    expect(resultArgument(doubles, ME)).toEqual({
      kind: 'called-off',
      ending: { by: { kind: 'player', name: 'tomek.p' }, how: 'departure', format: 'doubles' },
    });
    expect(resultArgument({ ...doubles, calledOffBy: { playerId: ME, name: 'me_' } }, ME)).toEqual({
      kind: 'called-off',
      ending: { by: { kind: 'you' }, how: 'departure', format: 'doubles' },
    });
  });

  it('names nobody by name where users has lost the account', () => {
    const nameless = game({
      standing: 'CALLED_OFF',
      seats: [{ side: 'A', playerId: ME, name: 'me_' }, { side: 'B' }],
      calledOffBy: { playerId: OPPONENT },
    });

    expect(resultArgument(nameless, ME)).toMatchObject({
      ending: { by: { kind: 'unknown' }, how: 'departure' },
    });
  });
});

describe('one score on the table', () => {
  const played = {
    standing: 'AWAITING_ANSWER',
    playedAt: '2026-09-04T20:12:00Z',
    entryClosesAt: undefined,
    proposals: [PROPOSAL],
  } as const;

  it('is a correction to the side that put it there, and never a second turn', () => {
    const argument = resultArgument(game(played), ME);

    expect(argument).toEqual({ kind: 'ours-stands', proposal: PROPOSAL });
    expect(actsOffered(argument)).toEqual(['correct']);
  });

  /**
   * ADR-0137 §4's one narrowing, read from the client: *"the correction is the side's and not
   * its author's"*, so a player who disagrees with their own partner has a way to say so and
   * neither side gets two turns.
   */
  it('is a correction to the partner too, because the score is the side’s', () => {
    expect(actsOffered(resultArgument(game(played), PARTNER))).toEqual(['correct']);
  });

  it('is an agreement or a disagreement across the net, and the agreement leads', () => {
    const argument = resultArgument(game(played), OPPONENT);

    expect(argument).toEqual({
      kind: 'theirs-stands',
      proposal: PROPOSAL,
      // Whoever put it up, in the reader's own terms — the person *That's right* settles a
      // score against, which this screen could not name until a seat carried a handle (#319).
      by: { kind: 'player', name: 'me_' },
    });
    expect(actsOffered(argument)).toEqual(['accept', 'counter']);
  });
});

describe('two scores on the table', () => {
  const arguing = {
    standing: 'AWAITING_ANSWER',
    playedAt: '2026-09-04T20:12:00Z',
    entryClosesAt: undefined,
    proposals: [PROPOSAL, COUNTER],
  } as const;

  /**
   * The count *is* the state. It used to be read off the standing, because the field it
   * replaced was absent for *nothing entered* and for *both sides have spoken* alike
   * ([#317](https://github.com/Raketa02/Raketa/issues/317)).
   */
  it('hands both scores over, the reader’s own named as theirs', () => {
    expect(resultArgument(game(arguing), ME)).toEqual({
      kind: 'both-stand',
      ours: PROPOSAL,
      theirs: COUNTER,
    });
    expect(resultArgument(game(arguing), OPPONENT)).toEqual({
      kind: 'both-stand',
      ours: COUNTER,
      theirs: PROPOSAL,
    });
  });

  /**
   * **The only exit that is not the game going unscored** — ADR-0137 §4, and the act the
   * aggregate has allowed here all along. There is no counter: this side has had its turn, and
   * the cap of one score per side is what bounds the argument to two rounds.
   */
  it('offers an agreement with the other side’s score, and never a second one of our own', () => {
    expect(actsOffered(resultArgument(game(arguing), ME))).toEqual(['accept']);
  });

  /**
   * **Neither side may counter here, and that is the aggregate's cap rather than a rule about
   * agreements**: each side gets one score and both have used theirs, so `state_result` refuses
   * with `your_side_has_already_answered`. It is the one thing the `agreed` state has to know
   * how many scores are up to say correctly.
   */
  it('offers nothing once somebody has agreed, whichever score they agreed with', () => {
    for (const side of ['A', 'B'] as const) {
      const argument = resultArgument(game({ ...arguing, acceptance: agreed(side) }), ME);

      expect(argument).toMatchObject({ kind: 'agreed', ours: PROPOSAL, theirs: COUNTER });
      expect(actsOffered(argument)).toEqual([]);
    }
  });
});

describe('an agreement waiting out its grace', () => {
  const played = {
    standing: 'AWAITING_ANSWER',
    playedAt: '2026-09-04T20:12:00Z',
    entryClosesAt: undefined,
  } as const;

  /**
   * `state_result` refuses this with `the_other_side_has_answered`, so the control was a
   * promise the server breaks — and the screen kept offering it because nothing on the response
   * said an answer had arrived.
   */
  it('takes the correction away from the side whose score was agreed with', () => {
    const argument = resultArgument(
      game({ ...played, proposals: [PROPOSAL], acceptance: agreed('A') }),
      ME,
    );

    expect(argument).toEqual({
      kind: 'agreed',
      agreement: {
        with: 'ours',
        by: { kind: 'player', name: 'tomek.p' },
        settlesAt: '2026-09-06T02:12:00Z',
      },
      ours: PROPOSAL,
    });
    expect(actsOffered(argument)).toEqual([]);
    expect(editingAct(argument)).toBeUndefined();
  });

  /**
   * Inside the grace a disagreement still wins — that is the rule the grace exists for — so the
   * one control that survives an agreement is the one that beats it.
   */
  it('leaves the disagreement standing on the side that agreed, and takes the agreement away', () => {
    const argument = resultArgument(
      game({ ...played, proposals: [PROPOSAL], acceptance: agreed('A') }),
      OPPONENT,
    );

    expect(argument).toEqual({
      kind: 'agreed',
      // Read by the opponent, who is the one who agreed: *You agreed with their score*, which
      // is the same fact from the other end and a different sentence.
      agreement: { with: 'theirs', by: { kind: 'you' }, settlesAt: '2026-09-06T02:12:00Z' },
      theirs: PROPOSAL,
    });
    expect(actsOffered(argument)).toEqual(['counter']);
    expect(editingAct(argument)).toBe('counter');
  });
});

describe('the ends', () => {
  it('confirms with the agreed score and what it says about you', () => {
    const argument = resultArgument(
      game({
        standing: 'CONFIRMED',
        playedAt: '2026-09-04T20:12:00Z',
        score: PROPOSAL.score,
        outcome: 'WIN',
      }),
      ME,
    );

    expect(argument).toEqual({ kind: 'confirmed', score: PROPOSAL.score, outcome: 'WIN' });
    expect(actsOffered(argument)).toEqual([]);
  });

  it('leaves an unscored game alone — a settled result is final, and so is no result', () => {
    const argument = resultArgument(
      game({ standing: 'UNSCORED', playedAt: '2026-09-04T20:12:00Z' }),
      ME,
    );

    expect(argument).toEqual({ kind: 'unscored' });
    expect(actsOffered(argument)).toEqual([]);
  });
});

describe('somebody who was not on this court', () => {
  /**
   * Unreachable through the list, which serves your games and nobody else's — and a state the
   * screen has to hold anyway, because a link is not a list. It is the client half of
   * `you_were_not_on_this_court`, and it names the same two cases the server refuses to tell
   * apart.
   */
  it('has no side, so there is no argument and nothing to offer', () => {
    const argument = resultArgument(game(), 'stranger-1-4444-8888-00000005');

    expect(argument).toEqual({ kind: 'not-yours' });
    expect(actsOffered(argument)).toEqual([]);
  });
});

describe('a state this build cannot name', () => {
  /**
   * A standing *is* the whole line, so it draws the out-of-date sentence rather than being
   * dropped — `the-words.md` §3's named gap, exactly as a challenge's standing does. What it
   * must never do is offer an act: acting on a game whose state we cannot name is how a
   * correction becomes a second proposal.
   */
  it('has an argument with no acts in it', () => {
    const argument = resultArgument(game({ standing: undefined }), ME);

    expect(argument).toEqual({ kind: 'unreadable' });
    expect(actsOffered(argument)).toEqual([]);
  });

  /**
   * An answer awaited with nothing on the table, which the aggregate cannot produce and the
   * standing's own fold states rather than leaves to a `max()` over an empty sequence. Reading
   * it as a disagreement would offer an agreement with a score nobody put up.
   */
  it('says the same about an answer awaited with no score to answer', () => {
    const argument = resultArgument(
      game({ standing: 'AWAITING_ANSWER', playedAt: '2026-09-04T20:12:00Z' }),
      ME,
    );

    expect(argument).toEqual({ kind: 'unreadable' });
    expect(actsOffered(argument)).toEqual([]);
  });
});

/**
 * **A score waiting on your agreement** — the *result to confirm* Home's badge counts
 * ([#550](https://github.com/Raketa02/Raketa/issues/550),
 * [the mechanics §3](../../../../../docs/specs/games-and-fill-in/the-mechanics.md#3-where-everything-lives)).
 * It is a game where agreeing is yours to do: the other side's score is up and nobody has settled
 * it. Your own score waiting on them is not, and neither is an agreement already running out its
 * grace — the disagreement it leaves is a right, not a task.
 */
describe('whether a score is waiting on your agreement', () => {
  const played = {
    standing: 'AWAITING_ANSWER',
    playedAt: '2026-09-04T20:12:00Z',
    entryClosesAt: undefined,
  } as const;

  it('is, across the net from a score nobody has answered', () => {
    expect(awaitsYourAgreement(game({ ...played, proposals: [PROPOSAL] }), OPPONENT)).toBe(true);
  });

  it('is not on the side whose score it is — that one waits on the other side', () => {
    expect(awaitsYourAgreement(game({ ...played, proposals: [PROPOSAL] }), ME)).toBe(false);
    expect(awaitsYourAgreement(game({ ...played, proposals: [PROPOSAL] }), PARTNER)).toBe(false);
  });

  it('is, on both sides, while two scores stand and nobody has agreed', () => {
    const arguing = game({ ...played, proposals: [PROPOSAL, COUNTER] });

    expect(awaitsYourAgreement(arguing, ME)).toBe(true);
    expect(awaitsYourAgreement(arguing, OPPONENT)).toBe(true);
  });

  it('is not once somebody has agreed, on either side', () => {
    const settling = game({ ...played, proposals: [PROPOSAL], acceptance: agreed('A') });

    expect(awaitsYourAgreement(settling, ME)).toBe(false);
    expect(awaitsYourAgreement(settling, OPPONENT)).toBe(false);
  });

  it('is not before anybody has said the game happened, nor after it ended', () => {
    expect(awaitsYourAgreement(game(), ME)).toBe(false);
    expect(awaitsYourAgreement(game({ standing: 'CONFIRMED' }), ME)).toBe(false);
  });

  it('is not for somebody who was not on the court', () => {
    const stranger = 'stranger-1111-4444-8888-00000009';

    expect(awaitsYourAgreement(game({ ...played, proposals: [PROPOSAL] }), stranger)).toBe(false);
  });
});

/**
 * **Somebody didn't come** ([#560](https://github.com/Raketa02/Raketa/issues/560); the Games & Fill
 * in mechanics §15.3). A report has a day: while one runs the game waits, and the player it names
 * may say they came — the one act this arm offers, and only to them, only inside their own day,
 * measured against the instant the list was read. Once every report has had its day, the ones
 * nobody disputed are who did not come.
 */
describe('a no-show report', () => {
  /** A report made last night, whose day runs to tonight — named as the seat names them. */
  function report(playerId: string, over: Partial<NoShowReport> = {}): NoShowReport {
    const name = game().seats.find((seat) => seat.playerId === playerId)?.name;
    return {
      playerId,
      ...(name === undefined ? {} : { name }),
      reportedAt: '2026-09-04T20:00:00Z',
      disputeBy: '2026-09-05T20:00:00Z',
      ...over,
    };
  }

  const reported = (...noShows: NoShowReport[]) =>
    game({ standing: 'NO_SHOW_REPORTED', entryClosesAt: undefined, noShows });

  it('offers the dispute to the player it names, inside their day', () => {
    const argument = resultArgument(reported(report(ME)), ME);

    expect(argument).toEqual({
      kind: 'no-show-reported',
      yours: { who: { kind: 'you' }, disputeBy: '2026-09-05T20:00:00Z', state: 'open' },
      others: [],
    });
    expect(actsOffered(argument)).toEqual(['dispute']);
  });

  it('names who was reported to everybody else, and offers them nothing to answer', () => {
    const argument = resultArgument(reported(report(OPPONENT)), PARTNER);

    expect(argument).toEqual({
      kind: 'no-show-reported',
      others: [
        {
          who: { kind: 'player', name: 'tomek.p' },
          disputeBy: '2026-09-05T20:00:00Z',
          state: 'open',
        },
      ],
    });
    expect(actsOffered(argument)).toEqual([]);
  });

  it('offers no second dispute once the player has said they came', () => {
    const argument = resultArgument(
      reported(report(ME, { disputedAt: '2026-09-05T08:00:00Z' }), report(OPPONENT)),
      ME,
    );

    expect(argument).toMatchObject({
      kind: 'no-show-reported',
      yours: { who: { kind: 'you' }, state: 'disputed' },
      others: [{ who: { kind: 'player', name: 'tomek.p' }, state: 'open' }],
    });
    expect(actsOffered(argument)).toEqual([]);
  });

  /** Another report's day can keep the game waiting after the reader's own day has ended. */
  it('offers no dispute once the reader’s own day has passed, though another still runs', () => {
    const argument = resultArgument(
      reported(
        report(ME, { reportedAt: '2026-09-04T08:00:00Z', disputeBy: '2026-09-05T08:00:00Z' }),
        report(OPPONENT),
      ),
      ME,
    );

    expect(argument).toMatchObject({
      kind: 'no-show-reported',
      yours: { state: 'stood' },
      others: [{ state: 'open' }],
    });
    expect(actsOffered(argument)).toEqual([]);
  });

  it('ends naming who did not come — the reports nobody disputed — and offers nothing', () => {
    const argument = resultArgument(
      game({
        standing: 'NO_SHOW',
        entryClosesAt: undefined,
        noShows: [report(ME), report(OPPONENT, { disputedAt: '2026-09-05T08:00:00Z' })],
        readAt: '2026-09-06T09:00:00Z',
      }),
      PARTNER,
    );

    expect(argument).toEqual({ kind: 'no-show', didNotCome: [{ kind: 'player', name: 'me_' }] });
    expect(actsOffered(argument)).toEqual([]);
  });
});
