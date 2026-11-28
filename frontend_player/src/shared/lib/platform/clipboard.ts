/**
 * The clipboard, behind a port. **The only module that imports `expo-clipboard`**
 * ([#512](https://github.com/Rakieta02/Rakieta/issues/512)).
 *
 * The first read of it arrived with *Join a group*'s **Paste** chip: a group link copied out of
 * WhatsApp is one tap from the field (PRD #500 story 30). It is a port and not a line in a
 * component on the other ports' argument — a native module has no JS implementation underneath
 * it, so a screen that imports one is a screen no suite can put a link in front of.
 *
 * **Two verbs, read and write.** The write arrived with a group page's **Copy link**
 * ([#513](https://github.com/Rakieta02/Rakieta/issues/513), story 65): the link the player sends
 * the crowd, one tap from anywhere they can paste.
 *
 * **Neither rejects.** A clipboard that cannot be read — refused by the OS, empty, holding an
 * image — is an empty string, and the chip does nothing with it; a write the OS refused answers
 * `false`, so the screen confirms only a copy that happened. The fake in
 * `src/test-support/platform.ts` keeps the same promises.
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
  /** Put this text on the clipboard. `true` once it is there, `false` if the OS refused it. */
  readonly writeText: (text: string) => Promise<boolean>;
}

export const deviceClipboard: ClipboardPort = {
  async readText() {
    try {
      return await Clipboard.getStringAsync();
    } catch {
      return '';
    }
  },
  async writeText(text) {
    try {
      return await Clipboard.setStringAsync(text);
    } catch {
      return false;
    }
  },
};
