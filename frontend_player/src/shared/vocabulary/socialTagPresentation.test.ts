/**
 * The words on a Social tag, without a renderer.
 *
 * The labels are copy and copy changes; what these hold is the two things that must not.
 * Every id this build can draw has words, and no two ids share the same ones — two chips
 * reading alike are two choices a player cannot tell apart, and two reason lines reading
 * alike are two facts a player cannot tell apart either.
 */

import { socialTagGroupHeading, socialTagLabel, socialTagName } from './socialTagPresentation';
import { SOCIAL_TAG_GROUP_IDS, SOCIAL_TAG_IDS } from './socialTags';

describe('what a tag is called', () => {
  it('gives every id this build can draw its own words', () => {
    // A tag added without copy fails here rather than shipping as a chip with nothing on it.
    const labels = SOCIAL_TAG_IDS.map(socialTagLabel);

    expect(labels.every((label) => label.length > 0)).toBe(true);
    expect(new Set(labels).size).toBe(SOCIAL_TAG_IDS.length);
  });

  it('gives every group a heading naming what it is about', () => {
    const headings = SOCIAL_TAG_GROUP_IDS.map(socialTagGroupHeading);

    expect(headings).toEqual(['After the match', 'On the court', "Why you're here"]);
  });
});

describe('drawn with a glyph, spoken and written without one', () => {
  it('carries the emoji on the chip and never in the words', () => {
    expect(socialTagLabel('PLAYS_TO_WIN')).toBe('🏆 Plays to win');
    expect(socialTagName('PLAYS_TO_WIN')).toBe('Plays to win');
  });

  it('leaves every spoken name free of the glyph its chip draws', () => {
    // A reason line naming two tags is prose, and prose does not carry glyphs — the same
    // rule that keeps a screen reader from reading the app's layout aloud.
    for (const tagId of SOCIAL_TAG_IDS) {
      expect(socialTagLabel(tagId).endsWith(socialTagName(tagId))).toBe(true);
      expect(socialTagName(tagId)).toMatch(/^[A-Za-z]/);
    }
  });
});
