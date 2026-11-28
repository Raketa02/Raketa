/**
 * The rooms you are in, as `GET /conversations` answers.
 *
 * One of the two layers allowed to read generated types, and the only place this path is written
 * down. Every room here is a booked game's, filed under its booking (#575, #577).
 *
 * **Four of the five routes are here**, and the fifth is deliberately not: the live channel is
 * `text/event-stream` and belongs behind a platform port with the rest of the transports this app
 * does not write itself ([#365](https://github.com/Rakieta02/Rakieta/issues/365)). A route nothing
 * calls is a route nobody is checking, so each of the four arrives with the screen that uses it.
 *
 * ## `signal` on the three reads and none on the send
 *
 * `challengesApi`'s own asymmetry, and it lands the same way twice over: a `GET` records nothing,
 * so an abandoned one costs nobody a row — while **the send records before it answers**, and a
 * cancelled one leaves a message other people can read with nobody holding its `seq`.
 *
 * ## No `Idempotency-Key` on the send, and that is not `challenges`' argument
 *
 * `client_message_id` is in the **body** because it does two jobs: it is what makes a repeat safe,
 * and it is what an optimistic bubble is reconciled on (`domain/stream.ts`). A header would do the
 * first and be invisible to the second — and unlike `challenges`' pair rule, there is nothing
 * here that refuses a repeat on its own, so the key is the mechanism rather than a weaker copy of
 * one. A repeat answers `200` with the same message and the same `seq`, recording nothing.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type ConversationListResponse = components['schemas']['ConversationListResponse'];
type ConversationResponse = components['schemas']['ConversationResponse'];
type EntryPageResponse = components['schemas']['EntryPageResponse'];
type MessageSchema = components['schemas']['MessageSchema'];
type SendMessageRequest = components['schemas']['SendMessageRequest'];

/** The read may be abandoned. See the module note. */
export interface Cancellable {
  readonly signal?: AbortSignal;
}

/**
 * **Every room you are a member of, the ones that moved last first.**
 *
 * Each is a booked game's, its members the game's court as it stands — and **only live rooms are
 * here, because there are only live rooms**: a conversation is destroyed rather than delisted once
 * the episode it was opened for is over.
 */
export function getConversations({ signal }: Cancellable = {}): Promise<ConversationListResponse> {
  return httpRequest<ConversationListResponse>({
    method: 'GET',
    path: '/api/v1/conversations',
    authenticated: true,
    signal,
  });
}

/**
 * **One room's header and its newest page, from one fold.**
 *
 * `read_at` is one instant for both, *"so members and entries can never disagree"* — and it is the
 * clock every question on that screen is asked of.
 *
 * `404 conversation_not_found` is **one code for two cases**: there is no room with that id, or
 * there is one and you are not in it. They are not told apart on purpose, because a `403` would
 * answer *is this id real* about a stranger's evening — and past its end a room answers it
 * whether or not a sweep has run, which makes it three
 * ([ADR-0153](../../../../../docs/adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md)
 * §5).
 */
export function getConversation(
  conversationId: string,
  { signal }: Cancellable = {},
): Promise<ConversationResponse> {
  return httpRequest<ConversationResponse>({
    method: 'GET',
    path: `/api/v1/conversations/${conversationId}`,
    authenticated: true,
    signal,
  });
}

/** How far back one page reaches. The route's own default, named here because the client asks. */
export const ENTRY_PAGE = 50;

export interface EntryPageAsk extends Cancellable {
  readonly conversationId: string;
  /**
   * Return the entries **before** this one. Omitted for the newest page.
   *
   * There is no offset and no `has_more`: a gapless sequence makes `seq` 1 the beginning of the
   * conversation, so *what is before the oldest thing I hold* is the whole of the question, and an
   * empty answer means the beginning is held.
   */
  readonly beforeSeq?: number;
}

/**
 * **A page backward** — oldest first inside it, and no header on it at all.
 *
 * The limit is sent rather than left to the route's default, because a client that does not say
 * how much it wants cannot notice the day the default changes under it. Over the cap is a `422`
 * rather than a silent clamp, which is why nothing here computes one.
 */
export function getEntries({
  conversationId,
  beforeSeq,
  signal,
}: EntryPageAsk): Promise<EntryPageResponse> {
  const before = beforeSeq === undefined ? '' : `&before_seq=${beforeSeq}`;

  return httpRequest<EntryPageResponse>({
    method: 'GET',
    path: `/api/v1/conversations/${conversationId}/entries?limit=${ENTRY_PAGE}${before}`,
    authenticated: true,
    signal,
  });
}

/**
 * **Say something** — and get back the message as it was recorded, or the one that already stands.
 *
 * `text` crosses as the player typed it: leading and trailing whitespace is trimmed server-side,
 * empty after trimming is `message_is_empty` and past the cap is `message_is_too_long`. **Neither
 * is silently fixed** — a shortened message is one the sender believes they sent whole, in front
 * of other people — so nothing here truncates either.
 */
export function postMessage(
  conversationId: string,
  body: SendMessageRequest,
): Promise<MessageSchema> {
  return httpRequest<MessageSchema>({
    method: 'POST',
    path: `/api/v1/conversations/${conversationId}/messages`,
    body,
    authenticated: true,
  });
}

/**
 * **Say you are typing** — a heartbeat, not a state
 * ([ADR-0156](../../../../../docs/adr/0156-the-live-channel-carries-presence-and-a-heartbeat-is-the-only-honest-shape.md)).
 *
 * `204`, no body: what is being typed is nobody's business until it is sent. There is no
 * *stopped* — the server's own expiry is what clears the indicator, so a killed app clears it
 * too, having sent nothing. Gated exactly like a send: a non-member gets `conversation_not_found`
 * and a held account is refused, because an indicator is drawn on other people's screens.
 *
 * **It takes a `signal`, and it is the one write here that does.** A heartbeat outliving the
 * composer that beat it would be a request from a screen that has gone; the caller aborts it on
 * the way out, which is what keeps *no fire-and-forget request in a component* true of a `POST`
 * nobody awaits an answer to.
 */
export function postTyping(conversationId: string, { signal }: Cancellable = {}): Promise<void> {
  return httpRequest<void>({
    method: 'POST',
    path: `/api/v1/conversations/${conversationId}/typing`,
    authenticated: true,
    signal,
  });
}
