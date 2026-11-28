/**
 * **What a conversation says** — the system-line sentences, and every word on the room's screen.
 *
 * The words are the client's because a code is all that crosses
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §23,
 * [ADR-0146](../../../../../docs/adr/0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md)),
 * and what happened in a room is this feature's.
 *
 * It wrote the Chats tab's rows too — the last entry on one line, a place drawn without its court —
 * until that tab was removed with the old loop ([#576](https://github.com/Rakieta02/Rakieta/issues/576)).
 * The plan's lines (*set the place*, *locked the plan*) stay in the table below although no room
 * writes them any more: a stored line still folds, and a code with no words would not compile.
 *
 * ## `{name}` comes from the people the response names, and never from `values`
 *
 * The line carries an `actor_id` and no handle, *"so a corrected one fixes the whole backlog"*.
 * `personNamed` over the response's **`people`** is what fills the slot — not the roster, because
 * the actor of a `SEAT_LEFT` line was never a member and a roster lookup drew `? said no`
 * ([#409](https://github.com/Rakieta02/Rakieta/issues/409)) — and an actor the response cannot
 * answer for draws the unknown player's `?`. **It is never *You***: these are third-person records
 * of what happened in a room, read identically by everybody in it — see `domain/membership.ts`.
 * The one sentence here that still reads the roster is {@link typingLine}, because a typist is a
 * member by construction.
 *
 * ## A line this build cannot read is a named gap, and so is one whose values it cannot read
 *
 * §3 owes a **named gap** wherever the code *is* the content, and here it is: a system line is
 * its sentence and nothing else, so a dropped one is a blank slot rather than a shorter list. **The same answer covers an unreadable value**, and that is one rule rather than two: a
 * `SEAT_LEFT` whose departure this build has no word for, or a `DAY_RECORDED` whose value is not
 * a calendar date, leaves exactly the same nothing behind as a code with no sentence. Guessing —
 * *that seat is open again* with no answer, a raw `2026-13-40` — would be the app stating a fact
 * it has not read.
 *
 * ## Four of the nine are shaped by the wire rather than by taste
 *
 * **A seat leaving is one code with the answer as a value**, because *that seat is open again* is
 * the same news either way — and a lapse is still not a decline, which is why the two sentences
 * differ in their first clause and agree in their second. **Setting a slot and moving one are one
 * code told twice**, which is the opposite rule for the opposite case: there is no value telling a
 * first fill from a change, because they are the same fact. **And the lock quotes nothing**
 * ([ADR-0155](../../../../../docs/adr/0155-the-plan-gains-a-lock-and-locking-is-an-act-rather-than-a-count.md)):
 * the three slots are the value and the room already holds a line for each, so `{name} locked
 * the plan` is the whole sentence — the one plan line whose `values` is empty, and the one that
 * says somebody *agreed* rather than that somebody wrote something down. **And the side line
 * names nobody** ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §8): a doubles room born of a mutual holds two people on one side and two empty seats across
 * the net, and *You two are a side. Fill the seats to find your opponents.* is addressed to both
 * of them at once — the one sentence in this table that is second person, because it is the one
 * line whose readers are exactly the people it is about, and the one with no `{name}` to fill.
 *
 * **And there is no *Game on* line**, here or anywhere: everybody having accepted is an
 * arrangement of the seats, so a sentence announcing it would be a second place for a derived
 * standing to be true. Six events publish nothing at all and §23.1 names each with its reason.
 */

import { weekdayOf } from '@/shared/date/platformZone';
import { counted } from '@/shared/formatting/counted';
import { handleLine } from '@/shared/formatting/handleList';
import { sentenceList } from '@/shared/formatting/sentenceList';
import { handleStem, playerName } from '@/shared/formatting/playerName';
import { dayName } from '@/shared/vocabulary/availabilityPresentation';
import { OUT_OF_DATE_GAP } from '@/shared/vocabulary/outOfDate';

import type { LiveState } from '../domain/liveState';
import {
  departureOf,
  invitedCount,
  type EntryValues,
  type SystemLine,
  type SystemLineCode,
} from '../domain/entry';
import {
  personNamed,
  type ConversationMember,
  type ConversationPerson,
} from '../domain/membership';

/** Everything a sentence in the table below is allowed to read. */
interface SystemLineFacts {
  /** The actor, already named off `people`. Never *You*, and never read from `values`. */
  readonly name: string;
  readonly values: EntryValues;
}

/**
 * **The doubles room's first words** — the one system line a room is born with (ADR-0169 §8).
 *
 * Exported for the suite that walks the room: an assertion spelling the sentence as a literal is
 * a red build for the ticket that rewords it.
 */
export const SIDE_FORMED_LINE = 'You two are a side. Fill the seats to find your opponents.';

/**
 * §23's nine, keyed by the union — **so a code with no words does not compile.**
 *
 * One function per code rather than a `Record<Code, string>`, because eight of the nine quote
 * at least a handle: the split §1 draws is between a code with no payload and one with a
 * payload, and the one member of this vocabulary in the first group — `SIDE_FORMED` — takes the
 * same shape rather than a second table, so the stream has one way of turning a code into words.
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
    // The third way (ADR-0162): they had agreed, and left the game. The same second clause,
    // because it is the same news — and `people` names them, as it names a decliner.
    if (departure === 'LEFT') return `${name} left — that seat is open again`;
    return OUT_OF_DATE_GAP;
  },

  GAME_PLAYED: ({ name }) => `${name} said you played`,

  PLACE_RECORDED: ({ name, values }) =>
    values.value === undefined ? OUT_OF_DATE_GAP : `${name} set the place · ${values.value}`,

  DAY_RECORDED: ({ name, values }) => {
    const day = values.value === undefined ? undefined : weekdayOf(values.value);
    return day === undefined ? OUT_OF_DATE_GAP : `${name} set the day · ${dayName(day)}`;
  },

  HOUR_RECORDED: ({ name, values }) =>
    values.value === undefined ? OUT_OF_DATE_GAP : `${name} set the time · ${values.value}`,

  // No value and no gap to fall into: the sentence is whole with the name alone, and a value
  // this line was never meant to carry is not read rather than guessed at.
  PLAN_LOCKED: ({ name }) => `${name} locked the plan`,

  // No value and no name either: the line is about both people on the side and addresses them,
  // so the facts are not read at all — an actor the wire never sends is not reached for.
  SIDE_FORMED: () => SIDE_FORMED_LINE,
};

/** One system line, as a sentence — the stream's, keyed by code ([#364](https://github.com/Rakieta02/Rakieta/issues/364)). */
export function systemLineSentence(
  line: SystemLine,
  people: readonly ConversationPerson[],
): string {
  if (line.code === undefined) return OUT_OF_DATE_GAP;

  return SYSTEM_LINE[line.code]({
    name: playerName(personNamed(people, line.actorId)),
    values: line.values,
  });
}

/**
 * What the screen is called **before it knows who is in it.**
 *
 * The header's real title is the handles, which is a fact off the read — so this is the word over
 * the three states that have no room to name: the read is still coming, it failed, or no room of
 * yours has that address.
 */
export const CONVERSATION_SCREEN_TITLE = 'Conversation';

/**
 * **One sentence for three states.**
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
 * **The title line — each handle's stem, comma-separated, giving way by whole names**
 * ([#401](https://github.com/Rakieta02/Rakieta/issues/401)).
 *
 * `handleStem` is the sanctioned cut: the handle up to its first word break, `Sergio.Sabater`
 * drawn as `Sergio`. It is **not** the first name ADR-0107 forbids — that record is against
 * *inventing* a familiar form, a stem is a prefix of the handle the person chose, cut at a
 * character they typed, and `the-words.md` §15 is what permits a box to truncate what a sentence
 * may not; `handleStem`'s own docstring carries the argument and the two conditions, and both
 * hold here: the spoken name keeps every handle whole (`conversationHeaderLabel`), and a handle
 * that opens with a break keeps all of itself.
 *
 * The stems are then **shorter inputs to the same rule**: `handleLine` still drops whole names at
 * a separator and never cuts one (§15), so more names fit and nothing about the dropping changes.
 *
 * **With nobody to name, the line says what the room is doing** — {@link WAITING_FOR_OTHERS}.
 * The organiser alone again is a real room: somebody joined and left while the rest were still
 * deciding ([#429](https://github.com/Rakieta02/Rakieta/issues/429) E4), and the room stands with
 * one member until somebody accepts. `handleLine` of nothing is the empty string, which drew a
 * blank at `h1` over the sport; the rule lives here rather than at the call site so there is no
 * arrangement of props that draws that gap.
 *
 * @param budget the line's width in characters at `h1` — `headerHandleBudget`.
 */
export function headerTitle(handles: readonly string[], budget: number): string {
  return handles.length === 0 ? WAITING_FOR_OTHERS : handleLine(handles.map(handleStem), budget);
}

/**
 * **The title where there is nobody else in the room** — the organiser alone again, waiting on
 * the seats still deciding. Present tense and pointed at what happens next, on §22.1's rule that
 * an empty state never asserts that nothing is happening: the challenge is out, and the room is
 * waiting for its answers. Drawn in the title slot and spoken in its place
 * (`conversationHeaderLabel`), since there is no handle to keep whole.
 */
export const WAITING_FOR_OTHERS = 'Waiting for others to join';

/**
 * **The second line — the sport, and where the game stands.**
 *
 * `Padel · booked`: the booking's own word in lower case, handed in by the booked game's chat, so
 * the room says where the game stands without a trip back to its details — the word the player
 * already reads on the game's card, and **not** the twenty-state standing ADR-0148 §6 refused
 * ([ADR-0157](../../../../../docs/adr/0157-the-conversation-header-names-its-people-by-their-stems-and-says-which-rung-the-game-is-on.md)
 * says why that is a different thing). With no word, the line is the sport alone, and none is
 * invented.
 */
export function headerSubline(sportName: string, state: string | undefined): string {
  return state === undefined ? sportName : `${sportName}${LINE_JOIN}${state}`;
}

/** What separates the sport from the state on the drawn line. Structure; a listener never hears it. */
const LINE_JOIN = ' · ';

/**
 * **The chat door, wherever it is drawn** — *"the same words as every other chat door"*
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §24.5).
 *
 * It lives here rather than in the feature that draws it, because what it opens is a
 * conversation: a booked game's details draw it today, and one constant is what makes *the same
 * words* true by construction wherever the next one is drawn.
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

/**
 * **The hint in the empty box** — a placeholder and not a label, which 6.13 keeps apart on
 * purpose: the placeholder goes the moment somebody types, so the name a listener gets is
 * `COMPOSER_LABEL` above and this is only what the box says while it is empty
 * ([#402](https://github.com/Rakieta02/Rakieta/issues/402), the-words §22.4). *About this game*
 * because that is what the room is for — the whole episode, and nothing else.
 */
export const COMPOSER_PLACEHOLDER = 'Message about this game…';

/** The one control beside it. */
export const SEND = 'Send';

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

/**
 * **Somebody is typing**, said — §22.5's third state, and the sentence a pulsing dot cannot say.
 *
 * Three shapes and one rule: **a name, two names, a count from three.** The client already holds
 * the handles the frame's `player_ids` point at and a name is what the room is about, so a person
 * is named — **in a pair too**, where a listener already knows who the one possible typist is:
 * *somebody is typing* would be a second sentence kept only to withhold a name, and the drawn
 * bubble carries none at all, so the spoken name is where the name goes (§20.4, §24.6). Three or
 * more collapses to a count on §19's rule rather than growing a list; the reader is never in the
 * list, so the collapse is reached only in a four where everybody else is typing at once.
 *
 * **The whole handle, never a first name** (ADR-0107), filled from membership and never from the
 * frame — so a corrected name fixes the indicator with no frame re-sent. **The roster and not
 * `people`**, deliberately: a typist is gated on membership and is one (ADR-0156), so the one list
 * a departed player is on is the one list that cannot be typing. **The ellipsis is one
 * character**, so a screen reader does not read *dot dot dot*.
 *
 * `undefined` for nobody: there is no sentence to say and no region to fill, which is how the
 * indicator goes away without announcing that it did (§24.6).
 */
export function typingLine(
  playerIds: readonly string[],
  members: readonly ConversationMember[],
): string | undefined {
  if (playerIds.length === 0) return undefined;
  if (playerIds.length >= TYPISTS_NAMED_UP_TO + 1) {
    return `${counted(playerIds.length, 'person', 'people')} are typing…`;
  }

  const names = playerIds.map((id) => playerName(personNamed(members, id)));

  return names.length === 1 ? `${names[0]} is typing…` : `${sentenceList(names)} are typing…`;
}

/** How many typists are named before the sentence counts them instead. §22.5: two. */
const TYPISTS_NAMED_UP_TO = 2;

/**
 * **The chat has ended, and the room is still on screen** — §22.5's fourth state, one sentence
 * in the composer's place ([#429](https://github.com/Rakieta02/Rakieta/issues/429)).
 *
 * A booked game's room ends with its game — the grace after its hour running out, or the game
 * called off — and why is the game's card to say, so the room says only that the chat has ended.
 * It named who had left, or that nobody else was coming, in the old loop's rooms, which could end
 * before they had a game; no room can since that loop was removed
 * ([#576](https://github.com/Rakieta02/Rakieta/issues/576)).
 *
 * The register is a fact, not a warning and not a refusal: nothing here is reversible and nothing
 * was refused, so it is neither amber nor coral.
 */
export const ROOM_OVER_LINE = 'This chat has ended.';
