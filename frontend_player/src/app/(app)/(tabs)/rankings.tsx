import { useLocalSearchParams } from 'expo-router';

import { RankingsScreen, parseRankingsParams } from '@/features/rankings/types';

/**
 * **Rankings** (#775) — pushed over Home by the trophy, on the trophy's sport; or landed by the entry
 * gate, on the sport a pass begun at *Get your {sport} level* returns to. A sport the address names
 * that this build does not know is no sport: the page opens on the deck's last, or padel.
 */
export default function RankingsRoute() {
  const { sport } = parseRankingsParams(useLocalSearchParams());
  return <RankingsScreen {...(sport === undefined ? {} : { sport })} />;
}
