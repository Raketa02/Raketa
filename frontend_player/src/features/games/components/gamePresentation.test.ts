/**
 * The copy deck, and the four sentences the ticket says carry unusual weight.
 *
 * What is asserted is **not the wording** — that is what makes a copy deck a copy deck — but the
 * rules the wording has to keep: silence is named before it happens, an unscored game is never
 * an error, a correction is never called a proposal, and nothing anywhere blames anybody.
 */

import type { ResultConversation } from '../domain/conversation';
import type { Game } from '../domain/game';

import {
  COUNTER_IS_THEIR_SCORE,
  COUNTER_LABEL,
  CORRECT_LABEL,
  UNSCORED_FACTS,
  acceptedLine,
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
    { side: 'A', playerId: 'me' },
    { side: 'B', playerId: 'them' },
  ],
  plannedAt: '2026-09-01T09:00:00Z',
  readAt: READ_AT,
};

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
    const line = standingLine({ kind: 'theirs-stands', proposal: PROPOSAL }, READ_AT);

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

  it('lists what it still is, and names nobody, because the contract carries no handle', () => {
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
    expect(resultBody({ kind: 'both-stand' })).toContain('Nobody is marked');
  });

  it('says so where agreeing might otherwise look like the safe move', () => {
    expect(resultBody({ kind: 'theirs-stands', proposal: PROPOSAL })).toContain('there is none');
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
    expect(clockLine({ kind: 'theirs-stands', proposal: PROPOSAL }, READ_AT)?.line).toContain(
      'silence confirms it',
    );
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
    const clock = clockLine({ kind: 'theirs-stands', proposal: PROPOSAL }, READ_AT);

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
  it('states the shape and names nobody, because the contract carries no handle', () => {
    expect(courtLine(2, 2)).toContain('Doubles');
    expect(courtLine(1, 1)).toContain('Singles');
  });

  it('labels the columns for the shape the reader is in', () => {
    expect(sideLabels(1)).toEqual({ ours: 'You', theirs: 'Them' });
    expect(sideLabels(2)).toEqual({ ours: 'Your side', theirs: 'Their side' });
  });
});

describe('the rest', () => {
  it('measures the grace from the score and never from the tap', () => {
    expect(acceptedLine(PROPOSAL.settlesAt, READ_AT)).toContain('6 hours');
  });

  it('says what a confirmed result said about you, and nothing when it said nothing', () => {
    expect(outcomeLine('WIN')).toBe('You won.');
    expect(outcomeLine(undefined)).toBeUndefined();
  });

  it('tells two games apart by a duration, because there is no calendar to print', () => {
    expect(gameEyebrow('Padel', GAME)).toBe('Padel · arranged 4 days ago');
  });
});
