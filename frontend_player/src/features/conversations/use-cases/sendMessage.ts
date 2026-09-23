/**
 * **Say something in a room.**
 *
 * The `client_message_id` is minted **here, once per send**, and it is the whole of what makes
 * this act safe to repeat: it is the idempotency key a resumed send carries and the key the
 * optimistic bubble is reconciled on (`domain/stream.ts`). A repeat answers `200` with the same
 * message and the same `seq`, recording nothing — so a send that paused offline and resumed can
 * never become two messages.
 *
 * **It is minted by the caller and passed in**, not generated in this function, because the
 * optimistic bubble needs the same value the request carries and a use-case that made its own
 * would leave the screen with nothing to match on. What is here is the shape of the ask.
 *
 * The text crosses as it was typed. Trimming is the server's — *"leading and trailing whitespace
 * is trimmed; empty after trimming is `message_is_empty`, and past the cap is
 * `message_is_too_long`. Neither is silently fixed"* — and a client that shortened a message would
 * be doing exactly the thing that refusal exists to prevent.
 */

import { postMessage } from '../api/conversationsApi';
import type { Message } from '../domain/entry';
import { toMessage } from '../mappers/conversationMappers';

export interface SendMessageAsk {
  readonly conversationId: string;
  /** What the player typed, unchanged. */
  readonly text: string;
  /** Minted once per send by whoever drew the bubble. See the module note. */
  readonly clientMessageId: string;
}

export async function sendMessage({
  conversationId,
  text,
  clientMessageId,
}: SendMessageAsk): Promise<Message> {
  return toMessage(await postMessage(conversationId, { text, client_message_id: clientMessageId }));
}
