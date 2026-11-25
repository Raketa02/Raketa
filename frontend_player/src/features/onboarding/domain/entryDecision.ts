/**
 * Where a signed-in player belongs on launch.
 *
 * This is the whole entry gate as a pure function, which is the point: routing a player
 * into a flow they cannot leave is a business rule, and a rule expressed as a chain of
 * `if` statements inside a layout is a rule nobody can test.
 *
 * The order is deliberate and not arbitrary:
 *
 *   the club it wore last          -> that administrator area, while the account still holds it
 *   only administrator profiles    -> the administrator area, before anything is asked of a player
 *   no profile at all              -> Start playing's first step, the Adult attestation
 *   no nickname                    -> the naming step, before anything else
 *   no Player profile              -> the profile steps, from their first
 *   otherwise                      -> the app
 *
 * **Onboarding is a nickname and a profile**
 * ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §1,
 * [#730](https://github.com/Raketa02/Raketa/issues/730)). The questionnaire left it: a level is
 * asked where play begins — a group's tabs, *Post a game* and Members — so **zero ratings and an
 * unfinished run route nowhere**, and neither is an input here. The gate used to answer *resume*
 * for a run left halfway and *welcome* for a player rated in nothing; the first took over every
 * launch until the run was finished, and the second put the questionnaire between sign-up and
 * Home. A run left halfway is now offered where play begins, by the door that says *Carry on*
 * (§5), and never forced.
 *
 * **The nickname is asked first, because every destination after it says the player's nickname**
 * ([ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §3). Sign-up
 * creates the account with none; the naming step is onboarding's first screen, and the profile
 * steps and every surface inside the app address the player by what it records. A Player profile
 * held by an account with no nickname cannot be produced by the flow — the naming precedes the
 * steps — but the gate does not assume it away: a shape the flow cannot produce is still a shape
 * the gate must route, or it loops.
 *
 * ## The profiles are read first, because not every account has asked to play
 *
 * An account holds **profiles** — it may act as a player, and as the Administrator of each club
 * that named it ([ADR-0185](../../../../../docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)
 * §1–§3). **An account that only runs a club's groups goes to its administrator area and is never
 * sent into onboarding**: it has not asked to play, and nothing below it — a nickname, a profile —
 * is a question it owes an answer to. It is read ahead of the naming because an account an
 * Invitation opened holds no nickname (ADR-0199 §4), which for anybody who does play is the naming
 * still owed. The area opens on the first club it administers, in the
 * server's order; which one a person with two clubs opens on is the switcher's
 * ([#518](https://github.com/Raketa02/Raketa/issues/518)), as is the last-used profile of an account
 * that holds both — which opens in Player until then, so it passes straight through to the player's
 * gate below.
 *
 * **An account that holds no profile at all is offered the player setup, from its first step**
 * (ADR-0185 §3, [#517](https://github.com/Raketa02/Raketa/issues/517)). The only way to be one is an
 * administrator-only account whose club removed it; the account stays, and signing in again must
 * never be a dead end. So it takes *Start playing*'s three steps from the gate instead of from the
 * administrator's You tab — and the first is the **Adult attestation**, which such an account has
 * never given and which comes before anything player-side (ADR-0185 §5), the naming included.
 *
 * **Named is holding a nickname** (ADR-0199 §3, amending ADR-0185 §4). An account an Invitation
 * opened holds no player name and no nickname — the name its club typed stays the Administrator's
 * — so once it attests and acts as a player the naming step is owed, as it is for every account
 * sign-up creates.
 *
 * ## The profile steps, and why their destination is not the flag the glossary bans
 *
 * The profile steps hold a client-side draft and write nothing until their final commit
 * ([ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md)), so a player who
 * reaches them and closes the app has a nickname and no Player profile — and a gate that did not
 * ask would send them into the app past the steps, permanently, with no route back to them.
 *
 * *Does a Player profile exist* is a per-player question with a per-player answer, which is
 * why it is allowed to be one. The glossary bans a per-player flag standing in for a fact
 * that is genuinely per sport, and its own test — *is this really asking whether a rating
 * exists for this sport?* — answers no here: tags, photos, a week, a location and who a
 * player plays with have no sport dimension at all. **A Player profile with no rating is the
 * common shape now** (ADR-0200, Consequences): it is read straight after the nickname, and a
 * rating is no part of the answer.
 */

import type { HeldProfiles, ProfileChoice } from '@/features/auth/types';

export type EntryDestination =
  /** The authenticated tree. Onboarding — a nickname and a profile — is behind them. */
  | { readonly kind: 'app' }
  /**
   * **The administrator area** of the club named — its own screens and its own tabs, outside the
   * player's shell. Only for an account that holds nothing but administrator profiles.
   */
  | { readonly kind: 'administrator'; readonly clubId: string }
  /**
   * **Start playing's first step, the Adult attestation** — for an account that holds no profile at
   * all. The naming and the player setup follow it, through this gate.
   */
  | { readonly kind: 'start-playing' }
  /**
   * The naming step — *How should people see you?* — which an account with no nickname cannot
   * get past: it submits the naming, re-reads the player, and only then moves on.
   */
  | { readonly kind: 'naming' }
  /**
   * The profile steps, **from their first**. Never from the middle: the draft is client-held and
   * starts empty, so a player dropped at step four would commit a profile built from screens
   * they never saw.
   */
  | { readonly kind: 'social-steps' };

export interface EntryInput {
  /**
   * Whether the player is **named** — holds a nickname
   * ([ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §3). Served
   * on the authenticated player beside `hasPlayerProfile`, and read from the `User`'s own stream
   * for the same reason: the moment after the naming is exactly when a lagging read model would
   * send a player back to the step they just finished. A per-player question with a per-player
   * answer — a nickname has no sport dimension — so the glossary's ban on a per-player onboarding
   * flag does not bite.
   */
  readonly named: boolean;
  /**
   * Whether the profile steps have been committed. Served on the authenticated player rather
   * than fetched separately, and read from the profile's own event stream rather than from
   * a projection — so it is correct in the moment after the commit, which is exactly when
   * a lagging read model would send a player back into steps they just finished.
   */
  readonly hasPlayerProfile: boolean;
  /**
   * **Which profiles the account holds**, served on the authenticated player beside the two facts
   * above (ADR-0185 §2) — whether it acts as a player, and each club whose groups it runs.
   */
  readonly profiles: HeldProfiles;
  /**
   * **The profile this account wore last on this phone**, as the phone keeps it (ADR-0188 §2) —
   * absent when nothing was chosen, which is Player. Checked here against what the account holds
   * now, so a club that has since removed it is Player again (§4).
   */
  readonly lastProfile?: ProfileChoice;
}

/**
 * **Where the account's profiles send it before anything a player is asked** — the administrator
 * area for an account that only runs a club's groups, *Start playing*'s first step for one that
 * holds no profile at all, and nothing for every account that acts as a player. The first step of
 * `entryDestination`, and readable on its own: the gate's hook asks it the moment the player is
 * read, because nothing else it waits for is a question such an account owes an answer to.
 */
export function profileDestination(
  profiles: EntryInput['profiles'],
  lastProfile?: ProfileChoice,
): Extract<EntryDestination, { kind: 'administrator' | 'start-playing' }> | undefined {
  const last =
    lastProfile?.kind === 'administrator'
      ? profiles.administers.find((club) => club.clubId === lastProfile.clubId)
      : undefined;
  if (last !== undefined) return { kind: 'administrator', clubId: last.clubId };
  if (profiles.actsAsPlayer) return undefined;
  const [club] = profiles.administers;
  return club === undefined
    ? { kind: 'start-playing' }
    : { kind: 'administrator', clubId: club.clubId };
}

/**
 * **Whether the launch waits for the profile the phone remembers** — an account that runs a club's
 * groups, which opens in the profile it wore last (ADR-0188 §2) and so must not be routed before the
 * phone has said which. Every other account has nothing else to have worn, and nothing waits for it.
 * The gate's hook and the launch both ask it, so neither decides early where the other would wait.
 */
export function decidedByTheLastProfile(profiles: EntryInput['profiles']): boolean {
  return profiles.administers.length > 0;
}

export function entryDestination({
  named,
  hasPlayerProfile,
  profiles,
  lastProfile,
}: EntryInput): EntryDestination {
  const byProfile = profileDestination(profiles, lastProfile);
  if (byProfile !== undefined) return byProfile;
  if (!named) return { kind: 'naming' };
  if (!hasPlayerProfile) return { kind: 'social-steps' };
  return { kind: 'app' };
}
