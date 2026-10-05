/**
 * What Games & money says (the screens A7, A7.1; mocks 37–39): the row's line and the bound under
 * the two cards say the same limits, the games line turns singular at one, and the ceiling's line
 * names the price it hides above.
 */

import {
  boundText,
  ceilingChipLabel,
  ceilingLine,
  gamesAndMoneyRowLine,
  gamesLine,
  gamesSpoken,
  rangeLine,
} from './gamesAndMoneyCopy';

describe('the row on the You tab', () => {
  it('says the games a week, as mock 37 does', () => {
    expect(gamesAndMoneyRowLine({ gamesPerWeek: 4, mostIllPayGrosze: null })).toBe(
      'At most 4 games a week',
    );
    expect(gamesAndMoneyRowLine({ gamesPerWeek: 1, mostIllPayGrosze: null })).toBe(
      'At most 1 game a week',
    );
  });

  it('repeats the week’s money bound once a ceiling is set', () => {
    expect(gamesAndMoneyRowLine({ gamesPerWeek: 4, mostIllPayGrosze: 4500 })).toBe(
      'At most 4 games a week · up to 180 zł',
    );
  });
});

describe('the bound under the cards', () => {
  it('is the games alone while the ceiling is off', () => {
    expect(boundText({ gamesPerWeek: 4, mostIllPayGrosze: null })).toBe(
      'Your bound: at most 4 games a week.',
    );
  });

  it('adds the money with a ceiling, and turns singular at one', () => {
    expect(boundText({ gamesPerWeek: 4, mostIllPayGrosze: 4500 })).toBe(
      'Your bound: at most 4 games · up to 180 zł a week.',
    );
    expect(boundText({ gamesPerWeek: 1, mostIllPayGrosze: 3500 })).toBe(
      'Your bound: at most 1 game · up to 35 zł a week.',
    );
  });
});

describe('the games per week card', () => {
  it('names the range the server offers', () => {
    expect(rangeLine({ least: 1, most: 7 })).toBe('Mon–Sun · 1 to 7');
  });

  it('says what the cap does, singular at one', () => {
    expect(gamesLine(4)).toBe(
      'Once they are booked, your other yeses that week pause — they come back if a game is called off.',
    );
    expect(gamesLine(1)).toBe(
      'Once it is booked, your other yeses that week pause — they come back if the game is called off.',
    );
  });

  it('speaks the value with its unit', () => {
    expect(gamesSpoken(4)).toBe('4 games a week');
    expect(gamesSpoken(1)).toBe('1 game a week');
  });
});

describe('the most I’ll pay card', () => {
  it('draws Off and each ceiling in złoty', () => {
    expect(ceilingChipLabel(null)).toBe('Off');
    expect(ceilingChipLabel(3500)).toBe('35 zł');
  });

  it('says every card is shown while off, and which are hidden once set', () => {
    expect(ceilingLine(null)).toBe('Every card is shown, whatever its share.');
    expect(ceilingLine(4500)).toBe('Cards above 45 zł are never shown to you.');
  });
});
