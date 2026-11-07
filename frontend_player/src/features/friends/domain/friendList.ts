/**
 * **The Friends page's lists, the Add friends sheet's groups, and who PLAYED WITH names**
 * ([#754](https://github.com/Raketa02/Raketa/issues/754); the friends screens §3–§5; ADR-0202 §1).
 *
 * The shapes the reads arrive in, and the one rule a surface would otherwise spell in a ternary:
 * when the result screen's card is hidden. **Every list is the server's, in the server's order** —
 * friends by nickname, requests newest first, groups newest joined first — and nothing here
 * re-sorts one.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { FriendRelation, RequestDirection } from './vocabulary';

/** A sport a friend is rated in: their Level, and its band's published name (*Established*). */
export interface FriendSport {
  readonly sport: Sport;
  readonly level: number;
  readonly band: string;
}

/** **One of your friends**, from any of your groups (*Friends* tab; the picker, #757). */
export interface Friend {
  readonly playerId: string;
  /** Whole, never with an @ (ADR-0199 §1). */
  readonly nickname: string;
  /** Omitted when they have no photograph: the face draws their poster. */
  readonly photoUrl?: string;
  /** Every sport they are rated in, in the sports' own order — a sport this build can't name left off. */
  readonly sports: readonly FriendSport[];
}

/** **A friend's Level in one sport** — the picker's line and their caption on a court (#757). */
export function levelIn(
  friend: Pick<Friend, 'sports'> | undefined,
  sport: Sport,
): FriendSport | undefined {
  return friend?.sports.find((one) => one.sport === sport);
}

/** **An open request** — on *Asked you* made of you, on *You asked* yours. */
export interface FriendRequest {
  readonly playerId: string;
  readonly nickname: string;
  readonly photoUrl?: string;
  /** *Asked you* only: you said *Not now*. It stays open, and **Accept** still answers it. */
  readonly setAside: boolean;
}

/** **A group of yours, in the Add friends sheet** — *8 members · 2 to add*. */
export interface GroupToAddFrom {
  readonly groupId: string;
  readonly name: string;
  /** Everybody in it, you included. */
  readonly memberCount: number;
  /** Members you could still ask: not you, not a friend, no open request either way, not blocked. */
  readonly toAdd: number;
}

/** **The page's three tabs from You** — *Friends · Asked you · You asked* (the screens §4.1). */
export type FriendsTab = 'friends' | RequestDirection;

/**
 * **Somebody else on a game, as PLAYED WITH draws them** — their face, name and Level off the
 * game's seats, and where the reader stands with them. The composer joins the two; a nickname is
 * absent for an account that can no longer be named.
 */
export interface PlayedWithPerson {
  readonly playerId: string;
  readonly nickname?: string;
  readonly photoUrl?: string;
  /** Their Level in the game's sport; absent if unrated. */
  readonly level?: number;
  readonly relation: FriendRelation;
}

/** A person PLAYED WITH can draw and ask: one with a name. */
export type ShownPlayedWith = PlayedWithPerson & { readonly nickname: string };

/**
 * **Who PLAYED WITH lists — or nobody, and the card is hidden** (the screens §3; Q26): the others on
 * the game in the order the read gave them, **hidden once every one of them is your friend**, since
 * nothing on the card would be left to do. Somebody who can no longer be named is left off first —
 * there is no face to draw and nobody to ask — so a card whose only stranger is a deleted account
 * hides too.
 */
export function playedWithShown(people: readonly PlayedWithPerson[]): readonly ShownPlayedWith[] {
  const named = people.filter((one): one is ShownPlayedWith => one.nickname !== undefined);
  return named.every((one) => one.relation === 'FRIEND') ? [] : named;
}
