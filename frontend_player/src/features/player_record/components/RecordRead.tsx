/**
 * **A record, read, in every state** — what the record sheet draws while it reads, when it is
 * refused, and when it could not be reached; and the record itself, handed to the caller
 * ([#803](https://github.com/Raketa02/Raketa/issues/803)).
 *
 * The record sheet is one surface that reads a record; **the vibe sheet** (Discovery's, the Home
 * rows screens §6.3) is the second: it *reads the record*, and shows what the record shows — so it
 * opens only where the record would, and says *This record isn't available* where the record does.
 * The read, its refusal and its words stay this feature's, and the caller draws what it shows of
 * the record (`children`).
 *
 * **The refusal wins over a record already drawn**: the gates are live, so a read again that is
 * refused means the record no longer opens — the record sheet's own rule (see its module note).
 */

import type { ReactNode } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { codeMessage, type AppError } from '@/shared/errors';
import { Button, Note, theme } from '@/shared/ui';

import type { PlayerRecord } from '../domain/playerRecord';
import { usePlayerRecord } from '../hooks/usePlayerRecord';

import {
  READING_RECORD_LABEL,
  RECORD_UNAVAILABLE,
  RECORD_UNAVAILABLE_CODE,
  RETRY_RECORD_LABEL,
} from './recordPresentation';

/** The one code, for all four causes — and the one sentence this client draws from it. */
const RECORD_FAILURES: Readonly<Record<string, string>> = {
  [RECORD_UNAVAILABLE_CODE]: RECORD_UNAVAILABLE,
};

export interface RecordReadProps {
  /** Whose record — somebody else's: a reader's own face opens the record sheet. */
  readonly playerId: string;
  /** The surface being up. Nothing is read for a face nobody tapped. */
  readonly enabled: boolean;
  /** What the surface draws of the record, once it is in and not refused. */
  readonly children: (record: PlayerRecord) => ReactNode;
}

export function RecordRead({ playerId, enabled, children }: RecordReadProps) {
  const record = usePlayerRecord({ subject: { kind: 'player', playerId }, enabled });
  if (record.data === undefined || isRecordRefusal(record.error)) {
    return <RecordStanding error={record.error} onRetry={() => void record.refetch()} />;
  }
  return <>{children(record.data)}</>;
}

/** **The record's one refusal** — it closes the record, drawn or not. */
export function isRecordRefusal(error: AppError | null): boolean {
  return error?.code === RECORD_UNAVAILABLE_CODE;
}

/**
 * The two states that are not a record: still reading, and could not.
 *
 * A refusal is **one line and no control**, since re-asking a refusal returns the refusal.
 * Everything else is the recovery sentence with the control the failure belongs to, which is this
 * read and nothing else on the screen underneath.
 */
export function RecordStanding({
  error,
  onRetry,
}: {
  readonly error: AppError | null;
  readonly onRetry: () => void;
}) {
  if (error === null) {
    return (
      <ActivityIndicator accessibilityLabel={READING_RECORD_LABEL} color={theme.color.muted} />
    );
  }

  if (isRecordRefusal(error)) {
    return <Text style={s.refusal}>{RECORD_UNAVAILABLE}</Text>;
  }

  return (
    <View style={s.failure}>
      <Note variant="coral" accessibilityRole="alert">
        {codeMessage(RECORD_FAILURES, error)}
      </Note>
      <Button label={RETRY_RECORD_LABEL} variant="secondary" onPress={onRetry} />
    </View>
  );
}

const s = StyleSheet.create({
  refusal: { ...theme.type.tiny, color: theme.color.muted },
  failure: { gap: theme.space.sm },
});
