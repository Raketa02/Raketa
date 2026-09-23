/**
 * **Say you are typing in a room.**
 *
 * A pass-through, honestly: the throttle is `domain/typing.ts`' rule and the hook applies it, the
 * hold is the server's refusal, and what crosses is a `POST` with nothing on it. What this
 * function fixes is the shape of the ask, so the hook and a test agree about it.
 */

import { postTyping, type Cancellable } from '../api/conversationsApi';

export interface SayTypingAsk extends Cancellable {
  readonly conversationId: string;
}

export function sayTyping({ conversationId, signal }: SayTypingAsk): Promise<void> {
  return postTyping(conversationId, { signal });
}
