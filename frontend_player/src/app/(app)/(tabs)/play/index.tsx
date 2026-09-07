/**
 * Play's entry. A directory rather than a file, because the deck, the builder and the pool
 * are `/play/…` and the bar's active column is read off that first segment.
 */

import { FindAGameScreen } from '@/features/play/types';

export default function FindAGameRoute() {
  return <FindAGameScreen />;
}
