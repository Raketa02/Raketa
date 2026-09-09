/**
 * **The room is not there any more, and the answer to that is to leave.**
 *
 * `conversation_not_found` is **one code for three cases**: there is no room with that id, there
 * is one and the reader is not in it, or it is past its end whether or not a sweep has run
 * ([ADR-0153](../../../../../docs/adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md)
 * §5). They are deliberately not told apart — a `403` would answer *is this id real* about a
 * stranger's evening — and there is nothing a player would do differently in any of the three.
 *
 * **A client holding a cursor into a destroyed conversation leaves the screen**
 * ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §3.7), on
 * `challenge_not_found`'s own arm in §2.4's table. It does **not** retry, and the deletion is
 * **not inferable from a gap in the sequence**, because there is no sequence left to have a gap
 * in.
 *
 * It is `domain/` and not a `catch` in a screen because it is a rule somebody can be wrong about:
 * a room can go while the reader is looking at it — a withdraw destroys it in the same act — so
 * the read that discovers it is the app's own focus refetch rather than the one the screen
 * mounted on, and a screen that only checked its first read would go on drawing a room that is
 * gone. `challenges/domain/actRefusal.ts` is the same shape one context over.
 */

import type { AppError } from '@/shared/errors';

/** Whether this failure means there is no longer a room here to draw. */
export function roomIsGone(error: AppError | null): boolean {
  return error?.code === 'conversation_not_found';
}
