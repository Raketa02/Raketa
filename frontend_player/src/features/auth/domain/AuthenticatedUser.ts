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
 * A `UserResponse` mapped into the app's vocabulary.
 *
 * The wire's `authority`, `is_admin` and `created_at` are deliberately dropped rather
 * than carried: nothing in the player app may branch on them. A client that renders
 * differently for an admin has invented an authorization decision it cannot enforce.
 *
 * `hasPlayerProfile` and `name` are the two fields kept for the opposite reason — the client
 * is *required* to branch on them, at launch, before any route tree exists.
 */
export interface AuthenticatedUser {
  readonly id: string;
  readonly email: string;
  /**
   * What this player is called — **what every screen says about them**, and the entry gate's
   * first destination when it is absent
   * ([ADR-0171](../../../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)).
   *
   * Absent until the naming, and this is the one read on which it may be: sign-up creates
   * the account unnamed, and the gate holds it at the naming step until it is not. Read from
   * the `User`'s own stream for `hasPlayerProfile`'s reason — the moment after the naming is
   * exactly when a lagging read model would send a player back to the step they just finished.
   */
  readonly name?: string;
  /**
   * Their handle, unique across the platform — drawn as `@nickname` under the name on their
   * own You tab and on their record, and **said nowhere else**. Absent until the naming, with
   * the name: the two are one act.
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
}

/** What a player types to sign in. Never logged, never persisted. */
export interface SignInCredentials {
  readonly email: string;
  readonly password: string;
}

/**
 * What a player types to create an account — **credentials, and nothing about who they are.**
 *
 * The nickname left this shape with ADR-0171 §2: sign-up is choosing credentials, and saying
 * who you are is a different moment, asked first thing in onboarding by {@link Naming}.
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
 * **The naming** — *How should people see you?* — the one act that names a player
 * ([ADR-0171](../../../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)
 * §2).
 *
 * Both together, always: there is no event for one without the other, so a shape carrying one
 * would be a naming the server cannot record. The name is what the player wants to be called
 * — free text, spaces allowed, never unique; the nickname is a handle under the rule the sign-up
 * form used to state, unique across the platform and refused with `nickname_already_taken` when
 * it is another player's. **Repeatable**: a later change is the same act, and this is also what
 * the naming answers with — the name as recorded, trimmed and collapsed, which is why the screen
 * re-reads the player rather than trusting what it typed.
 */
export interface Naming {
  readonly name: string;
  readonly nickname: string;
}
