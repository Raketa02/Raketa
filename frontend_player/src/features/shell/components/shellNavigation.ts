/**
 * The shell's only navigation move: **throw everything above Home away and lay the tab down over
 * it.**
 *
 * There is one stack, not three. `expo-router`'s `<Tabs>` gives every tab its own history and
 * restores it on return — which is what it is for, and which fails
 * [#227](https://github.com/Raketa02/Raketa/issues/227)'s rule *silently*: a player who
 * leaves a group's page and comes back lands on the page, nothing throws, nothing looks wrong,
 * and the only way to notice is to do it deliberately. So the shell is a plain `Stack` and every
 * tab press **replaces** what is above Home.
 *
 * **Home itself is kept** (`TAB_STACK`: every stack starts with it). It used to be replaced too —
 * by every press of every tab, ⚡Play included, because Play's stack starts with Home — and Home is
 * the screen that costs the most to draw: a device spent four seconds rebuilding it per press.
 * Nothing about the rule needed that: the start of Home is Home, so popping back to the one already
 * there is landing at its start, and the shell tells it to show its top (`homeStart`).
 *
 * ## One function, and its callers
 *
 * `resetShellStack` is the whole mechanism, and what calls it are the halves of the rule: Home
 * lays down nothing over itself, You and ⚡Play each lay their root over Home, and **a game that has
 * just filled lands on `[Home]`** before its details are pushed over it (#555), so *back* from a
 * game is Home.
 *
 * ## Why the imperative `router` and not `useRouter()`
 *
 * Not every caller is a render path. The fill lands from the moment's own callback, and a rule
 * that had to be reached through a hook would be a rule the one caller that most needs it
 * cannot reach. The singleton is `expo-router`'s own imperative API, not a way around React.
 */

import { router } from 'expo-router';

import type { TabBarKey } from '@/shared/ui';

import { SHELL_TAB_ROOT, TAB_STACK, type ShellRoute } from '../domain/shellTabs';

import { sendHomeToItsStart } from './homeStart';

/** A stack the shell lays down: Home at the bottom, and whatever the tab puts over it. */
type ShellStack = readonly [typeof SHELL_TAB_ROOT.home, ...ShellRoute[]];

/**
 * Make the shell show exactly these screens, bottom first — **keeping the Home at the bottom.**
 *
 * Three moves: collapse whatever depth the player was in, land on Home, then push the rest.
 * `dismissAll` is what makes Home the *bottom* of the new stack rather than a screen pushed on top
 * of an old one — without it, leaving a group's members for You would leave the group's page
 * sitting behind You, and back would walk a history nobody made.
 *
 * **Landing on Home is `dismissTo`, never `replace`.** After `dismissAll` the screen left is the
 * stack's bottom, which is Home on every stack the shell lays down — and `dismissTo` leaves a Home
 * it finds exactly where it is, mounted, which is the whole saving. It replaces the screen only when
 * it is *not* Home: a stack that began somewhere else, like a link opened straight onto `/you`.
 */
function resetShellStack(stack: ShellStack): void {
  const [home, ...above] = stack;

  if (router.canDismiss()) router.dismissAll();
  router.dismissTo(home);
  if (above.length === 0) sendHomeToItsStart();
  for (const route of above) router.push(route);
}

/**
 * Open a tab. **Always at its start** — there is no position to restore, by construction.
 *
 * No tab is a special case with a special caller: each is a row of `TAB_STACK`, Home's one screen
 * deep and You's and ⚡Play's two.
 *
 * ## A tab you are already standing on is not somewhere to be sent
 *
 * The reset is the whole mechanism, and for a while it ran on **every** press — so a player
 * tapping Play while Play's root was on screen had it rebuilt underneath them, and whatever
 * they had on it went with it. No screen was reached that was not already there; what the press
 * bought was a reload. On the gesture people press twice when something feels slow, that is the
 * worst possible answer.
 *
 * The rule this function serves is *pressing a tab goes to that tab's start*, and it is
 * satisfied — with nothing to do — for a player who is already there. So the press is
 * measured against **where they are**, and the only case it declines is the one where the
 * answer and the question are the same screen. Every other press still resets: from another
 * tab, and from anywhere deeper inside this one, which is where *the shell keeps no per-tab
 * history* is actually observable.
 *
 * **It is `where` and not a flag the bar holds.** The bar already draws its active column
 * from the path (`tabForPathname`) rather than from state, for the reason a second copy is
 * always the one that disagrees — after a deep link, a redirect, or the hardware back
 * button — and a press that consulted a different answer than the one drawn under the
 * player's thumb would be that same bug with a longer fuse.
 *
 * @param where the pathname the player is on. `usePathname()`'s, which is the same value the
 *   bar's own lit column is read from.
 */
export function openTab(tab: TabBarKey, where: string): void {
  if (where === startOf(tab)) return;

  resetShellStack(TAB_STACK[tab]);
}

/**
 * The screen a press of this tab would land on — the **top** of what it lays down.
 *
 * You's and Play's starts are two screens and the one a player would be looking at is the second,
 * so this is the last entry of the stack rather than its root. Read off `TAB_STACK` itself rather
 * than spelled again, because *which screen a tab opens on* is a fact that already has one home
 * and a second spelling of it is the one that goes stale.
 */
function startOf(tab: TabBarKey): string {
  const stack = TAB_STACK[tab];
  return stack[stack.length - 1]!;
}

/**
 * **Where a game that has just filled lands: `[Home]`**, with its details pushed over it by the
 * caller (#555) — so *back* from the game is Home, whichever screen the yes was said on.
 */
export function landOnHome(): void {
  resetShellStack(TAB_STACK.home);
}
