/**
 * How this platform names a person.
 *
 * One rule, and it is ADR-0107 §4's, read on the nickname again since
 * [ADR-0199](../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md):
 * **the whole nickname, or nobody**, and never with an @. The nickname is the handle the player
 * chose — *ania.k*, *kuba*, *dorota_w* — and the assertions are about what the formatter refuses
 * to do with it: never a first word, never an initial, never a truncation, never a mark.
 *
 * `handleStem` beneath it is not an exception to that rule and the second suite says why: it
 * returns a **prefix of the nickname somebody typed**, cut at a character they typed, for a box to
 * draw. What a sentence says is untouched.
 */

import { handleInitials, handleStem, playerName } from './playerName';

const LONG = 'niepokonany.wojownik_z_warszawy-grajacy.wieczorami';

describe('naming one person', () => {
  it('is you, to yourself', () => {
    expect(playerName({ kind: 'you' })).toBe('You');
  });

  it('is the whole nickname, however long', () => {
    // 2 to 64 characters of the player's choosing. Inventing a familiar form is the product
    // addressing a person by a name they never gave it.
    expect(playerName({ kind: 'player', name: LONG })).toBe(LONG);
  });

  it('never takes the first part of one', () => {
    const name = playerName({ kind: 'player', name: LONG });

    expect(name).not.toBe('niepokonany');
    expect(name).not.toMatch(/…|\.\.\./);
  });

  it('never writes it with an @ (ADR-0199 §1)', () => {
    expect(playerName({ kind: 'player', name: 'ania.k' })).toBe('ania.k');
  });

  it('leaves an empty seat a question mark, which is not a word', () => {
    expect(playerName({ kind: 'unknown' })).toBe('?');
  });
});

/**
 * **A prefix of the nickname they typed, and never a name they did not.** ADR-0107 bites on
 * *inventing* a familiar form; cutting a nickname at a character its owner put there invents
 * nothing, and it is drawn only where a box is drawing. ADR-0157's cut, at the first dot, as it
 * stood before ADR-0171 (ADR-0199, *Leaves standing*).
 */
describe('the stem a box draws', () => {
  it('cuts at the first dot', () => {
    expect(handleStem('sergio.sabater')).toBe('sergio');
    expect(handleStem('ania.k')).toBe('ania');
    expect(handleStem('paula.casals.nadal')).toBe('paula');
  });

  it('never cuts at a dash or an underscore', () => {
    // ADR-0199 left the stem at the first dot, where the initials now break at all three.
    expect(handleStem('anne-marie')).toBe('anne-marie');
    expect(handleStem('dorota_w')).toBe('dorota_w');
  });

  it('leaves a nickname with no dot, and one that opens with one, entirely alone', () => {
    expect(handleStem('kuba')).toBe('kuba');
    // An empty stem is not a shorter nickname; it is none, and there is nothing to draw.
    expect(handleStem('.leading')).toBe('.leading');
  });

  it('leaves what a sentence says untouched — the two are different registers', () => {
    const whole = 'diego.fabregat';

    expect(playerName({ kind: 'player', name: whole })).toBe(whole);
  });
});

/**
 * **Two initials over a poster, and nowhere else** —
 * [ADR-0167](../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
 * §3's one exception to the rule the suites above hold, cut from the nickname by ADR-0199 §2: its
 * first character, then the first character after its first `.`, `_` or `-`, else its second. It
 * is a drawing and never a sentence: the cut is tested here, and that no sentence carries it is
 * the yes screen's own suite's to hold.
 */
describe('the initials a poster draws', () => {
  it('takes the first character, and the first after the first dot, underscore or dash', () => {
    expect(handleInitials('ania.k')).toBe('AK');
    expect(handleInitials('dorota_w')).toBe('DW');
    expect(handleInitials('anne-marie')).toBe('AM');
  });

  it('breaks at the first separator only, whichever of the three it is', () => {
    expect(handleInitials('paula.casals.nadal')).toBe('PC');
    expect(handleInitials('ewa_m.k')).toBe('EM');
    expect(handleInitials('jan-k_w')).toBe('JK');
  });

  it('takes the first two characters of a nickname with no separator', () => {
    expect(handleInitials('kuba')).toBe('KU');
    expect(handleInitials('Diego')).toBe('DI');
  });

  it('takes the second character where nothing follows the separator', () => {
    expect(handleInitials('marek.')).toBe('MA');
  });

  it('gives a one-character nickname its one', () => {
    expect(handleInitials('x')).toBe('X');
  });

  it('upper-cases for drawing only, and leaves the nickname a sentence says untouched', () => {
    expect(handleInitials('ewa.malinowska')).toBe('EM');
    expect(playerName({ kind: 'player', name: 'ewa.malinowska' })).toBe('ewa.malinowska');
  });
});
