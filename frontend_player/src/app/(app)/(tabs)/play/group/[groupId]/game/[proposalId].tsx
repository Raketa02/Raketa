import { Redirect, useLocalSearchParams } from 'expo-router';

import { GameDetailsScreen, parseGameDetailsParams } from '@/features/proposals/types';

/**
 * **A game still filling, in detail** — pushed over a group's page from its Games deck (the card, or
 * its **i**), under Play so the column stays lit, and *back* is the deck.
 *
 * Params that do not survive the schema are a screen about nothing — no group, no game, or a sport
 * or a kind the deck was never read for — and go to Play, as the group page's own route sends them.
 */
export default function GameDetailsRoute() {
  const parsed = parseGameDetailsParams(useLocalSearchParams());

  if (parsed === undefined) return <Redirect href="/play" />;

  return (
    <GameDetailsScreen
      groupId={parsed.groupId}
      proposalId={parsed.proposalId}
      sport={parsed.sport}
      kind={parsed.kind}
    />
  );
}
