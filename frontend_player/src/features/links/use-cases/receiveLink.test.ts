/**
 * **A link arriving** — read, and where it lands decided, before anything is routed (#520). What is
 * held and what is routed to is the component's; this is the workflow's two questions.
 */

import { receiveLink } from './receiveLink';

const TOKEN = 'Rs7_reset-token-9Pq3Wn5Lk1Tz8Vb2Hc4Jf6Md0Ng';

const arrival = (address: string, overrides: Partial<Parameters<typeof receiveLink>[0]> = {}) =>
  receiveLink({ address, initial: false, session: 'signed-out', domain: null, ...overrides });

describe('a link arriving', () => {
  it('is read and landed on its own screen with nobody signed in', () => {
    expect(arrival(`raketa://reset/${TOKEN}`)).toEqual({
      link: { kind: 'reset', token: TOKEN },
      landing: { kind: 'its-screen', link: { kind: 'reset', token: TOKEN } },
    });
  });

  it('is held on a phone that is signed in', () => {
    expect(arrival(`raketa://reset/${TOKEN}`, { session: 'signed-in' })).toEqual({
      link: { kind: 'reset', token: TOKEN },
      landing: { kind: 'held' },
    });
  });

  /** A friend link is held whoever is on the phone, as a group link is (#756). */
  it('holds a friend link with nobody signed in', () => {
    expect(arrival('raketa://f/tk4m9q2z')).toEqual({
      link: { kind: 'friend', code: 'tk4m9q2z' },
      landing: { kind: 'held' },
    });
  });

  it('is nothing when it is not a link', () => {
    expect(arrival('raketa://sign-in')).toBeUndefined();
  });

  /**
   * A launch from the home screen hands the router the app's bare address too, so at a launch it
   * asks nothing of anybody — the invitation sheet offers what is open on every launch anyway.
   */
  it('takes the app’s bare address as a link only while the app is running', () => {
    expect(arrival('raketa://', { initial: true })).toBeUndefined();
    expect(arrival('raketa://')).toEqual({ link: { kind: 'open' }, landing: { kind: 'held' } });
  });
});
