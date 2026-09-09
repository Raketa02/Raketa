/**
 * **What a conversation says** — the seven system-line sentences, the section's name, the line a
 * row draws, and every word on the screen behind it.
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
import type { LiveState } from '../domain/liveState';
import type { QuickChip } from '../domain/quickChips';
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

/**
 * What the screen is called **before it knows who is in it.**
 *
 * The header's real title is the handles, which is a fact off the read — so this is the word over
 * the three states that have no room to name: the read is still coming, it failed, or no room of
 * yours has that address. `ChallengeScreen` holds the same constant for the same three.
 */
export const CONVERSATION_SCREEN_TITLE = 'Conversation';

/**
 * **One sentence for three states**, exactly as the challenge screen's is.
 *
 * `conversation_not_found` is one code for three cases — there is no such room, there is one and
 * you are not in it, or it is past its end whether or not the sweep has run
 * ([ADR-0153](../../../../../docs/adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md)
 * §5) — and a sport this build cannot name lands here too. They are deliberately not told apart:
 * a `403` would answer *is this id real* about a stranger's evening, and there is nothing a
 * player would do differently in any of the four.
 */
export const NO_CONVERSATION_HERE = 'No conversation of yours has this address.';

/**
 * **The door to the game**, and the visible half of it is the design's word.
 *
 * Drawn only where there is a game: a `LINE_UP_INCOMPLETE` room has no game and no plan, so
 * there is nothing to open and **no door is drawn rather than a dead one**. The spoken half is
 * `conversationAccessibility.ts`', and the two differ on purpose.
 */
export const DETAILS = 'Details';

/**
 * **The chat door, wherever it is drawn** — *"the same words as every other chat door"*
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §24.5).
 *
 * It lives here rather than in the feature that draws it, because what it opens is a
 * conversation and three surfaces will draw it: the challenge screen's half-built court is the
 * first, and the game screen's planning arms and Now's ✉ are the other two. One constant is what
 * makes *the same words* true by construction rather than by three people remembering.
 */
export const OPEN_THE_CHAT = 'Open the chat';

/**
 * The composer's name, and **it is spoken rather than drawn**.
 *
 * A field under a header naming the people and the sport, with `Send` beside it, does not need a
 * word over it saying `MESSAGE` — but a listener arrives on the box itself with none of that
 * around it, so the name is required and only the drawing is dropped
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §24.4, and 6.13's
 * `labelHidden`).
 */
export const COMPOSER_LABEL = 'Message';

/** The one control beside it. */
export const SEND = 'Send';

/**
 * §22.4's four, keyed by the union — **so a chip with no words does not compile.**
 *
 * A `Record` rather than a function per code, which is §1's split read the other way: not one of
 * these quotes a value, and that is the rule rather than a coincidence. **Each chip asks the
 * question its slot is about and names nothing** — the prototype's three were a weekday, a part
 * of day and one fixture venue, and *a chip naming Saturday is a chip that is wrong six days a
 * week*.
 *
 * **A chip posts words and changes nothing** (ADR-0144): filling the slot it asks about would
 * record an agreement nobody had yet.
 */
export const QUICK_CHIP: Readonly<Record<QuickChip, string>> = {
  where: 'Where shall we play?',
  day: 'Which day works?',
  hour: 'What time?',
  'on-my-way': 'On my way',
};

/**
 * **The two states the room says something about itself in** — §22.5, keyed by the union, so a
 * fourth state does not compile without words and `live` cannot be given any.
 *
 * `live` is deliberately absent from the key: it is the absence of a claim rather than a claim,
 * and a `Record` over the whole union would invite somebody to fill it in with *Live* — which is
 * a badge saying that everything is normal, on a screen where normal is what nothing is drawn
 * about.
 *
 * **Not live says two things because two things are true.** Sends are ordinary authenticated
 * `POST`s and the channel is unidirectional by construction, so *writing is unaffected and only
 * reading has stopped being live* — and only a sentence carries two parts, which is the whole
 * argument against the dot Part 13 refuses anyway. Players see this **routinely and briefly**:
 * the stream closes at the access token's `exp`, so a reconnect runs roughly every fifteen
 * minutes in production, which is the dividend
 * [ADR-0147](../../../../../docs/adr/0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md)
 * §6 named.
 *
 * **Held names the fact and promises nothing**, because there is no appeal surface in this build
 * and a sentence offering one would be a promise nobody made. It is ADR-0130's register: state
 * the class of problem, name nobody, grade nothing. **This app has never drawn a hold** — these
 * are the first words it has for one — and nothing says how a hold ends, because nothing in this
 * build can end one.
 *
 * **One note for every refused control on the screen**, never one per control: it is one fact
 * about the account, and saying it five times is the failure §1.6 names about counts.
 */
export const LIVE_NOTE: Readonly<Record<Exclude<LiveState, 'live'>, string>> = {
  'not-live': 'Not live — you can still send, and anything you missed arrives when it reconnects.',
  held: 'Your account is on hold. You can read here, but not write.',
};
