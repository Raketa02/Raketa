/**
 * Which route each of the five tabs is, and which tab a route is inside.
 *
 * **The shell keeps no per-tab history**, so this table is not "each tab's last position" —
 * it is each tab's *only* position. Four of the five are single-screen roots; Play is the
 * one with depth, and that depth is thrown away every time a player leaves it
 * ([#227](https://github.com/Raketa02/Raketa/issues/227) — one stack, not five).
 *
 * Pure on purpose: the rule below is what draws the bar's active column on every screen in
 * the app, and it is worth being able to state a route and read back a tab without a
 * renderer.
 */

import type { TabBarKey } from '@/shared/ui';

/**
 * Each tab's route, as a literal the router's typed hrefs accept.
 *
 * `now` is `/` rather than `/now` because it is the shell's root: the entry gate lands a
 * player at `/`, and a second spelling for the screen they land on would be two answers to
 * where the app opens.
 */
export const SHELL_TAB_ROOT = {
  now: '/',
  around: '/around',
  play: '/play',
  chats: '/chats',
  you: '/you',
} as const satisfies Record<TabBarKey, string>;

/** Any one of the five, as a route. Named so a caller can hold one without widening it. */
export type ShellRoute = (typeof SHELL_TAB_ROOT)[TabBarKey];

/**
 * The stack ⚡Play lays down: **Now underneath, Find a game on top.**
 *
 * Two entries rather than one, and that is the whole of *back leaves Play entirely* — a
 * player who presses back from Find a game is on Now because Now is what is behind it, not
 * because a screen refused to be the last one. It is also why the depth is stated here
 * rather than pushed at a call site: the second caller of the reset is the *Find a game*
 * segment ([#268](https://github.com/Raketa02/Raketa/issues/268)), which re-enters the
 * tab from inside it, and re-entering has to mean the same arrangement as arriving.
 */
export const PLAY_STACK = [SHELL_TAB_ROOT.now, SHELL_TAB_ROOT.play] as const;

/**
 * The table read the other way: first path segment to tab, with `''` for the root.
 *
 * Inverted from `SHELL_TAB_ROOT` rather than written out, so the two can never disagree
 * about a route — which is the failure a second hand-kept table has.
 */
const TAB_FOR_SEGMENT: Readonly<Partial<Record<string, TabBarKey>>> = Object.fromEntries(
  Object.entries(SHELL_TAB_ROOT).map(([tab, route]) => [route.slice(1), tab as TabBarKey]),
);

/**
 * Which tab a pathname belongs to — **by its first segment**, so Play stays lit for every
 * screen inside Play.
 *
 * That is not a convenience: the builder, the pool and the deck are `/play/…` and a player
 * is inside the tab for the length of a whole flow, which is exactly what the ring is for.
 * Matching the whole path would go dark on the second screen.
 *
 * A path the shell does not own answers `now`, because the shell's own root is the only
 * honest answer to a question it should never be asked: everything outside `(tabs)` —
 * sign-in, the questionnaire, the seven profile steps — draws no bar at all.
 */
export function tabForPathname(pathname: string): TabBarKey {
  const [, segment = ''] = pathname.split('/');
  return TAB_FOR_SEGMENT[segment] ?? 'now';
}
