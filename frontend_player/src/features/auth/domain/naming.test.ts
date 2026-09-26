/**
 * **Named in full**, and the name an account holds without its nickname — ADR-0185 §4, with no
 * renderer and no network.
 */

import { heldNameWithoutNickname, namedInFull } from './naming';

describe('named in full', () => {
  it('is a name and a nickname', () => {
    expect(namedInFull({ name: 'Ania Kowalska', nickname: 'ania_k' })).toBe(true);
  });

  it('is not an account sign-up created, which holds neither until the naming', () => {
    expect(namedInFull({})).toBe(false);
  });

  // An account an Invitation opened: the club typed the name, and nobody chose a handle.
  it('is not a name the club gave, with no nickname', () => {
    expect(namedInFull({ name: 'Marta Nowak' })).toBe(false);
  });
});

describe('the name held without a nickname', () => {
  it('is the club’s name, which the naming keeps and asks only the nickname beside', () => {
    expect(heldNameWithoutNickname({ name: 'Marta Nowak' })).toBe('Marta Nowak');
  });

  it('is nothing for an account holding neither, which is asked both', () => {
    expect(heldNameWithoutNickname({})).toBeUndefined();
  });

  it('is nothing for an account named in full', () => {
    expect(heldNameWithoutNickname({ name: 'Ania Kowalska', nickname: 'ania_k' })).toBeUndefined();
  });
});
