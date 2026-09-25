/**
 * The clipboard, behind a port. **The only module that imports `expo-clipboard`**
 * ([#512](https://github.com/Raketa02/Raketa/issues/512)).
 *
 * The first read of it arrived with *Join a group*'s **Paste** chip: a group link copied out of
 * WhatsApp is one tap from the field (PRD #500 story 30). It is a port and not a line in a
 * component on the other ports' argument — a native module has no JS implementation underneath
 * it, so a screen that imports one is a screen no suite can put a link in front of.
 *
 * **One verb, read.** The app never writes to the clipboard here; *Copy link* is #513's, and it
 * grows a verb when it arrives.
 *
 * **It never rejects.** A clipboard that cannot be read — refused by the OS, empty, holding an
 * image — is an empty string, and the chip does nothing with it. The fake in
 * `src/test-support/platform.ts` keeps the same promise.
 */

import * as Clipboard from 'expo-clipboard';

/**
 * What the app may ask of the clipboard.
 *
 * Screens depend on this interface; `deviceClipboard` is the one implementation that talks to the
 * OS, and a test substitutes `fakeClipboard()` from `src/test-support/platform.ts`.
 */
export interface ClipboardPort {
  /** The text on the clipboard, or `''` when there is none the app can read. */
  readonly readText: () => Promise<string>;
}

export const deviceClipboard: ClipboardPort = {
  async readText() {
    try {
      return await Clipboard.getStringAsync();
    } catch {
      return '';
    }
  },
};
