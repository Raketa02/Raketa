/**
 * The gate could not be read.
 *
 * There is no safe default to fall through to: sending an unrated player into the app
 * skips onboarding entirely, and sending a rated one into onboarding re-rates a sport
 * they have already proved. Both are worse than saying so and offering the retry.
 *
 * This is the launch screen a player on a dead connection sees, so it says what happened
 * and nothing else.
 *
 * **Two states, and the difference is whether anything was attempted.** A read that failed
 * has something to say and something to retry. A launch with no connection has neither: the
 * gate's queries are *paused*, they resume themselves the moment the connection is back, and
 * the retry would be the one control on this screen that does nothing. So the offline half is
 * amber rather than coral — reversible, not yet wrong — and carries no button.
 *
 * **The failed half stays up while it tries again**, automatically or because the player pressed:
 * the button says _Trying again…_ and takes no second press, so an attempt in flight is never an
 * empty screen and never two attempts.
 */

import { StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { offlineMessage } from '@/shared/errors';
import { Button, Note, theme } from '@/shared/ui';

import type { EntryUnavailable } from '../hooks/useEntryDecision';

import { onboardingErrorMessage } from './onboardingErrorMessage';

export interface EntryUnavailableScreenProps {
  readonly reason: EntryUnavailable;
  /**
   * Required even though the offline half never calls it. The gate always has a retry to
   * offer — it is the read's `refetch` — and an optional prop would let a *failed* branch be
   * rendered with nothing to press, which is the one state on this screen with no way out.
   */
  readonly onRetry: () => void;
}

/**
 * The screen, as three facts read off one branch.
 *
 * One `reason.kind` test rather than one per element: three ternaries in a tree is three
 * places for the amber half to keep a coral sentence, and the retryable half is exactly the
 * half with something to retry.
 */
function saying(reason: EntryUnavailable) {
  if (reason.kind === 'offline') {
    return {
      title: 'Waiting for a connection',
      variant: 'amber' as const,
      sentence: offlineMessage('resumes'),
      retryable: false,
      trying: false,
    };
  }

  return {
    title: "We couldn't pick up where you left off",
    variant: 'coral' as const,
    sentence: onboardingErrorMessage(reason.error),
    retryable: true,
    trying: reason.trying,
  };
}

export function EntryUnavailableScreen({ reason, onRetry }: EntryUnavailableScreenProps) {
  const said = saying(reason);

  return (
    <SafeAreaView style={s.screen} edges={['top', 'bottom']}>
      <View style={s.content}>
        <Text style={s.title} accessibilityRole="header">
          {said.title}
        </Text>
        <Note variant={said.variant} accessibilityRole="alert">
          {said.sentence}
        </Note>
        {said.retryable ? (
          <Button
            label="Try again"
            busy={said.trying}
            busyLabel="Trying again…"
            size="lg"
            onPress={onRetry}
          />
        ) : null}
      </View>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: theme.color.paper },
  content: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: theme.size.gutter,
    gap: theme.space.md,
  },
  title: { ...theme.type.h1, color: theme.color.ink },
});
