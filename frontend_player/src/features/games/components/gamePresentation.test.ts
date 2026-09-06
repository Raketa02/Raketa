/**
 * The copy deck, and the four sentences the ticket says carry unusual weight.
 *
 * What is asserted is **not the wording** — that is what makes a copy deck a copy deck — but the
 * rules the wording has to keep: silence is named before it happens, an unscored game is never
 * an error, a correction is never called a proposal, and nothing anywhere blames anybody.
 */

import type { NamedPlayer } from '@/shared/formatting/playerName';

import type { ResultConversation } from '../domain/conversation';
import type { Game } from '../domain/game';

import {
  COUNTER_IS_THEIR_SCORE,
  COUNTER_LABEL,
  CORRECT_LABEL,
  UNSCORED_FACTS,
  clockLine,
  courtLine,
  gameEyebrow,
  outcomeLine,
  resultBody,
  scoreProblemLine,
  setLabel,
  sideLabels,
  spokenScore,
  standingLine,
  worthLine,
} from './gamePresentation';

const READ_AT = '2026-09-05T09:00:00Z';

const GAME: Game = {
  gameId: 'g1',
  challengeId: 'c1',
  sport: 'padel',
  kind: 'COUNTED',
  standing: 'AWAITING_ANSWER',
  seats: [
    { side: 'A', playerId: 'me', nickname: 'me_' },
    { side: 'B', playerId: 'them', nickname: 'tomek.p' },
  ],
  plannedAt: '2026-09-01T09:00:00Z',
  proposals: [],
  readAt: READ_AT,
};

/** The two people any of these sentences can name: you, and the player across the net. */
const YOU: NamedPlayer = { kind: 'you' };
const THEM: NamedPlayer = { kind: 'player', nickname: 'tomek.p' };

const PROPOSAL = {
  side: 'A',
  proposedBy: 'me',
  score: {
    sets: [
      { a: 6, b: 4 },
      { a: 6, b: 2 },
    ],
  },
  answerBy: '2026-09-06T08:00:00Z',
  settlesAt: '2026-09-05T15:00:00Z',
} as const;

/** The other side's answer to it, which is what makes the argument two scores rather than one. */
const COUNTER = {
  side: 'B',
  proposedBy: 'them',
  score: {
    sets: [
      { a: 6, b: 4 },
      { a: 4, b: 6 },
    ],
  },
  answerBy: '2026-09-06T10:00:00Z',
  settlesAt: '2026-09-05T17:00:00Z',
} as const;

/** The disagreement, read from the side that put `PROPOSAL` up. */
const ARGUING: ResultConversation = { kind: 'both-stand', ours: PROPOSAL, theirs: COUNTER };

/** One agreement, as the two sides read it — six hours from `READ_AT`, measured from the score. */
const AGREED_WITH_OURS: ResultConversation = {
  kind: 'agreed',
  agreement: { with: 'ours', by: THEM, settlesAt: '2026-09-05T15:00:00Z' },
  ours: PROPOSAL,
};

const AGREED_WITH_THEIRS: ResultConversation = {
  kind: 'agreed',
  agreement: { with: 'theirs', by: YOU, settlesAt: '2026-09-05T15:00:00Z' },
  theirs: COUNTER,
};

/** The same agreement over a disagreement, where each side has already used its one turn. */
const AGREED_OVER_BOTH: ResultConversation = { ...AGREED_WITH_OURS, theirs: COUNTER };

describe('silence confirming, which has to be visible before it happens', () => {
  /**
   * The ticket's own words: *"the screen has to say so **before** the clock runs, or silence
   * becomes a trap rather than a default."* It is in the **standing line**, which is the row's
   * sentence as well as the screen's, so it cannot be a footnote somebody reaches by tapping.
   */
  it('names the hour and what happens at the end of it, on the side that put the score up', () => {
    const line = standingLine({ kind: 'ours-stands', proposal: PROPOSAL }, READ_AT);

    expect(line).toContain('23 hours');
    expect(line).toContain('stands');
  });

  it('says it to the side that has not answered, which is the side it costs', () => {
    const line = standingLine({ kind: 'theirs-stands', proposal: PROPOSAL, by: THEM }, READ_AT);

    expect(line).toContain('23 hours');
    expect(line).toContain('stands');
  });

  it('names the entry window too, so a game does not quietly become a ghost', () => {
    const line = standingLine(
      { kind: 'awaiting-entry', entryClosesAt: '2026-09-08T09:00:00Z' },
      READ_AT,
    );

    expect(line).toContain('3 days');
  });

  it('drops the clause rather than inventing a deadline when the wire sent none', () => {
    expect(standingLine({ kind: 'awaiting-entry' }, READ_AT)).toBe(
      'Nobody has said this one happened yet.',
    );
  });
});

describe('an unscored game reads as an evening, not as an error', () => {
  const unscored: ResultConversation = { kind: 'unscored' };

  it('says what it still is, and that nobody is marked for it', () => {
    const body = resultBody(unscored);

    expect(body).toContain('evening');
    expect(body).toContain('Nobody is marked');
  });

  it('lists what it still is, and leaves the naming to the eyebrow above it', () => {
    expect(UNSCORED_FACTS).toHaveLength(3);
    expect(UNSCORED_FACTS.join(' ')).toContain('in how much you have played');
    expect(UNSCORED_FACTS.join(' ')).toContain('nobody lost anything');
  });

  it('never reads as a failure', () => {
    const said = `${standingLine(unscored, READ_AT)} ${resultBody(unscored) ?? ''}`;

    expect(said).not.toMatch(/failed|error|sorry|unfortunately|could not|couldn’t/i);
  });
});

describe('nobody is penalised, which is a sentence and not an omission', () => {
  it('says so on the game that never happened', () => {
    expect(resultBody({ kind: 'never-played' })).toContain('Nobody is marked');
  });

  it('says so on the disagreement, on both sides of it', () => {
    expect(resultBody(ARGUING)).toContain('Nobody is marked');
  });

  it('says so where agreeing might otherwise look like the safe move', () => {
    expect(resultBody({ kind: 'theirs-stands', proposal: PROPOSAL, by: THEM })).toContain(
      'there is none',
    );
  });
});

describe('a correction is not a second proposal, and the words never call it one', () => {
  it('says it does not use the side’s one turn up', () => {
    const body = resultBody({ kind: 'ours-stands', proposal: PROPOSAL });

    expect(body).toContain('does not use your side’s one turn up');
  });

  /**
   * The control's own name is where this is actually answered — *change what I entered* cannot
   * be read as a second turn, where *propose* could. Both words are the prototype's, and the
   * spec delta this flow was written in is explicit that the product's word for a counter is
   * **propose a modification** and never *dispute*.
   */
  it('names the two acts as the product names them', () => {
    expect(CORRECT_LABEL).toBe('Change what I entered');
    expect(COUNTER_LABEL).toBe('Propose a modification');
    expect(COUNTER_LABEL).not.toMatch(/dispute|reject/i);
  });
});

describe('the clock, which is how silence is made visible', () => {
  /**
   * The same fact read from the two sides, which is what the prototype recorded as the main
   * thing to react to: *this stands unless you act* to one of them, *this stands unless they
   * act* to the other.
   */
  it('tells the waiting side they are waiting, and the asked side that silence confirms', () => {
    expect(clockLine({ kind: 'ours-stands', proposal: PROPOSAL }, READ_AT)).toEqual({
      figure: '23 hours',
      line: 'left for the other side to answer. If they say nothing, this becomes the result.',
    });
    expect(
      clockLine({ kind: 'theirs-stands', proposal: PROPOSAL, by: THEM }, READ_AT)?.line,
    ).toContain('silence confirms it');
  });

  it('runs on the entry window too, so a game does not quietly become a ghost', () => {
    expect(
      clockLine({ kind: 'awaiting-entry', entryClosesAt: '2026-09-08T09:00:00Z' }, READ_AT)?.figure,
    ).toBe('3 days');
  });

  /**
   * The prototype quoted an absolute time beside the duration — *"a countdown alone never says
   * WHEN"*. It is deleted rather than translated: this platform has no calendar, and an absolute
   * time here would be the first one in the app.
   */
  it('quotes no clock time and no date, because there is no calendar to print one against', () => {
    const clock = clockLine({ kind: 'theirs-stands', proposal: PROPOSAL, by: THEM }, READ_AT);

    expect(`${clock?.figure ?? ''} ${clock?.line ?? ''}`).not.toMatch(/\d{1,2}:\d{2}|Sunday/);
  });

  it('has nothing to say about a game that has ended', () => {
    expect(clockLine({ kind: 'unscored' }, READ_AT)).toBeUndefined();
    expect(clockLine({ kind: 'confirmed' }, READ_AT)).toBeUndefined();
  });
});

describe('what an evening is worth is stamped, never derived', () => {
  it('says a counted game moves Levels and a friendly does not', () => {
    expect(worthLine('COUNTED')).toContain('part of your record');
    // The claim this sentence must NOT make: nothing reads a confirmed result forward yet.
    expect(worthLine('COUNTED')).not.toMatch(/Level/);
    expect(worthLine('FRIENDLY')).toContain('not evidence');
  });

  it('drops the clause for a kind this build cannot read, and says nothing false', () => {
    expect(worthLine(undefined)).toBeUndefined();
  });
});

describe('the score, in words', () => {
  it('names both sides in every set, because a listener has no column heads', () => {
    const sides = sideLabels(1);

    expect(spokenScore({ score: PROPOSAL.score, sport: 'padel', mine: 'A', sides })).toBe(
      'Set 1, You 6, Them 4. Set 2, You 6, Them 2',
    );
  });

  it('reads it from the other side of the net without flipping anything twice', () => {
    expect(
      spokenScore({ score: PROPOSAL.score, sport: 'padel', mine: 'B', sides: sideLabels(2) }),
    ).toBe('Set 1, Your side 4, Their side 6. Set 2, Your side 2, Their side 6');
  });

  it('calls a row what the sport calls it', () => {
    expect(setLabel('padel', 2)).toBe('Set 2');
    expect(setLabel('squash', 2)).toBe('Game 2');
  });
});

describe('what the grid declines, said to a player', () => {
  it('names the row and the sport’s own word for it', () => {
    expect(scoreProblemLine({ code: 'level-set', set: 2 }, 'badminton')).toContain('Game 2');
    expect(scoreProblemLine({ code: 'half-a-set', set: 1 }, 'tennis')).toContain('Set 1');
  });

  it('tells somebody to agree rather than to send the same score back', () => {
    expect(COUNTER_IS_THEIR_SCORE).toContain('Agree with it');
    expect(COUNTER_IS_THEIR_SCORE).toContain('unscored');
  });
});

describe('the court, with nobody on it', () => {
  it('states the shape of the court and not who was on it — the eyebrow does that', () => {
    expect(courtLine(2, 2)).toContain('Doubles');
    expect(courtLine(1, 1)).toContain('Singles');
  });

  it('labels the columns for the shape the reader is in', () => {
    expect(sideLabels(1)).toEqual({ ours: 'You', theirs: 'Them' });
    expect(sideLabels(2)).toEqual({ ours: 'Your side', theirs: 'Their side' });
  });
});

describe('a disagreement names its way out, and never only its ending', () => {
  /**
   * The paragraph used to state the ending and promise no control, because the wire returned
   * neither score and *"the client could offer the act only by asking somebody to agree with a
   * score it cannot show them"* ([#317](https://github.com/Raketa02/Raketa/issues/317)). Both
   * scores travel now, so it names the exit — and goes on saying the other ending is free.
   */
  it('names the agreement that ends it, and keeps going unscored costless', () => {
    const body = resultBody(ARGUING);

    expect(body).toContain('agreeing with the other’s score');
    expect(body).toContain('unscored');
    expect(body).toContain('Nobody is marked');
  });

  it('still refuses to pick between them, which is the thing the platform does not do', () => {
    expect(resultBody(ARGUING)).toContain('doesn’t decide between them');
  });
});

describe('an agreement, which the proposing side could not see at all', () => {
  /**
   * The side that put the score up was being told *if nobody answers within N, this stands*
   * for the whole grace after somebody already had. It is the standing line rather than a note
   * because the standing line is **the row's sentence too**, so the news reaches Now.
   */
  it('tells the proposing side their score was agreed, instead of waiting on silence', () => {
    const line = standingLine(AGREED_WITH_OURS, READ_AT);

    expect(line).toContain('agreed with your score');
    expect(line).toContain('6 hours');
    expect(line).not.toContain('nobody answers');
  });

  it('tells the side that agreed the same fact from their end', () => {
    const line = standingLine(AGREED_WITH_THEIRS, READ_AT);

    expect(line).toContain('You agreed with their score');
    expect(line).toContain('6 hours');
  });

  /**
   * The grace runs from the **score** and the answer window from the same moment, so the two
   * are different spans: a clock still counting the answer window would be counting a question
   * nobody is being asked any more.
   */
  it('moves the clock off the answer window and onto the grace', () => {
    const clock = clockLine(AGREED_WITH_OURS, READ_AT);

    expect(clock?.figure).toBe('6 hours');
    expect(clock?.line).not.toContain('silence');
  });

  /** Inside the grace nothing has settled, and the body is that rule rather than a repetition. */
  it('says a different score can still go up, which is what the wait is for', () => {
    expect(resultBody(AGREED_WITH_OURS)).toContain('can still put a different score up');
    expect(resultBody(AGREED_WITH_THEIRS)).toContain('can still put a different score up');
  });

  /**
   * **The one sentence that has to count the scores.** Over a disagreement each side has already
   * used its one turn, so promising a different score could still go up would promise an act
   * `state_result` refuses with `your_side_has_already_answered` — the same failure the old
   * `both-stand` copy was written to avoid, one state along.
   */
  it('never promises a score nobody may send, over an argument already down to one exit', () => {
    const body = resultBody(AGREED_OVER_BOTH);

    expect(body).not.toContain('can still put a different score up');
    expect(body).toContain('each side gets one');
    expect(body).toContain('Nobody is marked');
  });
});

describe('the rest', () => {
  it('says what a confirmed result said about you, and nothing when it said nothing', () => {
    expect(outcomeLine('WIN')).toBe('You won.');
    expect(outcomeLine(undefined)).toBeUndefined();
  });

  it('tells two games apart by who was on the court, and by a duration after that', () => {
    // The duration was the **only** distinguishing fact until a seat carried a handle, which
    // made three padel games in a week three near-identical rows (#319). It is still here,
    // because there is no calendar to print a date against.
    expect(gameEyebrow('Padel', GAME, 'me')).toBe('Padel · with tomek.p · arranged 4 days ago');
  });

  it('names the whole court in the order it was handed over, and never you', () => {
    const doubles: Game = {
      ...GAME,
      seats: [
        { side: 'A', playerId: 'me', nickname: 'me_' },
        { side: 'A', playerId: 'partner', nickname: 'kasia_w' },
        { side: 'B', playerId: 'them', nickname: 'tomek.p' },
        { side: 'B', playerId: 'other', nickname: 'marekb' },
      ],
    };

    expect(gameEyebrow('Padel', doubles, 'me')).toContain('with kasia_w, tomek.p and marekb');
  });

  it('draws the unknown player for a seat users can no longer answer for', () => {
    // A missing handle is never a missing seat: dropping it would draw a three-person doubles
    // game, so the court keeps its shape and loses a word.
    const erased: Game = {
      ...GAME,
      seats: [
        { side: 'A', playerId: 'me', nickname: 'me_' },
        { side: 'B', playerId: 'them' },
      ],
    };

    expect(gameEyebrow('Padel', erased, 'me')).toBe('Padel · with ? · arranged 4 days ago');
  });
});

describe('who a sentence names, and who it deliberately does not', () => {
  /**
   * *That's right* settles a score against a person, and until a seat carried a handle the
   * screen could not say which — the second of #319's two costs.
   */
  it('names whoever on the other side put the score up', () => {
    const line = standingLine({ kind: 'theirs-stands', proposal: PROPOSAL, by: THEM }, READ_AT);

    expect(line).toContain('tomek.p put a score up');
  });

  it('names the person who agreed, and says You where that person is the reader', () => {
    expect(standingLine(AGREED_WITH_OURS, READ_AT)).toContain('tomek.p agreed with your score');
    expect(standingLine(AGREED_WITH_THEIRS, READ_AT)).toContain('You agreed with their score');
  });

  /**
   * **A score is a side's claim**, capped one per side and answerable by either of the two who
   * played it — so a column headed with a handle would charge a doubles score to one of them.
   */
  it('still calls the two columns of a score sides, never people', () => {
    expect(sideLabels(2)).toEqual({ ours: 'Your side', theirs: 'Their side' });
    expect(sideLabels(1)).toEqual({ ours: 'You', theirs: 'Them' });
  });
});
