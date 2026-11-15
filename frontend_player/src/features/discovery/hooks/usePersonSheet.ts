/**
 * **Whose sheet is up over a people list** — the comparison sheet (#802) and the vibe sheet (#803)
 * keep the same state, on Home's row and in See all alike: whose sheet it is, and whether it is open.
 *
 * - **The sheet draws the latest read of the person**, so a friend write that re-reads the list
 *   moves its button too (the Home rows screens §8.5).
 * - **A read can move them out of the list** — a row holds still through a friend write, but its
 *   next read works §9.1 out again: somebody asked is a gap, and on a row with more fresh matches than
 *   places the next one takes theirs; a block takes them off at once. **The sheet then closes, drawn
 *   as they last were** rather than emptying under the thumb, and the card leaves with them (a call:
 *   the sheet has nowhere left to read them from).
 * - **It never reopens by itself**: a later read bringing them back leaves it shut until it is
 *   tapped, as the round button's own sheets do.
 */

import { useState } from 'react';

export interface PersonSheet<Person> {
  /** Whose sheet it is — their latest read, kept as it was once they leave the list. */
  readonly person: Person | undefined;
  readonly open: boolean;
  readonly show: (person: Person) => void;
  readonly close: () => void;
}

export function usePersonSheet<Person extends { readonly playerId: string }>(
  people: readonly Person[],
): PersonSheet<Person> {
  const [shown, setShown] = useState<Person>();
  const [open, setOpen] = useState(false);
  const current =
    shown === undefined ? undefined : people.find((one) => one.playerId === shown.playerId);
  if (current !== undefined && current !== shown) setShown(current);
  if (open && shown !== undefined && current === undefined) setOpen(false);

  return {
    person: current ?? shown,
    open,
    show: (person) => {
      setShown(person);
      setOpen(true);
    },
    close: () => setOpen(false),
  };
}
