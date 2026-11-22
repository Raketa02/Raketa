/**
 * **Which served tag ids this build can draw** — the twenty-seven, and nothing it has no words for
 * ([ADR-0207](../../../../docs/adr/0207-for-fun-is-built-by-shared-social-tags-and-every-for-fun-game-carries-a-social-vibe.md)
 * §7: *an app that doesn't know a tag code skips it, and never crashes*).
 *
 * `toSocialTagId` is the one narrowing the record and Same vibe's tiles and sheet go through, where
 * the wire spells a tag as a plain string; the picker's own mapper keeps a typed twin.
 */

import { SOCIAL_TAG_IDS, toSocialTagId } from './socialTags';

describe('the vocabulary this build knows', () => {
  it('is twenty-seven ids, each once', () => {
    expect(SOCIAL_TAG_IDS).toHaveLength(27);
    expect(new Set(SOCIAL_TAG_IDS).size).toBe(27);
  });

  it('knows the eight added at the end of their groups', () => {
    for (const served of [
      'STAYS_FOR_A_COFFEE',
      'UP_FOR_A_BITE_AFTER',
      'KEEPS_IN_TOUCH',
      'HAPPY_TO_SWAP_PARTNERS',
      'PATIENT_WITH_BEGINNERS',
      'HAPPY_TO_SHARE_TIPS',
      'BRINGS_THE_ENERGY',
      'NEW_IN_TOWN',
    ]) {
      expect(toSocialTagId(served)).toBe(served);
    }
  });
});

describe('a served id this build has no words for', () => {
  it('is skipped, never guessed at and never thrown over', () => {
    // A phone that has not been updated is served a tag minted after it shipped.
    expect(toSocialTagId('CALLS_THE_SCORE_OUT_LOUD')).toBeUndefined();
    expect(toSocialTagId('')).toBeUndefined();
    expect(toSocialTagId('new_in_town')).toBeUndefined();
  });

  it('leaves the rest of a list standing, in the served order', () => {
    const served = ['NEW_IN_TOWN', 'SINGS_IN_THE_CAR', 'STAYS_FOR_A_COFFEE'];

    expect(served.flatMap((tag) => toSocialTagId(tag) ?? [])).toEqual([
      'NEW_IN_TOWN',
      'STAYS_FOR_A_COFFEE',
    ]);
  });
});
