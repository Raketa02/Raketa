/**
 * The Social vibe's bands — one word and one tone per range (ADR-0207 §8, #838).
 *
 * Three rules are asserted. **Every boundary lands in its band**, both sides of each break. **The
 * tones are one hue family**, never the forecast's green / amber / red. And **the row's spoken name**
 * is the name, the figure in words, then the band's word.
 */

import { balanceTone } from './balancePresentation';
import { socialVibeBand, socialVibeSpoken } from './socialVibePresentation';

describe('the bands', () => {
  it.each([
    [100, 'Great vibe', 'volt'],
    [70, 'Great vibe', 'volt'],
    [69, 'Good vibe', 'volt'],
    [45, 'Good vibe', 'volt'],
    [44, 'Some common ground', 'dimVolt'],
    [20, 'Some common ground', 'dimVolt'],
    [19, 'Fresh mix', 'grey'],
    [0, 'Fresh mix', 'grey'],
  ] as const)('reads %i%% as %s, in %s', (pct, word, tone) => {
    expect(socialVibeBand(pct)).toEqual({ word, tone });
  });

  it('gives every percentage a word, because the tone is not allowed to be the only cue', () => {
    for (let pct = 0; pct <= 100; pct += 1) expect(socialVibeBand(pct).word).not.toBe('');
  });

  it('never borrows the forecast’s green, amber or red', () => {
    const forecastTones: readonly string[] = [balanceTone(100), balanceTone(60), balanceTone(0)];
    for (let pct = 0; pct <= 100; pct += 1) {
      expect(forecastTones).not.toContain(socialVibeBand(pct).tone);
    }
  });
});

describe('the row’s spoken name', () => {
  it('is the name, the figure in words, then the band’s word', () => {
    expect(socialVibeSpoken(82)).toBe('Social vibe, 82 percent, Great vibe');
    expect(socialVibeSpoken(35)).toBe('Social vibe, 35 percent, Some common ground');
    expect(socialVibeSpoken(0)).toBe('Social vibe, 0 percent, Fresh mix');
  });
});
