/**
 * Play's entry — its *Groups | Explore* segment. A directory rather than a file, because the
 * groups screens are `/play/…` and the bar's active column is read off that first segment.
 */

import { PlayScreen } from '@/features/shell/types';

export default function PlayRoute() {
  return <PlayScreen />;
}
