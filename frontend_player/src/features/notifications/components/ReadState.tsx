/**
 * **A read with nothing to draw yet** — on its way, held offline, or refused with a retry — for the
 * screens here, which draw the same three (the receipts' shape, #555). What is drawn once the read
 * has landed is each screen's own.
 */

import { StyleSheet, Text, View } from 'react-native';

import { offlineMessage, recoveryMessage, type AppError } from '@/shared/errors';
import { Button, Note, theme } from '@/shared/ui';

import { NOTIFICATIONS_COPY } from './notificationsCopy';

export interface ReadStateProps {
  readonly read: {
    readonly fetchStatus: 'fetching' | 'paused' | 'idle';
    readonly error: AppError | null;
    readonly isFetching: boolean;
    readonly refetch: () => Promise<unknown>;
  };
  /** What is said while the read is on its way. */
  readonly loading: string;
}

export function ReadState({ read, loading }: ReadStateProps) {
  if (read.fetchStatus === 'paused')
    return <Note variant="amber">{offlineMessage('resumes')}</Note>;
  if (read.error === null || read.isFetching) return <Text style={s.quiet}>{loading}</Text>;
  return (
    <View style={s.failure}>
      <Note variant="coral" accessibilityRole="alert">
        {recoveryMessage(read.error)}
      </Note>
      <Button
        label={NOTIFICATIONS_COPY.readAgain}
        variant="secondary"
        size="sm"
        onPress={() => void read.refetch()}
      />
    </View>
  );
}

const s = StyleSheet.create({
  quiet: { ...theme.type.rlLabel, color: theme.color.muted },
  failure: { gap: theme.space.sm },
});
