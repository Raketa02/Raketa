/**
 * **A held link belongs to the session it arrived in** — or to the next one, when it arrived with
 * nobody signed in (#520). When a session ends, whatever it held is let go of: a group link somebody
 * tapped, and above all an invitation's or a reset's token, is never handed to the next person to
 * sign in on the phone.
 */

import { resetSessionStatus, setSessionStatus } from '@/shared/lib/auth';

import { useHeldLinkStore } from '../store/heldLink.store';

import { holdLink, letGoOf } from './heldLink';

const TOKEN = 'Rs7_reset-token-9Pq3Wn5Lk1Tz8Vb2Hc4Jf6Md0Ng';
const RESET = { kind: 'reset', token: TOKEN } as const;

const held = () => useHeldLinkStore.getState().link;

beforeEach(() => {
  resetSessionStatus();
  useHeldLinkStore.getState().reset();
});

describe('a held link and the session', () => {
  it('is let go of when the session it arrived in ends', () => {
    setSessionStatus('authenticated');
    holdLink(RESET);

    setSessionStatus('unauthenticated');

    expect(held()).toBeNull();
  });

  /** The invitation opened signed out is answered by the sign-in it leads to. */
  it('is kept through the sign-in that follows a link opened signed out', () => {
    setSessionStatus('unauthenticated');
    holdLink(RESET);

    setSessionStatus('authenticated');

    expect(held()).toEqual(RESET);
  });

  /** A cold start's link arrives before the keychain is read; the session it restores keeps it. */
  it('is kept through a cold start’s session being restored', () => {
    holdLink({ kind: 'join', code: 'k7pq2mxa' });

    setSessionStatus('authenticated');

    expect(held()).toEqual({ kind: 'join', code: 'k7pq2mxa' });
  });

  it('does not reach a link that arrived after the session ended', () => {
    setSessionStatus('authenticated');
    holdLink({ kind: 'join', code: 'k7pq2mxa' });
    letGoOf({ kind: 'join', code: 'k7pq2mxa' });
    setSessionStatus('unauthenticated');
    holdLink(RESET);

    setSessionStatus('authenticated');

    expect(held()).toEqual(RESET);
  });
});
