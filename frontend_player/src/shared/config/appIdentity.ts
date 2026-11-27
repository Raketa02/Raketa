/**
 * Who the app says it is, as a pure function of the environment.
 *
 * Two questions, one answer: what the OS shows under the icon, and whether a badge sits
 * over the running app. They are one decision because they are one sentence — *this build
 * is not production* — said in the two places a person looks.
 *
 * **This module imports nothing at runtime**, and that is what the separation is for. It
 * is loaded twice by two different runtimes: by Metro inside the app, and by Node when
 * Expo evaluates `app.config.ts`. `AppEnvironment` is a type-only import, so it erases —
 * pulling in `env.ts` would drag zod and `process.env` substitution into a config
 * document that runs before any of that exists. It also means the table below is
 * unit-testable without booting the platform's config resolver: no `loadEnv`, no
 * memoized module state, no `EXPO_PUBLIC_*` at all.
 *
 * There is exactly **one** installable variant — one bundle identifier, one URL scheme,
 * no build profiles. Three installable apps that all reach the same laptop would be
 * ceremony; per-environment identifiers wait until a second backend exists. So the
 * identity is a *runtime* fact about the build, and the badge is how you read it.
 */

import type { AppEnvironment } from './env';

export interface AppIdentity {
  /** The `expo.name` the OS shows under the icon and in the app switcher. */
  readonly displayName: string;
  /**
   * The badge's text, or `null` for no badge at all.
   *
   * One nullable field rather than `showBadge: boolean` beside `badgeLabel: string` —
   * those two can disagree, and a badge that is shown with nothing written on it is a
   * state nobody should have to defend against. Absent or present-with-a-word.
   */
  readonly badge: string | null;
}

/**
 * Written out per environment rather than derived from the name, for the reason
 * `REQUIRED_SCHEME` is: an exhaustive `Record<AppEnvironment, …>` means a fifth
 * environment fails to compile until somebody decides what the app is called there and
 * whether it is badged — rather than silently inheriting production's clean look, which
 * is the one wrong answer that is invisible.
 *
 * `production` is the only unbadged one, and it is deliberately also the only one whose
 * name has nothing appended: production stays visually clean, and everything else says
 * so on its face.
 */
const IDENTITIES: Readonly<Record<AppEnvironment, AppIdentity>> = {
  local: { displayName: 'Rakieta local', badge: 'LOCAL' },
  development: { displayName: 'Rakieta development', badge: 'DEVELOPMENT' },
  staging: { displayName: 'Rakieta staging', badge: 'STAGING' },
  production: { displayName: 'Rakieta', badge: null },
};

/**
 * The environments this table identifies — its own keys, never a second list.
 *
 * `env.ts` owns `ENVIRONMENTS`; this is the same four arrived at from the other side, and
 * a test asserts they agree. `Record<AppEnvironment, …>` already refuses a missing or
 * extra key at compile time, so the cast restores the literal type `Object.keys` erases
 * rather than asserting anything the type system has not already checked.
 */
export const IDENTIFIED_ENVIRONMENTS = Object.keys(IDENTITIES) as readonly AppEnvironment[];

/** The app's name and badge for an environment. Total — every environment has one. */
export function appIdentity(environment: AppEnvironment): AppIdentity {
  return IDENTITIES[environment];
}

/**
 * Narrow a raw string — `process.env.EXPO_PUBLIC_ENV` as Node hands it to `app.config.ts`,
 * where zod and the startup screen do not exist yet.
 *
 * Checked against `IDENTITIES`' own keys rather than against a second list of names, for
 * the reason above. `Object.hasOwn`, not `in`, because `'toString' in IDENTITIES` is true.
 */
export function isAppEnvironment(value: unknown): value is AppEnvironment {
  return typeof value === 'string' && Object.hasOwn(IDENTITIES, value);
}
