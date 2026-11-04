/**
 * The signed-in player, as the app talks about them.
 *
 * This layer is **types and nothing else**, deliberately. Authentication has no business
 * rule the client is entitled to enforce: whether a password is right, whether an account
 * may sign in, whether a token is still good — every one of those is the server's answer,
 * and a client-side copy of it would be a second, weaker authority that disagrees the
 * first time the backend's rules change. Backend authorization is the only authorization.
 *
 * ADR-0009's escape hatch covers exactly this case: keep the folder for predictability,
 * do not invent a fake invariant to fill it.
 */

/**
 * `GET /users/me`'s answer mapped into the app's vocabulary.
 *
 * The wire's `authority`, `is_admin` and `created_at` are deliberately dropped rather
 * than carried: nothing in the player app may branch on them. A client that renders
 * differently for an admin has invented an authorization decision it cannot enforce.
 *
 * `hasPlayerProfile` and `nickname` are the two fields kept for the opposite reason — the client
 * is *required* to branch on them, at launch, before any route tree exists. The wire no
 * longer carries `is_tester` at all: its one reader was feature-flag evaluation, which left
 * with the flags (#576), and the mark left the server after it (#581).
 */
export interface AuthenticatedUser {
  readonly id: string;
  readonly email: string;
  /**
   * What this player is called — their handle, unique across the platform, and **what every
   * screen says about them**, whole and never with an @
   * ([ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §1). The
   * entry gate's first destination when it is absent.
   *
   * Absent until the naming, and this is the one read on which it may be: sign-up creates
   * the account with none, an account an Invitation opened holds none either (§4), and the gate
   * holds it at the naming step until it has one. Read from the `User`'s own stream for
   * `hasPlayerProfile`'s reason — the moment after the naming is exactly when a lagging read model
   * would send a player back to the step they just finished.
   */
  readonly nickname?: string;
  /**
   * Whether onboarding's second part has been committed — the entry gate's fourth branch
   * ([ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md)).
   *
   * It travels on the authenticated player rather than as its own read because it is a
   * fact about that player, and because the gate already asks who they are — a second
   * round trip at launch to answer one boolean is what the field on this response avoids.
   * Whether a *Player profile* exists is a per-player question with a per-player answer,
   * which is why it may be one: it is not the per-player onboarding flag the shared
   * glossary bans, and the glossary's own test — *is this really asking whether a rating
   * exists for this sport?* — answers no.
   */
  readonly hasPlayerProfile: boolean;
  /**
   * **Which profiles the account holds** — the entry gate's first read, ahead of every onboarding
   * destination
   * ([ADR-0185](../../../../../docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)
   * §2–§3). Carried for the reason `hasPlayerProfile` is: the client is required to branch on it
   * at launch, before any route tree exists — an account that only runs a club's groups has not
   * asked to play, and must never be sent into onboarding.
   */
  readonly profiles: AccountProfiles;
}

/**
 * **The hats one account wears** (ADR-0185 §1). *Profile* is the switcher's word, not a domain
 * term — a **Player profile** is an aggregate, and this is not it.
 */
export interface AccountProfiles {
  /**
   * Whether the account acts as a player: it gave the Adult attestation — every sign-up did — or
   * holds a Player profile. `false` only for an account an Invitation opened that has not started
   * playing.
   */
  readonly actsAsPlayer: boolean;
  /** One per club whose groups this account runs as its **Administrator**, in the server's order. */
  readonly administers: readonly AdministeredClub[];
  /**
   * **Invitations to this account's email still open**, soonest to expire first (ADR-0185 §2) — what
   * the invitation sheet offers on launch. The server drops one once it is accepted, removed or past
   * its 72 hours, so a list read after that no longer holds it.
   */
  readonly pendingInvitations: readonly PendingInvitation[];
  /**
   * **Groups a club handed this account that it has not been told about**, oldest first
   * ([ADR-0192](../../../../../docs/adr/0192-a-handover-is-told-to-whom-it-was-handed-and-the-app-follows-the-account.md)) —
   * what the handover sheet tells. The server drops one once the sheet says it was seen, or when
   * the club hands the group on.
   */
  readonly handovers: readonly Handover[];
}

/**
 * **The profiles an account holds, without the invitations it is offered** — what the entry gate,
 * the switcher and a removal read. An invitation is not a profile until it is accepted.
 */
export type HeldProfiles = Pick<AccountProfiles, 'actsAsPlayer' | 'administers'>;

/** **A club's invitation to be its Administrator**, waiting for this account to accept it. */
export interface PendingInvitation {
  /** What accepting it names. */
  readonly administratorId: string;
  readonly clubId: string;
  readonly clubName: string;
  /** When it lapses — the server's instant, carried as it came. */
  readonly expiresAt: string;
}

/** **A group a club handed this account**, which it has not been told about yet. */
export interface Handover {
  readonly clubId: string;
  readonly clubName: string;
  /** What saying it was seen names. */
  readonly groupId: string;
  readonly groupName: string;
  /** How many wait to join it: the queue the handover gave them. */
  readonly waitingCount: number;
}

/** A club this account is an active Administrator of — the administrator area opens on it. */
export interface AdministeredClub {
  readonly clubId: string;
  readonly clubName: string;
}

/** What a player types to sign in. Never logged, never persisted. */
export interface SignInCredentials {
  readonly email: string;
  readonly password: string;
}

/**
 * What a player types to create an account — **credentials, and nothing about who they are.**
 *
 * Sign-up is choosing credentials, and saying who you are is a different moment, asked first
 * thing in onboarding by {@link Naming} (ADR-0199 §3).
 */
export interface Registration {
  readonly email: string;
  readonly password: string;
  /**
   * The player's own claim that they are an adult — an **attestation**, one boolean, and
   * never a date of birth
   * ([ADR-0124](../../../../../docs/adr/0124-the-matcher-gates-account-state-never-age.md)).
   *
   * Required rather than optional, and there is no `false` this app sends: the form
   * refuses before a round trip and the server refuses again by code. Typing it as a
   * boolean the caller must supply is what makes *forgot to ask* unrepresentable, which is
   * the only failure an attestation exists to rule out.
   *
   * This is the one thing on this interface the platform is not entitled to assume. It is
   * also **not age verification**: it records that the question was asked and answered.
   */
  readonly adultAttested: boolean;
}

/**
 * **The naming** — *How should people see you?* — the one act that names a player: **a nickname,
 * and nothing else**
 * ([ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §3).
 *
 * A handle under the rule the sign-up form used to state, unique across the platform and refused
 * with `nickname_already_taken` when another account holds it. **Repeatable**: a later change
 * from the You tab is the same act, at any time, and keeping your own is admitted. This is also
 * what the naming answers with — the nickname as recorded — which is why the screen re-reads the
 * player rather than trusting what it typed.
 */
export interface Naming {
  readonly nickname: string;
}
