import { GET_THE_APP_COPY } from '@/features/get-the-app/copy';

/** **The friend link's page's words**, and its preview's (the friends screens §11). */

export const FRIEND_LINK_COPY = {
  /**
   * What to do once installed. **An iPhone's install forgets the link**, so the person comes back
   * and taps the button once more (the friends mechanics §4.3); on Android the store button has
   * carried it through, and the line costs nothing.
   */
  comeBack: `Once you have the app, come back here and tap ${GET_THE_APP_COPY.openInRaketa}`,
} as const;

/** *Tomek invited you to play on Raketa*: the page's heading, and the preview's title. */
export function invitedYou(nickname: string): string {
  return `${nickname} invited you to play on Raketa`;
}

/**
 * *Tomek wants to be your friend*: the line a messenger draws under the title, and what the link
 * comes to once opened in the app, where Home words the request the same way.
 */
export function wantsToBeYourFriend(nickname: string): string {
  return `${nickname} wants to be your friend`;
}
