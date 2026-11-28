/**
 * **A list on its way** — offline, refused, or being read ([#754](https://github.com/Rakieta02/Rakieta/issues/754)):
 * You › Friends' three tabs and the Add friends sheet's groups, each drawing this in place of its
 * list until the list is in. `blocks`' three states, in its register:
 *
 * - **paused** — the read waits for the network: the amber line, never a *Reading…* that never ends;
 * - **refused** — the recovery sentence and *Try again*, never an empty list;
 * - **reading** — the caller's quiet line.
 */

import { StyleSheet, Text, View } from 'react-native';

import { offlineMessage, recoveryMessage, type AppError } from '@/shared/errors';
import { Button, Note, theme } from '@/shared/ui';

import { FRIENDS_COPY } from './friendsCopy';

/** The four facts read off a query — structurally, so it is not Query's type. */
export interface ListRead {
  readonly fetchStatus: 'fetching' | 'paused' | 'idle';
  readonly isFetching: boolean;
  readonly error: AppError | null;
  readonly refetch: () => Promise<unknown>;
}

export function ListReading({
  read,
  reading,
}: {
  readonly read: ListRead;
  /** The quiet line while it is read — *Reading…*, *Reading your groups…*. */
  readonly reading: string;
}) {
  if (read.fetchStatus === 'paused') {
    return <Note variant="amber">{offlineMessage('resumes')}</Note>;
  }
  if (read.error === null || read.isFetching) return <Text style={s.quiet}>{reading}</Text>;
  return (
    <View style={s.failure}>
      <Note variant="coral" accessibilityRole="alert">
        {recoveryMessage(read.error)}
      </Note>
      <Button
        label={FRIENDS_COPY.page.readAgain}
        variant="secondary"
        size="sm"
        onPress={() => void read.refetch()}
        style={s.again}
      />
    </View>
  );
}

const s = StyleSheet.create({
  quiet: { ...theme.type.rlLabel, color: theme.color.muted },
  failure: { gap: theme.space.sm },
  again: { alignSelf: 'flex-start' },
});
