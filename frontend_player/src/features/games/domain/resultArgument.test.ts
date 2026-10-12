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
 * One of these describes an act the **aggregate refuses**, and it is here rather than left to a
 * red note after the tap: a second score from a side that has already put one up. **An agreement
 * is not a state any more** (#654): *That's right* settles the result at once, so the next read is
 * `CONFIRMED` and there is no grace in which anything is still offered.
 */

import type { Attendance, Game, StandingProposal } from './game';
import { actsOffered, editingAct, resultArgument } from './resultArgument';

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
};

function game(over: Partial<Game> = {}): Game {
  return {
    gameId: 'game-1111-4444-8888-00000000001',
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
    attendance: [],
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

  /**
   * **A full game nobody recorded was played** (#655; ADR-0195 §2): the window closing is an end,
   * not a ghost, and there is nothing left to do about it.
   */
  it('offers nothing once the window has closed — played, with no score', () => {
    const argument = resultArgument(game({ standing: 'PLAYED_NO_SCORE' }), ME);

    expect(argument).toEqual({ kind: 'played-no-score' });
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
      // Either of the two on this side may answer, so *if neither of you answers* is the sentence.
      withPartner: true,
    });
    expect(actsOffered(argument)).toEqual(['accept', 'counter']);
  });

  it('asks the reader alone across a singles net', () => {
    const singles = game({
      ...played,
      seats: [
        { side: 'A', playerId: ME, name: 'me_' },
        { side: 'B', playerId: OPPONENT, name: 'tomek.p' },
      ],
    });

    expect(resultArgument(singles, OPPONENT)).toMatchObject({
      kind: 'theirs-stands',
      withPartner: false,
    });
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
    expect(resultArgument(game(arguing), ME)).toMatchObject({
      kind: 'both-stand',
      ours: PROPOSAL,
      theirs: COUNTER,
    });
    expect(resultArgument(game(arguing), OPPONENT)).toMatchObject({
      kind: 'both-stand',
      ours: COUNTER,
      theirs: PROPOSAL,
    });
  });

  /**
   * **Two scores nobody agrees with settle when the later one's day is up** (#654): the closer
   * score where both name the same winner, disputed where they don't — the same instant to both
   * sides, whichever score is theirs.
   */
  it('settles when the later of the two scores’ days is up', () => {
    expect(resultArgument(game(arguing), ME)).toMatchObject({ settlesAt: COUNTER.answerBy });
    expect(resultArgument(game(arguing), OPPONENT)).toMatchObject({
      settlesAt: COUNTER.answerBy,
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
});

describe('the ends', () => {
  /**
   * **However it settled** — a *That's right*, silence, or the closer of two scores naming the same
   * winner (#654): the wire does not say which, so neither does the argument.
   */
  it('confirms with the score that stands and what it says about you', () => {
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

  /**
   * **Two scores naming different winners** (#654; ADR-0195 §5): no Level moves, nobody decides who
   * won, and there is nothing left to do — neither score travels any more.
   */
  it('ends disputed, with nothing to offer', () => {
    const argument = resultArgument(
      game({ standing: 'DISPUTED', playedAt: '2026-09-04T20:12:00Z' }),
      ME,
    );

    expect(argument).toEqual({ kind: 'disputed' });
    expect(actsOffered(argument)).toEqual([]);
  });
});

/**
 * **For fun asks nothing** (#654; the Games & Fill in mechanics §15.2): it reads *Played*, and a
 * score can be added that stands the moment it is put up — nobody answers it, so there is no
 * standing proposal and no waiting arm.
 */
describe('a For fun game', () => {
  const forFun = { kind: 'FRIENDLY' } as const;

  it('reads played with nothing on it, and still takes a score', () => {
    const argument = resultArgument(game(forFun), ME);

    expect(argument).toEqual({ kind: 'for-fun', seatOpen: false });
    expect(actsOffered(argument)).toEqual(['enter']);
    expect(editingAct(argument)).toBe('enter');
  });

  it('reads played with its score once one is up, and asks nothing more', () => {
    const argument = resultArgument(
      game({
        ...forFun,
        standing: 'CONFIRMED',
        playedAt: '2026-09-04T20:12:00Z',
        entryClosesAt: undefined,
        score: PROPOSAL.score,
        outcome: 'WIN',
      }),
      OPPONENT,
    );

    expect(argument).toEqual({
      kind: 'for-fun',
      score: PROPOSAL.score,
      outcome: 'WIN',
      seatOpen: false,
    });
    expect(actsOffered(argument)).toEqual([]);
  });

  it('takes no score while a seat somebody left is open', () => {
    const short = game({
      ...forFun,
      seats: [{ side: 'A', playerId: ME, name: 'me_' }, { side: 'B' }],
    });

    expect(actsOffered(resultArgument(short, ME))).toEqual([]);
  });

  it('ends as any full game nobody recorded does', () => {
    expect(resultArgument(game({ ...forFun, standing: 'PLAYED_NO_SCORE' }), ME)).toEqual({
      kind: 'played-no-score',
    });
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
 * **Who turned up, caught at the court** ([#658](https://github.com/Raketa02/Raketa/issues/658);
 * ADR-0195 §3). While somebody tapped *isn't here yet* is awaited no score is taken, and once the
 * half hour has run with them not arrived the game is one somebody Didn't come to. Neither arm
 * offers a result act: the taps are the attendance block's (`attendance.ts`).
 */
describe('attendance', () => {
  const OPPONENT_2 = 'opp2-1111-4444-8888-00000004';

  function row(playerId: string, over: Partial<Attendance> = {}): Attendance {
    const name = game().seats.find((seat) => seat.playerId === playerId)?.name;
    return {
      playerId,
      ...(name === undefined ? {} : { name }),
      state: 'WAITING',
      notedAt: '2026-09-04T18:05:00Z',
      arriveBy: '2026-09-04T18:30:00Z',
      claimBy: '2026-09-05T18:30:00Z',
      ...over,
    };
  }

  it('names who is awaited to everybody else, and who is waiting to the player awaited', () => {
    const awaited = game({ standing: 'NOT_HERE_YET', attendance: [row(OPPONENT)] });

    expect(resultArgument(awaited, PARTNER)).toEqual({
      kind: 'not-here-yet',
      awaited: [{ kind: 'player', name: 'tomek.p' }],
      here: [
        { kind: 'player', name: 'me_' },
        { kind: 'player', name: 'marekb' },
      ],
      yours: false,
      arriveBy: '2026-09-04T18:30:00Z',
    });
    expect(resultArgument(awaited, OPPONENT)).toMatchObject({
      kind: 'not-here-yet',
      awaited: [{ kind: 'you' }],
      here: [
        { kind: 'player', name: 'me_' },
        { kind: 'player', name: 'kasia_w' },
        { kind: 'player', name: 'marekb' },
      ],
      yours: true,
    });
    expect(actsOffered(resultArgument(awaited, OPPONENT))).toEqual([]);
  });

  it('leaves a second absentee out of who is waiting', () => {
    const two = game({
      standing: 'NOT_HERE_YET',
      attendance: [row(OPPONENT), row(OPPONENT_2)],
    });

    expect(resultArgument(two, ME)).toMatchObject({
      awaited: [
        { kind: 'player', name: 'tomek.p' },
        { kind: 'player', name: 'marekb' },
      ],
      here: [{ kind: 'player', name: 'kasia_w' }],
    });
  });

  it('names who didn’t come — a claim still waiting among them — and offers nothing', () => {
    const argument = resultArgument(
      game({
        standing: 'DIDNT_COME',
        entryClosesAt: undefined,
        readAt: '2026-09-05T08:00:00Z',
        attendance: [
          row(OPPONENT, { state: 'DIDNT_COME' }),
          row(OPPONENT_2, { state: 'CLAIMED', claimedAt: '2026-09-05T07:00:00Z' }),
        ],
      }),
      ME,
    );

    expect(argument).toEqual({
      kind: 'didnt-come',
      absent: [
        { kind: 'player', name: 'tomek.p' },
        { kind: 'player', name: 'marekb' },
      ],
    });
    expect(actsOffered(argument)).toEqual([]);
  });

  it('tells the player who didn’t come whether they may still say they were there', () => {
    const didntCome = (over: Partial<Attendance>, readAt = '2026-09-05T08:00:00Z') =>
      resultArgument(
        game({
          standing: 'DIDNT_COME',
          entryClosesAt: undefined,
          readAt,
          attendance: [row(ME, { state: 'DIDNT_COME', ...over })],
        }),
        ME,
      );

    expect(didntCome({})).toEqual({
      kind: 'didnt-come',
      absent: [{ kind: 'you' }],
      yours: { state: 'may-claim', claimBy: '2026-09-05T18:30:00Z' },
    });
    expect(didntCome({ state: 'CLAIMED', claimedAt: '2026-09-05T07:00:00Z' })).toMatchObject({
      yours: { state: 'claimed' },
    });
    expect(didntCome({}, '2026-09-05T18:30:00Z')).toMatchObject({ yours: { state: 'final' } });
  });

  it('takes a late arrival as an ordinary game — the standing says so, not the rows', () => {
    const late = game({
      attendance: [row(OPPONENT, { state: 'CAME_LATE', arrivedAt: '2026-09-04T18:20:00Z' })],
    });

    expect(resultArgument(late, ME)).toMatchObject({ kind: 'awaiting-entry' });
    expect(actsOffered(resultArgument(late, ME))).toEqual(['enter']);
  });
});
