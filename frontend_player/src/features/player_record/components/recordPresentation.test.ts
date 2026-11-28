/**
 * **The sheet's words**, and the four claims a build session could quietly undo.
 *
 * Most of these are about a sentence that must **not** be written: no place name from an area
 * code, no distance about yourself, no claim of nothing-in-common out of the app's own
 * ignorance, and no figure the run of five did not actually count.
 */

import type { SocialTagOverlap } from '@/shared/vocabulary/socialTagOverlap';

import type { ReliabilityCounts } from '../domain/playerRecord';

import {
  IN_YOUR_AREA,
  FIT_ROW_NAME,
  fitRowLabel,
  OWN_RECORD_TITLE,
  RECORD_TITLE,
  RELIABILITY_BAND_WORD,
  YOU_MARK,
  countLines,
  identityLine,
  introLine,
  lastFiveReading,
  SPORTSMANSHIP_LABEL,
  opinionFigure,
  recordCloseLabel,
  recordCardLabel,
  recordHandle,
  recordBlocksLabel,
  recordHeaderLabel,
  skillCardLabel,
  skillHeadline,
  reliabilityHead,
  reliabilityMark,
  socialTagsLabel,
  varietyValue,
} from './recordPresentation';

const HERE = 'A+050612+0019938';
const THERE = 'A+050614+0019944';

describe('the identity line', () => {
  const about = (facts: Omit<Parameters<typeof identityLine>[0], 'isSelf'>) =>
    identityLine({ ...facts, isSelf: false });

  it('states the area only where two codes actually match', () => {
    expect(about({ areaCode: HERE, viewerAreaCode: HERE, distanceKm: 0.6 })).toBe(
      `${IN_YOUR_AREA} · 0,6 km`,
    );
    expect(about({ areaCode: HERE, viewerAreaCode: THERE, distanceKm: 4.3 })).toBe('4,3 km');
  });

  /**
   * **One decimal, everywhere** (ADR-0174 §2). The kilometres are the spot-to-spot number the
   * server serves to one place, and the line prints it through the one formatter the deck card
   * and the why-fit sentence use — so a person in the reader's own cell reads *In your area ·
   * 0,6 km*, and a served whole number still carries its decimal rather than printing a whole
   * kilometre.
   */
  it('prints the kilometres to one decimal, never whole', () => {
    expect(about({ areaCode: HERE, viewerAreaCode: THERE, distanceKm: 4 })).toBe('4,0 km');
  });

  /**
   * *The comparison cannot be made* and *they are not in your area* are two facts and only one
   * of them is a claim. A reader whose own area is unknown must not be told twenty strangers
   * are in it, and must not be told they are not either.
   */
  it('makes no claim at all where the reader’s own area is unknown', () => {
    expect(about({ areaCode: HERE, distanceKm: 4.3 })).toBe('4,3 km');
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
    expect(about({ areaCode: HERE, viewerAreaCode: HERE, distanceKm: 4.3 })).not.toContain(HERE);
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

  it('marks your own nickname rather than replacing it, and never writes an @', () => {
    expect(recordHandle('bea_k', true)).toBe(`bea_k ${YOU_MARK}`);
    expect(recordHandle('bea_k', false)).toBe('bea_k');
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
 * **The figure's head** — the points and the word beside them, the one spelling the You row's
 * line, the record block and the spoken readings are all built from (#660, ADR-0195 §1).
 */
describe('the figure and its word', () => {
  /** The band's four words, keyed by the served code — the phone holds no thresholds. */
  it('says the band in the server’s four words, and never the retired ladder’s', () => {
    expect(RELIABILITY_BAND_WORD).toEqual({
      VERY_HIGH: 'Very high',
      HIGH: 'High',
      MEDIUM: 'Medium',
      LOW: 'Low',
    });
    expect(Object.values(RELIABILITY_BAND_WORD).join(' ')).not.toMatch(
      /Reliable|Holding|Under the bar/,
    );
  });

  it('reads 75 · High for Sergio', () => {
    expect(reliabilityHead({ playerScore: 75, band: 'HIGH', isNew: false })).toBe('75 · High');
  });

  /**
   * **New takes the band's place**, whatever the band is: fewer than 3 games played through is
   * a figure nobody has tested yet, which is what *New* says and *Very high* would not.
   */
  it('reads 100 · New for Nerea, and New in the band’s place for anybody new', () => {
    expect(reliabilityHead({ playerScore: 100, band: 'VERY_HIGH', isNew: true })).toBe('100 · New');
    expect(reliabilityHead({ playerScore: 75, band: 'HIGH', isNew: true })).toBe('75 · New');
  });

  /** A band this build cannot name leaves the figure alone, never a guessed word. */
  it('reads the bare figure where the band could not be named', () => {
    expect(reliabilityHead({ playerScore: 42, isNew: false })).toBe('42');
    expect(reliabilityMark({ playerScore: 42, isNew: false })).toBeUndefined();
  });
});

/**
 * **The three blocks, as one element** — and the three absences that do not move together.
 *
 * Player reliability is always there now (ADR-0195 §1), so its block is the one a newcomer
 * draws; the run and the count still come and go with the sport.
 */
describe('the record blocks, as one element', () => {
  const SERGIO = { playerScore: 75, band: 'HIGH', isNew: false } as const;

  it('reads left to right, and spells the scale and the band the figure alone could not', () => {
    expect(
      recordBlocksLabel({ reliability: SERGIO, lastFive: ['WIN', 'WIN', 'LOSS'], countedGames: 5 }),
    ).toBe('Player reliability 75 out of 100, High. 2 of the last 3 won. 5 counted games');
  });

  it('says New for a player who is new', () => {
    expect(
      recordBlocksLabel({ reliability: { playerScore: 100, band: 'VERY_HIGH', isNew: true } }),
    ).toBe('Player reliability 100 out of 100, New');
  });

  it('says nothing at all about a block it did not draw', () => {
    expect(recordBlocksLabel({ reliability: SERGIO })).toBe(
      'Player reliability 75 out of 100, High',
    );
    expect(recordBlocksLabel({ countedGames: 1 })).toBe('1 counted game');
    expect(recordBlocksLabel({})).toBe('');
  });

  /**
   * An empty run and an omitted one are one absence, exactly as they are at the mapper and in
   * the drawing: a run's length is a claim, so nought squares is nothing to say rather than
   * *0 of the last 0 won*.
   */
  it('treats an empty run as no run', () => {
    expect(recordBlocksLabel({ reliability: SERGIO, lastFive: [] })).toBe(
      recordBlocksLabel({ reliability: SERGIO }),
    );
  });
});

describe('the header, as one element', () => {
  /**
   * The nickname first, because that is the order the header draws — and nothing after it that
   * is not drawn: there is no handle line under the nickname
   * ([ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §1), and a
   * listener is told what a reader is shown.
   */
  it('leads with the nickname, and drops what is absent rather than speaking nothing', () => {
    expect(
      recordHeaderLabel({
        name: 'bea_k',
        onCourt: true,
        identity: 'In your area · 0,6 km',
        sports: ['Padel 2,75'],
      }),
    ).toBe('bea_k. Photo checked: on court. In your area · 0,6 km. Padel 2,75');

    expect(
      recordHeaderLabel({
        name: 'bea_k',
        onCourt: false,
        identity: '',
        sports: [],
      }),
    ).toBe('bea_k');
  });

  it('speaks the intro inside its marks, after the nickname and before where they are', () => {
    // The drawn order: the line sits under the nickname, so it is heard there too — as their own
    // words, which the quotation marks say, and never as a name (ADR-0170 §4).
    expect(
      recordHeaderLabel({
        name: 'bea_k',
        onCourt: false,
        intro: introLine('Will travel for a hard game.'),
        identity: '4,3 km',
        sports: ['Padel 2,75'],
      }),
    ).toBe('bea_k. “Will travel for a hard game.”. 4,3 km. Padel 2,75');
  });

  /**
   * ADR-0133's clause survives ADR-0138 untouched: the check's own confidence crosses on no
   * route, so there is nothing here to print a number from — and *nobody looked* and *checked
   * and flagged* both reach this function as `false` and say nothing at all.
   */
  it('says nothing about a photograph that was flagged or never checked', () => {
    expect(
      recordHeaderLabel({
        name: 'bea_k',
        onCourt: false,
        identity: '4,3 km',
        sports: [],
      }),
    ).toBe('bea_k. 4,3 km');
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
 * **The card's own words** — the four counts as the record serves them, over the last 6 months
 * (#660, ADR-0195 §1), and the two rows under them.
 */
describe('the record card', () => {
  /** Sergio's: turned up 12 of 13, kept 13 of 14, late once, nothing left in dispute. */
  const SERGIO: ReliabilityCounts = {
    turnedUp: 12,
    turnedUpOf: 13,
    late: 1,
    kept: 13,
    keptOf: 14,
    leftInDispute: 0,
  };

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
   * **Four counts, each in its own words and never a ratio** — the raw pair where there is an
   * *of*, a count where there is none, and no percentage anywhere: the figure is points, and
   * these are what it is read beside.
   */
  it('prints Shows up, Keeps plans, Being late and Results left in dispute as counts', () => {
    expect(countLines(SERGIO)).toEqual([
      { label: 'Shows up', value: 'turned up 12 of 13' },
      { label: 'Keeps plans', value: 'kept 13 of 14' },
      { label: 'Being late', value: 'late 1 time' },
      { label: 'Results left in dispute', value: '0' },
    ]);
  });

  it('counts being late through the one pluralisation helper', () => {
    const late = (times: number) =>
      countLines({ ...SERGIO, late: times }).find((line) => line.label === 'Being late')?.value;

    expect(late(0)).toBe('late 0 times');
    expect(late(2)).toBe('late 2 times');
  });

  /**
   * **The strands are gone, and so are their names.** *Answers about results* left the figure
   * with the rest (ADR-0195 §1) — silence on a score costs nothing — and no row may say it.
   */
  it('names no strand the figure no longer has', () => {
    const words = countLines(SERGIO)
      .map((line) => `${line.label} ${line.value}`)
      .join(' ');

    expect(words).not.toMatch(/Answers|Settles up|confirm|%/i);
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

  /** The card is one accessibility element: one clause per row, in the order they are drawn. */
  it('reaches a listener as one clause a row', () => {
    expect(
      recordCardLabel({ counts: SERGIO, variety: { distinctOpponents: 14, timesOnCourt: 20 } }),
    ).toBe(
      'Shows up, turned up 12 of 13. Keeps plans, kept 13 of 14. Being late, late 1 time. ' +
        'Results left in dispute, 0. Opponent variety, 70%, 14 of 20',
    );
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
    const spoken = recordCardLabel({ counts: SERGIO, opinion: { average: 4.7, raters: 17 } });

    expect(spoken).toMatch(
      new RegExp(`Results left in dispute, 0\\. ${SPORTSMANSHIP_LABEL}, 4,7 out of 5, 17 players$`),
    );
    expect(spoken).not.toContain('holds nobody back');
  });
});

/**
 * **The sportsmanship row's words**, and the one thing they must never say.
 *
 * A figure without its count is this field's one way of lying — `3,0 / 5` over one rater reads
 * as a settled fact about somebody — so the count is asserted inseparable. The second thing
 * this suite used to hold, that a figure about *yourself* is never drawn, is reversed: ADR-0179
 * §5 serves the subject the figure, and the band that stood in for it is retired
 * ([#473](https://github.com/Rakieta02/Rakieta/issues/473)) — so what is pinned now is that the
 * row has one reading, the figure's, and no word in it.
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

  /**
   * **One reading, and it is the figure's** — the row's label, then the average out of five and
   * the people it rests on, for a subject as for a stranger. The band this row used to speak
   * for the subject (*Good · Mixed · Poor*) is retired with the arm that carried it, so the
   * three words are spelled here only to be asserted absent: no export names them any more.
   */
  it('speaks the figure and its count for everybody, and never a band word', () => {
    const spoken = recordCardLabel({
      counts: { turnedUp: 0, turnedUpOf: 0, late: 0, kept: 0, keptOf: 0, leftInDispute: 0 },
      opinion: { average: 4.7, raters: 17 },
    });

    expect(spoken).toMatch(new RegExp(`${SPORTSMANSHIP_LABEL}, 4,7 out of 5, 17 players$`));
    expect(spoken).not.toMatch(/\b(Good|Mixed|Poor)\b/);
  });
});
