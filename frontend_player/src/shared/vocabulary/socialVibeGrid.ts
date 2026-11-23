/**
 * **What the Social vibe card draws** — the table's number, its columns and your tags' rows
 * ([#840](https://github.com/Raketa02/Raketa/issues/840);
 * [ADR-0207](../../../../docs/adr/0207-for-fun-is-built-by-shared-social-tags-and-every-for-fun-game-carries-a-social-vibe.md)
 * §6, for fun 7).
 *
 * ## Why the shape is here, below both features
 *
 * `socialTagOverlap`'s reason, a second time. The card is one component in `shared/ui`, because a
 * game still filling (`proposals`, #840) and a booked game (`games`, #841) both draw it, and neither
 * may import the other. A component beneath every feature cannot read a type that lives inside one,
 * and a `domain/` rule cannot import a module that imports React Native — so the value a pure rule
 * returns and the card consumes has one home below both, and this is it.
 *
 * **The rules stay in the features.** Which people are the columns and in what order, and which
 * rows another player shares, are read off each feature's own read: `proposals/domain/details.ts`
 * builds one from `GET /proposals/{id}`. The card derives nothing; it draws what it is handed.
 */

import type { SocialTagId } from './socialTags';

/** One person at the table — a column, headed by their face and their nickname. */
export interface SocialVibeColumn {
  readonly playerId: string;
  /** The reader: the first column, named *You*. */
  readonly isYou: boolean;
  /** Their nickname, whole — the column shortens it. Absent for an account no longer named. */
  readonly name?: string;
  /** Omitted when they have no photograph: the column draws their poster. */
  readonly photoUrl?: string;
}

/** One of **your** tags, and who at the table carries it. */
export interface SocialVibeRow {
  readonly tag: SocialTagId;
  /** One per column, in the columns' order: `true` under each player who carries the tag. */
  readonly dots: readonly boolean[];
  /**
   * **Somebody else carries it too** — the pale volt band, dark words and olive dots. Otherwise the
   * row is yours alone: grey words and a grey dot, no band.
   */
  readonly shared: boolean;
}

/** The card's whole input: how much the table shares, and who shares yours. */
export interface SocialVibeGrid {
  /** The served Social vibe — the deck card's own number, a whole percent. */
  readonly pct: number;
  /** **You first**, then the others in the tiles' order. */
  readonly columns: readonly SocialVibeColumn[];
  /** Your tags, in the vocabulary's order. */
  readonly rows: readonly SocialVibeRow[];
}
