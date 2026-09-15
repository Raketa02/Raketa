/**
 * **The sheet's words**, and the four claims a build session could quietly undo.
 *
 * Most of these are about a sentence that must **not** be written: no place name from an area
 * code, no distance about yourself, no claim of nothing-in-common out of the app's own
 * ignorance, and no figure the run of five did not actually count.
 */

import type { SocialTagOverlap } from '@/shared/vocabulary/socialTagOverlap';

import type { StrandRow } from '../domain/playerRecord';

import {
  IN_YOUR_AREA,
  FIT_ROW_NAME,
  fitRowLabel,
  OPINION_BAND_NAME,
  OWN_RECORD_TITLE,
  RECORD_TITLE,
  STRAND_NAME,
  YOU_MARK,
  identityLine,
  introLine,
  lastFiveReading,
  SPORTSMANSHIP_LABEL,
  opinionValue,
  opinionFigure,
  recordCloseLabel,
  recordCardLabel,
  recordHandle,
  recordBlocksLabel,
  recordHeaderLabel,
  skillCardLabel,
  skillHeadline,
  socialTagsLabel,
  strandFraction,
  varietyValue,
} from './recordPresentation';

const HERE = 'A+050612+0019938';
const THERE = 'A+050614+0019944';

describe('the identity line', () => {
  const about = (facts: Omit<Parameters<typeof identityLine>[0], 'isSelf'>) =>
    identityLine({ ...facts, isSelf: false });

  it('states the area only where two codes actually match', () => {
    expect(about({ areaCode: HERE, viewerAreaCode: HERE, distanceKm: 1 })).toBe(
      `${IN_YOUR_AREA} · 1 km`,
    );
    expect(about({ areaCode: HERE, viewerAreaCode: THERE, distanceKm: 4 })).toBe('4 km');
  });

  /**
   * *The comparison cannot be made* and *they are not in your area* are two facts and only one
   * of them is a claim. A reader whose own area is unknown must not be told twenty strangers
   * are in it, and must not be told they are not either.
   */
  it('makes no claim at all where the reader’s own area is unknown', () => {
    expect(about({ areaCode: HERE, distanceKm: 4 })).toBe('4 km');
  });

  /**
   * **The whole line goes on your own record, and not only the distance.** The two codes are
   * equal by construction there, so a line that dropped the kilometres alone would tell somebody
   * they are in their own area — which is the failure that hides behind *no distance about
   * yourself* being the obvious half of the rule.
   */
  it('says nothing at all about where you are on your own record', () => {
    expect(
      identityLine({ areaCode: HERE, viewerAreaCode: HERE, distanceKm: 0, isSelf: true }),
    ).toBe('');
    expect(identityLine({ areaCode: HERE, viewerAreaCode: HERE, isSelf: true })).toBe('');
  });

  it('leaves no separator behind where only one part is absent', () => {
    expect(about({ areaCode: HERE, viewerAreaCode: HERE })).toBe(IN_YOUR_AREA);
    expect(about({ areaCode: HERE })).toBe('');
  });

  it('never prints the area code itself, which is a coordinate and not a name', () => {
    expect(about({ areaCode: HERE, viewerAreaCode: HERE, distanceKm: 4 })).not.toContain(HERE);
  });
});

describe('the intro, drawn', () => {
  it('is their line inside the drawing’s own quotation marks, and nothing else', () => {
    // The marks are the drawing's and never the player's: a line that already carries its
    // own quotes is quoted again, because what the marks say is *this is them speaking*.
    expect(introLine('Will travel for a hard game.')).toBe('“Will travel for a hard game.”');
  });
});

describe('the sheet’s two titles', () => {
  it('says whose view this is, and the close control says what it closes', () => {
    expect(recordCloseLabel(false)).toBe(`Close ${RECORD_TITLE.toLowerCase()}`);
    expect(recordCloseLabel(true)).toBe(`Close ${OWN_RECORD_TITLE.toLowerCase()}`);
  });

  it('marks your own name rather than replacing it', () => {
    expect(recordHandle('Bea Kowalczyk', true)).toBe(`Bea Kowalczyk ${YOU_MARK}`);
    expect(recordHandle('Bea Kowalczyk', false)).toBe('Bea Kowalczyk');
  });
});

describe('the skill card’s headline, and what left it', () => {
  it('is one run, in one order, and the count is no longer in it', () => {
    expect(skillHeadline({ sportName: 'Padel', level: 2.75, confidence: 77 })).toBe(
      'PADEL · 2,75 · 77% sure',
    );
  });

  /**
   * **The count is drawn once on this sheet, and this is the assertion that keeps it that way.**
   * It moved into `COUNTED_BLOCK` a few points below the headline, and a build session restoring
   * `· 21 counted` here would put one figure in two registers inches apart — the double
   * announcement §20.1 spends the whole sheet avoiding, made visible.
   */
  it('never says the counted figure twice', () => {
    const headline = skillHeadline({ sportName: 'Padel', level: 2.75, confidence: 77 });

    expect(headline).not.toContain('21');
    expect(headline).not.toContain('counted');
    expect(recordBlocksLabel({ countedGames: 21 })).toBe('21 counted games');
  });

  it('says a run of three is out of three, because the gap is the honest statement', () => {
    expect(lastFiveReading(['WIN', 'LOSS', 'WIN'])).toBe('2 of the last 3 won');
    expect(lastFiveReading(['WIN', 'WIN', 'LOSS', 'WIN', 'WIN'])).toBe('4 of the last 5 won');
  });

  /**
   * **The spoken card is one sport's, and the block row beside it is not.** The run and the
   * count went with the drawing, which leaves this label the four facts that are genuinely about
   * the resolved Sport — and stops a reliability figure being announced inside a sentence that
   * opened with *Padel*.
   */
  it('speaks the Level, the certainty and the range, and neither of the two that left', () => {
    expect(
      skillCardLabel({
        sportName: 'Padel',
        level: 2.75,
        band: 'Established',
        confidence: 77,
        likelyRange: { low: 2.47, high: 3.03 },
      }),
    ).toBe('Padel. Level 2,75, Established. 77% sure. Likely 2,47 – 3,03');
  });
});

/**
 * **The three blocks, as one element** — and the three absences that do not move together.
 *
 * A player with a Player Score and no rating at all is the case the row exists outside the skill
 * card for: they draw one box, and it is the one figure the matcher acts on.
 */
describe('the record blocks, as one element', () => {
  it('reads left to right, and spells the scale the figure alone could not', () => {
    expect(
      recordBlocksLabel({ playerScore: 91, lastFive: ['WIN', 'WIN', 'LOSS'], countedGames: 5 }),
    ).toBe('Player reliability 91 out of 100. 2 of the last 3 won. 5 counted games');
  });

  it('says nothing at all about a block it did not draw', () => {
    expect(recordBlocksLabel({ playerScore: 91 })).toBe('Player reliability 91 out of 100');
    expect(recordBlocksLabel({ countedGames: 1 })).toBe('1 counted game');
    expect(recordBlocksLabel({})).toBe('');
  });

  /**
   * An empty run and an omitted one are one absence, exactly as they are at the mapper and in
   * the drawing: a run's length is a claim, so nought squares is nothing to say rather than
   * *0 of the last 0 won*.
   */
  it('treats an empty run as no run', () => {
    expect(recordBlocksLabel({ playerScore: 91, lastFive: [] })).toBe(
      recordBlocksLabel({ playerScore: 91 }),
    );
  });
});

describe('the header, as one element', () => {
  /**
   * The name first and the handle second, because that is the order they are drawn — and the
   * handle *is* here: this sheet is one of the two places it is drawn
   * ([ADR-0171](../../../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)
   * §4), and a listener is told what a reader is shown.
   */
  it('leads with the name and the handle, and drops what is absent rather than speaking nothing', () => {
    expect(
      recordHeaderLabel({
        name: 'Bea Kowalczyk',
        handle: '@bea_k',
        onCourt: true,
        identity: 'In your area · 4 km',
        sports: ['Padel 2,75'],
      }),
    ).toBe('Bea Kowalczyk. @bea_k. Photo checked: on court. In your area · 4 km. Padel 2,75');

    expect(
      recordHeaderLabel({
        name: 'Bea Kowalczyk',
        handle: '@bea_k',
        onCourt: false,
        identity: '',
        sports: [],
      }),
    ).toBe('Bea Kowalczyk. @bea_k');
  });

  it('speaks the intro inside its marks, after the handle and before where they are', () => {
    // The drawn order: the line sits under the name, so it is heard there too — as their own
    // words, which the quotation marks say, and never as the name (ADR-0170 §4).
    expect(
      recordHeaderLabel({
        name: 'Bea Kowalczyk',
        handle: '@bea_k',
        onCourt: false,
        intro: introLine('Will travel for a hard game.'),
        identity: '4 km',
        sports: ['Padel 2,75'],
      }),
    ).toBe('Bea Kowalczyk. @bea_k. “Will travel for a hard game.”. 4 km. Padel 2,75');
  });

  /**
   * ADR-0133's clause survives ADR-0138 untouched: the check's own confidence crosses on no
   * route, so there is nothing here to print a number from — and *nobody looked* and *checked
   * and flagged* both reach this function as `false` and say nothing at all.
   */
  it('says nothing about a photograph that was flagged or never checked', () => {
    expect(
      recordHeaderLabel({
        name: 'Bea Kowalczyk',
        handle: '@bea_k',
        onCourt: false,
        identity: '4 km',
        sports: [],
      }),
    ).toBe('Bea Kowalczyk. @bea_k. 4 km');
  });
});

describe('the Social tag row’s three silences', () => {
  const unknown: SocialTagOverlap = { kind: 'unknown', tags: ['PLAYS_TO_WIN'] };
  const none: SocialTagOverlap = { kind: 'none-in-common' };

  it('claims nothing where no comparison was made', () => {
    expect(socialTagsLabel(unknown)).toBe('Their tags: Plays to win');
    expect(socialTagsLabel(unknown)).not.toBe(socialTagsLabel(none));
  });

  it('says whose fact each half is', () => {
    const shared: SocialTagOverlap = {
      kind: 'shared',
      tags: [
        { id: 'PLAYS_TO_WIN', shared: true },
        { id: 'STAYS_FOR_A_DRINK', shared: false },
      ],
    };

    expect(socialTagsLabel(shared)).toBe(
      'Tags you share: Plays to win. Their other tags: Stays for a drink',
    );
  });

  it('says nothing at all where there is nothing to draw', () => {
    expect(socialTagsLabel({ kind: 'hidden' })).toBe('');
  });
});

describe('the pairing control', () => {
  /**
   * **The visible name and the spoken one are one string now**, which is §20.6's flat rule
   * rather than its one exception. The name was `Why ✦ 78`: a glyph doing work, and a figure
   * that moved the control's own name every time the pairing was rescored. The figure lives on
   * the sheet the button opens, which is where a reader who wants it is going anyway.
   */
  it('names what it opens, carries no glyph, and rounds where it prints', () => {
    expect(FIT_ROW_NAME).toBe('Player fit');
    expect(FIT_ROW_NAME).not.toContain('✦');
    // Rounded here because here is where it is printed: a served 78,4 must not promise a
    // figure the sheet it opens does not draw.
    expect(fitRowLabel(78.4)).toBe('Player fit 78');
    expect(fitRowLabel(77.5)).toBe('Player fit 78');
  });
});

/**
 * **The card's own words**, and the two rules a build session could quietly undo: the raw pair
 * beside every figure, and the strand that is named for what it counts.
 */
describe('the record card', () => {
  const row = (over: Partial<StrandRow> = {}): StrandRow => ({
    strand: 'SHOWS_UP',
    good: 9,
    opportunities: 9,
    pct: 100,
    ...over,
  });

  /**
   * **The card has no heading, and the row that needed one carries it.**
   *
   * It read *counted by the system, not written by people* — a promise about authorship, and
   * the reason the star average stood outside the card. The rating belongs on the record, so
   * the heading went; what it was carrying is now three words on the one row that has an
   * author, where every row above it plainly has none.
   */
  it('names its author on the row rather than over the card', () => {
    // **Not *by opponents***: the card asks about everybody on the court, partner included,
    // and `the-decisions.md` struck that wording by name for exactly that reason.
    expect(SPORTSMANSHIP_LABEL).toBe('Sportsmanship, by players');
  });

  /**
   * **Answering, never confirming.** Countering a score you believe is wrong is an answer and
   * costs nothing; a player who did exactly that and watched a *confirms* figure rise is the
   * one person certain to notice the word was wrong.
   */
  it('names the results strand for the thing it counts', () => {
    expect(STRAND_NAME.ANSWERS_RESULTS).toBe('Answers about results');
    expect(Object.values(STRAND_NAME).join(' ')).not.toMatch(/confirm/i);
  });

  /**
   * A perfect record over nine games and one over forty draw the same bar. The pair is what
   * tells them apart, which is why it is printed and why the bar is allowed to say nothing.
   */
  it('prints the raw pair, so nine and forty are visibly different claims', () => {
    expect(strandFraction(row({ good: 9, opportunities: 9 }))).toBe('9 of 9');
    expect(strandFraction(row({ good: 40, opportunities: 40 }))).toBe('40 of 40');
  });

  /**
   * **Variety obeys the same honesty rule as the rows above it.** A bare `70%` would break the
   * rule the card had just made about itself, so the pair is printed beside the share — and the
   * share is this client's one division, because the platform serves two counts and no
   * percentage.
   */
  it('prints variety as a percentage and its raw pair, never one of the two', () => {
    expect(varietyValue({ distinctOpponents: 14, timesOnCourt: 20 })).toBe('70% · 14 of 20');
  });

  it('writes the share as a whole percentage, through the app’s one formatter', () => {
    expect(varietyValue({ distinctOpponents: 2, timesOnCourt: 3 })).toBe('67% · 2 of 3');
  });

  /**
   * The card is one accessibility element: the heading leads, one clause per row follows, and
   * **no bar is in it** — every meter draws a fraction spoken two words earlier.
   */
  it('reaches a listener as the heading and one clause a row', () => {
    expect(
      recordCardLabel({
        rows: [row(), row({ strand: 'ANSWERS_RESULTS', good: 8, opportunities: 10, pct: 80 })],
        variety: { distinctOpponents: 14, timesOnCourt: 20 },
      }),
    ).toBe('Shows up, 9 of 9. Answers about results, 8 of 10. Opponent variety, 70%, 14 of 20');
  });

  /** A card with one row is one clause. Nothing is spoken as absent. */
  it('says nothing about a row it was not given', () => {
    expect(recordCardLabel({ rows: [row()] })).toBe('Shows up, 9 of 9');
  });

  /**
   * **The card speaks the rows it drew and nothing about authorship beyond the row's label.**
   *
   * It used to close on `WRITTEN_BY_PLAYERS` — *it is not in the Player Score, and it hides
   * nobody and holds nobody back* — which the contract asks for by name wherever the star
   * figure is drawn beside the reliability figure. That sentence was removed with its drawn
   * copy, so a listener now gets exactly what a reader gets, which is the point of pinning it
   * here: the two registers said different things for as long as one carried the promise.
   */
  it('speaks the rating as a row, and makes no promise about it', () => {
    const spoken = recordCardLabel({
      rows: [row()],
      opinion: { kind: 'figure', average: 4.7, raters: 17 },
    });

    expect(spoken).toBe(`Shows up, 9 of 9. ${SPORTSMANSHIP_LABEL}, 4,7 out of 5, 17 players`);
    expect(spoken).not.toContain('holds nobody back');
  });
});

/**
 * **The second block's words**, and the two things they must never say.
 *
 * A figure without its count is this field's one way of lying — `3,0 / 5` over one rater reads
 * as a settled fact about somebody — and a figure about *yourself* is the leak the whole design
 * exists to prevent. Both are asserted here, because both are a sentence rather than a rule.
 */
describe('what opponents said', () => {
  /**
   * **The count is never separable from the figure.** `4,7 / 5 · 17 players` and
   * `3,0 / 5 · 1 player` are the same field, and the second one has to visibly read as one
   * person's opinion.
   */
  it('prints the average with the scale and the count of people it rests on', () => {
    expect(opinionFigure({ average: 4.7, raters: 17 })).toBe('4,7 / 5 · 17 players');
    expect(opinionFigure({ average: 3, raters: 1 })).toBe('3,0 / 5 · 1 player');
  });

  /**
   * One decimal, because that is what the platform publishes: `4,70` would claim a second place
   * nobody serves, on a scale whose whole point is that it is coarse enough to be honest.
   */
  it('writes one decimal, in the house comma', () => {
    expect(opinionFigure({ average: 4.25, raters: 4 })).toBe('4,3 / 5 · 4 players');
  });

  it('names the three steps a subject may be told, and nothing finer', () => {
    expect(OPINION_BAND_NAME).toEqual({ GOOD: 'Good', MIXED: 'Mixed', POOR: 'Poor' });
  });

  /**
   * **The block names its own author**, which is what keeps the card above answerable for
   * *counted by the system, not written by people* — and it says the matcher never reads it,
   * because it is drawn on the same sheet as the pill that the matcher does read.
   */
  it('draws the figure and its count, and never one without the other', () => {
    expect(opinionValue({ kind: 'figure', average: 4.7, raters: 17 })).toBe('4,7 / 5 · 17 players');
  });

  /**
   * **Your own record carries no figure and no count anywhere**, spoken or drawn — a published
   * average beside a published count is a subtraction that names each new rating, and the
   * subject knows who they played.
   */
  it('draws a band with no number in it at all', () => {
    const drawn = opinionValue({ kind: 'band', band: 'GOOD' });

    expect(drawn).toBe('Good');
    expect(drawn).not.toMatch(/\d/);
    expect(recordCardLabel({ rows: [], opinion: { kind: 'band', band: 'GOOD' } })).toBe(
      `${SPORTSMANSHIP_LABEL}, Good`,
    );
  });
});
