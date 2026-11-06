/**
 * **Every sentence this feature says** — the row at the foot of a record, the confirm sheet, and
 * You › Account › Blocked players ([#587](https://github.com/Raketa02/Raketa/issues/587), PRD #571;
 * [ADR-0193](../../../../../docs/adr/0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md)).
 *
 * ## The whole name, and no pronoun
 *
 * The PRD proposed *Block Kuba* and *He isn't told*, and said the design pass may refine them. Two
 * rules refine them here:
 *
 * - **The nickname is said whole.** ADR-0199 §1 (ADR-0107 §4's rule, read on the nickname again):
 *   every sentence naming somebody uses the whole nickname, never with an @, and nothing invents a
 *   familiar form. A row's label is its spoken name, so *Block kuba.w*; a box may cut the drawing,
 *   never the words.
 * - **No pronoun.** This app does not know whether Kuba is *he*: the one thing that could say is
 *   the gender answer, and the gender step promises nobody is ever shown it. So the sheet says
 *   *They aren't told.*
 *
 * ## The sheet's two ways out never share a name
 *
 * *Cancel* is the button under *Block*; the sheet's close control does the same under its own name,
 * *Not now* — the links sheet's rule, *two controls never share one*.
 */

export const BLOCKS_COPY = {
  /**
   * **The record's right button, drawn** (#753): *Block* beside the friend button, *Unblock* alone and
   * full width. Spoken whole — `blockRowLabel`, `unblockRowLabel` — since the drawing names nobody.
   */
  row: { block: 'Block', unblock: 'Unblock' },
  sheet: {
    /** The act, once, on the control that does it. */
    block: 'Block',
    blocking: 'Blocking…',
    /** The button under it — nothing changes. */
    cancel: 'Cancel',
    /** The sheet's close does the same, under its own name. */
    close: 'Not now',
  },
  unblocking: 'Unblocking…',
  blockedPlayers: {
    title: 'Blocked players',
    /** Drawn beside each name on the list; the spoken name carries the person too. */
    unblock: 'Unblock',
    /** The contract's own words for an empty list. */
    empty: "You haven't blocked anyone.",
    loading: 'Reading your blocks…',
    readAgain: 'Try again',
  },
} as const;

/** The row at the foot of somebody else's record, while the reader has not blocked them. */
export function blockRowLabel(name: string): string {
  return `Block ${name}`;
}

/** The same row once the reader has — and the spoken name of a list row's *Unblock*. */
export function unblockRowLabel(name: string): string {
  return `Unblock ${name}`;
}

/** The confirm sheet's title: the question the *Block* under it answers. */
export function blockSheetTitle(name: string): string {
  return `Block ${name}?`;
}

/**
 * **What a block does, before it does it** — ADR-0193's Consequences: *the confirm sheet must say
 * what blocking does, because nothing afterwards will.*
 */
export function blockSheetBody(name: string): string {
  return `You won't be put in games with ${name}. They aren't told.`;
}

/** *Blocked players*' line on You › Account — how many, or *Nobody*. */
export function blockedCountLine(count: number): string {
  if (count === 0) return 'Nobody';
  return count === 1 ? '1 player' : `${count} players`;
}
