/**
 * The system share sheet, behind a port — and **WhatsApp**, the one app a message is sent to by
 * name. **The only module that imports React Native's `Share`**
 * ([#513](https://github.com/Raketa02/Raketa/issues/513)).
 *
 * A group's page sends its link through whatever the player has installed — WhatsApp, Messages,
 * a mail — with **Share the link** (PRD #500 story 64). It is a port and not a line in a component
 * on the clipboard's argument: the sheet is native, a suite cannot open one, and a screen that
 * called it directly is a screen no suite could see send anything.
 *
 * **Neither verb rejects.** Dismissing the sheet is the player's answer rather than an error, and a
 * sheet that could not open has nothing the screen could say about it; either way the page stays
 * as it was. The fake in `src/test-support/platform.ts` keeps the same promise and records what was
 * offered.
 *
 * ## WhatsApp, by its scheme, and the answer is whether it opened
 *
 * An administrator's one job is posting a group's link into its WhatsApp group, so **Post to
 * WhatsApp** opens WhatsApp with the message typed (PRD #500 story 128;
 * [#516](https://github.com/Raketa02/Raketa/issues/516)). It is the second verb here because it is
 * the same act as the sheet — a sentence carrying a link, sent out through another app — aimed at
 * one app. `whatsapp://send?text=` is WhatsApp's own scheme on both platforms, and **opening it is
 * the test of whether WhatsApp is installed**: `Linking.openURL` rejects on iOS when no app claims
 * the scheme and on Android when no activity resolves the intent. `canOpenURL` is not asked: on
 * iOS it answers only for schemes listed in `LSApplicationQueriesSchemes`, and on Android 11+ only
 * for packages declared in `<queries>` — two native settings for a question `openURL` answers on
 * its own. **The fallback is not here**: the port says whether WhatsApp took the message, and the
 * screen decides what a phone without it gets — the sheet — so a suite can see the decision made.
 */

import { Linking, Share } from 'react-native';

/**
 * What the app may ask of the share sheet.
 *
 * Screens depend on this interface; `deviceShare` is the one implementation that talks to the OS,
 * and a test substitutes `fakeShare()` from `src/test-support/platform.ts`.
 */
export interface SharePort {
  /** Open the sheet with this text in it — a sentence carrying a link. Settles once it closes. */
  readonly shareText: (message: string) => Promise<void>;
  /**
   * Open WhatsApp with this text typed, for the person to pick the chat and send. `true` once
   * WhatsApp has it; `false` when the phone has no WhatsApp to open.
   */
  readonly openWhatsApp: (message: string) => Promise<boolean>;
}

/** WhatsApp's own scheme — the chat picker, with the message typed and not yet sent. */
export function whatsAppUrl(message: string): string {
  return `whatsapp://send?text=${encodeURIComponent(message)}`;
}

export const deviceShare: SharePort = {
  async shareText(message) {
    try {
      await Share.share({ message });
    } catch {
      // Not opened. The button stays where it is, and pressing it again asks again.
    }
  },
  async openWhatsApp(message) {
    try {
      await Linking.openURL(whatsAppUrl(message));
      return true;
    } catch {
      // Nothing claims the scheme: no WhatsApp on this phone.
      return false;
    }
  },
};
