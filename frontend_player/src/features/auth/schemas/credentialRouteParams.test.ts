import {
  parseEmailParam,
  parseResetLinkParams,
  parseResetTicketParams,
} from './credentialRouteParams';

/** URL-safe base64, 43 characters — what `secrets.token_urlsafe(32)` mints. */
const MINTED = 'Zx9_link-token-4Kq2Wm8Rt6Yv0Bn3Hs5Jd7Lf1Pg';

describe('the email a recovery screen opens with', () => {
  it('reads what the screen before handed over', () => {
    expect(parseEmailParam({ email: 'tomek@example.com' })).toBe('tomek@example.com');
  });

  /** It only fills a box the person can read and change, so a bad one opens the box empty. */
  it.each([
    {},
    undefined,
    { email: ['a@example.com', 'b@example.com'] },
    { email: 'x'.repeat(321) },
  ])('opens the box empty for %p', (params) => {
    expect(parseEmailParam(params)).toBe('');
  });
});

describe("the email's link token and a claimed ticket", () => {
  it('reads one as the server mints it', () => {
    expect(parseResetLinkParams({ token: MINTED })).toEqual({ token: MINTED });
    expect(parseResetTicketParams({ ticket: MINTED })).toEqual({ ticket: MINTED });
  });

  it.each([
    { token: '' },
    { token: 'not.a~token' },
    { token: 'has space' },
    { token: 'x'.repeat(257) },
    { token: [MINTED, MINTED] },
    {},
    undefined,
  ])('refuses %p', (params) => {
    expect(parseResetLinkParams(params)).toBeUndefined();
  });

  it('refuses a ticket that is missing', () => {
    expect(parseResetTicketParams({ token: MINTED })).toBeUndefined();
  });
});
