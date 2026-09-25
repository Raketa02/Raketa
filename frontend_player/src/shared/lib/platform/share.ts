/**
 * The system share sheet, behind a port. **The only module that imports React Native's `Share`**
 * ([#513](https://github.com/Raketa02/Raketa/issues/513)).
 *
 * A group's page sends its link through whatever the player has installed — WhatsApp, Messages,
 * a mail — with **Share the link** (PRD #500 story 64). It is a port and not a line in a component
 * on the clipboard's argument: the sheet is native, a suite cannot open one, and a screen that
 * called it directly is a screen no suite could see send anything.
 *
 * **One verb, and it never rejects.** Dismissing the sheet is the player's answer rather than an
 * error, and a sheet that could not open has nothing the screen could say about it; either way
 * the page stays as it was. The fake in `src/test-support/platform.ts` keeps the same promise and
 * records what was offered.
 */

import { Share } from 'react-native';

/**
 * What the app may ask of the share sheet.
 *
 * Screens depend on this interface; `deviceShare` is the one implementation that talks to the OS,
 * and a test substitutes `fakeShare()` from `src/test-support/platform.ts`.
 */
export interface SharePort {
  /** Open the sheet with this text in it — a sentence carrying a link. Settles once it closes. */
  readonly shareText: (message: string) => Promise<void>;
}

export const deviceShare: SharePort = {
  async shareText(message) {
    try {
      await Share.share({ message });
    } catch {
      // Not opened. The button stays where it is, and pressing it again asks again.
    }
  },
};
