/**
 * **A booked game's result** — today's game screen, over the game's details
 * ([#556](https://github.com/Raketa02/Raketa/issues/556); the mechanics §14.1: the result states are
 * *unchanged from today*).
 *
 * A booking opens an ordinary Game (#541), and its result is told and agreed exactly as any game's
 * is: `games`' `GameScreen`, at the Game the booking names. It is composed here with the score
 * leading and nothing in its three Classic slots — **no plan** (the booking is the plan), **no
 * card** (the details below it are the card) and **no fill** (a seat open on a booking is a rescue,
 * #557's) — and no court, because the details drew the forecast already. The Game is found off the
 * booking's own read, which the details have just made.
 */

import { router } from 'expo-router';
import { ActivityIndicator, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { GameScreen } from '@/features/games/types';
import { Note, ScreenHeader, theme } from '@/shared/ui';

import { useBooking } from '../hooks/useHome';

import { HOME_GAME_COPY } from './homeCopy';

const COPY = HOME_GAME_COPY.details;

export interface BookedGameResultProps {
  /** Validated by `schemas/bookingParams` before it reaches here; the route does that. */
  readonly bookingId: string;
}

export function BookedGameResult({ bookingId }: BookedGameResultProps) {
  const read = useBooking(bookingId);
  const game = read.data ?? undefined;

  if (game !== undefined) {
    return (
      <GameScreen
        gameId={game.gameId}
        entryLead="the-score"
        card={null}
        court={null}
        plan={null}
        fill={null}
      />
    );
  }

  return (
    <SafeAreaView style={s.screen} edges={['top']}>
      <ScreenHeader compact onBack={() => router.back()} backLabel={COPY.back} />
      <View style={s.body}>
        {read.isPending ? (
          <ActivityIndicator accessibilityLabel={COPY.reading} color={theme.color.muted} />
        ) : (
          <Note>{COPY.gone}</Note>
        )}
      </View>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  body: { padding: theme.size.gutter, gap: theme.space.sm },
});
