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
  OWN_RECORD_TITLE,
  RECORD_CARD_TITLE,
  RECORD_CARD_TITLE_DRAWN,
  RECORD_TITLE,
  STRAND_NAME,
  YOU_MARK,
  fitRowLabel,
  fitRowTitle,
  identityLine,
  lastFiveReading,
  recordCloseLabel,
  recordCardLabel,
  recordHandle,
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

describe('the sheet’s two titles', () => {
  it('says whose view this is, and the close control says what it closes', () => {
    expect(recordCloseLabel(false)).toBe(`Close ${RECORD_TITLE.toLowerCase()}`);
    expect(recordCloseLabel(true)).toBe(`Close ${OWN_RECORD_TITLE.toLowerCase()}`);
  });

  it('marks your own handle rather than replacing it', () => {
    expect(recordHandle('bea_k', true)).toBe(`bea_k ${YOU_MARK}`);
    expect(recordHandle('bea_k', false)).toBe('bea_k');
  });
});

describe('the skill card’s three inseparable figures', () => {
  it('is one run, in one order, with the counted figure beside the confidence', () => {
    expect(
      skillHeadline({ sportName: 'Padel', level: 2.75, confidence: 77, countedGames: 21 }),
    ).toBe('PADEL · 2,75 · 77% sure · 21 counted');
  });

  it('says a run of three is out of three, because the gap is the honest statement', () => {
    expect(lastFiveReading(['WIN', 'LOSS', 'WIN'])).toBe('2 of the last 3 won');
    expect(lastFiveReading(['WIN', 'WIN', 'LOSS', 'WIN', 'WIN'])).toBe('4 of the last 5 won');
  });

  it('leaves the run out of the spoken card entirely where there is none', () => {
    const facts = {
      sportName: 'Padel',
      level: 2.75,
      band: 'Established',
      confidence: 77,
      countedGames: 21,
      likelyRange: { low: 2.47, high: 3.03 },
    };

    expect(skillCardLabel(facts)).toBe(
      'Padel. Level 2,75, Established. 77% sure. 21 counted games. Likely 2,47 – 3,03',
    );
    expect(skillCardLabel({ ...facts, lastFive: [] })).toBe(skillCardLabel(facts));
  });
});

describe('the header, as one element', () => {
  it('leads with the handle and drops what is absent rather than speaking nothing', () => {
    expect(
      recordHeaderLabel({
        handle: 'bea_k',
        onCourt: true,
        identity: 'In your area · 4 km',
        sports: ['Padel 2,75'],
        playerScore: 93,
      }),
    ).toBe(
      'bea_k. Photo checked: on court. In your area · 4 km. Padel 2,75. Player Score 93 out of 100',
    );

    expect(recordHeaderLabel({ handle: 'bea_k', onCourt: false, identity: '', sports: [] })).toBe(
      'bea_k',
    );
  });

  /**
   * ADR-0133's clause survives ADR-0138 untouched: the check's own confidence crosses on no
   * route, so there is nothing here to print a number from — and *nobody looked* and *checked
   * and flagged* both reach this function as `false` and say nothing at all.
   */
  it('says nothing about a photograph that was flagged or never checked', () => {
    expect(
      recordHeaderLabel({ handle: 'bea_k', onCourt: false, identity: '4 km', sports: [] }),
    ).toBe('bea_k. 4 km');
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

describe('the pairing row', () => {
  /** The visible name carries the ✦ and the spoken one must not — §20.6's one exception. */
  it('keeps the glyph out of what is spoken', () => {
    expect(fitRowTitle(78)).toContain('✦');
    expect(fitRowLabel(78)).not.toContain('✦');
    expect(fitRowLabel(78).startsWith('Why fit 78')).toBe(true);
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
   * **The heading is the rule, not a label.** It is the sentence the whole card is answerable
   * for, so it is asserted rather than left to whoever edits the file next — and it is spoken
   * in sentence case, because a run of capitals reaches some engines as letters.
   */
  it('is headed with the rule it enforces, drawn in caps and spoken in words', () => {
    expect(RECORD_CARD_TITLE).toBe('The record — counted by the system, not written by people');
    expect(RECORD_CARD_TITLE_DRAWN).toBe(RECORD_CARD_TITLE.toUpperCase());
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
    expect(varietyValue({ distinctOpponents: 14, gamesPlayed: 20 })).toBe('70% · 14 of 20');
  });

  it('writes the share as a whole percentage, through the app’s one formatter', () => {
    expect(varietyValue({ distinctOpponents: 2, gamesPlayed: 3 })).toBe('67% · 2 of 3');
  });

  /**
   * The card is one accessibility element: the heading leads, one clause per row follows, and
   * **no bar is in it** — every meter draws a fraction spoken two words earlier.
   */
  it('reaches a listener as the heading and one clause a row', () => {
    expect(
      recordCardLabel({
        rows: [row(), row({ strand: 'ANSWERS_RESULTS', good: 8, opportunities: 10, pct: 80 })],
        variety: { distinctOpponents: 14, gamesPlayed: 20 },
      }),
    ).toBe(
      `${RECORD_CARD_TITLE}. Shows up, 9 of 9. Answers about results, 8 of 10. ` +
        'Opponent variety, 70%, 14 of 20',
    );
  });

  /** A card with one row is one clause. Nothing is spoken as absent. */
  it('says nothing about a row it was not given', () => {
    expect(recordCardLabel({ rows: [row()] })).toBe(`${RECORD_CARD_TITLE}. Shows up, 9 of 9`);
  });
});
