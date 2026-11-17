/**
 * **Needs your answer, as a suite reaches it** (#816, ADR-0205 §1): the envelope on Home's header,
 * and the sheet it opens. A friend request or an ask for a level waits there rather than on Home, so
 * a suite that answers one opens the sheet first.
 *
 * Not app code — nothing under `src/` outside tests imports this.
 */

import { fireEvent, screen } from 'expo-router/testing-library';

import { NEEDS_YOUR_ANSWER_COPY } from '@/features/shell/types';

const { title: TITLE, close: CLOSE } = NEEDS_YOUR_ANSWER_COPY;

/** The header's envelope, or `null` while nothing waits. */
export function envelope() {
  return screen.queryByRole('button', { name: TITLE });
}

/** The sheet's title, or `null` while it is not up. */
export function sheetTitle() {
  return screen.queryByRole('header', { name: TITLE });
}

/** The envelope pressed, once Home has drawn it, and the sheet up. */
export async function openNeedsYourAnswer(): Promise<void> {
  fireEvent.press(await screen.findByRole('button', { name: TITLE }));
  await screen.findByRole('header', { name: TITLE });
}

/** The sheet's ✕. */
export function closeNeedsYourAnswer(): void {
  fireEvent.press(screen.getByRole('button', { name: CLOSE }));
}
