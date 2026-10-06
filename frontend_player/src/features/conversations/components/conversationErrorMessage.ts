/**
 * Backend `code` → the sentence a refused message writes, over `recoveryMessage`'s fallback.
 *
 * `challengeErrorMessage`'s shape one context over, and the reason is the same: localization goes
 * **code → message, never message → message**, and the fallback under the table is by *recovery
 * category*, so a code this build has never seen still says something true about what to do next.
 *
 * ## Two codes, and only one of them is reachable
 *
 * `message_is_empty` cannot happen from this client — `Send` is closed on a box holding nothing
 * but whitespace, which is the server's own trim read one step early — so it gets no row. What is
 * left is the one refusal this client genuinely cannot prevent: **the message length cap is
 * deliberately not on the wire**, because an over-long message is a refusal the Conversation
 * context owns and names rather than a `422` about a field. So a client cannot know the number,
 * must not guess at one, and must not `maxLength` a box against it — *a shortened message is one
 * the sender believes they sent whole*.
 *
 * **These are this app's first words for the code, and `the-words.md` does not have them.** §22's
 * loop sentences were written before the composer had a refusal to draw. The register is
 * ADR-0130's, which every refusal in this app already uses: state the class of problem, name
 * nobody, grade nothing — and here, say the one thing that fixes it.
 *
 * ## What is not in here, and why
 *
 * `conversation_not_found` is not a send's sentence: the room is gone and there is no retry that
 * changes it. A room nothing was read from leaves the screen — `challenge_not_found`'s own arm,
 * verbatim (§3.7) — and a room that ends while it is on screen closes in place with §22.5's own
 * sentence (`ROOM_OVER_LINE`), which is the read's to draw and never a refusal note's.
 *
 * **`account_held` never reaches this table**, and that is a decision rather than a gap
 * ([#365](https://github.com/Raketa02/Raketa/issues/365)). A hold is a fact about the **account**
 * rather than about the message that met it, so the screen folds it into `liveState` and draws
 * §22.5's amber note above the strip, with the composer and every chip greyed under it — *you are
 * never told off for having tapped*. A coral sentence beside the control as well would say one fact
 * twice, in the register the hold is deliberately not in.
 */

import { codeMessage, type AppError } from '@/shared/errors';

const BY_CODE: Readonly<Record<string, string>> = {
  /** Refused whole, never truncated — so the remedy is the sender's and it is a short one. */
  message_is_too_long: "That's longer than a message can be. Shorten it and send it again.",
};

export function conversationErrorMessage(error: AppError): string {
  return codeMessage(BY_CODE, error);
}
