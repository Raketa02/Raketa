/**
 * **The next Find a game — empty, for now.**
 *
 * What the Play tab's root shows when the `classic_play` flag is off
 * ([ADR-0180](../../../../../docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md)
 * §7, [#479](https://github.com/Raketa02/Raketa/issues/479)). Find a game is about to be rebuilt,
 * and the rebuild needs somewhere to live while the current one keeps working: this feature is
 * that place, and this screen is where it starts.
 *
 * **No copy, deliberately.** Nothing here says *coming soon*, because there is no promise to make
 * yet and a sentence written now is one the rebuild inherits without anybody deciding it. The tab
 * bar is the shell's and stays drawn, so a player who lands here can leave the way they came.
 *
 * Its own feature rather than a file in `features/play`, so the new version grows in a folder
 * that has never held the old one, and deleting the old one later is deleting a folder.
 */

import { StyleSheet, View } from 'react-native';

import { theme } from '@/shared/ui';

/**
 * How a suite finds a screen with nothing on it. There is no text to query by and no control to
 * press, so the one observable thing about it is that it is the screen that is there.
 */
export const FIND_A_GAME_NEXT_TEST_ID = 'find-a-game-next';

export function FindAGameNextScreen() {
  return <View style={s.screen} testID={FIND_A_GAME_NEXT_TEST_ID} />;
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
});
