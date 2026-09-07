import {
  declarationAgreesWithMode,
  declarationNamesAKind,
  intentForMode,
  modeForIntent,
  MODE_WITHOUT_A_DECLARATION,
} from './playMode';
import { SEARCH_MODES } from './vocabulary';

describe('the mode Play opens in', () => {
  it('takes the declaration where there is one', () => {
    expect(modeForIntent('COMPETITIVE')).toBe('COMPETITIVE');
    expect(modeForIntent('FOR_FUN')).toBe('FOR_FUN');
  });

  it('reads NO_PREFERENCE as for fun — indifference is not a third kind of evening', () => {
    expect(modeForIntent('NO_PREFERENCE')).toBe('FOR_FUN');
  });

  it('opens for fun with no declaration at all, the same as indifference', () => {
    expect(MODE_WITHOUT_A_DECLARATION).toBe('FOR_FUN');
  });
});

describe('the declaration a drift prompt offers', () => {
  it('is the mode the searches kept choosing', () => {
    expect(intentForMode('COMPETITIVE')).toBe('COMPETITIVE');
    expect(intentForMode('FOR_FUN')).toBe('FOR_FUN');
  });

  it('never offers indifference, which the drift never observed', () => {
    // Five searches in one mode is evidence of a preference. `modeForIntent` collapses
    // three values into two and cannot be run backwards to produce the third.
    expect(SEARCH_MODES.map(intentForMode)).not.toContain('NO_PREFERENCE');
  });
});

describe('when a search and a declaration disagree', () => {
  it('agrees where the mode is the declaration', () => {
    expect(declarationAgreesWithMode('COMPETITIVE', 'COMPETITIVE')).toBe(true);
    expect(declarationAgreesWithMode('FOR_FUN', 'FOR_FUN')).toBe(true);
  });

  it('disagrees where it is the other one', () => {
    expect(declarationAgreesWithMode('COMPETITIVE', 'FOR_FUN')).toBe(false);
    expect(declarationAgreesWithMode('FOR_FUN', 'COMPETITIVE')).toBe(false);
  });

  /**
   * The rule the backend's own drift loop applies — *"`NO_PREFERENCE` agrees with **both**"* —
   * read here rather than written a second time. Somebody who said either kind of evening suits
   * them has said nothing a search can contradict, so the line never offers to narrow it off
   * evidence of nothing.
   */
  it('is contradicted by no search at all where either suits them', () => {
    expect(SEARCH_MODES.every((mode) => declarationAgreesWithMode('NO_PREFERENCE', mode))).toBe(
      true,
    );
  });
});

describe('what a declaration is on a surface with no mode', () => {
  it('names a kind of evening where the answer was one of the two', () => {
    expect(declarationNamesAKind('COMPETITIVE')).toBe(true);
    expect(declarationNamesAKind('FOR_FUN')).toBe(true);
  });

  /**
   * The deck deals a `NO_PREFERENCE` player on `modeForIntent`'s **inherited** for-fun vector,
   * and the two are not the same fact: ADR-0094's *"indifference about the kind of evening is
   * not a third kind of evening"* is exactly what makes reporting the inheritance back as the
   * player's own answer a lie the sentence has to avoid.
   */
  it('names none where either suits them, whatever the deal inherits', () => {
    expect(declarationNamesAKind('NO_PREFERENCE')).toBe(false);
    expect(modeForIntent('NO_PREFERENCE')).toBe('FOR_FUN');
  });
});
