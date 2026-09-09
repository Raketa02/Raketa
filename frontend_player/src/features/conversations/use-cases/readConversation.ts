/**
 * **One room, a page at a time** — the newest page with the header on it, and every page before
 * that without one.
 *
 * Two routes and one use-case, because a caller paging backward is asking one question — *give me
 * what is before what I hold* — and the header rides on the first answer only. `GET
 * /conversations/{id}` is *"one room's header **and** its newest page, from one fold"*, and
 * `GET …/entries` is the same page shape with nothing above it, so what the two share is exactly
 * what a page is.
 *
 * **The room is on the first page and nowhere else.** Absent on a later one is not *this room has
 * no header*, it is *you already have it* — which is why {@link ConversationPage} spells it
 * optional rather than repeating a header the wire deliberately does not resend.
 *
 * There is no rule to run over either answer. The order is the server's, the membership is the
 * server's fold, and every question a client could be wrong about — which day a separator names,
 * whether an agreed day is today, which send has landed — is asked of `domain/` at the moment it
 * is drawn.
 */

import type { Cancellable } from '../api/conversationsApi';
import { getConversation, getEntries } from '../api/conversationsApi';
import type { Entry } from '../domain/entry';
import type { ConversationRoom } from '../domain/room';
import { toConversationRoom, toEntryPage } from '../mappers/conversationMappers';

export interface ConversationPage {
  /**
   * The room, on the newest page alone.
   *
   * Also absent on the newest page when the sport is one this build cannot name — the mapper
   * refuses the record whole, and the screen says the one thing true of that and of a `404`
   * alike.
   */
  readonly room?: ConversationRoom;
  /** The page itself, oldest first inside it. */
  readonly entries: readonly Entry[];
  /**
   * The oldest `seq` this page **carried**, which is not always the oldest one it mapped.
   *
   * An entry shape this build has never seen is dropped at the wire boundary, so a page of
   * nothing but those maps to `[]` — and a cursor read off the mapped list would say the backlog
   * had ended when it had not. This is read off the response, so where the next ask starts is
   * always what the server sent.
   */
  readonly oldest?: number;
}

export interface ConversationPageAsk extends Cancellable {
  readonly conversationId: string;
  /** Omitted for the newest page. See `domain/room.ts` on why there is no `has_more`. */
  readonly beforeSeq?: number;
}

export async function readConversation({
  conversationId,
  beforeSeq,
  signal,
}: ConversationPageAsk): Promise<ConversationPage> {
  if (beforeSeq === undefined) {
    const answer = await getConversation(conversationId, { signal });
    const opened = toConversationRoom(answer);

    return { ...(opened ?? { entries: [] }), ...oldestOf(answer.entries) };
  }

  const page = await getEntries({ conversationId, beforeSeq, signal });

  return { entries: toEntryPage(page), ...oldestOf(page.entries) };
}

/** The first `seq` on the wire's own page — see {@link ConversationPage.oldest}. */
function oldestOf(entries: readonly { readonly seq: number }[]): { oldest?: number } {
  const oldest = entries[0]?.seq;

  return oldest === undefined ? {} : { oldest };
}
