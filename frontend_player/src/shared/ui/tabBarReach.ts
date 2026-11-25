/**
 * **The tab bar's reach** — the room the bar takes at the bottom of the phone
 * ([ADR-0210](../../../../docs/adr/0210-the-tab-bar-floats-as-glass-and-its-selection-travels.md)
 * §3, [#881](https://github.com/Raketa02/Raketa/issues/881)).
 *
 * The bar floats over the screen and owns no layout (10.1): every screen inside the tabs draws to
 * the bottom of the phone, so nothing ends above the bar because it is a flex sibling any more. What
 * used to be free is now **placed by one measure** — the bar's height and the bottom inset under it
 * while it is drawn, and **nothing while it stands down** (the chat, and Android's keyboard up):
 *
 * | What | Where |
 * | --- | --- |
 * | A scroller's end | padding of reach + its own gap — 15 for most, today's gap above the bar |
 * | The Games deck's ✕ · i · ✓ | reach + 15 |
 * | Post a game, *New group*, the rankings' jump | reach + the gutter |
 * | A screen with a pinned button | its layout ends at the reach, the button above the bar in flow |
 * | The Undo toast | 9 above the reach, or above the bottom inset while the bar stands down (`useRoomAtTheBottom`) |
 * | The toast | 9 above the **full** reach on every screen, from the insets alone (`useFullTabBarReach`) |
 *
 * ## A followed value, and drawn
 *
 * It is the page band's pattern (`onScreen.ts`): a value the shell says and anything follows,
 * rather than a context — because what follows it is not all under the shell. A sheet's content
 * keeps the root's contexts only (ADR-0178), and the toast host sits at the root, above the shell.
 * **Unlike the band, the reach is drawn**: it sets paddings and where a screen ends, so a reader
 * redraws when it moves — at the chat's stand-down and return, and at the Android keyboard's
 * (#882). A reader that took it once at mount would keep a band the bar no longer takes.
 *
 * **There is one shell at a time** — the root is a `Slot`, so the player's tabs and the
 * administrator's area never stand side by side — and so one value.
 *
 * It never imports a feature: which bar a shell draws, and when it stands down, are the shell's.
 */

import { useLayoutEffect, useRef, useSyncExternalStore } from 'react';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { followable } from './onScreen';
import { tabBarReachOver, type TabBarKind } from './TabBar';

/** What the shell drawing a bar says — nothing while no shell has said anything. */
const reach = followable<number>();

/**
 * What a shell mounting now will say, before its layout effect has told anyone (below) — ahead of
 * whatever the shell it replaces still says, which is gone by the end of the same commit.
 */
let opening: number | undefined;

const reachNow = () => opening ?? reach.get() ?? 0;

/**
 * **The reach now** — the bar's height and the bottom inset while a shell draws it, and nothing
 * while it stands down or outside every shell. A screen inside the tabs ends at it.
 */
export function useTabBarReach(): number {
  return useSyncExternalStore(reach.follow, reachNow, reachNow);
}

/**
 * **The full reach** — the player's bar's, from the insets alone, whether a bar is drawn, standing
 * down or absent. **The toast's**: it sits 9 above it on every screen, as it sat 9 above the full bar
 * on every screen before the bar floated — so in the chat, where there is no bar, it still clears the
 * composer, and in the administrator's area it clears that shorter bar too (9.2).
 */
export function useFullTabBarReach(): number {
  return tabBarReachOver('player', useSafeAreaInsets().bottom);
}

/**
 * **The room something standing at the bottom leaves** — the reach while a bar is drawn, and the
 * bottom inset, the home indicator's, while none is. The Undo toast follows the bar this way, and so
 * does a pinned button on a screen drawn both inside a shell and outside one (*Start playing*).
 */
export function useRoomAtTheBottom(): number {
  return Math.max(useTabBarReach(), useSafeAreaInsets().bottom);
}

/**
 * **What a shell says**: the reach of the bar it draws while `drawn`, and nothing while it stands
 * down — said again whenever either moves, and withdrawn when the shell goes.
 *
 * **A screen mounted with the shell reads it on its first render.** The shell renders before what it
 * holds, so on the shell's first render its value is put in place without telling anyone — the
 * screens mounting with it are not following yet — and the layout effect then says it properly.
 * Otherwise every screen would draw its first frame at the phone's foot and jump to the reach a frame
 * later: the administrator's *New group*, as the area opens. **It goes ahead of the shell it
 * replaces**: a profile switch swaps one shell for the other in one commit, the old one's reach still
 * standing while the new area renders — the code review's catch, a frame 14pt off.
 */
export function useSaysTabBarReach(bar: TabBarKind, drawn: boolean): void {
  const { bottom } = useSafeAreaInsets();
  const said = drawn ? tabBarReachOver(bar, bottom) : 0;
  const mounting = useRef(true);

  if (mounting.current) opening = said;

  useLayoutEffect(() => {
    mounting.current = false;
    opening = undefined;
    reach.set(said);
  }, [said]);

  useLayoutEffect(
    () => () => {
      reach.set(undefined);
    },
    [],
  );
}
