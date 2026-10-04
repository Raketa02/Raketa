/**
 * The wire boundary: generated DTO -> the app's own objects.
 *
 * Its job is to stop transport naming leaking upward. `access_token` and `is_admin` are
 * FastAPI's spelling of things; above this line the app says `accessToken`, and says
 * nothing at all about `is_admin` because it must not branch on it.
 */

import type { components } from '@/generated/schema';
import type { Tokens } from '@/shared/lib/auth';

import type { AccountProfiles, AuthenticatedUser, Naming } from '../domain/AuthenticatedUser';
import type { InvitationLink } from '../domain/invitation';

type TokenResponse = components['schemas']['TokenResponse'];
type MeResponse = components['schemas']['MeResponse'];
type NamingResponse = components['schemas']['NamingResponse'];
type ClaimTicketResponse = components['schemas']['ClaimTicketResponse'];
type InvitationByTokenResponse = components['schemas']['InvitationByTokenResponse'];
type AccountProfilesSchema = components['schemas']['AccountProfilesSchema'];

/**
 * `expires_in` is deliberately dropped. Expiry is discovered from the server's 401, not
 * predicted from a clock: a phone's clock is user-settable and routinely wrong, and a
 * client that pre-emptively refreshed on its own arithmetic would rotate tokens against
 * a server that never asked it to.
 */
export function toTokens(wire: TokenResponse): Tokens {
  return {
    accessToken: wire.access_token,
    refreshToken: wire.refresh_token,
  };
}

export function toAuthenticatedUser(wire: MeResponse): AuthenticatedUser {
  // `null` on the wire is *not yet named* — the one read where it may be (ADR-0171 §2) — and
  // it is carried as absence, which is how every other shape in this app spells a name it
  // does not have. The entry gate reads the absence.
  const name = wire.name ?? undefined;
  const nickname = wire.nickname ?? undefined;
  return {
    id: wire.id,
    email: wire.email,
    ...(name === undefined ? {} : { name }),
    ...(nickname === undefined ? {} : { nickname }),
    // Kept where `is_admin` is dropped, because the app must branch on it: the entry gate
    // reads it to decide whether onboarding's second part is still owed. It defaults to
    // false on the wire for responses that are not about the authenticated player — such
    // as the one registration returns — and a brand-new account has no profile anyway.
    hasPlayerProfile: wire.has_player_profile,
    // Kept where `is_admin` is dropped for the opposite reason to theirs: it grants nothing.
    // Its one reader is flag evaluation, which decides which build of a screen is drawn and
    // never what anybody may do (ADR-0180 §9).
    isTester: wire.is_tester,
    // Kept for `hasPlayerProfile`'s reason, one read earlier: the gate routes an account that
    // only runs a club's groups to its administrator area before it asks anything about playing
    // (ADR-0185 §3), and the invitations waiting for it are what the invitation sheet offers.
    profiles: toAccountProfiles(wire.profiles),
  };
}

/**
 * **The account's profiles** — on `/users/me`, and as accepting an invitation answers them, so the
 * switcher is drawn from one mapping whichever read it came from.
 */
export function toAccountProfiles(wire: AccountProfilesSchema): AccountProfiles {
  return {
    actsAsPlayer: wire.acts_as_player,
    administers: wire.administers.map((club) => ({
      clubId: club.club_id,
      clubName: club.club_name,
    })),
    pendingInvitations: wire.pending_invitations.map((invitation) => ({
      administratorId: invitation.administrator_id,
      clubId: invitation.club_id,
      clubName: invitation.club_name,
      expiresAt: invitation.expires_at,
    })),
    handovers: wire.handovers.map((handover) => ({
      clubId: handover.club_id,
      clubName: handover.club_name,
      groupId: handover.group_id,
      groupName: handover.group_name,
      waitingCount: handover.waiting_count,
    })),
  };
}

/**
 * The ticket a right code bought — *Forgot password?*'s or an invitation's, one machinery (ADR-0184
 * §4). `expires_in` is dropped for `toTokens`' reason: the server says
 * `ticket_expired` when it is, and a phone's clock is not the judge of that.
 */
export function toClaimTicket(wire: ClaimTicketResponse): string {
  return wire.ticket;
}

/** What the naming recorded: the name as normalised by the server, and the handle. */
export function toNaming(wire: NamingResponse): Naming {
  return { name: wire.name, nickname: wire.nickname };
}

/**
 * What an invitation's link opens: the address *Set your password* locks to, whether it still works,
 * and the club it is from — a link opened by the account it was sent to has the sheet offer that
 * club's invitation again (#520). The name the club typed is dropped: nothing says it, since the
 * email's own greeting already did.
 */
export function toInvitationLink(wire: InvitationByTokenResponse): InvitationLink {
  return { email: wire.email, clubName: wire.club_name, state: wire.state };
}
