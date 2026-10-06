/**
 * The words on the gender step, and the one of them that is a **requirement** rather than
 * copy.
 *
 * Nothing here is evidence — there is no version identifier, and re-wording any of it makes
 * nothing that was true yesterday false. What is
 * pinned instead is the *shape* of the mutuality note: that a narrowed preference always
 * produces one, that it names **both** directions, and that an unconstrained one produces
 * none at all.
 *
 * That last one is not pedantry. A screen that reassured a player about a consequence they
 * had not chosen would be talking about something that is not happening; and a note that
 * mentioned only the direction the player asked for — *you will not be matched with men* —
 * would leave out the half that decides whether their inbox is quiet next week, which is
 * precisely the failure mutuality was chosen to prevent
 * ([ADR-0096](../../../../../docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)).
 */

import { GENDERS, GENDER_PREFERENCES, reachOf } from '../domain/gender';

import { genderLabel, preferenceLabel, reachNote } from './genderPresentation';

describe('the labels', () => {
  it('gives every answer words, so no control can render blank', () => {
    for (const gender of GENDERS) expect(genderLabel(gender).length).toBeGreaterThan(0);
    for (const preference of GENDER_PREFERENCES) {
      expect(preferenceLabel(preference).length).toBeGreaterThan(0);
    }
  });

  it('says the answers plainly rather than in a euphemism', () => {
    // The engine's third refusal is that it never produces something it cannot explain in
    // one sentence, and a softened label here would be the product being embarrassed about
    // a question it decided to ask.
    expect(genderLabel('woman')).toBe('Woman');
    expect(genderLabel('man')).toBe('Man');
    expect(genderLabel('prefer-not-to-say')).toBe('Prefer not to say');
  });
});

describe('what narrowing costs, said at the moment of setting', () => {
  it('says nothing at all when nothing is narrowed', () => {
    expect(reachNote(reachOf('any'))).toBeUndefined();
  });

  it('names both directions for a narrowed preference', () => {
    // The half the player asked for, and the half they did not: setting *women only* also
    // hides them from every man, including men who searched for anybody. One without the
    // other is the browse filter this design was written in reaction to.
    const women = reachNote(reachOf('women-only')) ?? '';

    expect(women).toContain('not be matched with men');
    expect(women).toContain('men will not see you');

    const men = reachNote(reachOf('men-only')) ?? '';

    expect(men).toContain('not be matched with women');
    expect(men).toContain('women will not see you');
  });

  it('produces a note for every preference that narrows, and only for those', () => {
    // Written against the vocabulary rather than against the two values, so a fourth
    // preference added one day arrives here with no sentence and reddens this file rather
    // than shipping a silent narrowing.
    for (const preference of GENDER_PREFERENCES) {
      const reach = reachOf(preference);
      const note = reachNote(reach);

      expect(note === undefined).toBe(reach.kind === 'unconstrained');
    }
  });
});
