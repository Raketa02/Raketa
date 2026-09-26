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
 *   not named in full              -> the naming step, before anything else
 *   run in progress, not set aside -> resume it, at its outstanding question
 *   no ratings at all              -> onboarding, from welcome
 *   no Player profile              -> onboarding's second part, from its first step
 *   otherwise                      -> the app
 *
 * **The name is asked first, because every destination after it says the player's name**
 * ([ADR-0171](../../../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)
 * §3). Sign-up creates the account unnamed; the naming step is onboarding's first screen, and
 * the questionnaire and every surface inside the app address the player by what it records.
 * A run half-answered by an account with no name cannot be produced by the flow — the naming
 * precedes welcome — but the gate does not assume it away, which is the lesson the fourth
 * destination wrote about itself below: a shape the flow cannot produce is still a shape the
 * gate must route, or it loops.
 *
 * **An unfinished run outranks an existing rating**, because a player rated at padel with
 * a tennis run half-answered should land back in the tennis questionnaire, not in the app
 * with those answers stranded.
 *
 * The first two inputs answer genuinely different questions and neither substitutes for
 * the other: one asks whether a *run* is unfinished, the other whether a *rating exists*.
 *
 * The third is the player's own decision, and it is the only reason this gate is not a
 * trap. A run they asked to come back to later is still unfinished — the server is right
 * — and resuming it the instant they leave would mean the questionnaire had no exit.
 * The deferral lasts one app session, so the next launch resumes exactly as it should;
 * the permanent way out is abandonment, which changes the run rather than the routing.
 *
 * ## The profiles are read first, because not every account has asked to play
 *
 * An account holds **profiles** — it may act as a player, and as the Administrator of each club
 * that named it ([ADR-0185](../../../../../docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)
 * §1–§3). **An account that only runs a club's groups goes to its administrator area and is never
 * sent into onboarding**: it has not asked to play, and nothing below it — a name, a rating, a run —
 * is a question it owes an answer to. It is read ahead of the naming because an account an
 * Invitation opened carries the club-typed Name and no Nickname, and ADR-0185 §4 makes that *not
 * named in full* for anybody who does play. The area opens on the first club it administers, in the
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
 * **Named in full is a name and a nickname** (ADR-0185 §4). An account an Invitation opened carries
 * the club-typed Name and no Nickname, so once it attests and acts as a player the naming step is
 * still owed — and asks only for the nickname. For every account sign-up creates this is the same
 * destination as before: it has neither until the naming.
 *
 * ## The fourth destination, and why it is not the flag the glossary bans
 *
 * Onboarding is two parts ([ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md)),
 * and **the part is the checkpoint unit**. The second part holds a client-side draft and
 * writes nothing until its final commit, so a player who reaches it and closes the app has
 * a Skill rating and no Player profile — and a gate reading only *is there a rating* sends
 * them into the app past the second part, permanently, with no route back to it.
 *
 * *Does a Player profile exist* is a per-player question with a per-player answer, which is
 * why it is allowed to be one. The glossary bans a per-player flag standing in for a fact
 * that is genuinely per sport, and its own test — *is this really asking whether a rating
 * exists for this sport?* — answers no here: tags, photos, a week, a location and a consent
 * have no sport dimension at all.
 *
 * **It is read after ratings, never before.** The second part is only reachable once the
 * first has produced something, so a brand-new account — no ratings, no profile — belongs
 * at welcome. Reading the profile first would open the social steps to a player who has not
 * been rated, which is the one shape the flow cannot produce.
 */

import type { HeldProfiles, ProfileChoice } from '@/features/auth/types';

import type { AssessmentRun } from './Assessment';
import type { SkillRating } from './SkillRating';

export type EntryDestination =
  /** The authenticated tree. Onboarding is behind them, at least for one sport. */
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
   * The naming step — *How should people see you?* — which an account not named in full cannot
   * get past: it submits the naming, re-reads the player, and only then moves on.
   */
  | { readonly kind: 'naming' }
  /** Onboarding from the beginning: what it produces, then the sports picker. */
  | { readonly kind: 'welcome' }
  /**
   * Onboarding's second part, **from its first step**. Never from the middle: the draft is
   * client-held and starts empty, so a player dropped at step four would commit a profile
   * built from screens they never saw.
   */
  | { readonly kind: 'social-steps' }
  /** Straight back to the outstanding question of a run they already started. */
  | { readonly kind: 'resume'; readonly run: AssessmentRun };

export interface EntryInput {
  /**
   * Whether the player is **named in full** — a name *and* a nickname (ADR-0185 §4). Served on the
   * authenticated player beside `hasPlayerProfile`, and read from the `User`'s own stream for the
   * same reason: the moment after the naming is exactly when a lagging read model would send a
   * player back to the step they just finished. A per-player question with a per-player answer — a
   * name has no sport dimension — so the glossary's ban on a per-player onboarding flag does not
   * bite.
   */
  readonly namedInFull: boolean;
  readonly ratings: readonly SkillRating[];
  readonly runInProgress: AssessmentRun | undefined;
  /** Runs the player chose to come back to later, since this launch. */
  readonly deferredRunIds: readonly string[];
  /**
   * Whether the second part has been committed. Served on the authenticated player rather
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

export function entryDestination({
  namedInFull,
  ratings,
  runInProgress,
  deferredRunIds,
  hasPlayerProfile,
  profiles,
  lastProfile,
}: EntryInput): EntryDestination {
  const byProfile = profileDestination(profiles, lastProfile);
  if (byProfile !== undefined) return byProfile;
  if (!namedInFull) return { kind: 'naming' };
  if (runInProgress !== undefined && !deferredRunIds.includes(runInProgress.assessmentId)) {
    return { kind: 'resume', run: runInProgress };
  }
  if (ratings.length === 0) return { kind: 'welcome' };
  if (!hasPlayerProfile) return { kind: 'social-steps' };
  return { kind: 'app' };
}
