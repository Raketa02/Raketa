/** **Which links are the same link** — what a held link is let go of by (#520). */

import { sameLink } from './incomingLink';

const TOKEN = 'Zx9_invite-token-4Kq2Wm8Rt6Yv0Bn3Hs5Jd7Lf1Pg';

describe('the same link', () => {
  it('is the same page with the same value', () => {
    expect(sameLink({ kind: 'join', code: 'k7pq2mxa' }, { kind: 'join', code: 'k7pq2mxa' })).toBe(
      true,
    );
    expect(sameLink({ kind: 'reset', token: TOKEN }, { kind: 'reset', token: TOKEN })).toBe(true);
    expect(sameLink({ kind: 'open' }, { kind: 'open' })).toBe(true);
    expect(
      sameLink({ kind: 'friend', code: 'tk4m9q2z' }, { kind: 'friend', code: 'tk4m9q2z' }),
    ).toBe(true);
  });

  it('is not another group, nor another token', () => {
    expect(sameLink({ kind: 'join', code: 'k7pq2mxa' }, { kind: 'join', code: 'zzzzzzzz' })).toBe(
      false,
    );
    expect(sameLink({ kind: 'invite', token: TOKEN }, { kind: 'invite', token: `${TOKEN}x` })).toBe(
      false,
    );
  });

  /** An invitation's and a reset's tokens come from one machinery, and are still two links. */
  it('is not another page with the same value', () => {
    expect(sameLink({ kind: 'invite', token: TOKEN }, { kind: 'reset', token: TOKEN })).toBe(false);
    expect(sameLink({ kind: 'join', code: 'tk4m9q2z' }, { kind: 'friend', code: 'tk4m9q2z' })).toBe(
      false,
    );
  });
});
