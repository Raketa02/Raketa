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
 * The segments that are **inside** a tab without being its root.
 *
 * Play needs none: its root is `/play`, so everything under it shares that first segment and the
 * rule below lights the right column for free. Now is the one tab that cannot do that — its root
 * is `/`, which is the shell's own root and has no segment — so a screen pushed over it is
 * necessarily a sibling at the top level. Naming it here is what makes the Now column stay lit
 * on a game rather than falling through to the default answer below, which is the same answer
 * for a path the shell does not own at all.
 */
const INSIDE_A_TAB: Readonly<Partial<Record<string, TabBarKey>>> = {
  games: 'now',
};

/**
 * The table read the other way: first path segment to tab, with `''` for the root.
 *
 * Inverted from `SHELL_TAB_ROOT` rather than written out, so the two can never disagree
 * about a route — which is the failure a second hand-kept table has.
 */
const TAB_FOR_SEGMENT: Readonly<Partial<Record<string, TabBarKey>>> = {
  ...Object.fromEntries(
    Object.entries(SHELL_TAB_ROOT).map(([tab, route]) => [route.slice(1), tab as TabBarKey]),
  ),
  ...INSIDE_A_TAB,
};

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

/**
 * Whether the bar **stands down** on a pathname — drawn nowhere, rather than drawn and hidden.
 *
 * Two routes do this, and each is named in full. The first is the conversation, where the
 * composer replaces the bar so the keyboard and the stream get the whole screen
 * ([#400](https://github.com/Raketa02/Raketa/issues/400),
 * [`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §3). The
 * second is the **yes screen** under a challenge, where nothing replaces the bar and that is the
 * point: the screen is the whole phone — the faces, one word, two doors — and a bar under it
 * would be a way out the record says it does not have
 * ([ADR-0167](../../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
 * §2). It is a fact about **which screen the player is on** and so belongs beside
 * `tabForPathname`, which is the other thing the shell reads off a route — and it is pure for
 * the same reason that one is: stated here it can be read back without a renderer, and the
 * shell that draws the bar learns nothing about what a conversation or a yes is.
 *
 * **The match is the whole shape and not a prefix.** Everything under `/chats/…` shares the
 * inbox's column, and three of those screens keep their bar: the inbox itself, the challenge
 * screen and the game screen behind the room's own *Details* door at `…/details` — a `/chats/*`
 * match would take the bar off all of them, and a prefix match would take it off the last. What
 * stands it down is exactly the room — `chats`, `conversation`, the room's id, and nothing
 * after — and exactly the yes screen: `chats`, `challenge`, the challenge's id, `yes`, and
 * nothing after. The builder at `…/fill` beside it keeps its bar.
 *
 * **The column stays lit while the bar is down.** `tabForPathname` still answers `chats` for
 * both, and that is deliberate: standing the bar down is a fact about the chrome, not about
 * where the player is, and the two answers are read by two different callers.
 */
export function barStandsDown(pathname: string): boolean {
  // The first segment is read through the rule that already reads it, so *inside the Chats tab*
  // is one answer and not a second spelling of `SHELL_TAB_ROOT.chats`. What follows it is §0.2's
  // vocabulary: the static **kind** above the id, then the id, then nothing — or, for the yes
  // screen, the one static segment the challenge's screens hang under its id.
  const [, , kind, id, ...rest] = pathname.split('/');
  if (tabForPathname(pathname) !== 'chats' || id === undefined || id === '') return false;
  if (kind === 'conversation') return rest.length === 0;
  if (kind === 'challenge') return rest.length === 1 && rest[0] === YES_SCREEN_SEGMENT;
  return false;
}

/** The yes screen's own segment under a challenge — `/chats/challenge/{id}/yes`. */
const YES_SCREEN_SEGMENT = 'yes';
