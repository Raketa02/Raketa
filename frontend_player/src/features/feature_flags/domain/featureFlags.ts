/**
 * **Feature flags** — what the app gates, what each gate says when nothing has been decided, and
 * which datafiles it can read
 * ([ADR-0180](../../../../../docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md)).
 *
 * A flag is defined in another repository, `Raketa02/raketa-features`, and turned on or off by a
 * pull request there. This file is the client's half of that agreement, and **the only list
 * there is**: a key declared here and missing from the datafile evaluates to its code default,
 * silently, so a typo here is a feature that never turns off. Nothing checks the two repositories
 * against each other — ADR-0180 names that as the cost.
 *
 * Pure: no React, no SDK, no storage. The Featurevisor SDK reads a datafile; this says which ones
 * it is handed.
 */

/**
 * **Every feature the app gates, and its code default** — declared once.
 *
 * The code default is what a player gets when no datafile has ever arrived: a first launch with
 * no network, or a flags host that has never answered. It is the app *as it ships*. A flag may be defaulted per environment in the flags repo; it is
 * never derived from the environment here (`docs/environments.md`).
 *
 * **Each key says who owns it, what it is for, and when it goes** (architecture Part 21): a flag
 * is scaffolding for one change and is deleted when that change has shipped. Its rollout strategy
 * is not here — it is the flags repo's YAML, where a pull request changes it.
 */
export const FEATURE_DEFAULTS = {
  /**
   * **Find a game**, the Play tab's first screen, with the builder and the pool behind it.
   *
   * **Off by default since [#512](https://github.com/Raketa02/Raketa/issues/512)**: the app ships
   * Play › Groups, with the *Groups | Explore* segment where the empty placeholder used to be and
   * the placeholder under *Explore*, where the rebuilt Find a game will grow (PRD #500). On
   * restores Find a game whole — the bridge is not burned (story 141). With it off, a link to the
   * builder or pool under Play lands on Play's root — a search already under way is finished.
   * Fill-the-seat and the Players tab are not behind it.
   *
   * - **Owner:** the Play tab — `features/play` for Find a game, `features/find_a_game_next` for
   *   what grows under Explore.
   * - **Purpose:** keep the current Find a game one pull request away while Groups ships and the
   *   rebuild grows under Explore.
   * - **Removal:** when the rebuild has reached everyone, this key goes with the old screen, the
   *   gate in `play/index.tsx` and the two redirects in `play/builder.tsx` and `play/pool.tsx`.
   */
  find_a_game: false,
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
 * refuses it. `isTester` is how a feature reaches the testers first without the datafile ever
 * saying who they are (§9).
 *
 * `platform` and `appVersion` are absent when the build cannot say — a rule that targets them
 * then does not match, which is the honest answer for a device that did not identify itself.
 */
export interface FlagContext {
  readonly playerId: string;
  readonly isTester: boolean;
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
