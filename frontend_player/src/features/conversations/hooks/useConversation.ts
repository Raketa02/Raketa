/**
 * **The room, opened** — the read that pages backward, and the one act on it.
 *
 * | | |
 * | --- | --- |
 * | `useConversation` | `GET /conversations/{id}` and `…/entries` — the header, and every page held |
 * | `useSendMessage` | `POST …/messages` — **optimistic**, and the only optimistic act on this map |
 * | `useSendingMessages` | what this phone has said and the server has not answered for |
 *
 * ## One infinite query over two routes
 *
 * The newest page carries the header and every page before it does not, which is exactly what an
 * infinite query's page params are for: the first ask has no cursor, and each one after it is
 * *what is before the oldest entry I hold*. `earlierThan` answers that and answers `undefined` at
 * `seq` 1, so **there is no `has_more` anywhere** — a gapless sequence makes 1 the beginning, and
 * a flag beside it would be the same fact twice.
 *
 * **The page order is TanStack's and the entry order is the wire's**, which is why the fold below
 * is here rather than in `domain/`: `pages[0]` is the newest page because that is the one asked
 * for first, and each page is oldest-first inside itself because that is how the route answers.
 * Neither is a rule anybody could be wrong about in the sense `domain/` means — they are two
 * libraries' orders, joined once.
 *
 * ## It takes the app-wide defaults, and the live channel is what makes them enough
 *
 * Thirty seconds stale with the focus refetch already wired from `AppState`, which is
 * `conversationKeys`' own reasoning about the list one screen up: nothing here is a number and
 * nothing draws a clock, so a stream served from cache is internally consistent rather than merely
 * recent. **What another member said arrives on a nudge**
 * ([#365](https://github.com/Raketa02/Raketa/issues/365)), and the nudge **invalidates** — the
 * Query cache stays the single copy and there is no second store for a conversation
 * ([ADR-0147](../../../../../docs/adr/0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md) §5).
 * Until that lands, foregrounding is what makes a room current.
 *
 * Play's *nothing background-refetches* does not reach here, and
 * [`the-loop-components.md`](../../../../../docs/specs/the-loop/the-loop-components.md) §2.4 calls
 * that a **scope clarification rather than an exception**: that rule is about a ranked list
 * reordering under a finger, and a conversation is append-ordered.
 *
 * ## The send is optimistic, and it is the one act on this map that is
 *
 * *Pending, never optimistic* holds everywhere else because those acts derive a standing several
 * people read. A message cannot be **wrong**: there is nothing derived to guess at, and the reply
 * is the message itself. So the bubble is on screen before the round trip, and **the sender's own
 * message never waits for a nudge** — the one place ADR-0147's two-round-trip cost can honestly
 * be avoided.
 *
 * **It pauses offline and resumes, which is the app default and deliberately not `challenges`'
 * rule.** That feature sets `networkMode: 'always'` because an answer window is derived at the
 * tap; a message carries no deadline anybody chose, so a queue of them draining on reconnect is
 * the behaviour you want. `client_message_id` is what makes it safe — the same key goes out on
 * the resumed attempt, and a repeat answers `200` with the same message and the same `seq`.
 *
 * **The optimistic bubble is read out of the mutation cache rather than written into the query
 * cache.** A paused send outlives the screen that made it, so a route-local list would lose it on
 * a walk away and back while the mutation was still waiting; and writing client state into the
 * query cache would put a message the server has never seen into the copy every other reader
 * treats as the server's. `useMutationState` is neither: what is pending **is** the list of things
 * still going out, and `streamOf` reconciles it against what has landed.
 */

import {
  useInfiniteQuery,
  useMutation,
  useMutationState,
  useQueryClient,
} from '@tanstack/react-query';
import type { InfiniteData } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { Entry, Message } from '../domain/entry';
import { mergedPeople } from '../domain/membership';
import { earlierThan, type OpenConversation } from '../domain/room';
import type { SendingMessage } from '../domain/stream';
import { readConversation, type ConversationPage } from '../use-cases/readConversation';
import { sendMessage, type SendMessageAsk } from '../use-cases/sendMessage';

import { conversationKeys } from './conversationKeys';

/** What the pages of one room look like in the cache, spelled once for the two writers of it. */
type ConversationPages = InfiniteData<ConversationPage, number | undefined>;

/**
 * One room and every page of it this client holds.
 *
 * `data` is `undefined` in three states the screen tells apart by `error` and `isPending`: the
 * read is still coming, it failed, or the record carries a sport this build cannot name — and the
 * screen says the one thing true of all three, exactly as `ChallengeScreen` does.
 */
export function useConversation(conversationId: string) {
  return useInfiniteQuery<
    ConversationPage,
    AppError,
    OpenConversation | undefined,
    readonly string[],
    number | undefined
  >({
    queryKey: conversationKeys.room(conversationId),
    queryFn: ({ pageParam, signal }) =>
      readConversation({
        conversationId,
        ...(pageParam === undefined ? {} : { beforeSeq: pageParam }),
        signal,
      }),
    initialPageParam: undefined,
    getNextPageParam: (lastPage) => earlierThan(lastPage.oldest),
    select: folded,
  });
}

/**
 * The header off the first page, every page's entries in one order, oldest first — and everybody
 * those pages name, **merged** newest page first.
 *
 * A page backward carries its own authors and actors and nothing about the roster
 * ([#409](https://github.com/Raketa02/Raketa/issues/409)), so its people are added to what is
 * held rather than put in its place: replacing would forget the members the moment the first
 * older page landed, and a page's people are exactly the ones the room's first read could not
 * have known. `mergedPeople` keeps the first face seen per id, which here is the newest page's —
 * the read the room is folded against.
 */
function folded(pages: ConversationPages): OpenConversation | undefined {
  const room = pages.pages[0]?.room;
  if (room === undefined) return undefined;

  return {
    room,
    entries: [...pages.pages].reverse().flatMap((page) => page.entries),
    people: mergedPeople(pages.pages.map((page) => page.people)),
  };
}

/**
 * **Say something.**
 *
 * The reply is written straight into the newest page rather than refetched: it *is* the message,
 * with the `seq` the server minted, so a read to learn what the reply already said would be a
 * request asking a question this client can answer. It is written **by `clientMessageId`**, so a
 * repeat — a resumed send, or a message that arrived through the channel first — lands once.
 *
 * **The list is invalidated**, because `GET /conversations` orders rooms by their last entry and
 * draws it: the reply says nothing about either, and a client that re-sorted the list itself would
 * be asserting an order it was not told.
 */
export function useSendMessage(conversationId: string) {
  const client = useQueryClient();

  return useMutation<Message, AppError, SendMessageAsk>({
    mutationKey: conversationKeys.sending(conversationId),
    mutationFn: sendMessage,
    onSuccess: (message) => {
      client.setQueryData<ConversationPages>(conversationKeys.room(conversationId), (held) =>
        held === undefined ? held : withMessage(held, message),
      );

      void client.invalidateQueries({ queryKey: conversationKeys.list() });
    },
  });
}

/** The pages with one message appended to the newest of them, or unchanged if it is already in. */
function withMessage(pages: ConversationPages, message: Message): ConversationPages {
  const [newest, ...older] = pages.pages;
  if (newest === undefined || holds(newest.entries, message)) return pages;

  return { ...pages, pages: [{ ...newest, entries: [...newest.entries, message] }, ...older] };
}

function holds(entries: readonly Entry[], message: Message): boolean {
  return entries.some(
    (entry) => entry.kind === 'message' && entry.clientMessageId === message.clientMessageId,
  );
}

/**
 * **What this phone has said and the server has not answered for**, in the order it was said.
 *
 * Read off the mutation cache, which is what makes it survive a walk away and back while a send
 * is paused — see the module note. `authorId` is the reader's because nobody else's send can be
 * in flight on this device, and a bubble needs an author to draw its side and speak its name.
 */
export function useSendingMessages(
  conversationId: string,
  authorId: string,
): readonly SendingMessage[] {
  const asks = useMutationState<unknown>({
    filters: { mutationKey: conversationKeys.sending(conversationId), status: 'pending' },
    select: (mutation) => mutation.state.variables,
  });

  return asks.flatMap((ask) =>
    isSendMessageAsk(ask)
      ? [
          {
            kind: 'sending' as const,
            clientMessageId: ask.clientMessageId,
            authorId,
            text: ask.text,
          },
        ]
      : [],
  );
}

/**
 * The mutation cache is untyped by construction — one cache, every feature's acts — so what comes
 * back out of it is narrowed rather than asserted. Nothing else writes under this key, so this can
 * only fail in a build where it has been changed to.
 */
function isSendMessageAsk(value: unknown): value is SendMessageAsk {
  if (typeof value !== 'object' || value === null) return false;
  const ask = value as Partial<SendMessageAsk>;

  return typeof ask.text === 'string' && typeof ask.clientMessageId === 'string';
}
