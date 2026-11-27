/**
 * **A link carried through an Android install, arriving** (#756) — read, and held only into an
 * empty hand: a link the phone was opened with, or opened meanwhile, is what the person tapped now.
 */

import { receiveReferrer } from './receiveReferrer';

describe('the install referrer arriving', () => {
  it('is a group link or a friend link it carried', () => {
    expect(receiveReferrer('https://rakieta.app/f/tk4m9q2z', null)).toEqual({
      kind: 'friend',
      code: 'tk4m9q2z',
    });
    expect(receiveReferrer('https://rakieta.app/join/k7pq2mxa', null)).toEqual({
      kind: 'join',
      code: 'k7pq2mxa',
    });
  });

  it('is nothing when there is none, or it is no link', () => {
    expect(receiveReferrer(null, null)).toBeUndefined();
    expect(receiveReferrer('utm_source=google-play&utm_medium=organic', null)).toBeUndefined();
  });

  it('never takes the place of a link already held', () => {
    expect(
      receiveReferrer('https://rakieta.app/f/tk4m9q2z', { kind: 'join', code: 'k7pq2mxa' }),
    ).toBeUndefined();
  });
});
