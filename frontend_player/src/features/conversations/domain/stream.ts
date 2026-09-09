/**
 * **What is on screen in the stream** — the entries the server has recorded, and the messages
 * this phone has sent that it has not answered for yet.
 *
 * ## The optimistic half is here, and it is one rule
 *
 * A message send is **optimistic**, which is the deliberate opposite of everything else on this
 * map ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §3.5).
 * The accept is pending because it derives a standing four people read; a message *reaches*
 * other people but cannot be **wrong** — there is nothing derived to guess at — so the sender's
 * own words go on screen immediately rather than waiting for a nudge and a round trip.
 *
 * **The reconciliation is `client_message_id` and nothing else.** That value does two jobs, which
 * is why it is in the body rather than in an `Idempotency-Key` header: it is the idempotency key
 * a resumed send repeats, and it is the key an optimistic bubble is replaced on. A repeat answers
 * `200` with the same message and the same `seq`, so **a send that paused offline and resumed can
 * never become two messages** — here that is one `has` check rather than a rule anybody applies.
 *
 * ## A message still going out has no moment, and draws no separator
 *
 * {@link SendingMessage} carries no `sentAt`, and that is a refusal rather than an omission: the
 * instant a message happened is the server's, and the only clock this phone could offer instead
 * is the one `durationLeft` refuses everywhere else in the app. So a message in flight sits under
 * whatever separator is already there and gets its own the moment the server answers with the
 * moment it landed. Nothing invents a *when*.
 *
 * ## It is still two components at the surface
 *
 * The third arm is a **message that has not landed**, not a third shape: it draws through the
 * same bubble, because what a bubble draws is somebody's words and a side. ADR-0146's refusal is
 * about a system line and a message sharing one shape with a `kind` on it, and nothing here
 * brings that back — the stream picks a component off `kind`, which is what a discriminated
 * union is for.
 */

import type { Weekday } from '@/shared/vocabulary/week';

import { separatorBefore, type Entry } from './entry';

/** One message this phone has sent and the server has not yet answered for. */
export interface SendingMessage {
  readonly kind: 'sending';
  /** The id this client generated for the send — the whole of the reconciliation. */
  readonly clientMessageId: string;
  /** The sender, which is always the reader: nobody else's message can be in flight here. */
  readonly authorId: string;
  readonly text: string;
}

/** What the stream draws, in one order: the recorded backlog, then whatever is still going out. */
export type StreamEntry = Entry | SendingMessage;

/**
 * The recorded entries with the still-unanswered sends after them, **the answered ones dropped.**
 *
 * A send is dropped the moment the message it produced is in `entries`, matched on
 * `clientMessageId` — so the bubble a player is looking at becomes the real one without moving,
 * and a mutation still in flight against a message that has already arrived through the live
 * channel draws once rather than twice.
 */
export function streamOf(
  entries: readonly Entry[],
  sending: readonly SendingMessage[],
): readonly StreamEntry[] {
  const landed = new Set(
    entries.flatMap((entry) => (entry.kind === 'message' ? [entry.clientMessageId] : [])),
  );

  return [...entries, ...sending.filter((one) => !landed.has(one.clientMessageId))];
}

/**
 * A fresh `client_message_id` — **one per send, minted where the bubble is.**
 *
 * A version-4 UUID, because the field is one on the wire, and built from `Math.random` because
 * **this is a correlation key rather than a secret**: what it has to be is unique among one
 * player's own unanswered sends, and it is read by exactly two things — the server, to notice a
 * repeat, and `streamOf`, to notice the reply. Nothing is authorised by it and nothing is
 * guessable from it.
 *
 * It is here rather than behind a native crypto module for the same reason: `expo-crypto` is a
 * platform capability, which in this app means a port, a fake and a chokepoint — a great deal of
 * machinery for a value whose whole requirement is *not the same as the last one*.
 */
export function newClientMessageId(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (placeholder) => {
    const digit = Math.floor(Math.random() * 16);
    // The two fixed nibbles a version-4 UUID carries: the version, written into the template
    // above, and the variant, which is one of 8, 9, a, b.
    return (placeholder === 'x' ? digit : (digit % 4) + 8).toString(16);
  });
}

/**
 * **Is there anything to send** — whitespace-only is empty, which is the server's own trim read
 * one step early.
 *
 * A rule rather than a `disabled={…}` expression, and the difference matters because there are
 * two readers: the control that closes and the act that refuses. Two copies of *is this
 * sendable* is exactly how one of them stops agreeing with the other.
 *
 * It is **the one refusal this client can prevent without guessing**. The other — a message past
 * the cap — is a number deliberately not on the wire, so nothing here may pre-empt it.
 */
export function mayPost(text: string): boolean {
  return text.trim() !== '';
}

/**
 * **The weekday to draw above a row of the stream**, or nothing.
 *
 * `separatorBefore`'s rule over this file's own union, so the third arm is answered once here
 * rather than guarded twice in a component: **a message still going out has no recorded moment**,
 * so it draws no separator and supplies none to the row after it.
 */
export function separatorAbove(
  entry: StreamEntry,
  older: StreamEntry | undefined,
): Weekday | undefined {
  return entry.kind === 'sending' ? undefined : separatorBefore(entry, recorded(older));
}

/** The entry, or nothing where it is a send the server has not answered for. */
function recorded(entry: StreamEntry | undefined): Entry | undefined {
  return entry === undefined || entry.kind === 'sending' ? undefined : entry;
}
