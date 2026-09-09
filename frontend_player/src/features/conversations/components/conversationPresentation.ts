/**
 * **What a conversation says** — the seven system-line sentences, the section's name, and the
 * line a row draws.
 *
 * The words are the client's because a code is all that crosses
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §23,
 * [ADR-0146](../../../../../docs/adr/0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md)).
 * §22 assigns this file §23 by **vocabulary owner** rather than by screen: the tab's own
 * sentences are the shell's, the plan's are `planPresentation.ts`'s, and what happened in a room
 * is this feature's.
 *
 * ## One module, two surfaces, and the difference is a prop
 *
 * The Chats row draws `last_entry`, which is one of the same two shapes the stream draws, and it
 * renders **through this module rather than a second copy** — a row that formatted a system line
 * its own way is the drift a shared presentation module exists to prevent, and it would be found
 * the first time a code gained a value
 * ([`the-loop-components.md`](../../../../../docs/specs/the-loop/the-loop-components.md) §2.2).
 * What the row does differently is a **prop**: {@link LineRoom}, and nothing else.
 *
 * **The prop exists because *when it does not fit* is not something a copy deck can measure.**
 * #335's answer to a system line overflowing a Chats row is *a shorter value, not a second line*
 * — one rule for both row kinds instead of two — and the value it names is the place, drawn
 * without the court. So how much room there is arrives as an argument: a row has one line and
 * asks for the short place, and a stream has the width and prints what somebody typed.
 *
 * ## `{name}` comes from membership and never from `values`
 *
 * The line carries an `actor_id` and no handle, *"so a corrected one fixes the whole backlog"*.
 * `memberNamed` is what fills the slot, and an actor the room cannot answer for draws the unknown
 * player's `?`. **It is never *You***: these are third-person records of what happened in a room,
 * read identically by everybody in it — see `domain/membership.ts`.
 *
 * ## A line this build cannot read is a named gap, and so is one whose values it cannot read
 *
 * §3 owes a **named gap** wherever the code *is* the content, and here it is: a row's second line
 * is the last entry and nothing else, so a dropped sentence is a blank slot rather than a shorter
 * list. **The same answer covers an unreadable value**, and that is one rule rather than two: a
 * `SEAT_LEFT` whose departure this build has no word for, or a `DAY_RECORDED` whose value is not
 * a calendar date, leaves exactly the same nothing behind as a code with no sentence. Guessing —
 * *that seat is open again* with no answer, a raw `2026-13-40` — would be the app stating a fact
 * it has not read.
 *
 * ## Two of the seven are shaped by the wire rather than by taste
 *
 * **A seat leaving is one code with the answer as a value**, because *that seat is open again* is
 * the same news either way — and a lapse is still not a decline, which is why the two sentences
 * differ in their first clause and agree in their second. **Setting a slot and moving one are one
 * code told twice**, which is the opposite rule for the opposite case: there is no value telling a
 * first fill from a change, because they are the same fact.
 *
 * **And there is no *Game on* line**, here or anywhere: everybody having accepted is an
 * arrangement of the seats, so a sentence announcing it would be a second place for a derived
 * standing to be true. Six events publish nothing at all and §23.1 names each with its reason.
 */

import { counted } from '@/shared/formatting/counted';
import { playerName } from '@/shared/formatting/playerName';
import { dayName } from '@/shared/vocabulary/availabilityPresentation';
import { OUT_OF_DATE_GAP } from '@/shared/vocabulary/outOfDate';

import type { Conversation } from '../domain/conversation';
import {
  departureOf,
  invitedCount,
  weekdayOf,
  type Entry,
  type EntryValues,
  type SystemLine,
  type SystemLineCode,
} from '../domain/entry';
import { memberNamed, type ConversationMember } from '../domain/membership';

/**
 * How much room the surface drawing this line has — **the whole of what the row does
 * differently.**
 *
 * `one-line` is a Chats row: one line, tail-truncated, and a place drawn without its court.
 * `full` is the stream, which has the width and prints the value as it was typed.
 */
export type LineRoom = 'one-line' | 'full';

/** Everything a sentence in the table below is allowed to read. */
interface SystemLineFacts {
  /** The actor, already named through membership. Never *You*, and never read from `values`. */
  readonly name: string;
  readonly values: EntryValues;
  readonly room: LineRoom;
}

/**
 * §23's seven, keyed by the union — **so a code with no words does not compile.**
 *
 * One function per code rather than a `Record<Code, string>`, because every one of the seven
 * quotes at least a handle: the split §1 draws is between a code with no payload and one with a
 * payload, and there is no member of this vocabulary in the first group.
 */
const SYSTEM_LINE: Readonly<Record<SystemLineCode, (facts: SystemLineFacts) => string>> = {
  SEAT_ACCEPTED: ({ name }) => `${name} is in`,

  SEATS_INVITED: ({ name, values }) => {
    const asked = invitedCount(values);
    return asked === undefined
      ? OUT_OF_DATE_GAP
      : `${name} asked ${counted(asked, 'more', 'more')}`;
  },

  SEAT_LEFT: ({ name, values }) => {
    const departure = departureOf(values);
    if (departure === 'DECLINED') return `${name} said no — that seat is open again`;
    if (departure === 'LAPSED') return `${name}'s day ran out — that seat is open again`;
    return OUT_OF_DATE_GAP;
  },

  GAME_PLAYED: ({ name }) => `${name} said you played`,

  PLACE_RECORDED: ({ name, values, room }) => {
    const place = values.value;
    return place === undefined
      ? OUT_OF_DATE_GAP
      : `${name} set the place · ${room === 'one-line' ? placeWithoutTheCourt(place) : place}`;
  },

  DAY_RECORDED: ({ name, values }) => {
    const day = values.value === undefined ? undefined : weekdayOf(values.value);
    return day === undefined ? OUT_OF_DATE_GAP : `${name} set the day · ${dayName(day)}`;
  },

  HOUR_RECORDED: ({ name, values }) =>
    values.value === undefined ? OUT_OF_DATE_GAP : `${name} set the time · ${values.value}`,
};

/**
 * **The place, without the court** — the shorter value #335 chose over a second line.
 *
 * `Zabłocie Sport, court 3` is long because the value is long, and a venue's name is the half that
 * identifies it. The cut is at the **first comma, whatever follows it** — this reads no meaning
 * out of the value and never claims the tail was a court. That is affordable because nothing is
 * lost by it: the whole value is spoken in the row's accessible name, and it is on the screen
 * behind the row. A place with no comma in it is already the shorter value and is drawn whole.
 *
 * **Never applied to a handle** — §15 refuses that outright — which is why this takes a place and
 * not a string.
 */
function placeWithoutTheCourt(place: string): string {
  const [named] = place.split(',');
  return named === undefined || named.trim() === '' ? place : named.trim();
}

/**
 * One system line, as a sentence — the stream's and the row's, keyed by code.
 *
 * Exported because the stream draws it directly ([#364](https://github.com/Raketa02/Raketa/issues/364));
 * the row reaches it through {@link entryLine}, which is the same call with the message arm in
 * front of it.
 */
export function systemLineSentence(
  line: SystemLine,
  members: readonly ConversationMember[],
  room: LineRoom,
): string {
  if (line.code === undefined) return OUT_OF_DATE_GAP;

  return SYSTEM_LINE[line.code]({
    name: playerName(memberNamed(members, line.actorId)),
    values: line.values,
    room,
  });
}

/**
 * What one entry says — **a message as its text, a system line from its code and values.**
 *
 * A message is drawn as the words somebody typed and nothing else: there is no copy in that arm,
 * which is why the author is not in it. On a bubble the handle is a **label beside** the text and
 * conditional on the room having more than two members; on a row it is already in the handle line
 * above, and repeating it would name the same person twice in two type roles.
 */
export function entryLine(
  entry: Entry,
  members: readonly ConversationMember[],
  room: LineRoom,
): string {
  return entry.kind === 'message' ? entry.text : systemLineSentence(entry, members, room);
}

/**
 * **The conversation row's line**, or nothing where the room has no history.
 *
 * `undefined` rather than a sentence, because there is no true one to write: the opening writes no
 * line, so a room whose first acceptance is its whole history has genuinely had nothing happen in
 * it — and *nothing has happened yet* is the assertion both sections of this tab refuse. The row
 * draws its sport alone and says nothing more, which is the same answer 10.1's empty-state rule
 * gives one level up.
 *
 * **The row asks for it twice**, which is what {@link LineRoom} is for: `one-line` for the eye and
 * `full` for the spoken name, because §20.4 is *"the visible label truncates, the spoken one never
 * does"* and a place drawn without its court is exactly that truncation one register over.
 */
export function conversationRowLine(
  conversation: Conversation,
  room: LineRoom,
): string | undefined {
  return conversation.lastEntry === undefined
    ? undefined
    : entryLine(conversation.lastEntry, conversation.members, room);
}

/**
 * The section's own name, and **it carries no count**.
 *
 * The badge is the only number on this screen ([#326](https://github.com/Raketa02/Raketa/issues/326)
 * §6), and it counts unanswered challenges addressed to you — a second number beside it counting
 * rooms would be two numbers meaning different things on one screen, which is that record's own
 * named failure.
 *
 * Stored as a word rather than as `CONVERSATIONS`: the heading is uppercased by 3.3's `eyebrow`
 * role, and a listener should hear a section name rather than a shout.
 */
export const CONVERSATIONS_HEADING = 'Conversations';

/** The screen a row opens — its title, and the whole of what this file owes it today. */
export const CONVERSATION_SCREEN_TITLE = 'Conversation';

/**
 * The landing a row needs in order to be a door, before the screen behind it exists.
 *
 * 10.1's empty-state shape — one line of `tiny` in `muted`, present-tense, naming what belongs
 * here — held to the same two refusals every other line in this app is: it never promises a date
 * and it never says nothing is happening. What the screen becomes is
 * [#364](https://github.com/Raketa02/Raketa/issues/364)'s.
 */
export const CONVERSATION_SCREEN_NOT_BUILT =
  'The room where you agree the day, the hour and the place — not built yet';
