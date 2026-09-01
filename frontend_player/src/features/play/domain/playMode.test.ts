import { intentForMode, modeForIntent, MODE_WITHOUT_A_DECLARATION } from './playMode';
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
