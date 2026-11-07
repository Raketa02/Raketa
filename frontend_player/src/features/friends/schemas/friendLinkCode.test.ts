/**
 * **A friend link's code, read** (#756) — what follows `/f/`, from a link somebody else wrote:
 * eight letters and digits, a group code's shape (the friends mechanics §4.1), read lower case.
 */

import { parseFriendLinkCode } from './friendLinkCode';

describe('a friend link’s code', () => {
  it('is eight letters and digits, read lower case', () => {
    expect(parseFriendLinkCode('tk4m9q2z')).toBe('tk4m9q2z');
    expect(parseFriendLinkCode('TK4M9Q2Z')).toBe('tk4m9q2z');
  });

  it.each(['tk4m9q2', 'tk4m9q2z9', 'tk4m-q2z', 'tk4m9q2z/', '', undefined, 12345678])(
    'is no code: %p',
    (value) => {
      expect(parseFriendLinkCode(value)).toBeUndefined();
    },
  );
});
