/**
 * The shell's only navigation move: **throw the stack away and lay a new one down.**
 *
 * There is one stack, not five. `expo-router`'s `<Tabs>` gives every tab its own history and
 * restores it on return — which is what it is for, and which fails
 * [#227](https://github.com/Raketa02/Raketa/issues/227)'s rule *silently*: a player who
 * leaves the deck and comes back lands on the deck, nothing throws, nothing looks wrong, and
 * the only way to notice is to do it deliberately. So the shell is a plain `Stack` and every
 * tab press **replaces** what is on it.
 *
 * ## One function, and all three of its callers
 *
 * `resetShellStack` is the whole mechanism, and what calls it are the three halves of the rule:
 * a flanking tab lays down one screen, ⚡Play lays down two, and **the send lays down `[Now]`**,
 * which is *a sent game is gone for good* ([#274](https://github.com/Raketa02/Raketa/issues/274)).
 * There was a fourth for as long as the deck lived under Play — the *Find a game* segment
 * re-entered the tab from inside it ([#268](https://github.com/Raketa02/Raketa/issues/268)),
 * re-entering being arriving rather than going back — and it left with the segment when the
 * deck moved to its own tab (ADR-0169 §1).
 * **A Play session ends exactly when this function runs**, which is the definition
 * [#264](https://github.com/Raketa02/Raketa/issues/264) is owed — and the thing it does:
 * every path through this function calls `endPlaySession`, so the working copy and the line-up
 * are cleared by *arriving somewhere*, never by a screen remembering to tidy up after itself.
 *
 * **The clear is here rather than on a Play screen's unmount** because leaving Play is the
 * event, and an unmount is not one: the builder unmounts when the court is pushed over it, and
 * a rule keyed on that would throw a half-built line-up away in the middle of building it.
 *
 * This is also why the shell is the one feature that reads across the boundary — one import of
 * one function from `features/play`'s public surface. The alternative is Play subscribing to
 * navigation, which is the same coupling pointed the other way and with a listener to leak.
 *
 * ## Why the imperative `router` and not `useRouter()`
 *
 * Not every caller is a render path. The send resets from a mutation's `onSuccess`, and a rule
 * that had to be reached through a hook would be a rule the one caller that most needs it
 * cannot reach. The singleton is `expo-router`'s own imperative API, not a way around React.
 */

import { router } from 'expo-router';

import { endPlaySession } from '@/features/play/types';
import type { TabBarKey } from '@/shared/ui';

import { PLAY_STACK, SHELL_TAB_ROOT, type ShellRoute } from '../domain/shellTabs';

/** A stack always has a bottom, so the root is not optional and the type says so. */
type ShellStack = readonly [ShellRoute, ...ShellRoute[]];

/**
 * Replace whatever the shell is showing with exactly these screens, bottom first.
 *
 * Three moves rather than one: collapse whatever depth Play left behind, replace the screen
 * underneath it, then push the rest. `dismissAll` is what makes the first argument the
 * *bottom* of the new stack rather than a screen pushed on top of an old one — without it,
 * leaving the pool for Chats would leave the builder and the court sitting behind Chats,
 * and back would walk a history nobody made.
 */
export function resetShellStack(stack: ShellStack): void {
  const [root, ...above] = stack;

  // First, because it is the definition rather than a consequence: a session is over the
  // moment the player is sent somewhere, and ⚡Play arriving again is an arrival too — AC-2
  // lands a returning player on Find a game with the week re-seeded, not on a builder they
  // left an hour ago.
  endPlaySession();

  if (router.canDismiss()) router.dismissAll();
  router.replace(root);
  for (const route of above) router.push(route);
}

/**
 * Open a tab. **Always at its start** — there is no position to restore, by construction.
 *
 * ⚡Play is not a special case with a special caller; it is the one tab whose start is two
 * screens deep.
 *
 * ## A tab you are already standing on is not somewhere to be sent
 *
 * The reset is the whole mechanism, and for a while it ran on **every** press — so a player
 * tapping Play while Find a game was on screen had it rebuilt underneath them: the session
 * ended, the working week went back to the profile's copy, and whatever they had ticked went
 * with it. No screen was reached that was not already there; what the press bought was a
 * reload. On the gesture people press twice when something feels slow, that is the worst
 * possible answer.
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

  if (tab === 'play') {
    enterPlay();
    return;
  }

  resetShellStack([SHELL_TAB_ROOT[tab]]);
}

/**
 * The screen a press of this tab would land on — the **top** of what it lays down.
 *
 * Play's start is two screens and the one a player would be looking at is the second, so this
 * is the last entry of the stack rather than its root. Read off `PLAY_STACK` itself rather
 * than spelled again, because *which screen Play opens on* is a fact that already has one
 * home and a second spelling of it is the one that goes stale.
 */
function startOf(tab: TabBarKey): string {
  return tab === 'play' ? PLAY_STACK[PLAY_STACK.length - 1]! : SHELL_TAB_ROOT[tab];
}

/**
 * Play's entry: **Find a game, whichever Play screen was last open**, with Now behind it.
 *
 * Once the half of the shell another feature called — the segmented control's *Find a game*
 * was the same operation as pressing ⚡, which is why a player on the deck who tapped it did
 * not go back but arrived. The segment went with the deck's move to Players (ADR-0169 §1), so
 * this is now the bar's own move for one column, kept named because Play's start is the one
 * that is two screens deep.
 */
export function enterPlay(): void {
  resetShellStack(PLAY_STACK);
}

/**
 * **Where a sent challenge lands: `[Now]`, and the Play session is over.**
 *
 * The fourth caller of the reset, and the one the module docblock has been naming since the
 * shell was built. It is `[Now]` rather than `[Now, …]` because there is nothing left to be
 * behind: the court the challenge was built on is gone, the line-up with it, and a stack that
 * kept the builder underneath would let back walk into a court whose people have already been
 * asked.
 *
 * **The confirmation is not here.** It is a toast the `challenges` feature owns, fired by the
 * caller *after* this returns — so it is spoken once the destination has mounted and the
 * platform's own screen-change notification does not clobber it
 * ([`the-words.md`](../../../../docs/specs/matchmaking/the-words.md) §20.10). Now is a
 * placeholder, which is exactly why that sentence is the whole confirmation and why it is the
 * one announcement in the app that interrupts.
 */
export function landOnNow(): void {
  resetShellStack([SHELL_TAB_ROOT.now]);
}
