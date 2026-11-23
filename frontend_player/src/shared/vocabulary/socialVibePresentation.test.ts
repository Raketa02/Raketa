/**
 * The Social vibe's bands — one word and one tone per range (ADR-0207 §8, #838).
 *
 * Three rules are asserted. **Every boundary lands in its band**, both sides of each break. **The
 * tones are one hue family**, never the forecast's green / amber / red. And **the row's spoken name**
 * is the name, the figure in words, then the band's word.
 */

import { balanceTone } from './balancePresentation';
import {
  SOCIAL_VIBE_YOU,
  socialVibeBand,
  socialVibeColumnName,
  socialVibeRowSpoken,
  socialVibeSpoken,
} from './socialVibePresentation';

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

/**
 * The Social vibe card's rows, spoken (#840; ADR-0207 §6): *{tag}: you, {names}* — the tag's words
 * without its emoji, then everybody who carries it, you first, each nickname whole.
 */
describe('a row of the Social vibe card, spoken', () => {
  const you = { isYou: true } as const;

  it('says the tag, then you, then the others who carry it', () => {
    expect(socialVibeRowSpoken('STAYS_FOR_A_DRINK', [you, { isYou: false, name: 'kuba.w' }])).toBe(
      'Stays for a drink: you, kuba.w',
    );
    expect(
      socialVibeRowSpoken('HERE_TO_IMPROVE', [
        you,
        { isYou: false, name: 'filip.n' },
        { isYou: false, name: 'kuba.w' },
      ]),
    ).toBe('Here to improve: you, filip.n, kuba.w');
  });

  it('says you alone on a row only you carry, and 💘 like any other', () => {
    expect(socialVibeRowSpoken('HERE_FOR_A_REGULAR_GAME', [you])).toBe(
      'Here for a regular game: you',
    );
    expect(
      socialVibeRowSpoken('OPEN_TO_MEET_SOMEONE', [you, { isYou: false, name: 'ania.k' }]),
    ).toBe('Open to meet someone: you, ania.k');
  });

  it('says somebody for an account that can no longer be named', () => {
    expect(socialVibeRowSpoken('SHARES_A_LIFT', [you, { isYou: false }])).toBe(
      'Shares a lift: you, somebody',
    );
  });

  it('heads your column You, the others by their nickname whole, an unnamed one ?', () => {
    expect(SOCIAL_VIBE_YOU).toBe('You');
    expect(socialVibeColumnName(you)).toBe('You');
    expect(socialVibeColumnName({ isYou: false, name: 'magdalena.pietrzak' })).toBe(
      'magdalena.pietrzak',
    );
    expect(socialVibeColumnName({ isYou: false })).toBe('?');
  });
});
