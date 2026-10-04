/**
 * **A read that failed, said where its answer would have been** — why, and a way to ask again
 * when asking again can help. The Groups list, the two searches and a group's page each draw it
 * in place of what they could not read.
 *
 * **The retry follows the failure's recovery, never its code**: offered for a failure the network
 * or the player can get past, and not for a terminal one — `group_not_found` is the same answer
 * however often it is asked for. The sentence is the caller's when it can name the failure
 * (`codeMessage`), and the recovery's otherwise.
 */

import { View, StyleSheet } from 'react-native';

import { recoveryMessage, type AppError } from '@/shared/errors';
import { Button, Note, theme } from '@/shared/ui';

import { GROUPS_COPY } from './groupsCopy';

export interface ReadFailureProps {
  readonly error: AppError;
  /** The sentence, where the caller can name the failure. Absent, the recovery's. */
  readonly message?: string;
  readonly onRetry: () => void;
}

export function ReadFailure({ error, message, onRetry }: ReadFailureProps) {
  const retryable =
    error.recovery === 'retryable-automatically' || error.recovery === 'retryable-by-user';

  return (
    <View style={s.failure}>
      <Note variant="coral" accessibilityRole="alert">
        {message ?? recoveryMessage(error)}
      </Note>
      {retryable ? (
        <Button label={GROUPS_COPY.retry} variant="secondary" size="sm" onPress={onRetry} />
      ) : null}
    </View>
  );
}

const s = StyleSheet.create({
  failure: { gap: theme.space.sm },
});
