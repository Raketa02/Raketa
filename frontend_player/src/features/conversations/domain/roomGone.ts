/**
 * **The room is not there any more** — and the answer to that depends on whether anything was
 * ever read from it.
 *
 * `conversation_not_found` is **one code for three cases**: there is no room with that id, there
 * is one and the reader is not in it, or it is past its end whether or not a sweep has run
 * ([ADR-0153](../../../../../docs/adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md)
 * §5). They are deliberately not told apart — a `403` would answer *is this id real* about a
 * stranger's evening — and there is nothing a player would do differently in any of the three.
 *
 * **A client that never read the room leaves the screen** — a stale row opened into a room that
 * is not there ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md)
 * §3.7), on `challenge_not_found`'s own arm in §2.4's table. **A client holding the room when it
 * ends stays on it**, drawing what it held, closed, with one sentence saying so
 * (`roomOver.ts`; [#429](https://github.com/Raketa02/Raketa/issues/429)) — the ending is the one
 * thing that happened while the reader was looking, and a screen that vanished under them said
 * less about it than a screen that stayed. Neither retries, and the deletion is **not inferable
 * from a gap in the sequence**, because there is no sequence left to have a gap in.
 *
 * It is `domain/` and not a `catch` in a screen because it is a rule somebody can be wrong about:
 * a room can go while the reader is looking at it — the last other member leaves, and the room
 * is over in the same commit — so the read that discovers it is a nudge's re-read or the app's
 * own focus refetch rather than the one the screen mounted on, and a screen that only checked
 * its first read would go on drawing a room as live that has ended.
 * `challenges/domain/actRefusal.ts` is the same shape one context over.
 */

import type { AppError } from '@/shared/errors';

/** Whether this failure means there is no longer a room here to draw. */
export function roomIsGone(error: AppError | null): boolean {
  return error?.code === 'conversation_not_found';
}
