/**
 * The wire boundary: `ConversationListResponse` in, {@link Conversation}s out.
 *
 * ## Two kinds of unreadable code, treated the way `gameMappers` treats them
 *
 * - **Vocabulary degrades in place.** A **system-line code** this build cannot read becomes
 *   `undefined` and the line stays: the sentence *is* the whole of the slot the row draws it in,
 *   so [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §3 owes it a **named
 *   gap** rather than a drop, and the room keeps its row either way.
 * - **Structure is refused whole.** The **sport** is what the row calls the room, so a
 *   conversation carrying one this build cannot read is a row with a hole where the identifying
 *   fact goes. It is dropped, which is `gameMappers`' and `challengeMappers`' rule for the same
 *   field.
 *
 * An **entry shape** this build has never seen goes the third way and is neither: the row simply
 * has no last entry, which is a state the wire already has (`last_entry: null`, a room where
 * nothing has happened yet). Inventing a gap sentence there would tell a player their app is out
 * of date about a room in which, as far as anything can tell, nothing has happened.
 *
 * ## `null` is *this response said nothing*, and it collapses to absent
 *
 * Every optional here arrives as `T | null | undefined` and every one becomes `undefined`, so no
 * screen has two spellings of one absence to branch on.
 *
 * ## What is not mapped, and why that is the rule rather than an omission
 *
 * `challengeMappers` states the rule this follows — *"these fields are mapped by the ticket that
 * draws them"* — and [#364](https://github.com/Raketa02/Raketa/issues/364) is that ticket for two
 * of the three. **`challenge_id` is now mapped on the row**, because the challenge screen joins on
 * it to find its own way into the room; **`game_id` is mapped on the room**, because what it
 * decides there is whether the header draws *Details* — and, since the accept started going to
 * the room, **on the row as well**, for exactly one reader: a reply of `ON` says a game exists
 * before the teller has told the room which, and the push waits for the row to say so rather
 * than land in a room that draws no plan card yet (`useAwaitedChatDoor`). No row draws it.
 * `read_at` stays off the row and is on the room: it earns its place wherever something is
 * folded against an instant, and **a row draws no clock at all** while the room asks whether an
 * agreed day is today. A field mapped ahead of its reader is a shape somebody has to keep true
 * of a screen nobody has written.
 *
 * **An entry is mapped whole, and that is not the same call.** `sent_at`, `author_id` and
 * `client_message_id` have no reader on the row either — the row draws a message's text — but the
 * rule above is about **fields of a row**, where each is an independent fact a screen either draws
 * or does not. An entry is a **shape**: it is one arm of a discriminated union, `(conversation_id,
 * seq)` is its identity, and `client_message_id` is the key an optimistic bubble is replaced on.
 * A `Message` missing them is not a thinner Message, it is a different type that the stream would
 * have to widen — and widening a published domain type is the change this rule exists to avoid.
 *
 * ## There is no `wireVocabulary.ts` here, and that is a statement
 *
 * Every other feature holds its domain unions equal to the contract's with a compile-time
 * `Exact`. There is nothing to hold: a system line's `code` is a **`string`** on this wire and its
 * `values` a bare `Record<string, string>`, deliberately, because three contexts publish into this
 * stream through the outbox and a closed enum would make each new line a breaking contract change.
 * So the narrowing is a membership test against `domain/entry.ts`'s own list, and the phone
 * running last month's binary against this month's server is exactly the case §3 is written for.
 */

import type { components } from '@/generated/schema';
import { toSport } from '@/features/onboarding/types';

import type { Conversation } from '../domain/conversation';
import { toSystemLineCode, type Entry, type Message } from '../domain/entry';
import type { ConversationPerson } from '../domain/membership';
import type { EntryPage, OpenConversation } from '../domain/room';

type ConversationListResponse = components['schemas']['ConversationListResponse'];
type ConversationResponse = components['schemas']['ConversationResponse'];
type EntryPageResponse = components['schemas']['EntryPageResponse'];
type ConversationRowSchema = components['schemas']['ConversationRowSchema'];
type ConversationPersonSchema = components['schemas']['ConversationPersonSchema'];
type MessageSchema = components['schemas']['MessageSchema'];
type SystemLineSchema = components['schemas']['SystemLineSchema'];

/** Your rooms, in the order they were answered — see {@link Conversation}'s note on the order. */
export function toConversations(response: ConversationListResponse): readonly Conversation[] {
  return response.conversations.flatMap(toConversation);
}

function toConversation(row: ConversationRowSchema): readonly Conversation[] {
  const sport = toSport(row.sport);
  if (sport === undefined) return [];

  const lastEntry = row.last_entry == null ? undefined : toEntry(row.last_entry);

  return [
    {
      conversationId: row.conversation_id,
      challengeId: row.challenge_id,
      ...(row.game_id == null ? {} : { gameId: row.game_id }),
      sport,
      members: row.members.map(toPerson),
      people: row.people.map(toPerson),
      ...(lastEntry === undefined ? {} : { lastEntry }),
    },
  ];
}

/**
 * One face — a person's, and a member's, because **a member is a person under a narrower claim**.
 * `ConversationMemberSchema` has `ConversationPersonSchema`'s four fields exactly, so one mapper
 * reads both and `domain/membership.ts` is where the client decides the two are one type.
 */
function toPerson(person: ConversationPersonSchema): ConversationPerson {
  return {
    playerId: person.player_id,
    ...(person.name == null ? {} : { name: person.name }),
    ...(person.photo_url == null ? {} : { photoUrl: person.photo_url }),
  };
}

function toEntry(entry: MessageSchema | SystemLineSchema): Entry | undefined {
  if (entry.type === 'message') return toMessage(entry);

  if (entry.type === 'system_line') {
    const code = toSystemLineCode(entry.code);

    return {
      kind: 'system-line',
      seq: entry.seq,
      ...(code === undefined ? {} : { code }),
      occurredAt: entry.occurred_at,
      ...(entry.actor_id == null ? {} : { actorId: entry.actor_id }),
      values: entry.values,
    };
  }

  // A third shape on a two-shape union. See the module note: the row draws no last entry, which
  // is a state the wire already has, rather than a sentence about this build's age.
  return undefined;
}

/**
 * **One room and its newest page, or nothing where its sport is one this build cannot name.**
 *
 * The whole record is refused for the same reason a row is dropped for it: the sport is what the
 * header calls the room, and a screen with a hole where its identifying fact goes is worse than
 * the sentence a screen with no room draws. `challengeMappers` and `gameMappers` refuse the same
 * field the same way, and the screen says the one thing true of every cause — *no conversation of
 * yours has this address*.
 *
 * **The entries are narrowed one at a time and a shape this build has never seen is dropped**,
 * which is this file's third way and is not the named gap a code with no words gets: an entry that
 * is neither a message nor a system line has nothing at all to draw, where a system line with an
 * unreadable code still has a slot and a sentence owed. Nothing counts what was dropped — **no
 * reader may infer loss from a gap.**
 */
export function toConversationRoom(response: ConversationResponse): OpenConversation | undefined {
  const sport = toSport(response.sport);
  if (sport === undefined) return undefined;

  return {
    ...toEntryPage(response),
    room: {
      conversationId: response.conversation_id,
      challengeId: response.challenge_id,
      ...(response.game_id == null ? {} : { gameId: response.game_id }),
      readAt: response.read_at,
      sport,
      members: response.members.map(toPerson),
    },
  };
}

/**
 * A page — oldest first inside it, with the people it names, and no header on it at all.
 *
 * The newest page is the same shape with a header over it, which is why the room's own read goes
 * through here for its page half: `people` on the room is *the members and whoever the entries
 * are about*, and on a page backward it is the page's own authors and actors alone — the same
 * field under the same rule, merged by id as the pages accumulate.
 */
export function toEntryPage(page: Pick<EntryPageResponse, 'entries' | 'people'>): EntryPage {
  return { entries: page.entries.flatMap(toEntries), people: page.people.map(toPerson) };
}

/**
 * **One message, as the send answers with it** — the real `seq`, and the id it is reconciled on.
 *
 * The reply to a send is a `MessageSchema` and nothing else, so this is `toEntry`'s message arm
 * with the union narrowed by the route rather than by a discriminator. A repeat answers with the
 * message that already stands, which is why nothing here treats a second one as new.
 */
export function toMessage(message: MessageSchema): Message {
  return {
    kind: 'message',
    seq: message.seq,
    authorId: message.author_id,
    sentAt: message.sent_at,
    text: message.text,
    clientMessageId: message.client_message_id,
  };
}

function toEntries(entry: MessageSchema | SystemLineSchema): readonly Entry[] {
  const mapped = toEntry(entry);
  return mapped === undefined ? [] : [mapped];
}
