/**
 * How this platform names a person.
 *
 * One rule, and it is ADR-0107 §4's read through
 * [ADR-0171](../../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md):
 * **the whole name, or nobody**. The name is free text the player typed — *Ania Kowalska*,
 * *Diego* — and the assertions are about what the formatter refuses to do with it: never a
 * first word, never an initial, never a truncation, and never the nickname.
 *
 * `handleStem` beneath it is not an exception to that rule and the second suite says why: it
 * returns a **prefix of the name somebody typed**, cut at a character they typed, for a box to
 * draw. What a sentence says is untouched.
 */

import { atNickname, handleInitials, handleStem, playerName } from './playerName';

const LONG = 'Niepokonany Wojownik z Warszawy grający wieczorami';

describe('naming one person', () => {
  it('is you, to yourself', () => {
    expect(playerName({ kind: 'you' })).toBe('You');
  });

  it('is the whole name, however long', () => {
    // `Name` is 2 to 64 characters of whatever the player wants to be called. Inventing a
    // first name is the product addressing a person by a name they never gave it.
    expect(playerName({ kind: 'player', name: LONG })).toBe(LONG);
  });

  it('never takes the first word of one', () => {
    const name = playerName({ kind: 'player', name: LONG });

    expect(name).not.toBe('Niepokonany');
    expect(name).not.toMatch(/…|\.\.\./);
  });

  it('leaves an empty seat a question mark, which is not a word', () => {
    expect(playerName({ kind: 'unknown' })).toBe('?');
  });
});

/**
 * **A prefix of the name they typed, and never a name they did not.** ADR-0107 bites on
 * *inventing* a familiar form; cutting a name at a character its owner put there invents
 * nothing, and it is drawn only where a box is drawing. That the stem of *Diego Fabregat* is
 * what a first name looks like is the point ADR-0171 §4 makes: it is still not an invented one.
 */
describe('the stem a box draws', () => {
  it('cuts at the first space or dot, which is where a name separates words', () => {
    expect(handleStem('Diego Fabregat')).toBe('Diego');
    expect(handleStem('Sergio.Sabater')).toBe('Sergio');
    expect(handleStem('Paula Casals Nadal')).toBe('Paula');
  });

  it('never cuts at a dash or an underscore, which live inside one word as often as between two', () => {
    // `Anne-Marie` is one word somebody chose, not `Anne` with a suffix.
    expect(handleStem('Anne-Marie')).toBe('Anne-Marie');
    expect(handleStem('dorota_w')).toBe('dorota_w');
  });

  it('leaves a name with no break, and one that opens with one, entirely alone', () => {
    expect(handleStem('Dieguito')).toBe('Dieguito');
    // An empty stem is not a shorter name; it is no name, and there is nothing to draw.
    expect(handleStem('.leading')).toBe('.leading');
  });

  it('leaves what a sentence says untouched — the two are different registers', () => {
    const whole = 'Diego Fabregat';

    expect(playerName({ kind: 'player', name: whole })).toBe(whole);
  });
});

/**
 * **Two initials over a poster, and nowhere else** —
 * [ADR-0167](../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
 * §3's one exception to the rule the suites above hold, cut from the name since ADR-0171. It is
 * a drawing and never a sentence: the cut is tested here, and that no sentence carries it is the
 * yes screen's own suite's to hold.
 */
describe('the initials a poster draws', () => {
  it('takes the first letter of each word, split where a name separates words, at most two', () => {
    expect(handleInitials('Ania Kowalska')).toBe('AK');
    expect(handleInitials('Tomek.K')).toBe('TK');
    expect(handleInitials('Marek Z.')).toBe('MZ');
    expect(handleInitials('Paula Casals Nadal')).toBe('PC');
  });

  it('takes the first two characters of a one-word name, because a dash or an underscore is inside a word', () => {
    expect(handleInitials('Diego')).toBe('DI');
    expect(handleInitials('Anne-Marie')).toBe('AN');
    expect(handleInitials('dorota_w')).toBe('DO');
  });

  it('gives a one-character name its one', () => {
    expect(handleInitials('x')).toBe('X');
  });

  it('keeps what follows a break a name opens with, rather than an initial for nothing', () => {
    // `.leading` is one word once the empty part is dropped; ` Tomek K` is two.
    expect(handleInitials('.leading')).toBe('LE');
    expect(handleInitials(' Tomek K')).toBe('TK');
  });

  it('upper-cases for drawing only, and leaves the name a sentence says untouched', () => {
    expect(handleInitials('Ewa Malinowska')).toBe('EM');
    expect(playerName({ kind: 'player', name: 'Ewa Malinowska' })).toBe('Ewa Malinowska');
  });
});

/**
 * **`@nickname`, drawn under the name on two screens and said nowhere** — ADR-0171 §4. The
 * form is pinned here so the You tab and the record cannot spell it differently; that it appears
 * on no row, sentence, sheet, toast or seat label is every other suite's to hold, by never
 * being handed one.
 */
describe('the handle a record draws', () => {
  it('is the nickname with an at in front of it, and nothing else', () => {
    expect(atNickname('ania_k')).toBe('@ania_k');
    expect(atNickname('Diego.F')).toBe('@Diego.F');
  });
});
