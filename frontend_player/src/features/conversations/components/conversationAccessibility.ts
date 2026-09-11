/**
 * **What a conversation announces** — the row in the tab, and every element of the room behind
 * it. Written here, through the same mechanism the visible words are, and never inlined in a
 * component.
 *
 * [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §24.2, on §20.1's one rule:
 *
 * > **One accessibility element per action. Everything with no action of its own merges into the
 * > nearest action above it.**
 *
 * **A row is one element because it is one action** — the whole row is the door, and every act a
 * conversation has is on the screen behind it. The faces, the handles, the sport and the last
 * entry merge into the button.
 *
 * **The handles are whole.** The list truncates for the eye and never for the ear, which is
 * §20.4's *"the visible label truncates, the spoken one never does"* — and here it is stronger,
 * because what the eye loses is whole names rather than characters.
 *
 * **The identifying facts lead**, and the handles are joined with a final *and* — §24.2 spells
 * this row as `Tomek W. and Ola K., padel, Tomek set the day · Saturday`, and §22.6 gives the
 * platform's own join for a list in a sentence. It is what says where the people stop and the
 * sport begins; comma-joined, four facts are one undifferentiated run. The challenge row above
 * speaks the same join, so the tab does not change dialect between its two sections.
 *
 * **The line it is handed is the `full` one**, not the row's. §20.4: *the visible label truncates,
 * the spoken one never does* — so a place the row drew without its court is spoken whole.
 *
 * **A room with no history says its handles and its sport and stops.** There is no last entry to
 * read out, and *nothing has happened yet* is the assertion this tab refuses in both sections.
 */

import { spokenHandles } from '@/shared/formatting/handleList';

/** A row under `CONVERSATIONS`: who, which sport, and the last thing that happened in it. */
export function conversationRowLabel(
  handles: readonly string[],
  sportName: string,
  line: string | undefined,
): string {
  return roomSaid(handles, sportName, line);
}

/**
 * **The one dialect a room is spoken in**, on the row and in the header alike: the handles whole
 * with a final *and*, the sport, then whatever that surface has to add — the last entry on the
 * row, the game's state in the header — or nothing. One shape, so the tab and the room cannot
 * drift into two.
 */
function roomSaid(handles: readonly string[], sportName: string, then: string | undefined): string {
  return [spokenHandles(handles), sportName, ...(then === undefined ? [] : [then])].join(', ');
}

/**
 * **What the room's header is called** — every handle whole, then the sport, then the state.
 *
 * The drawn title is the handles' **stems** ([#401](https://github.com/Raketa02/Raketa/issues/401)),
 * and this is the other half of what makes that allowed: §20.4's *the visible label truncates, the
 * spoken one never does*, read with `handleStem`'s own condition — *every sentence, every accessible
 * name and every toast still carries all sixty-four characters*. It is the row's dialect one screen
 * on (§24.2's `Tomek W. and Ola K., padel, …`): the handles joined with a final *and*, so a
 * listener hears where the people stop, then the facts in the order the header draws them.
 *
 * **One name for the title and the line under it**, because the header is one element — the
 * sub-line qualifies what the title names and has no action of its own — and because the `·`
 * that separates the sport from the state on the drawn line is a mark a listener has no reading
 * for. A room with no game stops at the sport, exactly as the drawn line does.
 */
export function conversationHeaderLabel(
  handles: readonly string[],
  sportName: string,
  state: string | undefined,
): string {
  return roomSaid(handles, sportName, state);
}

/**
 * **§20.1 gains its complement: a stream is navigated by its entries**
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §24.1).
 *
 * > **One accessibility element per action — and one per entry in an ordered stream.**
 *
 * §20.1 was written against a card and a grid, and a conversation's backlog has **no actions in
 * it at all** — so the rule as written merges an entire history into one element a listener
 * cannot move through. That is 6.8's own argument from the other side: *"21 buttons announce 21
 * identical actions, where 21 checkboxes announce 21 answers."* A stream is navigated by entry,
 * the way a grid is navigated by cell, and the complement is stated narrowly enough that it
 * reaches nothing else on this map.
 *
 * **A bubble's name always names its author, even where the bubble does not.** The visible label
 * is drawn only in a room of more than two, because side and ground disambiguate a pair — and
 * *side and ground* is precisely what Part 13's **never colour as the only signal** refuses to
 * let a listener depend on. The **whole handle**, never a familiar form (ADR-0107); *You* for the
 * reader, which is `playerName`'s own arm and is right here because a bubble is addressed to the
 * person reading it rather than being a third-person record of what happened.
 */
export function bubbleLabel(author: string, text: string): string {
  return `${author}: ${text}`;
}

/**
 * **The `Details` door names the destination rather than the screen** (§24.4).
 *
 * *Details* is a word about a screen, and every other door on this map is named by its act. The
 * visible label is the design's and stays; this is what a listener arrives on.
 */
export const OPEN_THE_GAME = 'Open the game';
