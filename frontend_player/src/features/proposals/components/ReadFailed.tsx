/**
 * **A read that failed** — why, in the coral note, and the retry, unless the failure is one no retry
 * can mend. The Games tab's and a game's details' alike.
 *
 * The group page draws the same pair (`groups`' `ReadFailure`), and so does the invitation link; a
 * third copy is the one CLAUDE.md names as the moment to move it to `shared/`. It is not moved in
 * #553, which touches neither of the other two, and is recorded for the next change that does.
 */

import { StyleSheet, View } from 'react-native';

import { recoveryMessage, type AppError } from '@/shared/errors';
import { Button, Note, theme } from '@/shared/ui';

import { PROPOSALS_COPY } from './proposalsCopy';

export function ReadFailed({
  error,
  onRetry,
}: {
  readonly error: AppError;
  readonly onRetry: () => void;
}) {
  const retryable =
    error.recovery === 'retryable-automatically' || error.recovery === 'retryable-by-user';
  return (
    <View style={s.failure}>
      <Note variant="coral" accessibilityRole="alert">
        {recoveryMessage(error)}
      </Note>
      {retryable ? (
        <Button label={PROPOSALS_COPY.readAgain} variant="secondary" size="sm" onPress={onRetry} />
      ) : null}
    </View>
  );
}

const s = StyleSheet.create({
  failure: { gap: theme.space.sm },
});
