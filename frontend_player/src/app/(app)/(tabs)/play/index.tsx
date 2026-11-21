/**
 * Play's entry — the groups under a *Groups* title, or its *Groups | Explore* segment while the
 * `explore` feature flag is on (#826). A directory rather than a file, because the
 * groups screens are `/play/…` and the bar's active column is read off that first segment.
 */

import { PlayScreen } from '@/features/shell/types';

export default function PlayRoute() {
  return <PlayScreen />;
}
