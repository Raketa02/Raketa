/**
 * The deck card's own copy, held to the decisions in it: the third clause is a liveness code's
 * existing words and is drawn only on the code, the tiles are always three with a dash and never
 * a nought for an absence, and the intro is the person's line inside the card's marks.
 */

import { livenessLine } from './livenessPresentation';
import {
  AROUND_THIS_WEEK_CLAUSE,
  NO_VALUE,
  deckMetaLine,
  deckTileClauses,
  deckTiles,
  quotedIntro,
} from './deckCardPresentation';

const HERE = 'A+050612+0019938';

describe('the meta line', () => {
  it('adds *around this week* after the kilometres when the deal said so', () => {
    expect(
      deckMetaLine({ km: 1.9, theirAreaCode: HERE, myAreaCode: HERE, aroundThisWeek: true }),
    ).toBe('In your area · 1,9 km · around this week');
    expect(deckMetaLine({ km: 7.2, theirAreaCode: HERE, aroundThisWeek: true })).toBe(
      '7,2 km · around this week',
    );
  });

  it('says nothing about the week when the code is absent — never *active now*', () => {
    const line = deckMetaLine({
      km: 1.9,
      theirAreaCode: HERE,
      myAreaCode: HERE,
      aroundThisWeek: false,
    });

    expect(line).toBe('In your area · 1,9 km');
    expect(line).not.toMatch(/active|today|now/);
  });

  /**
   * ADR-0107 §3 stands: the clause is `RECENT_ACTIVITY`'s own un-datable words, drawn only on the
   * code — derived from the reason list's sentence so a re-wording of one moves the other, and
   * lower-cased only because it sits after a middle dot.
   */
  it('is the liveness code’s existing words, lower-cased for mid-line', () => {
    expect(AROUND_THIS_WEEK_CLAUSE).toBe(livenessLine('RECENT_ACTIVITY').toLowerCase());
    expect(AROUND_THIS_WEEK_CLAUSE).toBe('around this week');
  });

  /** The week is the liveness code's and does not stand down with the distance term. */
  it('says the week alone, in the code’s own words, where the distance stood down', () => {
    expect(deckMetaLine({ theirAreaCode: HERE, myAreaCode: HERE, aroundThisWeek: true })).toBe(
      livenessLine('RECENT_ACTIVITY'),
    );
    expect(
      deckMetaLine({ theirAreaCode: HERE, myAreaCode: HERE, aroundThisWeek: false }),
    ).toBeUndefined();
  });
});

describe('the intro', () => {
  it('is quoted with typographic marks, as the person’s own words', () => {
    expect(quotedIntro('Will travel for a hard game.')).toBe('“Will travel for a hard game.”');
  });
});

describe('the three tiles', () => {
  it('prints every figure in its own format, in one order', () => {
    expect(
      deckTiles({ balancePct: 72.4, playerScore: 88, sharedSlots: 9 }).map((tile) => [
        tile.label,
        tile.value,
      ]),
    ).toEqual([
      ['Balance', '72%'],
      ['Reliability', '88'],
      ['Overlap', '9 slots'],
    ]);
  });

  /** The row of tags above the tiles already leads with the shared ones; a count of them went. */
  it('has no Shared tags tile', () => {
    expect(deckTiles({}).map((tile) => tile.label)).not.toContain('Shared tags');
  });

  it('counts one slot without an s', () => {
    expect(deckTiles({ sharedSlots: 1 })[2]?.value).toBe('1 slot');
  });

  /** The row stays three: an absent number is a dash in place, never a missing tile. */
  it('is always three, with a dash where a number is absent', () => {
    const tiles = deckTiles({});

    expect(tiles).toHaveLength(3);
    expect(tiles.map((tile) => tile.value)).toEqual([NO_VALUE, NO_VALUE, NO_VALUE]);
    expect(NO_VALUE).toBe('—');
  });

  /** A nought is a figure and a dash is not: a measured zero prints, an absence does not. */
  it('prints a measured nought rather than a dash', () => {
    const tiles = deckTiles({ sharedSlots: 0, playerScore: 0 });

    expect(tiles[2]?.value).toBe('0 slots');
    expect(tiles[1]?.value).toBe('0');
  });

  it('speaks the tiles that have a figure and skips the dashes', () => {
    expect(deckTileClauses(deckTiles({ balancePct: 72, sharedSlots: 2 }))).toEqual([
      'Balance 72%',
      'Overlap 2 slots',
    ]);
  });
});
