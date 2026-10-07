/**
 * **What a block or an unblock says where it was pressed** — waiting for the network, or refused.
 * Amber for the first, which resumes on its own; the recovery sentence for the second, `alert`
 * because it appeared without being asked for; nothing otherwise. The confirm sheet, the record's
 * Unblock and each row of *Blocked players* draw it under their own control.
 */

import { offlineMessage, recoveryMessage, type AppError } from '@/shared/errors';
import { Note } from '@/shared/ui';

/** The two facts the note reads off a write — structurally, so it is not Query's type. */
export interface WriteState {
  readonly isPaused: boolean;
  readonly error: AppError | null;
}

export function WriteNote({ write }: { readonly write: WriteState }) {
  if (write.isPaused) return <Note variant="amber">{offlineMessage('resumes')}</Note>;
  if (write.error === null) return null;
  return (
    <Note variant="coral" accessibilityRole="alert">
      {recoveryMessage(write.error)}
    </Note>
  );
}
