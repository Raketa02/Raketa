/**
 * **What a booked game's screens draw before there is a game to draw** (#556) — the details, the
 * room and the result each wait on a read first, and each says the same four things in its place:
 * offline, the read resumes; still reading, the muted spinner; a failure the player can retry, why
 * and the retry; and the terminal sentence — the game is not this player's, or its chat is not open.
 * The back chevron is there throughout, because each is pushed over the screen it came from.
 */

import { router } from 'expo-router';
import { ActivityIndicator, StyleSheet, View } from 'react-native';
import { SafeAreaView, type Edge } from 'react-native-safe-area-context';

import { offlineMessage, type AppError } from '@/shared/errors';
import { Note, ScreenHeader, theme } from '@/shared/ui';

import { HOME_GAME_COPY } from './homeCopy';
import { ReadFailed } from './ReadFailed';

const COPY = HOME_GAME_COPY.details;

/**
 * `GET /bookings/{id}`'s one refusal — no such booked game for this player — which is the terminal
 * sentence rather than a failure to retry.
 */
const BOOKING_NOT_FOUND = 'booking_not_found';

/** A read, as far as these screens ask about it. */
export interface ReadState {
  /** Held while offline, to resume on reconnect. */
  readonly paused: boolean;
  /** No answer yet. */
  readonly pending: boolean;
  /** The answer was a refusal — or `null`. */
  readonly error: AppError | null;
  readonly retry: () => void;
}

export interface BookingAbsentProps {
  readonly read: ReadState;
  /** The sentence once the read has answered with nothing to draw. */
  readonly gone: string;
  /** What the spinner is called while it waits. */
  readonly waiting: string;
  /** The room takes both edges, because the bar stands down there. */
  readonly edges: readonly Edge[];
}

export function BookingAbsent({ read, gone, waiting, edges }: BookingAbsentProps) {
  return (
    <SafeAreaView style={s.screen} edges={edges}>
      <ScreenHeader compact onBack={() => router.back()} backLabel={COPY.back} />
      <View style={s.body}>
        {read.paused ? (
          <Note variant="amber">{offlineMessage('resumes')}</Note>
        ) : read.pending ? (
          <ActivityIndicator accessibilityLabel={waiting} color={theme.color.muted} />
        ) : read.error !== null && read.error.code !== BOOKING_NOT_FOUND ? (
          <ReadFailed error={read.error} onRetry={read.retry} />
        ) : (
          <Note>{gone}</Note>
        )}
      </View>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  body: { padding: theme.size.gutter, gap: theme.space.sm },
});
