import { toAuthenticatedUser, toTokens } from './authMappers';

describe('toTokens', () => {
  it("renames the wire's spelling without carrying expiry upward", () => {
    const tokens = toTokens({
      access_token: 'access-1',
      refresh_token: 'refresh-1',
      token_type: 'bearer',
      expires_in: 900,
    });

    expect(tokens).toEqual({ accessToken: 'access-1', refreshToken: 'refresh-1' });
    // Expiry is discovered from a 401, never predicted from a phone's clock.
    expect(tokens).not.toHaveProperty('expiresIn');
  });
});

describe('toAuthenticatedUser', () => {
  it('keeps identity and drops what the client must not branch on', () => {
    const user = toAuthenticatedUser({
      id: 'e2b1c0d4-0000-4000-8000-000000000001',
      email: 'ada@example.com',
      nickname: 'ada',
      authority: 'player',
      is_admin: true,
      is_active: true,
      has_player_profile: false,
      created_at: '2026-08-13T10:00:00Z',
    });

    expect(user).toEqual({
      id: 'e2b1c0d4-0000-4000-8000-000000000001',
      email: 'ada@example.com',
      nickname: 'ada',
      hasPlayerProfile: false,
    });
    // A client that renders differently for an admin has invented an authorization
    // decision it cannot enforce. Backend authorization is the only authorization.
    expect(user).not.toHaveProperty('isAdmin');
  });

  it('carries whether the second part of onboarding has been committed', () => {
    // The one field here the client is *entitled* to branch on, and the reason it is
    // carried where authority and is_admin are dropped: the entry gate decides where a
    // player belongs on launch, and without this it sends a rated player with no profile
    // into the app past the social steps, permanently.
    const user = toAuthenticatedUser({
      id: 'e2b1c0d4-0000-4000-8000-000000000001',
      email: 'ada@example.com',
      nickname: 'ada',
      authority: 'player',
      is_admin: false,
      is_active: true,
      has_player_profile: true,
      created_at: '2026-08-13T10:00:00Z',
    });

    expect(user.hasPlayerProfile).toBe(true);
  });
});
