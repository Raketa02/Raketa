/**
 * **Feature flags** — what the app gates, what each gate says when nothing has been decided, and
 * which datafiles it can read
 * ([ADR-0206](../../../../../docs/adr/0206-a-feature-is-turned-on-by-a-pull-request-again-and-explore-is-the-first.md)).
 *
 * A feature flag is defined in another repository, `Raketa02/raketa-features`, and turned on or off
 * by a pull request there. This file is the client's half of that agreement, and **the only list
 * there is**: a key declared here and missing from the datafile evaluates to its code default,
 * silently, so a typo here is a feature that never turns on. Nothing checks the two repositories
 * against each other — ADR-0206 names that as the cost.
 *
 * Pure: no React, no SDK, no storage. The Featurevisor SDK reads a datafile; this says which ones
 * it is handed.
 */

/**
 * **Every feature the app gates, and its code default** — declared once.
 *
 * The code default is what a player gets when no datafile has ever arrived: a first launch with
 * no network, or a flags host that has never answered. It is the app *as it ships*. A feature flag
 * may be defaulted per environment in the flags repo; it is never derived from the environment
 * here (`docs/environments.md`).
 *
 * **Each key carries its record** (architecture Part 21): who owns it, what it is for, its default,
 * how it rolls out and when it goes. A feature flag is scaffolding for one change and is deleted
 * when that change has shipped. The rollout itself is not here — it is the flags repo's YAML,
 * where a pull request changes it.
 */
export const FEATURE_DEFAULTS = {
  /**
   * **Explore** — Play's second segment, beside Groups
   * ([#826](https://github.com/Raketa02/Raketa/issues/826), ADR-0206 §11).
   *
   * **Off by default.** Off, Play is the player's groups under a single *Groups* title, with no
   * *Groups | Explore* switcher, and Explore cannot be reached: a saved `explore` segment is read
   * past and never written. On, Play is exactly what it was before this key: the switcher, Groups
   * first, the remembered segment honoured. Only an explicit **on** draws the switcher — no
   * datafile, a refused one, or no signed-in player is off.
   *
   * Read once, when Play mounts (`useFeatureOnMount`), so Explore never vanishes under a player's
   * thumb: a datafile that lands while Play is up changes nothing until Play next mounts.
   *
   * - **Owner:** the product owner, with the shell as the gate's code owner (`PlayScreen`).
   * - **Purpose:** keep Play to Groups while Explore is unbuilt.
   * - **Default:** off — here, and in every environment's definition in the flags repo.
   * - **Rollout:** decided when Explore has content; a percentage by `playerId`, in the flags repo.
   * - **Removal:** once it is on for everyone in production, this key, the flags repo's definition
   *   and spec, the gate in `PlayScreen` and its toggle-off branch go together.
   */
  explore: false,
} as const satisfies Readonly<Record<string, boolean>>;

/** A feature the app knows how to ask about. A key not declared above does not compile. */
export type FeatureKey = keyof typeof FEATURE_DEFAULTS;

/**
 * **The datafile formats this build reads** — Featurevisor's `schemaVersion`.
 *
 * A datafile carrying anything else is refused, and the one already in use stays in use (§10):
 * an upgrade in the flags repo that changes the format stops installed apps from *updating*,
 * never from *working*. The flags repo's CLI major moves only with this app's SDK major, and
 * this list is where that pairing is written on this side.
 */
export const READABLE_SCHEMA_VERSIONS: readonly string[] = ['2'];

export function isReadableSchemaVersion(schemaVersion: string): boolean {
  return READABLE_SCHEMA_VERSIONS.includes(schemaVersion);
}

/**
 * **A datafile the app has checked it can read** — one environment's features, as the flags
 * repo built them.
 *
 * Only the envelope is typed. What is inside a feature is the SDK's to interpret, and a
 * hand-written mirror of it here would be a second, weaker reading of a format another repository
 * owns.
 */
export interface Datafile {
  readonly schemaVersion: string;
  readonly revision: string;
  readonly segments: Readonly<Record<string, unknown>>;
  readonly features: Readonly<Record<string, unknown>>;
}

/**
 * **Who is asking** — the attributes a datafile's rules are written against, spelled as the flags
 * repo spells them (§8).
 *
 * `playerId` is here for `bucketBy` alone: a rollout's bucket follows the account, not the
 * device. **No rule may name one**, because the datafile is public; the flags repo's own lint
 * refuses it. **There is no tester mark** (§9): the account carries none since #581, so nothing on
 * this list says who a player is, only which bucket and which build.
 *
 * `platform` and `appVersion` are absent when the build cannot say — a rule that targets them
 * then does not match, which is the honest answer for a device that did not identify itself.
 */
export interface EvaluationContext {
  readonly playerId: string;
  readonly platform?: 'ios' | 'android';
  readonly appVersion?: string;
}

/**
 * **The fallback order: fresh, then cached, then code default** (§6).
 *
 * `fresh` is the datafile fetched this session, `cached` the last good one saved on this device.
 * `undefined` when neither exists, which is the code defaults' case.
 *
 * A fresh datafile that was *refused* never reaches this function — it is not a datafile — so the
 * refusal leaves the previous one in use by construction rather than by a rule here.
 */
export function datafileInUse(
  fresh: Datafile | undefined,
  cached: Datafile | null | undefined,
): Datafile | undefined {
  return fresh ?? cached ?? undefined;
}
