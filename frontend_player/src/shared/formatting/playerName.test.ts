/**
 * How this platform names a person.
 *
 * One rule, and it is ADR-0107's: **the whole handle, or nobody**. There is no name in this
 * platform to shorten, so the assertions are about what the formatter refuses to do — never a
 * first word, never an initial, never a truncation.
 */

import { playerName } from './playerName';

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
