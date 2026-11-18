/**
 * **A people row on Home, as read** — New in Raketa, Same competitive level, Same vibe: up to ten
 * cards in the server's order, and **how many the row could show**
 * ([#822](https://github.com/Raketa02/Raketa/issues/822); ADR-0205 §6; the Home rows mechanics §6.9,
 * §7.5, §8.8).
 *
 * The total is **the pool, never the good matches**: everybody who qualifies for the row under its
 * own exclusions, each person once however many sports or tags qualify them, **counted up to 100**.
 * It is the line's count and *See all N ›* — the same figure, though See all shows one sport at a
 * time — and it is the server's, refreshed only by the next read.
 */

import type { FriendRelation } from '@/features/friends/types';
export interface PeopleRow<Person> {
  readonly people: readonly Person[];
  readonly total: number;
}

/** A card on a people row: whom, and where the reader stands with them. */
interface Card {
  readonly playerId: string;
  readonly relation: FriendRelation;
}

/**
 * **A friend write's answer, drawn on the row as read** (the mechanics §13) — the one card's relation
 * moved, and the order, everybody else and the total as they were: a fresh match asked becomes a gap
 * only on the next read, and the total moves with that read too.
 */
export function withRelation<Person extends Card>(
  row: PeopleRow<Person>,
  playerId: string,
  relation: FriendRelation,
): PeopleRow<Person> {
  return {
    ...row,
    people: row.people.map((one) => (one.playerId === playerId ? { ...one, relation } : one)),
  };
}
