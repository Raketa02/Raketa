/**
 * Which route each of the three tabs is, and which tab a route is inside.
 *
 * **The shell keeps no per-tab history**, so this table is not "each tab's last position" —
 * it is each tab's *only* position. Home is the shell's root and is never laid down again once it
 * is up; You and Play are laid down over it, fresh, on every press, and their depth is thrown away
 * every time a player leaves them ([#227](https://github.com/Raketa02/Raketa/issues/227) — one
 * stack, not three).
 *
 * Pure on purpose: the rule below is what draws the bar's active column on every screen in
 * the app, and it is worth being able to state a route and read back a tab without a
 * renderer.
 */

import type { TabBarKey } from '@/shared/ui';

/**
 * Each tab's route, as a literal the router's typed hrefs accept.
 *
 * `home` is `/` rather than `/home` because it is the shell's root: the entry gate lands a
 * player at `/`, and a second spelling for the screen they land on would be two answers to
 * where the app opens. It was `now` until Now was renamed Home
 * ([#550](https://github.com/Raketa02/Raketa/issues/550)), and the route did not move.
 */
export const SHELL_TAB_ROOT = {
  home: '/',
  play: '/play',
  you: '/you',
} as const satisfies Record<TabBarKey, string>;

/** Any one of the three, as a route. Named so a caller can hold one without widening it. */
export type ShellRoute = (typeof SHELL_TAB_ROOT)[TabBarKey];

/**
 * The stack ⚡Play lays down: **Home underneath, Play's root on top.**
 *
 * Two entries rather than one, and that is the whole of *back leaves Play entirely* — a
 * player who presses back from Play is on Home because Home is what is behind it, not
 * because a screen refused to be the last one. The arrangement is stated once, here, rather
 * than pushed at a call site.
 */
export const PLAY_STACK = [SHELL_TAB_ROOT.home, SHELL_TAB_ROOT.play] as const;

/**
 * The stack You lays down: **Home underneath, You on top** — Play's arrangement, for the same
 * reason: *back* from a tab that is not Home goes to Home, the start of the app, and never out of
 * it from a screen that is not the start.
 */
export const YOU_STACK = [SHELL_TAB_ROOT.home, SHELL_TAB_ROOT.you] as const;

/**
 * **What a press of each tab lays down, bottom first — and the bottom is always Home.**
 *
 * That is what lets a press **keep** Home rather than build it again. Home is the heaviest screen
 * in the app — every row's cards, every face — and it was rebuilt from nothing on every press of
 * every tab, ⚡Play included, because Play's stack starts with it: a device measured four seconds
 * of a frozen bar for each. With Home the bottom of every stack, a press pops back to the Home that
 * is already there and lays only the tab's own screens over it, so *pressing a tab goes to its
 * start* is still exactly what happens, and Home is drawn once.
 */
export const TAB_STACK = {
  home: [SHELL_TAB_ROOT.home],
  play: PLAY_STACK,
  you: YOU_STACK,
} as const satisfies Record<TabBarKey, readonly [typeof SHELL_TAB_ROOT.home, ...ShellRoute[]]>;

/**
 * The segments that are **inside** a tab without being its root.
 *
 * Play needs none: its root is `/play`, so everything under it shares that first segment and the
 * rule below lights the right column for free. Home is the one tab that cannot do that — its root
 * is `/`, which is the shell's own root and has no segment — so a screen pushed over it is
 * necessarily a sibling at the top level. Naming it here is what makes the Home column stay lit
 * on a booked game rather than falling through to the default answer below, which is the same answer
 * for a path the shell does not own at all.
 */
const INSIDE_A_TAB: Readonly<Partial<Record<string, TabBarKey>>> = {
  // A booked game's details, its chat and its result (#556) — pushed over Home.
  booking: 'home',
  // The recent notices behind Home's bell (#559).
  notices: 'home',
  // Rankings, behind the trophy left of the bell (#775; Q11: the Home tab stays lit).
  rankings: 'home',
  // New in Rakieta's See all, behind its row's *See all ›* (#801; the Home rows screens §1).
  'new-in-rakieta': 'home',
  // Same competitive level's See all (#802; the Home rows screens §1).
  'same-level': 'home',
  // Same vibe's See all (#803).
  'same-vibe': 'home',
  // The Groups heating up page, behind its line's *All groups ›* (#823; ADR-0205 §7).
  'hottest-groups': 'home',
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
 * That is not a convenience: a group's page and everything over it are `/play/…`, and a player
 * is inside the tab for the length of a whole flow, which is exactly what the ring is for.
 * Matching the whole path would go dark on the second screen.
 *
 * A path the shell does not own answers `home`, because the shell's own root is the only
 * honest answer to a question it should never be asked: everything outside `(tabs)` —
 * sign-in, the questionnaire, the six profile steps — draws no bar at all.
 */
export function tabForPathname(pathname: string): TabBarKey {
  const [, segment = ''] = pathname.split('/');
  return TAB_FOR_SEGMENT[segment] ?? 'home';
}

/**
 * Whether the bar **stands down** on a pathname — drawn nowhere, rather than drawn and hidden.
 *
 * One route does this: **a booked game's chat** ([#556](https://github.com/Raketa02/Raketa/issues/556)),
 * where the composer replaces the bar so the keyboard and the stream get the whole screen
 * ([#400](https://github.com/Raketa02/Raketa/issues/400)). It is a fact about **which screen the
 * player is on** and so belongs beside `tabForPathname`, which is the other thing the shell reads
 * off a route — and it is pure for the same reason that one is: stated here it can be read back
 * without a renderer, and the shell that draws the bar learns nothing about what a room is.
 *
 * **The match is the whole shape and not a prefix**: `booking`, the booking's id, `chat`, and
 * nothing after. The details and the result beside it keep their bar.
 *
 * **The column stays lit while the bar is down.** `tabForPathname` still answers `home` for the
 * room, and that is deliberate: standing the bar down is a fact about the chrome, not about where
 * the player is, and the two answers are read by two different callers.
 */
export function barStandsDown(pathname: string): boolean {
  const [, first, bookingId, room, ...after] = pathname.split('/');
  return (
    first === BOOKING_SEGMENT &&
    bookingId !== undefined &&
    bookingId !== '' &&
    room === ROOM_SEGMENT &&
    after.length === 0
  );
}

/** A booked game's segment over Home, and its room's under it — `/booking/{id}/chat` (#556). */
const BOOKING_SEGMENT = 'booking';
const ROOM_SEGMENT = 'chat';
