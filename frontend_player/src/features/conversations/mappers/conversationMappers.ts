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
 * `read_at`, `challenge_id` and `game_id` all cross and none is mapped. `challengeMappers` states
 * the rule this follows — *"these fields are mapped by the ticket that draws them"* — and each has
 * a reader that is not this one: `read_at` earns its place on a list whose durations are folded
 * against it and **this row draws no clock at all**, and the two ids are the doors
 * [#364](https://github.com/Raketa02/Raketa/issues/364)'s header opens. A field mapped ahead of
 * its reader is a shape somebody has to keep true of a screen nobody has written.
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
import { toSystemLineCode, type Entry } from '../domain/entry';
import type { ConversationMember } from '../domain/membership';

type ConversationListResponse = components['schemas']['ConversationListResponse'];
type ConversationRowSchema = components['schemas']['ConversationRowSchema'];
type ConversationMemberSchema = components['schemas']['ConversationMemberSchema'];
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
      sport,
      members: row.members.map(toMember),
      ...(lastEntry === undefined ? {} : { lastEntry }),
    },
  ];
}

function toMember(member: ConversationMemberSchema): ConversationMember {
  return {
    playerId: member.player_id,
    ...(member.nickname == null ? {} : { nickname: member.nickname }),
    ...(member.photo_url == null ? {} : { photoUrl: member.photo_url }),
  };
}

function toEntry(entry: MessageSchema | SystemLineSchema): Entry | undefined {
  if (entry.type === 'message') {
    return {
      kind: 'message',
      seq: entry.seq,
      authorId: entry.author_id,
      sentAt: entry.sent_at,
      text: entry.text,
      clientMessageId: entry.client_message_id,
    };
  }

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
