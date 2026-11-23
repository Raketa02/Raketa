/**
 * **The system bars, on Android**: the status bar and the navigation bar. **The only module that
 * imports `expo-navigation-bar`** (#857). The contract and the status bar's stack are on
 * `systemBars.ts`; this file is the Android mechanics.
 *
 * ## The status bar
 *
 * One entry on React Native's stack, as on an iPhone, with the ground as well as light icons. **Its
 * translucency is left alone.** The root's bar draws the app under the status bar, and a paint that
 * changed that would move the whole splash and the tree under it by the bar's height.
 *
 * ## The navigation bar
 *
 * It has no stack: a write replaces what the window shows. So **each paint first reads what the bar
 * shows**, and its restore writes that look back: its colour and its buttons, light or dark. That is
 * what *exactly the system's own navigation bar* means on a phone whose look this app never chose.
 * It differs between makers, three buttons or a gesture bar, and between a light and a dark system
 * theme. It is read at every paint rather than once for the process, because a window Android
 * recreates under the same JavaScript (a font-size change) may have a look of its own by then.
 *
 * - **Every read and write waits for the one before it.** The module's calls are asynchronous, so a
 *   paint asked for while a restore's writes are still on their way reads the system's look after
 *   they land, never the night they are undoing.
 * - **A look that cannot be read is never painted over.** If the module will not say what the bar
 *   shows, the bar is left alone, because nothing here could give it back. The status bar is still
 *   painted.
 * - **The read drops the colour's alpha** (`#rrggbb`). The system's own bar is opaque until the app
 *   draws edge to edge, which SDK 52 does not.
 *
 * **A dev reload during the splash** starts a new JavaScript process on the same window, so its read
 * finds the night this one painted, and the night is what its restore gives back. Only a reload in
 * the splash's first three seconds does this, and only in development. Relaunching the app clears it.
 */

import * as NavigationBar from 'expo-navigation-bar';
import { StatusBar, type StatusBarProps } from 'react-native';

import type { SystemBarsPort } from './systemBars';

export type { SystemBarsPort } from './systemBars';

/** What the navigation bar shows: the two things a paint changes. */
interface NavigationLook {
  readonly colour: Awaited<ReturnType<typeof NavigationBar.getBackgroundColorAsync>>;
  readonly buttons: Awaited<ReturnType<typeof NavigationBar.getButtonStyleAsync>>;
}

/** What the navigation bar shows now, or `null` when the phone will not say. */
async function readLook(): Promise<NavigationLook | null> {
  try {
    const [colour, buttons] = await Promise.all([
      NavigationBar.getBackgroundColorAsync(),
      NavigationBar.getButtonStyleAsync(),
    ]);
    return { colour, buttons };
  } catch {
    return null;
  }
}

/** The navigation bar shows `look`: both writes are asked for, whichever the phone refuses. */
async function show(look: NavigationLook): Promise<void> {
  await Promise.all([
    NavigationBar.setBackgroundColorAsync(look.colour),
    NavigationBar.setButtonStyleAsync(look.buttons),
  ]);
}

/**
 * An Android phone's bars. A factory so a test can start from a phone nothing has painted yet; the
 * app holds one, `deviceSystemBars`, for the life of the process.
 */
export function androidSystemBars(): SystemBarsPort {
  /** The splash's entry on the status bar's stack, while it is painted. */
  let painted: StatusBarProps | null = null;
  /** What the navigation bar showed when it was last painted; `null` when it was left alone. */
  let found: NavigationLook | null = null;
  /** The navigation bar's reads and writes, one after another. */
  let turns: Promise<void> = Promise.resolve();

  function inTurn(step: () => Promise<void>): void {
    // A read or a write the phone refused leaves the bar as it was. The next step still runs.
    turns = turns.then(step).catch(() => undefined);
  }

  return {
    paint(ground) {
      if (painted !== null) return;
      painted = StatusBar.pushStackEntry({ barStyle: 'light-content', backgroundColor: ground });
      inTurn(async () => {
        found = await readLook();
        if (found !== null) await show({ colour: ground, buttons: 'light' });
      });
    },
    restore() {
      if (painted === null) return;
      StatusBar.popStackEntry(painted);
      painted = null;
      inTurn(async () => {
        if (found !== null) await show(found);
      });
    },
  };
}

export const deviceSystemBars: SystemBarsPort = androidSystemBars();
