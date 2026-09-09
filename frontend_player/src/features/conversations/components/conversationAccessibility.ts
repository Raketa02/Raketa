/**
 * **What a conversation row announces** — written here, through the same mechanism the visible
 * words are, and never inlined in a component.
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
  const said = [spokenHandles(handles), sportName, ...(line === undefined ? [] : [line])];

  return said.join(', ');
}
