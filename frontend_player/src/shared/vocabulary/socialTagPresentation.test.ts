/**
 * The words on a Social tag, without a renderer.
 *
 * The labels are copy and copy changes; what these hold is the two things that must not.
 * Every id this build can draw has words, and no two ids share the same ones — two chips
 * reading alike are two choices a player cannot tell apart, and two reason lines reading
 * alike are two facts a player cannot tell apart either.
 *
 * The Social tag row's own three words are asserted here too, and the assertion is the split
 * between the two registers: the chip carries a glyph and a per-tag marker, and the clause a
 * listener gets carries neither — that half is the drawing surface's and stays with it
 * ([#311](https://github.com/Raketa02/Raketa/issues/311)).
 */

import {
  NO_TAGS_IN_COMMON,
  socialTagChip,
  socialTagGroupHeading,
  socialTagLabel,
  socialTagName,
  thingsInCommon,
} from './socialTagPresentation';
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

describe('the social tag row’s words', () => {
  it('draws the tag with its glyph, and the marker only where it is shared', () => {
    expect(socialTagChip({ id: 'PLAYS_TO_WIN', shared: true })).toBe('🏆 Plays to win · you too');
    expect(socialTagChip({ id: 'PLAYS_TO_WIN', shared: false })).toBe('🏆 Plays to win');
  });

  it('states the one claim the row makes, and never accuses anybody of it', () => {
    // Amber's register: *watch this, reversible, not yet wrong*. Nobody has done anything
    // wrong by having different tags, so the sentence names the absence and stops there.
    expect(NO_TAGS_IN_COMMON).toBe('No tags in common');
  });
});

describe('how many tags two players share (§31.8, §31.10)', () => {
  it('counts things in common, one in the singular', () => {
    expect(thingsInCommon(6)).toBe('6 things in common');
    expect(thingsInCommon(2)).toBe('2 things in common');
    expect(thingsInCommon(1)).toBe('1 thing in common');
  });
});
