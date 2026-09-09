/**
 * **What the Chats inbox announces** — written here, through the same mechanism the visible
 * words are, and never inlined in a component.
 *
 * [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §20's rule is that an
 * accessible name is **copy**: it is localisable, it quotes a duration that needs a format, and
 * it composes sentences that already have a home. So it lives beside the rest of the copy, and
 * §20.1's one rule decides the element:
 *
 * > **One accessibility element per action. Everything with no action of its own merges into
 * > the nearest action above it.**
 *
 * **A row is one element because it is one action.** The whole row is the door and every act a
 * challenge has is on the screen behind it, so the faces, the handles, the sport and the line
 * merge into the button — and the urgency stripe is hidden outright, because the duration is
 * already in this label and a bar restating it is the second spelling #335 refused.
 *
 * **The handles are whole.** The list truncates for the eye and never for the ear (§24.2), which
 * is §20.4's *"the visible label truncates, the spoken one never does"* one surface over — and
 * here it is stronger, because what the eye loses is whole names rather than characters.
 *
 * **They are joined with a final *and***, which is §22.6's join for a list in a sentence and what
 * §24.2 spells the conversation row beside this one with. A one-handle row is unchanged by it —
 * `Ewa M., squash, 21 h left to answer` is exactly what §24.2 gives for this row — and a listener
 * moving between the tab's two sections hears one dialect
 * ([#363](https://github.com/Raketa02/Raketa/issues/363)).
 *
 * **The identifying facts lead.** Who and what sport, then what the row is asking of you: a
 * listener who has heard enough interrupts and acts, and *what* they would be acting on has to
 * come first.
 */

import { spokenHandles } from '@/shared/formatting/handleList';

/** A row under `CHALLENGES`: who, which sport, and the row's own line. */
export function challengeRowLabel(
  handles: readonly string[],
  sportName: string,
  line: string,
): string {
  return `${spokenHandles(handles)}, ${sportName}, ${line}`;
}

/**
 * **The withdraw's accessible name says what it withdraws** (§24.3).
 *
 * The visible control is one word, because the screen it sits on is about one challenge and the
 * space around it says which. A listener has no such space: they arrive on a button by moving to
 * it, and *Withdraw* alone in a run of controls is a verb with no object. It is
 * [6.9](../../../../docs/design-system.md)'s rule — *"names which photo it removes"* — applied
 * one surface over, and it is the one place on this screen where the two registers differ.
 *
 * It names the **challenge** rather than the people on it, which is what the act does: a
 * withdraw is whole-challenge and never removes one person, so a name that listed handles would
 * describe an act this route refuses.
 */
export const WITHDRAW_CHALLENGE_NAME = 'Withdraw this challenge';
