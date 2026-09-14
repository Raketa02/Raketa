/**
 * How this platform names a person.
 *
 * One rule, and it is ADR-0107's: **the whole handle, or nobody**. There is no name in this
 * platform to shorten, so the assertions are about what the formatter refuses to do — never a
 * first word, never an initial, never a truncation.
 *
 * `handleStem` beneath it is not an exception to that rule and the last suite says why: it
 * returns a **prefix of the handle somebody typed**, cut at a character they typed, for a box
 * to draw. What a sentence says is untouched.
 */

import { handleInitials, handleStem, playerName } from './playerName';

const LONG = 'niepokonany wojownik z warszawy grający wieczorami';

describe('naming one person', () => {
  it('is you, to yourself', () => {
    expect(playerName({ kind: 'you' })).toBe('You');
  });

  it('is the whole handle, however long', () => {
    // `Nickname` is 2 to 64 characters and `users` holds no name at all: inventing a first
    // name is the product addressing a person by a name they never gave it.
    expect(playerName({ kind: 'player', nickname: LONG })).toBe(LONG);
  });

  it('never takes the first word of one', () => {
    const name = playerName({ kind: 'player', nickname: LONG });

    expect(name).not.toBe('niepokonany');
    expect(name).not.toMatch(/…|\.\.\./);
  });

  it('leaves an empty seat a question mark, which is not a word', () => {
    expect(playerName({ kind: 'unknown' })).toBe('?');
  });
});

/**
 * **A prefix of the handle they typed, and never a name they did not.** ADR-0107 bites on
 * *inventing* a familiar form; cutting a handle at a character its owner put there invents
 * nothing, and it is drawn only where a box is drawing.
 */
describe('the handle a box draws', () => {
  it('cuts at the first dot or space, which is where a handle separates words', () => {
    expect(handleStem('Sergio.Sabater')).toBe('Sergio');
    expect(handleStem('Hugo Ferrer')).toBe('Hugo');
    expect(handleStem('Paula.Casals.Nadal')).toBe('Paula');
  });

  it('never cuts at a dash or an underscore, which live inside one word as often as between two', () => {
    // `bea_k` is four characters somebody chose, not `bea` with a suffix.
    expect(handleStem('bea_k')).toBe('bea_k');
    expect(handleStem('dorota_w')).toBe('dorota_w');
    expect(handleStem('anne-marie')).toBe('anne-marie');
  });

  it('leaves a handle with no break, and one that opens with one, entirely alone', () => {
    expect(handleStem('cyryl')).toBe('cyryl');
    // An empty stem is not a shorter name; it is no name, and there is nothing to draw.
    expect(handleStem('.leading')).toBe('.leading');
  });

  it('leaves what a sentence says untouched — the two are different registers', () => {
    const whole = 'Sergio.Sabater';

    expect(playerName({ kind: 'player', nickname: whole })).toBe(whole);
  });
});

/**
 * **Two initials over a poster, and nowhere else** —
 * [ADR-0167](../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
 * §3's one exception to the rule the suites above hold. It is a drawing and never a sentence: the
 * cut is tested here, and that no sentence carries it is the yes screen's own suite's to hold.
 */
describe('the initials a poster draws', () => {
  it('takes the first letter of each word, split where a handle separates words, at most two', () => {
    expect(handleInitials('Tomek.K')).toBe('TK');
    expect(handleInitials('Marek Z.')).toBe('MZ');
    expect(handleInitials('Ola.N')).toBe('ON');
    expect(handleInitials('Paula.Casals.Nadal')).toBe('PC');
  });

  it('takes the first two characters of a one-word handle, because a dash or an underscore is inside a word', () => {
    expect(handleInitials('dorota_w')).toBe('DO');
    expect(handleInitials('anne-marie')).toBe('AN');
    expect(handleInitials('cyryl')).toBe('CY');
  });

  it('gives a one-character handle its one', () => {
    expect(handleInitials('x')).toBe('X');
  });

  it('keeps what follows a break a handle opens with, rather than an initial for nothing', () => {
    // `.leading` is one word once the empty part is dropped; `.tomek.k` is two.
    expect(handleInitials('.leading')).toBe('LE');
    expect(handleInitials('.tomek.k')).toBe('TK');
  });

  it('upper-cases for drawing only, and leaves the handle a sentence says untouched', () => {
    expect(handleInitials('ewa.m')).toBe('EM');
    expect(playerName({ kind: 'player', nickname: 'ewa.m' })).toBe('ewa.m');
  });
});
