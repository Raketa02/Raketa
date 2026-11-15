/**
 * **Arriving in the app on a screen inside a tab, laid down before the shell draws anything.**
 *
 * `resetShellStack` lays a stack down on a shell that is already on screen: it dismisses, replaces
 * and pushes through `router`, and each of those reaches the shell's own navigator. That is what a
 * tab press needs, and it is the wrong move for **arriving**. A rating pass tears the app's tree
 * down while its questions are up (the questionnaire is a sibling of `(app)`, under the root's
 * `Slot`), and every way out of it comes back at `/` — so the shell mounts on Home, Home is drawn,
 * and only then could the gate push the group the pass began on over it: Home for a frame, and the
 * group sliding in over it. On a device that read as a blink.
 *
 * So arriving is **one reset of the navigation state at the root**, with the whole stack nested in
 * it: `(app)` › `(tabs)` › the tab's start and the screen on top. The root's navigator has been
 * mounted since launch, so the reset needs nothing below it to be listening yet — which is why the
 * gate can make it before it renders the shell at all, and the shell's first frame is the screen on
 * top with the rest beneath it. **No screen in it animates**: a stack that mounts already holding
 * three screens shows the third.
 *
 * The state names screens as the file tree does — a file, or its folder's `index` — which is
 * the name `Stack.Screen` takes, so the shell resolves a pathname against the screens it already
 * names (`PUSHED_SCREENS`, held to the tree by its test) and the two roots it does not push.
 */

import { useNavigationContainerRef } from 'expo-router';
import { useCallback } from 'react';

import type { TabBarKey } from '@/shared/ui';

import { TAB_STACK } from '../domain/shellTabs';

import { PUSHED_SCREENS } from './pushedScreens';

/** The route groups the shell is mounted under: `src/app/(app)/(tabs)/`. */
const APP_GROUP = '(app)';
const TABS_GROUP = '(tabs)';

/** Every screen the shell's stack holds, by its state name: the pushed ones and the two unpushed roots. */
const SHELL_SCREENS: readonly string[] = ['index', 'you/index', ...PUSHED_SCREENS];

/**
 * What a tab press lays down beneath anything pushed over the tab, by pathname — the press's own
 * table, so a landing leaves exactly the stack a press would, Home at its bottom.
 */
const TAB_START: Readonly<Record<TabBarKey, readonly string[]>> = TAB_STACK;

/** A screen inside the shell, as a route: its pathname pattern and its params, an absent one left out. */
export interface ShellPlace {
  readonly pathname: string;
  readonly params?: Readonly<Record<string, string | undefined>>;
}

interface ShellScreenState {
  readonly name: string;
  readonly params?: Readonly<Record<string, string>>;
}

/**
 * The screen a pathname names — the file, or its folder's `index`. A pathname naming none of the
 * shell's screens is a programming error, said at once rather than landing on nothing.
 */
function screenOf({ pathname, params }: ShellPlace): ShellScreenState {
  const path = pathname.replace(/^\//, '');
  const name = [path, path === '' ? 'index' : `${path}/index`].find((one) =>
    SHELL_SCREENS.includes(one),
  );
  if (name === undefined) throw new Error(`No screen in the shell at ${pathname}`);
  if (params === undefined) return { name };
  const given = Object.entries(params).filter(
    (entry): entry is [string, string] => entry[1] !== undefined,
  );
  return { name, params: Object.fromEntries(given) };
}

/**
 * The landing: `land(tab, top)` puts the player in the app on `top`, with `tab`'s start beneath it
 * — exactly what that tab's press and a push of `top` would leave, so *back* walks the same way.
 * Made from a layout effect of the gate, before it renders the shell.
 */
export function useShellLanding(): (tab: TabBarKey, top: ShellPlace) => void {
  const navigation = useNavigationContainerRef();

  return useCallback(
    (tab: TabBarKey, top: ShellPlace) => {
      const routes = [...TAB_START[tab].map((pathname) => screenOf({ pathname })), screenOf(top)];
      const tabs = { index: routes.length - 1, routes };
      const root = navigation.getRootState();
      navigation.resetRoot({
        ...root,
        // The `(app)` route keeps its key, so the gate making this reset is not remounted by it —
        // and loses its params: the way in left a nested *go to Home* in them, which the shell's
        // stack would obey as it mounts, popping straight back to Home.
        routes: root.routes.map((route) =>
          route.name === APP_GROUP
            ? {
                key: route.key,
                name: route.name,
                state: { index: 0, routes: [{ name: TABS_GROUP, state: tabs }] },
              }
            : route,
        ),
      });
    },
    [navigation],
  );
}
