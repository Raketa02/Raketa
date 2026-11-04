import type { components } from '@/generated/schema';

import { toAuthenticatedUser, toInvitationLink, toNaming, toTokens } from './authMappers';

type MeResponse = components['schemas']['MeResponse'];

/** A player who signed up — attested, holding no administrator profile and no invitation. */
const PLAYER_PROFILES: MeResponse['profiles'] = {
  acts_as_player: true,
  administers: [],
  pending_invitations: [],
  handovers: [],
};

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
      adult_attested: true,
      profiles: PLAYER_PROFILES,
      created_at: '2026-08-13T10:00:00Z',
    });

    expect(user).toEqual({
      id: 'e2b1c0d4-0000-4000-8000-000000000001',
      email: 'ada@example.com',
      nickname: 'ada',
      hasPlayerProfile: false,
      profiles: { actsAsPlayer: true, administers: [], pendingInvitations: [], handovers: [] },
    });
    // A client that renders differently for an admin has invented an authorization
    // decision it cannot enforce. Backend authorization is the only authorization.
    expect(user).not.toHaveProperty('isAdmin');
  });

  /**
   * **`null` on the wire is *no nickname yet*, and it is carried as absence** — the one read
   * where it may be null
   * ([ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §3). The
   * entry gate reads the absence and sends the player to the naming step.
   */
  it('carries a player with no nickname yet as one with none', () => {
    const user = toAuthenticatedUser({
      id: 'e2b1c0d4-0000-4000-8000-000000000001',
      email: 'ada@example.com',
      nickname: null,
      authority: 'player',
      is_admin: false,
      is_active: true,
      has_player_profile: false,
      adult_attested: true,
      profiles: PLAYER_PROFILES,
    });

    expect(user).not.toHaveProperty('name');
    expect(user).not.toHaveProperty('nickname');
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
      adult_attested: true,
      profiles: PLAYER_PROFILES,
      created_at: '2026-08-13T10:00:00Z',
    });

    expect(user.hasPlayerProfile).toBe(true);
  });

  /**
   * **Which profiles the account holds** — what the entry gate reads first
   * ([ADR-0185](../../../../../docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)
   * §2–§3): whether it acts as a player, and the clubs it administers, one per club, in the
   * server's order.
   */
  it('carries the profiles: acting as a player, and each club administered', () => {
    const user = toAuthenticatedUser({
      id: 'e2b1c0d4-0000-4000-8000-000000000001',
      email: 'marta@example.com',
      nickname: null,
      authority: 'player',
      is_admin: false,
      is_active: true,
      has_player_profile: false,
      adult_attested: false,
      profiles: {
        acts_as_player: false,
        administers: [
          { club_id: 'c0000000-0000-4000-8000-000000000001', club_name: 'Ogrody 33' },
          { club_id: 'c0000000-0000-4000-8000-000000000002', club_name: 'Bonarka Arena' },
        ],
        pending_invitations: [],
        handovers: [],
      },
    });

    expect(user.profiles).toEqual({
      actsAsPlayer: false,
      administers: [
        { clubId: 'c0000000-0000-4000-8000-000000000001', clubName: 'Ogrody 33' },
        { clubId: 'c0000000-0000-4000-8000-000000000002', clubName: 'Bonarka Arena' },
      ],
      pendingInvitations: [],
      handovers: [],
    });
    // An account an invitation opened holds no player name and no nickname (ADR-0199 §4): the
    // name its club typed is the Administrator's, on the club's pages.
    expect(user).not.toHaveProperty('name');
    expect(user).not.toHaveProperty('nickname');
  });
});

describe('the invitations an account is offered', () => {
  it('carries each one the accept names, with its club and when it lapses', () => {
    const user = toAuthenticatedUser({
      id: '11111111-2222-4333-8444-555555555555',
      email: 'tomek@example.com',
      nickname: 'tomek',
      authority: 'player',
      is_admin: false,
      is_active: true,
      has_player_profile: true,
      adult_attested: true,
      profiles: {
        acts_as_player: true,
        administers: [],
        pending_invitations: [
          {
            administrator_id: 'd0000000-0000-4000-8000-000000000001',
            club_id: 'c0000000-0000-4000-8000-000000000001',
            club_name: 'Ogrody 33',
            expires_at: '2026-09-29T12:00:00Z',
          },
        ],
        handovers: [],
      },
    });

    expect(user.profiles.pendingInvitations).toEqual([
      {
        administratorId: 'd0000000-0000-4000-8000-000000000001',
        clubId: 'c0000000-0000-4000-8000-000000000001',
        clubName: 'Ogrody 33',
        expiresAt: '2026-09-29T12:00:00Z',
      },
    ]);
  });
});

describe('the groups a club handed the account', () => {
  it('carries each one the account has not been told about, with its club and its queue', () => {
    const user = toAuthenticatedUser({
      id: '11111111-2222-4333-8444-555555555555',
      email: 'tomek@example.com',
      nickname: 'tomek',
      authority: 'player',
      is_admin: false,
      is_active: true,
      has_player_profile: true,
      adult_attested: true,
      profiles: {
        ...PLAYER_PROFILES,
        administers: [{ club_id: 'c0000000-0000-4000-8000-000000000001', club_name: 'Ogrody 33' }],
        handovers: [
          {
            club_id: 'c0000000-0000-4000-8000-000000000001',
            club_name: 'Ogrody 33',
            group_id: 'a0000000-0000-4000-8000-000000000001',
            group_name: 'Ogrody 33 Club',
            waiting_count: 2,
          },
        ],
      },
    });

    expect(user.profiles.handovers).toEqual([
      {
        clubId: 'c0000000-0000-4000-8000-000000000001',
        clubName: 'Ogrody 33',
        groupId: 'a0000000-0000-4000-8000-000000000001',
        groupName: 'Ogrody 33 Club',
        waitingCount: 2,
      },
    ]);
  });
});

describe('toNaming', () => {
  it('carries what the naming recorded — the nickname, and nothing else', () => {
    expect(toNaming({ nickname: 'ada' })).toEqual({ nickname: 'ada' });
  });
});

/**
 * **What an invitation's link opens** — the address *Set your password* locks to, whether it still
 * works, and the club it is from: a link opened by the account it was sent to has the sheet offer
 * that club's invitation again (#520). The name the club typed is not carried; nothing says it.
 */
describe('toInvitationLink', () => {
  it('keeps the address, the club and the state', () => {
    expect(
      toInvitationLink({
        email: 'tomek.k@example.com',
        name: 'Tomek Kowal',
        club_name: 'Ogrody 33',
        state: 'valid',
      }),
    ).toEqual({ email: 'tomek.k@example.com', clubName: 'Ogrody 33', state: 'valid' });
  });
});
