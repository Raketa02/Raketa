/**
 * **What a friends write says where it was pressed** — waiting for the network, or refused (#753).
 * `blocks`' note, a second caller of the same shape kept local until a third proves it belongs in
 * `shared/` (architecture: *the third caller*), with one difference: **a refusal that is the state
 * moving says nothing** (`stateMoved`) — the surface re-reads, and what it draws next is the answer.
 */

import { codeMessage, offlineMessage, type AppError } from '@/shared/errors';
import { Note } from '@/shared/ui';

import { stateMoved } from '../hooks/useFriendWrites';

import { FRIENDS_COPY } from './friendsCopy';

/** The two facts the note reads off a write — structurally, so it is not Query's type. */
export interface WriteState {
  readonly isPaused: boolean;
  readonly error: AppError | null;
}

export function WriteNote({ writes }: { readonly writes: readonly WriteState[] }) {
  if (writes.some((write) => write.isPaused)) {
    return <Note variant="amber">{offlineMessage('resumes')}</Note>;
  }
  const refused = writes
    .map((write) => write.error)
    .find((error): error is AppError => error !== null && !stateMoved(error));
  if (refused === undefined) return null;
  return (
    <Note variant="coral" accessibilityRole="alert">
      {codeMessage(FRIENDS_COPY.refused, refused)}
    </Note>
  );
}
