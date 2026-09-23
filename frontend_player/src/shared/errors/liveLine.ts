/**
 * **What a row says about its read** — the fact once it is in, nothing while it is on its way,
 * and the recovery sentence where it failed.
 *
 * The You tab is a list of facts, each drawn as a live line off a read, and a row whose read
 * failed and said nothing would be a fact quietly missing — the one thing a list of facts must
 * not do. So the failure is spoken on the row in the recovery register every other failure in
 * this app uses, and the screen behind the row is where the retry lives. One answer for every
 * row in every feature, which is why it is here beside `recoveryMessage` rather than in the
 * drawn row: a read's standing turned into a sentence is an errors concern, not a drawing.
 */

import type { AppError } from './AppError';
import { recoveryMessage } from './recoveryMessage';

/** The two halves of a read a row cares about — structurally, so it is not Query's type. */
export interface LiveRead<T> {
  readonly data: T | undefined;
  readonly error: AppError | null;
}

export function liveLine<T>(read: LiveRead<T>, draw: (data: T) => string): string | undefined {
  if (read.data !== undefined) return draw(read.data);
  return read.error === null ? undefined : recoveryMessage(read.error);
}
