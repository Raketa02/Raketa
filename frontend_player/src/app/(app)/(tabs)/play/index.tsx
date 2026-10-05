/**
 * Play's entry. A directory rather than a file, because the builder, the pool and the groups
 * screens are `/play/…` and the bar's active column is read off that first segment.
 *
 * **Behind `classic_play`**
 * ([ADR-0180](../../../../../../docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md)
 * §7, [ADR-0189](../../../../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md)
 * §6). Read once, when this screen mounts: on, it is Find a game, as the old loop had it; off —
 * **the code default** — it is Play's *Groups | Explore* segment, with the empty screen the next
 * Find a game will grow in under *Explore*. It was `find_a_game` until
 * [#550](https://github.com/Raketa02/Raketa/issues/550) folded Find a game into the one flag that
 * brings the whole old loop back. A datafile that arrives while it is up changes nothing here —
 * the shell lays this screen down again on every entry to the tab, which is when the new answer
 * shows.
 */

import { useFeatureOnMount } from '@/features/feature_flags/types';
import { FindAGameScreen } from '@/features/play/types';
import { PlayScreen } from '@/features/shell/types';

export default function PlayRoute() {
  const classicPlay = useFeatureOnMount('classic_play');

  return classicPlay ? <FindAGameScreen /> : <PlayScreen />;
}
