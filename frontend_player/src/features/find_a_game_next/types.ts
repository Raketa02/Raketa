/**
 * The next Find a game's only public surface — today, the empty screen the Play tab shows while
 * the `find_a_game` flag is off (ADR-0180 §7).
 *
 * The folder carries the full layer set, empty, so the rebuild lands in a feature that already
 * has its shape rather than one that grows it screen by screen.
 */

export { FIND_A_GAME_NEXT_TEST_ID, FindAGameNextScreen } from './components/FindAGameNextScreen';
