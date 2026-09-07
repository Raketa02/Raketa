import { PLAY_INTENTS } from './playIntent';
import { declarationOptionLabel, intentGloss, intentLabel } from './playIntentPresentation';

describe('the words for a declaration', () => {
  /**
   * The arity gap is ADR-0094's central move and it is visible in the copy: a search is
   * competitive or for fun, and a *player* may also say that either kind of evening suits them.
   * `NO_PREFERENCE`'s label says something rather than declining to.
   */
  it('gives all three an answer a player would recognise', () => {
    expect(intentLabel('COMPETITIVE')).toBe('Competitive');
    expect(intentLabel('FOR_FUN')).toBe('For fun');
    expect(intentLabel('NO_PREFERENCE')).toBe('Either suits me');
  });

  it('glosses each of them in one line, and never repeats the label', () => {
    for (const intent of PLAY_INTENTS) {
      expect(intentGloss(intent)).not.toBe('');
      expect(intentGloss(intent)).not.toContain('\n');
      expect(intentGloss(intent)).not.toBe(intentLabel(intent));
    }
  });

  /**
   * *Your usual* is the app's own phrase for the durable value, and the lifetime is the whole
   * of the name: `Competitive` is a mode on one screen and a declaration on two, and only this
   * clause tells a listener which one they are on.
   */
  it('announces an answer by its lifetime, not by the heading above it', () => {
    expect(declarationOptionLabel('COMPETITIVE', 'Padel')).toBe('Competitive, your usual at Padel');
    expect(declarationOptionLabel('NO_PREFERENCE', 'Tennis')).toBe(
      'Either suits me, your usual at Tennis',
    );
  });
});
