/**
 * What a You screen draws while the read it edits is not in — **and nothing once it is.**
 *
 * *Your week* and the screens beside it each open on a fact off `GET /players/me/profile`, and
 * a control drawn before that fact has landed would be a control over a value nobody has: a
 * grid with nothing ticked reads as an empty week. So each screen draws this instead until the
 * read answers, and it says which of the three states the read is in — paused, because
 * `networkMode: 'online'` holds a query rather than failing it and an offline player would
 * otherwise watch a spinner forever; on its way; or refused, with the control the failure
 * belongs to, which is the read itself.
 */

import { ActivityIndicator, StyleSheet, View } from 'react-native';

import { offlineMessage, recoveryMessage, type AppError } from '@/shared/errors';
import { Button, Note, theme } from '@/shared/ui';

import { TRY_AGAIN } from './youProfilePresentation';

export interface ProfileReadStandingProps {
  /** The read's fetch status, as Query reports it. */
  readonly fetchStatus: 'fetching' | 'paused' | 'idle';
  readonly isPending: boolean;
  readonly error: AppError | null;
  readonly onRetry: () => void;
  /** What is being read, for the spinner's spoken name — *Loading your week*. */
  readonly loadingLabel: string;
}

export function ProfileReadStanding({
  fetchStatus,
  isPending,
  error,
  onRetry,
  loadingLabel,
}: ProfileReadStandingProps) {
  return (
    <>
      {fetchStatus === 'paused' ? <Note variant="amber">{offlineMessage('resumes')}</Note> : null}

      {isPending && fetchStatus !== 'paused' ? (
        <ActivityIndicator accessibilityLabel={loadingLabel} color={theme.color.muted} />
      ) : null}

      {error !== null ? (
        <View style={s.failure}>
          <Note variant="coral" accessibilityRole="alert">
            {recoveryMessage(error)}
          </Note>
          <Button label={TRY_AGAIN} variant="secondary" onPress={onRetry} />
        </View>
      ) : null}
    </>
  );
}

const s = StyleSheet.create({
  failure: { gap: theme.space.sm },
});
