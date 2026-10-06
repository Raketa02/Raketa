/**
 * **The next Find a game — empty, for now.**
 *
 * What Play › Explore shows ([#479](https://github.com/Raketa02/Raketa/issues/479),
 * [#512](https://github.com/Raketa02/Raketa/issues/512)). Find a game is to be rebuilt, and the
 * rebuild needs somewhere to live: this feature is that place, and this screen is where it starts.
 * The old Find a game it once stood in for went with the old loop
 * ([#576](https://github.com/Raketa02/Raketa/issues/576)), and the flag that chose between them
 * with it.
 *
 * **No copy, deliberately.** Nothing here says *coming soon*, because there is no promise to make
 * yet and a sentence written now is one the rebuild inherits without anybody deciding it. The tab
 * bar is the shell's and stays drawn, so a player who lands here can leave the way they came.
 *
 * Its own feature rather than a file in the old Play feature, so the new version grows in a folder
 * that never held the old one — and deleting the old one was deleting a folder.
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
