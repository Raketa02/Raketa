/**
 * The rooms you are in, as `GET /conversations` answers.
 *
 * One of the two layers allowed to read generated types, and the only place this path is written
 * down. **This is one of two reads for the Chats tab and they are not merged**: `GET /challenges`
 * is the other, and the tab is two sections, two contexts, two queries, two caches
 * ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §1.1).
 *
 * The route's other four — one conversation, a page of entries, a message and the live channel —
 * arrive with the screen that uses them ([#364](https://github.com/Raketa02/Raketa/issues/364)).
 * A route nothing calls is a route nobody is checking.
 *
 * It takes a `signal`, on `challengesApi`'s own asymmetry: a `GET` records nothing, so an
 * abandoned one costs nobody a row.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type ConversationListResponse = components['schemas']['ConversationListResponse'];

/** The read may be abandoned. See the module note. */
export interface Cancellable {
  readonly signal?: AbortSignal;
}

/**
 * **Every room you are a member of, the ones that moved last first.**
 *
 * A doubles court whose line-up is still filling draws the members it has, not the court it will
 * be — and **only live rooms are here, because there are only live rooms**: a conversation is
 * destroyed rather than delisted once the episode it was opened for is over.
 */
export function getConversations({ signal }: Cancellable = {}): Promise<ConversationListResponse> {
  return httpRequest<ConversationListResponse>({
    method: 'GET',
    path: '/api/v1/conversations',
    authenticated: true,
    signal,
  });
}
