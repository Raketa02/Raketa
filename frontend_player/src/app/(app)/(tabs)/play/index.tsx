/**
 * Play's entry. A directory rather than a file, because the builder, the pool and the groups
 * screens are `/play/…` and the bar's active column is read off that first segment.
 *
 * **Behind `find_a_game`**
 * ([ADR-0180](../../../../../../docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md)
 * §7). Read once, when this screen mounts: on, it is Find a game; off — **the code default since
 * [#512](https://github.com/Raketa02/Raketa/issues/512)** — it is Play's *Groups | Explore*
 * segment, with the empty screen the next Find a game will grow in under *Explore*. A datafile
 * that arrives while it is up changes nothing here — the shell lays this screen down again on
 * every entry to the tab, which is when the new answer shows.
 */

import { useFeatureOnMount } from '@/features/feature_flags/types';
import { FindAGameScreen } from '@/features/play/types';
import { PlayScreen } from '@/features/shell/types';

export default function PlayRoute() {
  const findAGame = useFeatureOnMount('find_a_game');

  return findAGame ? <FindAGameScreen /> : <PlayScreen />;
}
