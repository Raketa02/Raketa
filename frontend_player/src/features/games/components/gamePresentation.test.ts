/**
 * The copy deck, and the four sentences the ticket says carry unusual weight.
 *
 * Mostly what is asserted is **not the wording** — that is what makes a copy deck a copy deck — but
 * the rules the wording has to keep: when silence makes a score the result is named before it
 * happens, and that saying nothing costs nothing; a game with no score is never an error; a
 * correction is never called a proposal; and nothing anywhere blames anybody. **The sentences
 * #656 settled are the exception, and are held word for word**: the moment silence settles a score,
 * the titles of the questions and the endings, and *Counted.* — the words the ticket's own
 * acceptance criteria quote, which is what a story walk reads them against.
 */

import type { NamedPlayer } from '@/shared/formatting/playerName';

import type { ResultArgument } from '../domain/resultArgument';
import type { Game } from '../domain/game';

import {
  COUNTER_IS_THEIR_SCORE,
  COUNTER_LABEL,
  CORRECT_LABEL,
  EVENING_FACTS,
  barLabels,
  clockLine,
  courtLine,
  attendanceLine,
  attendanceTapLabel,
  forecastSentence,
  formatEyebrow,
  gameEyebrow,
  outcomeLine,
  resultBody,
  saysWhatItIsWorth,
  scoreProblemLine,
  setLabel,
  sideLabels,
  spokenScore,
  resultTitle,
  standingLine,
  worthLine,
} from './gamePresentation';

/** Saturday 5 September, 11:00 in Kraków. */
const READ_AT = '2026-09-05T09:00:00Z';

const GAME: Game = {
  gameId: 'g1',
  sport: 'padel',
  kind: 'COUNTED',
  standing: 'AWAITING_ANSWER',
  seats: [
    { side: 'A', playerId: 'me', name: 'me_' },
    { side: 'B', playerId: 'them', name: 'tomek.p' },
  ],
  plannedAt: '2026-09-01T09:00:00Z',
  proposals: [],
  attendance: [],
  readAt: READ_AT,
};

/** The two people any of these sentences can name: you, and the player across the net. */
const YOU: NamedPlayer = { kind: 'you' };
const THEM: NamedPlayer = { kind: 'player', name: 'tomek.p' };

const PROPOSAL = {
  side: 'A',
  proposedBy: 'me',
  score: {
    sets: [
      { a: 6, b: 4 },
      { a: 6, b: 2 },
    ],
  },
  // Sunday, 10:00 in Kraków — 23 hours after the read.
  answerBy: '2026-09-06T08:00:00Z',
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
  // Sunday, 12:00 in Kraków — the later of the two, so the moment the disagreement settles.
  answerBy: '2026-09-06T10:00:00Z',
} as const;

/** The disagreement, read from the side that put `PROPOSAL` up. */
const ARGUING: ResultArgument = {
  kind: 'both-stand',
  ours: PROPOSAL,
  theirs: COUNTER,
  settlesAt: COUNTER.answerBy,
};

/** *Is that right?*, in doubles and in singles. */
const ASKED: ResultArgument = {
  kind: 'theirs-stands',
  proposal: PROPOSAL,
  by: THEM,
  withPartner: true,
};
const ASKED_ALONE: ResultArgument = { ...ASKED, withPartner: false };

describe('when silence makes a score the result, said before it happens', () => {
  /**
   * **The moment, on the club's clock** (#656): *if neither he nor Paula answers, 6–4 6–3 becomes
   * the result at 20:30 on Wednesday*. It is in the **standing line**, so it is never a footnote
   * somebody reaches by tapping, and the clock block under it carries the duration.
   */
  it('names the moment on the side that put the score up', () => {
    expect(standingLine({ kind: 'ours-stands', proposal: PROPOSAL }, READ_AT)).toBe(
      'Your side’s score is up. If nobody answers, it becomes the result at 10:00 on Sunday.',
    );
  });

  it('names it to the side being asked — both of them in doubles, the reader alone in singles', () => {
    expect(standingLine(ASKED, READ_AT)).toBe(
      'tomek.p put a score up. If neither of you answers, it becomes the result at 10:00 on Sunday.',
    );
    expect(standingLine(ASKED_ALONE, READ_AT)).toBe(
      'tomek.p put a score up. If you don’t answer, it becomes the result at 10:00 on Sunday.',
    );
  });

  it('says today rather than the day’s name when the moment is on the read’s own day', () => {
    const today = { ...PROPOSAL, answerBy: '2026-09-05T18:30:00Z' };

    expect(standingLine({ ...ASKED_ALONE, proposal: today }, READ_AT)).toContain('at 20:30 today');
  });

  it('drops the moment rather than inventing one where it cannot be read', () => {
    const unreadable = { ...PROPOSAL, answerBy: 'not an instant' };

    expect(standingLine({ kind: 'ours-stands', proposal: unreadable }, READ_AT)).toBe(
      'Your side’s score is up. If nobody answers, it becomes the result.',
    );
  });

  /** **Silence costs nothing** — the sentence the finding was about, said under the clock. */
  it('says, to the side being asked, that saying nothing costs nothing', () => {
    expect(clockLine(ASKED, READ_AT)).toEqual({
      figure: '23 hours',
      line: 'until this becomes the result if nobody answers. Saying nothing costs nothing.',
    });
  });

  /**
   * F-RESULT-35.1: the screen said *there is no penalty* over a silence that cost a miss. Silence
   * is free now, and the screen says so in those words rather than talking about penalties.
   */
  it('never talks about a penalty, and says a tap settles it now only where it does', () => {
    const said = [
      standingLine(ASKED, READ_AT),
      resultBody(ASKED),
      clockLine(ASKED, READ_AT)?.line,
      resultBody(ARGUING),
      resultBody({ kind: 'ours-stands', proposal: PROPOSAL }),
    ].join(' ');

    expect(said).not.toMatch(/penalt/i);
    expect(said).not.toMatch(/settles it now/);
    expect(resultBody(ASKED)).toContain('makes it the result now');
  });

  it('says when two scores settle if neither side agrees', () => {
    expect(standingLine(ARGUING, READ_AT)).toContain('it settles at 12:00 on Sunday');
    expect(clockLine(ARGUING, READ_AT)?.figure).toBe('25 hours');
  });

  it('names the entry window too, so the game does not end with nobody having been told', () => {
    const line = standingLine(
      { kind: 'awaiting-entry', entryClosesAt: '2026-09-08T09:00:00Z', seatOpen: false },
      READ_AT,
    );

    expect(line).toContain('3 days');
  });

  /**
   * **The hour's ending** ([ADR-0175](../../../../../docs/adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md)
   * §3): the wire names nobody by design, the heading is the shortage's, and the body says nobody
   * filled the seat — singles and doubles differing by one clause — over the ghost's own fact.
   */
  it('heads the hour’s call-off with the shortage and says nobody filled the seat', () => {
    const singles = { kind: 'called-off', ending: { how: 'the-hour', format: 'singles' } } as const;
    const doubles = { kind: 'called-off', ending: { how: 'the-hour', format: 'doubles' } } as const;

    expect(resultTitle(singles)).toBe('The game was called off for lack of players');
    expect(resultBody(singles)).toBe(
      'Nobody filled the seat in time, so the singles game is called off. Nobody is marked for it — not you, not them.',
    );
    expect(resultBody(doubles)).toBe(
      'Nobody filled the seat in time, so the doubles game is called off. Nobody is marked for it — not you, not any of them.',
    );
    expect(standingLine(singles, READ_AT)).toBe('Called off');
    expect(resultBody(singles)).not.toMatch(/\bby\b|who/);
  });

  /**
   * **The ending block, keyed by how it ended** ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
   * §8): a departure's heading says the game was called off for lack of players and its body
   * names who left, singles and doubles differing by one clause.
   */
  it('heads a departure with the shortage and names the leaver in the body', () => {
    const tomek = { kind: 'player', name: 'tomek.p' } as const;
    const singles = {
      kind: 'called-off',
      ending: { by: tomek, how: 'departure', format: 'singles' },
    } as const;
    const doubles = {
      kind: 'called-off',
      ending: { by: tomek, how: 'departure', format: 'doubles' },
    } as const;

    expect(resultTitle(singles)).toBe('The game was called off for lack of players');
    expect(resultBody(singles)).toBe(
      'tomek.p left, so the singles game is called off. Nobody is marked for it — not you, not them.',
    );
    expect(resultTitle(doubles)).toBe('The game was called off for lack of players');
    expect(resultBody(doubles)).toBe(
      'tomek.p was the last to leave, so the doubles game is called off. Nobody is marked for it — not you, not any of them.',
    );
  });

  it('never says cancel of an ending, and never names a presser', () => {
    const tomek = { kind: 'player', name: 'tomek.p' } as const;
    const endings = [
      { by: tomek, how: 'departure', format: 'singles' },
      { how: 'the-hour', format: 'singles' },
    ] as const;
    for (const ending of endings) {
      const argument = { kind: 'called-off', ending } as const;
      expect(`${resultTitle(argument)} ${resultBody(argument)}`).not.toMatch(
        /cancel|called the game off/i,
      );
    }
  });

  it('drops the clause rather than inventing a deadline when the wire sent none', () => {
    expect(standingLine({ kind: 'awaiting-entry', seatOpen: false }, READ_AT)).toBe(
      'No score yet.',
    );
  });

  /** *How did it go?* — the question the hour's end asks a Competitive game's four (§15.2). */
  it('asks how it went on the entry', () => {
    expect(resultTitle({ kind: 'awaiting-entry', seatOpen: false })).toBe('How did it go?');
  });
});

/**
 * **The endings with no score read as an evening, not as an error** — a full game nobody recorded
 * (#655) and two scores naming different winners (#654). Each says why there is no score, in plain
 * words, over the facts both share.
 */
describe('a game with no score reads as an evening, not as an error', () => {
  const endings: readonly ResultArgument[] = [{ kind: 'played-no-score' }, { kind: 'disputed' }];

  it('heads a full game nobody recorded as played, with no score', () => {
    expect(resultTitle({ kind: 'played-no-score' })).toBe('Played · no score');
    expect(resultBody({ kind: 'played-no-score' })).toContain('counts as a game played');
  });

  it('says a disputed game had two winners named, and that nobody decides between them', () => {
    expect(resultTitle({ kind: 'disputed' })).toBe('Disputed');
    expect(standingLine({ kind: 'disputed' }, READ_AT)).toBe(
      'The two scores named different winners.',
    );
    expect(resultBody({ kind: 'disputed' })).toContain('doesn’t decide who won');
  });

  /** The old body said *nobody wrote a score down* — of a game whose two scores had been written. */
  it('says why the game took no score, and never that nobody wrote one down', () => {
    for (const ending of endings) {
      expect(resultBody(ending)).not.toMatch(/wrote a score down/);
    }
  });

  it('lists what it still is — played, and moving nobody’s Level', () => {
    expect(EVENING_FACTS).toHaveLength(3);
    expect(EVENING_FACTS.join(' ')).toContain('in how much you have played');
    expect(EVENING_FACTS.join(' ')).toContain('moved nobody’s Level');
  });

  it('never reads as a failure', () => {
    for (const ending of endings) {
      const said = `${resultTitle(ending)} ${standingLine(ending, READ_AT)} ${resultBody(ending) ?? ''}`;

      expect(said).not.toMatch(/failed|error|sorry|unfortunately|could not|couldn’t|never/i);
    }
  });
});

/**
 * **For fun asks nothing** (#654; the mechanics §15.2): it reads *Played*, and a score can be
 * added that stands as it is put — nobody is asked to agree, and no Level moves.
 */
describe('a For fun game', () => {
  it('reads played, before a score and after one', () => {
    expect(resultTitle({ kind: 'for-fun', seatOpen: false })).toBe('Played');
    expect(resultTitle({ kind: 'for-fun', score: PROPOSAL.score, seatOpen: false })).toBe('Played');
  });

  it('says a score may be added, that nobody is asked to agree, and that no Level moves', () => {
    const body = resultBody({ kind: 'for-fun', seatOpen: false }) ?? '';

    expect(body).toContain('nobody is asked to agree');
    expect(body).toContain('no Level moves');
    // Until when — the entry window's day after the game, the same last day a correction has.
    expect(body).toContain('up to a day after the game');
    expect(standingLine({ kind: 'for-fun', seatOpen: false }, READ_AT)).not.toMatch(/\?/);
  });

  it('offers no score across an open seat, and says so by not offering one', () => {
    expect(resultBody({ kind: 'for-fun', seatOpen: true })).not.toContain('add the score');
  });

  it('asks nothing once its score is up, and has no clock', () => {
    const scored = { kind: 'for-fun', score: PROPOSAL.score, seatOpen: false } as const;

    expect(resultBody(scored)).toBeUndefined();
    expect(clockLine(scored, READ_AT)).toBeUndefined();
    expect(clockLine({ kind: 'for-fun', seatOpen: false }, READ_AT)).toBeUndefined();
  });
});

describe('nobody is penalised, which is a sentence and not an omission', () => {
  /**
   * *Never played* said *Nobody is marked for that* over a record that marked all four (#656), so
   * its ending says what the game **is** — played — and leaves the record to the record.
   */
  it('says a full game nobody recorded was played, and nothing about marks', () => {
    expect(resultBody({ kind: 'played-no-score' })).toContain('played for everybody');
    expect(resultBody({ kind: 'played-no-score' })).not.toContain('marked');
  });

  /**
   * **The fourth end is drawn as the ghost is** (#419 §3): neither an evening nor a game that
   * never happened, so nothing anybody is measured on moves (ADR-0163) — and the screen says so
   * rather than leaving the reader to wonder whether calling it off cost them.
   */
  it('says so on the game that was called off', () => {
    const ending = { how: 'the-hour', format: 'doubles' } as const;
    expect(resultBody({ kind: 'called-off', ending })).toContain('Nobody is marked');
  });

  it('says so where agreeing might otherwise look like the safe move', () => {
    expect(clockLine(ASKED, READ_AT)?.line).toContain('Saying nothing costs nothing');
  });
});

describe('a correction is not a second proposal, and the words never call it one', () => {
  it('says it does not use the side’s one turn, and that it has a last day', () => {
    const body = resultBody({ kind: 'ours-stands', proposal: PROPOSAL });

    expect(body).toContain('doesn’t use your side’s one turn');
    expect(body).toContain('a day after the game');
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
  it('tells the waiting side they are waiting, and the asked side that silence is free', () => {
    expect(clockLine({ kind: 'ours-stands', proposal: PROPOSAL }, READ_AT)).toEqual({
      figure: '23 hours',
      line: 'left for the other side to answer. If they say nothing, this becomes the result.',
    });
    expect(clockLine(ASKED, READ_AT)?.line).toContain('Saying nothing costs nothing');
  });

  /** The standing line names the moment; the clock is the duration under it, never both twice. */
  it('draws the duration, and leaves the moment to the line above it', () => {
    const clock = clockLine(ASKED, READ_AT);

    expect(`${clock?.figure ?? ''} ${clock?.line ?? ''}`).not.toMatch(/\d{1,2}:\d{2}|Sunday/);
  });

  it('has nothing to say about a game that has ended, or one nobody has scored yet', () => {
    expect(clockLine({ kind: 'confirmed' }, READ_AT)).toBeUndefined();
    expect(clockLine({ kind: 'disputed' }, READ_AT)).toBeUndefined();
    expect(clockLine({ kind: 'played-no-score' }, READ_AT)).toBeUndefined();
    expect(
      clockLine(
        { kind: 'awaiting-entry', entryClosesAt: '2026-09-08T09:00:00Z', seatOpen: false },
        READ_AT,
      ),
    ).toBeUndefined();
  });
});

/**
 * **However a result settled, it reads counted** (#654): an agreement, silence and the closer of two
 * scores naming one winner all end `CONFIRMED`, and the wire does not say which — so nothing calls
 * the score *agreed*.
 */
describe('a confirmed result', () => {
  it('reads counted, never agreed', () => {
    const confirmed = { kind: 'confirmed', score: PROPOSAL.score } as const;

    expect(standingLine(confirmed, READ_AT)).toBe('Counted.');
    expect(`${standingLine(confirmed, READ_AT)} ${worthLine('COUNTED') ?? ''}`).not.toMatch(
      /agreed/i,
    );
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
    expect(COUNTER_IS_THEIR_SCORE).toContain('agree with it');
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
   * scores travel, so it names the exit — and since #654, what happens if nobody takes it.
   */
  it('names the agreement that ends it at once, and the two ways it settles without one', () => {
    const body = resultBody(ARGUING) ?? '';

    expect(body).toContain('agrees with the other’s score, that settles it at once');
    expect(body).toContain('the closer one counts');
    expect(body).toContain('no Level moves');
  });

  it('still refuses to pick between them, which is the thing the platform does not do', () => {
    expect(resultBody(ARGUING)).toContain('doesn’t decide between them');
  });
});

describe('the eyebrow on the plan lead', () => {
  const doubles: Game = {
    ...GAME,
    seats: [
      { side: 'A', playerId: 'me', name: 'me_' },
      { side: 'A', playerId: 'partner', name: 'kasia_w' },
      { side: 'B', playerId: 'them', name: 'tomek.p' },
      { side: 'B', playerId: 'other', name: 'marekb' },
    ],
  };

  /**
   * **The format and the kind, and nothing else** ([#414](https://github.com/Raketa02/Raketa/issues/414)):
   * the card under it names the people and the plan names the day, so the handles and *arranged n
   * ago* go. The format is read off the seats, as the Now card's retired eyebrow read it. **Not
   * uppercased here** — the header's style does that, and a listener would get the letters.
   */
  it.each([
    ['singles, counted', GAME, 'Singles · Counted'],
    ['singles, friendly', { ...GAME, kind: 'FRIENDLY' } as const, 'Singles · Friendly'],
    ['doubles, counted', doubles, 'Doubles · Counted'],
    ['doubles, friendly', { ...doubles, kind: 'FRIENDLY' } as const, 'Doubles · Friendly'],
  ])('reads the format and the kind — %s', (_, game, eyebrow) => {
    expect(formatEyebrow(game)).toBe(eyebrow);
  });

  /** **`Counted`, never `Competitive`** — that is a search's word (§5.4 #8). */
  it('never says competitive', () => {
    expect(formatEyebrow(GAME).toLowerCase()).not.toContain('competitive');
  });

  /** A `GameKind` this build cannot read drops the clause, and the format stands. */
  it('drops the kind where the build cannot read one', () => {
    const { kind: _kind, ...unreadable } = GAME;

    expect(formatEyebrow(unreadable)).toBe('Singles');
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
        { side: 'A', playerId: 'me', name: 'me_' },
        { side: 'A', playerId: 'partner', name: 'kasia_w' },
        { side: 'B', playerId: 'them', name: 'tomek.p' },
        { side: 'B', playerId: 'other', name: 'marekb' },
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
        { side: 'A', playerId: 'me', name: 'me_' },
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
    expect(standingLine(ASKED, READ_AT)).toContain('tomek.p put a score up');
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

describe('the court’s pairing, in words', () => {
  /**
   * The sentence under the percentage says what a confirmed score **does** — the counted game
   * moves everybody, the friendly moves nobody — and is dropped, never guessed, for a kind this
   * build cannot read. The check is the same one `worthLine`'s is: the two kinds say opposite
   * things about movement, and neither reads as a failure.
   */
  it('says a counted game moves everybody’s level and a friendly moves nothing', () => {
    expect(forecastSentence('COUNTED')).toMatch(/counted/i);
    expect(forecastSentence('COUNTED')).toMatch(/moves/);
    expect(forecastSentence('FRIENDLY')).toMatch(/friendly/i);
    expect(forecastSentence('FRIENDLY')).toMatch(/nothing moves/i);
    expect(forecastSentence(undefined)).toBeUndefined();
  });

  /**
   * The bar's two labels are **stems**, because a segment half a card wide cannot hold sixty-four
   * characters: `You + {partner stem}` against `{stem} + {stem}` in doubles, `You` against
   * `{stem}` in singles. A handle that is a stem already is drawn whole.
   */
  it('labels the bar with stems — you and your partner against the other side', () => {
    const doubles = barLabels(
      [
        { side: 'A', playerId: 'me', name: 'tomek.p' },
        { side: 'A', playerId: 'p', name: 'Zofia.B' },
        { side: 'B', playerId: 'o1', name: 'kuba_w' },
        { side: 'B', playerId: 'o2', name: 'ola.n' },
      ],
      'me',
    );

    expect(doubles).toEqual(['You + Zofia', 'kuba_w + ola']);
  });

  it('labels a singles bar with you and one stem', () => {
    const singles = barLabels(
      [
        { side: 'B', playerId: 'o', name: 'kuba_w' },
        { side: 'A', playerId: 'me', name: 'tomek.p' },
      ],
      'me',
    );

    expect(singles).toEqual(['You', 'kuba_w']);
  });

  /** A seat `users` can no longer answer for is the unknown player's `?`, on the bar as anywhere. */
  it('draws the unknown player’s mark for a seat with no handle', () => {
    expect(
      barLabels(
        [
          { side: 'A', playerId: 'me' },
          { side: 'B', playerId: 'o' },
        ],
        'me',
      ),
    ).toEqual(['You', '?']);
  });
});

/**
 * **Who turned up, in words** ([#658](https://github.com/Raketa02/Raketa/issues/658); ADR-0195 §3).
 * The awaited player reads who is waiting for them and what the half hour decides, before it runs
 * out; everybody else reads whom the game waits for, and that saying so cost them nothing. The
 * player who didn't come is told how long they have to say they were there, the way silence on a
 * score is named before it settles.
 */
describe('attendance, in words', () => {
  const OSCAR: NamedPlayer = { kind: 'player', name: 'Oscar Nowak' };
  const IVAN: NamedPlayer = { kind: 'player', name: 'Ivan Petrov' };
  /** Wednesday 14 October, 17:10 in Warsaw: the first half hour, 20 minutes left of it. */
  const AT_THE_COURT = '2026-10-14T15:10:00Z';
  const ARRIVE_BY = '2026-10-14T15:30:00Z';

  const AWAITED: ResultArgument = {
    kind: 'not-here-yet',
    awaited: [YOU],
    here: [IVAN],
    yours: true,
    arriveBy: ARRIVE_BY,
  };
  const WAITING_FOR_OSCAR: ResultArgument = {
    kind: 'not-here-yet',
    awaited: [OSCAR],
    here: [],
    yours: false,
    arriveBy: ARRIVE_BY,
  };

  it('tells the awaited player who is waiting, and what the half hour decides', () => {
    expect(resultTitle(AWAITED)).toBe('Are you here?');
    expect(standingLine(AWAITED, AT_THE_COURT)).toBe('Ivan Petrov is waiting for you.');
    expect(clockLine(AWAITED, AT_THE_COURT)).toEqual({
      figure: '20 minutes',
      line: 'left to arrive. After that it’s Didn’t come.',
    });
    const body = resultBody(AWAITED, { booked: true, readAt: AT_THE_COURT }) ?? '';
    expect(body).toContain('Tap I’m here once you’re at the club');
    expect(body).toContain('If you haven’t arrived by 17:30, it’s Didn’t come');
  });

  it('says everybody the game waits with, when there is more than one', () => {
    expect(
      standingLine({ ...AWAITED, here: [IVAN, { kind: 'player', name: 'piotr.s' }] }, AT_THE_COURT),
    ).toBe('Ivan Petrov and piotr.s are waiting for you.');
  });

  it('tells everybody else whom the game waits for, and that saying so cost them nothing', () => {
    expect(resultTitle(WAITING_FOR_OSCAR)).toBe('Not here yet');
    expect(standingLine(WAITING_FOR_OSCAR, AT_THE_COURT)).toBe('Waiting for Oscar Nowak.');
    const body = resultBody(WAITING_FOR_OSCAR, { booked: true, readAt: AT_THE_COURT }) ?? '';
    expect(body).toContain('No score goes in while somebody is awaited');
    expect(body).toContain('Saying so costs you nothing');
  });

  it('tells the player who didn’t come how long they have to say they were there', () => {
    const mayClaim: ResultArgument = {
      kind: 'didnt-come',
      absent: [YOU],
      yours: { state: 'may-claim', claimBy: '2026-10-15T15:30:00Z' },
    };
    const theNextMorning = '2026-10-15T07:00:00Z';

    expect(resultTitle(mayClaim)).toBe('Were you there?');
    expect(standingLine(mayClaim, theNextMorning)).toBe('You didn’t come.');
    expect(clockLine(mayClaim, theNextMorning)?.figure).toBe('8 hours');
    expect(resultBody(mayClaim, { readAt: theNextMorning })).toContain(
      'say I was there by 17:30. Once somebody who played confirms it, it’s Came late',
    );
    // Read the evening before, the day is named.
    expect(resultBody(mayClaim, { readAt: '2026-10-14T16:00:00Z' })).toContain(
      'by 17:30 on Thursday',
    );
  });

  it('says a claim waits on somebody else, and a day that passed stands', () => {
    const claimed: ResultArgument = {
      kind: 'didnt-come',
      absent: [YOU],
      yours: { state: 'claimed', claimBy: '2026-10-15T15:30:00Z' },
    };
    const final: ResultArgument = {
      kind: 'didnt-come',
      absent: [YOU],
      yours: { state: 'final', claimBy: '2026-10-15T15:30:00Z' },
    };

    expect(resultTitle(claimed)).toBe('Didn’t come');
    expect(resultBody(claimed)).toContain('You said you were there');
    expect(clockLine(claimed, READ_AT)).toBeUndefined();
    expect(resultBody(final)).toBe('The game took no score and didn’t count, and no Level moved.');
  });

  it('names who didn’t come to everybody else, and blames nobody who came', () => {
    const ended: ResultArgument = { kind: 'didnt-come', absent: [OSCAR] };

    expect(resultTitle(ended)).toBe('Didn’t come');
    expect(standingLine(ended, READ_AT)).toBe('Oscar Nowak didn’t come.');
    expect(resultBody(ended)).toMatch(/nobody who came is marked/i);
  });

  it('names the player whole on every tap and line', () => {
    expect(attendanceTapLabel('not-here-yet', OSCAR)).toBe('Oscar Nowak isn’t here yet');
    expect(attendanceTapLabel('here', OSCAR)).toBe('Oscar Nowak is here');
    expect(attendanceTapLabel('was-here', OSCAR)).toBe('Yes, Oscar Nowak was here');
    expect(attendanceLine('came-late', OSCAR)).toBe('Oscar Nowak came late');
    expect(attendanceLine('came-late', YOU)).toBe('You came late');
    expect(attendanceLine('says-they-were-there', OSCAR)).toBe('Oscar Nowak says they were there');
  });

  it('asks nothing of a score while somebody is awaited or didn’t come', () => {
    expect(saysWhatItIsWorth(WAITING_FOR_OSCAR)).toBe(false);
    expect(saysWhatItIsWorth({ kind: 'didnt-come', absent: [OSCAR] })).toBe(false);
  });
});
