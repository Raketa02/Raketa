/**
 * **Home's *Hottest groups*, the phone's half** ([#800](https://github.com/Raketa02/Raketa/issues/800);
 * ADR-0204 §3; the Home rows mechanics §5). The heat, the tags, the order and the six are the
 * server's; what is left here is what a card and its sheet **offer** the reader, how many faces each
 * draws, and how a write's answer lands on the card it came from.
 */

import type { GroupPerson, HottestGroup } from './group';
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

/** **The row with one card's relation moved** — what a join, an ask or a withdraw draws at once. */
export function withRelation(
  groups: readonly HottestGroup[],
  groupId: string,
  relation: GroupRelation,
): readonly HottestGroup[] {
  return groups.map((group) => (group.id === groupId ? { ...group, relation } : group));
}
