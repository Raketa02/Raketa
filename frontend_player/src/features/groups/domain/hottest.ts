/**
 * **Home's *Hottest groups*, the phone's half** ([#800](https://github.com/Rakieta02/Rakieta/issues/800);
 * ADR-0204 §3; the Home rows mechanics §5). The heat, the tags, the order and the six are the
 * server's; what is left here is what a card and its sheet **offer** the reader, how many faces each
 * draws, and how a write's answer lands on the card it came from.
 */

import type { GroupPerson, HottestGroup, HottestPage, HottestRow } from './group';
import { groupAction, type GroupAction } from './groupRules';
import type { GroupRelation } from './vocabulary';

/** Faces on a card (home rows 3); the sheet draws every face served, which is six at most. */
export const CARD_FACES = 4;
/** Faces on the group sheet (home rows 6) — as many as the read serves. */
export const SHEET_FACES = 6;

/**
 * **A tap that joins or asks** — the two chips that write (`join`, `ask`), where *Asked* and *You're
 * in* open something instead. The card's chip is `groupAction`'s answer, every group row's rule.
 */
export function isJoinTap(action: GroupAction | SheetButton): action is 'join' | 'ask' {
  return action === 'join' || action === 'ask';
}

/** The sheet's one button: the chip's, except that a member's opens the group (the mechanics §5.9). */
export type SheetButton = Exclude<GroupAction, 'in'> | 'open';

export function sheetButton(group: HottestGroup): SheetButton {
  const action = groupAction(group);
  return action === 'in' ? 'open' : action;
}

export function cardFaces(group: HottestGroup): readonly GroupPerson[] {
  return group.faces.slice(0, CARD_FACES);
}

export function sheetFaces(group: HottestGroup): readonly GroupPerson[] {
  return group.faces.slice(0, SHEET_FACES);
}

/**
 * **The row, or a page of *Groups heating up*, with one card's relation moved** — what a join, an
 * ask or a withdraw draws at once, on each (#823). The rest stands: the row's total and a page's
 * cursor move with the next read, which every such write asks for (#822).
 */
export function withRelation<Held extends HottestRow | HottestPage>(
  held: Held,
  groupId: string,
  relation: GroupRelation,
): Held {
  return {
    ...held,
    groups: held.groups.map((group) => (group.id === groupId ? { ...group, relation } : group)),
  };
}

/**
 * ***Groups heating up*'s list** — the pages in the order read, **each group once**, where it was
 * first drawn. Heat is worked out on every read (the mechanics §5.10), so a group that cooled behind
 * a page's cursor is read again by the next, and a list keyed by group cannot draw it twice.
 */
export function joinHottestPages(pages: readonly HottestPage[]): readonly HottestGroup[] {
  const seen = new Set<string>();
  return pages.flatMap((page) =>
    page.groups.filter((group) => {
      if (seen.has(group.id)) return false;
      seen.add(group.id);
      return true;
    }),
  );
}
