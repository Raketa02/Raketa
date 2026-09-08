/**
 * **The sheet's words**, and the four claims a build session could quietly undo.
 *
 * Most of these are about a sentence that must **not** be written: no place name from an area
 * code, no distance about yourself, no claim of nothing-in-common out of the app's own
 * ignorance, and no figure the run of five did not actually count.
 */

import type { SocialTagOverlap } from '@/shared/vocabulary/socialTagOverlap';

import {
  IN_YOUR_AREA,
  OWN_RECORD_TITLE,
  RECORD_TITLE,
  YOU_MARK,
  fitRowLabel,
  fitRowTitle,
  identityLine,
  lastFiveReading,
  recordCloseLabel,
  recordHandle,
  recordHeaderLabel,
  skillCardLabel,
  skillHeadline,
  socialTagsLabel,
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
