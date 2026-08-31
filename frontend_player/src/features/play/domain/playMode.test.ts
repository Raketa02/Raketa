import { modeForIntent, MODE_WITHOUT_A_DECLARATION } from './playMode';

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
