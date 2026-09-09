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
 * **The identifying facts lead.** Who and what sport, then what the row is asking of you: a
 * listener who has heard enough interrupts and acts, and *what* they would be acting on has to
 * come first.
 */

import { HANDLE_SEPARATOR } from '../domain/challengeInbox';

/** A row under `CHALLENGES`: who, which sport, and the row's own line. */
export function challengeRowLabel(
  handles: readonly string[],
  sportName: string,
  line: string,
): string {
  return `${handles.join(HANDLE_SEPARATOR)}, ${sportName}, ${line}`;
}
