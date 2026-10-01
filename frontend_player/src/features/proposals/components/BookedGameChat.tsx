/**
 * **A booked game's chat** — the room, opened from the game's details and from nowhere else
 * ([#556](https://github.com/Raketa02/Raketa/issues/556); the screens A4.4; the mechanics §14.3).
 *
 * `conversations`' own screen in its booked form: no plan card, no plan chips, no *Details* door,
 * and the header's second line the booking's word. The room is found by the join keyed by the
 * game (`useGameRoom`) over the booking the details just read — both answered from the cache on the
 * way in — so the route carries only the booking's id, and *back* is the details by the stack.
 *
 * While the room is still being found the screen says so with the muted spinner; a room the list
 * does not hold — the game's chat closed, or not open yet — is one sentence and the back chevron.
 */

import { router } from 'expo-router';
import { ActivityIndicator, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ConversationScreen, useGameRoom } from '@/features/conversations/types';
import { Note, ScreenHeader, theme } from '@/shared/ui';

import { useBooking } from '../hooks/useHome';

import { HOME_GAME_COPY } from './homeCopy';
import { statusWord } from './homePresentation';

const COPY = HOME_GAME_COPY.details;

export interface BookedGameChatProps {
  /** Validated by `schemas/bookingParams` before it reaches here; the route does that. */
  readonly bookingId: string;
}

export function BookedGameChat({ bookingId }: BookedGameChatProps) {
  const read = useBooking(bookingId);
  const game = read.data ?? undefined;
  const room = useGameRoom(game?.gameId);

  if (game !== undefined && room.conversationId !== undefined) {
    return (
      <ConversationScreen
        conversationId={room.conversationId}
        booked={{ state: statusWord(game.status).toLowerCase() }}
      />
    );
  }

  const finding = read.isPending || (game !== undefined && !room.listed);
  return (
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      <ScreenHeader compact onBack={() => router.back()} backLabel={COPY.back} />
      <View style={s.body}>
        {finding ? (
          <ActivityIndicator accessibilityLabel={COPY.findingRoom} color={theme.color.muted} />
        ) : (
          <Note>{COPY.noRoom}</Note>
        )}
      </View>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  body: { padding: theme.size.gutter, gap: theme.space.sm },
});
