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
 * ## One function, two callers
 *
 * `resetShellStack` is the whole mechanism, and the two things that call it are the two
 * halves of the rule: a flanking tab lays down one screen, and Play lays down two. A later
 * ticket adds the third — the *Find a game* segment re-enters the tab from inside it
 * ([#268](https://github.com/Raketa02/Raketa/issues/268)), and re-entering is arriving, not
 * going back — and a fourth, the send, which ends a Play session by landing the player on
 * `[Now]` with the line-up gone
 * ([#274](https://github.com/Raketa02/Raketa/issues/274)). **A Play session ends exactly
 * when this function runs**, which is the definition
 * [#264](https://github.com/Raketa02/Raketa/issues/264) is owed — and now the thing it does:
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
 * The callers still to come are not all render paths. The send resets from a mutation's
 * `onSuccess`, and a rule that had to be reached through a hook would be a rule the one
 * caller that most needs it cannot reach. The singleton is `expo-router`'s own imperative
 * API, not a way around React.
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
 */
export function openTab(tab: TabBarKey): void {
  if (tab === 'play') {
    enterPlay();
    return;
  }

  resetShellStack([SHELL_TAB_ROOT[tab]]);
}

/**
 * Play's entry: **Find a game, whichever Play screen was last open**, with Now behind it.
 *
 * Separate from `openTab` because it is the half of the shell another feature calls. The
 * segmented control's *Find a game* is the same operation as pressing ⚡, which is why a
 * player on the deck who taps it does not go back — they arrive.
 */
export function enterPlay(): void {
  resetShellStack(PLAY_STACK);
}
