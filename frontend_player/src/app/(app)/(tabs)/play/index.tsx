/**
 * Play's entry. A directory rather than a file, because the deck, the builder and the pool
 * are `/play/…` and the bar's active column is read off that first segment.
 *
 * **Behind `find_a_game`**
 * ([ADR-0180](../../../../../../docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md)
 * §7). Read once, when this screen mounts: on, it is Find a game; off, it is the empty screen the
 * next version will grow in. A datafile that arrives while it is up changes nothing here — the
 * shell lays this screen down again on every entry to the tab, which is when the new answer shows.
 */

import { useFeatureOnMount } from '@/features/feature_flags/types';
import { FindAGameNextScreen } from '@/features/find_a_game_next/types';
import { FindAGameScreen } from '@/features/play/types';

export default function FindAGameRoute() {
  const findAGame = useFeatureOnMount('find_a_game');

  return findAGame ? <FindAGameScreen /> : <FindAGameNextScreen />;
}
