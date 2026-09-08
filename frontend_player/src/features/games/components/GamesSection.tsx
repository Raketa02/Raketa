/**
 * **Your games, on the Now tab** — the one way into the result argument.
 *
 * It is a section composed under a placeholder rather than the Now tab being built, which is
 * exactly what the You tab already does with `PlayIntentsSection`: the tab owns its citation and
 * nothing that is drawn under it. The line above it still says what Now becomes, because two
 * thirds of that is still owed.
 *
 * **One list and not several.** A game awaiting an entry, one awaiting an answer and one that
 * never happened are one thing at three moments of its life, and shelving them here would make
 * the client's shelves the platform's opinion about which of them matters. Nothing re-sorts it
 * either: the order is *newest arrangement first* and it is the server's.
 *
 * **Nothing is drawn when there is nothing.** Now *"deliberately never says nothing is
 * happening"* — it is where a send lands, and a challenge whose line-up has not completed is not
 * a game yet — so an empty list renders no section at all rather than an emptiness the tab has
 * refused to assert since it was built.
 *
 * **The row's sentence is the screen's sentence.** `standingLine` is called once and read twice,
 * so a player who reads a row, taps it, and finds a different deadline is not a state this can
 * reach.
 */

import { router } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { useCurrentUser } from '@/features/auth/types';
import { sportLabel } from '@/features/onboarding/types';
import { recoveryMessage } from '@/shared/errors';
import { Note, PressableCard, theme } from '@/shared/ui';

import type { Game } from '../domain/game';
import { resultArgument } from '../domain/resultArgument';
import { useGames } from '../hooks/useGames';

import { gameRowLabel } from './gameAccessibility';
import { GAMES_HEADING, gameEyebrow, standingLine } from './gamePresentation';

/** Where a row goes. Declared here because this is the only screen that pushes it. */
export const GAME_ROUTE = '/games/[gameId]';

export function GamesSection() {
  const games = useGames();
  const me = useCurrentUser().data?.id;

  const rows = games.data ?? [];

  // Nothing to say yet, and nothing to say about having nothing. The read's own failure is
  // still worth a sentence: a section that vanished on an error would be indistinguishable
  // from the empty case, which is the one thing a list of your own games must not be.
  if (games.error !== null) {
    return (
      <View style={s.section}>
        <Text style={s.heading}>{GAMES_HEADING}</Text>
        <Note variant="coral" accessibilityRole="alert">
          {recoveryMessage(games.error)}
        </Note>
      </View>
    );
  }

  if (rows.length === 0 || me === undefined) return null;

  return (
    <View style={s.section}>
      <Text style={s.heading}>{GAMES_HEADING}</Text>
      {rows.map((game) => (
        <GameRow key={game.gameId} game={game} playerId={me} />
      ))}
    </View>
  );
}

function GameRow({ game, playerId }: { readonly game: Game; readonly playerId: string }) {
  const sport = sportLabel(game.sport);
  const line = standingLine(resultArgument(game, playerId), game.readAt);

  return (
    <PressableCard
      accessibilityLabel={gameRowLabel(sport, game, playerId, line)}
      onPress={() => router.push({ pathname: GAME_ROUTE, params: { gameId: game.gameId } })}
    >
      <Text style={s.eyebrow}>{gameEyebrow(sport, game, playerId)}</Text>
      <Text style={s.line}>{line}</Text>
    </PressableCard>
  );
}

const s = StyleSheet.create({
  section: { gap: theme.space.sm, marginTop: theme.space.lg },
  heading: { ...theme.type.h2, color: theme.color.ink },
  eyebrow: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: 'uppercase',
    marginBottom: theme.space.xxs,
  },
  line: { ...theme.type.tiny, color: theme.color.ink },
});
