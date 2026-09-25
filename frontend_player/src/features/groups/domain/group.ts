/**
 * **A Group, as the player app reads it** — the crowd that already plays together, at a Home club
 * ([ADR-0183](../../../../../docs/adr/0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md),
 * the root glossary's **Groups** and **Club**).
 *
 * Four shapes, one per place a group is drawn: a card on the reader's Groups list, a row inside a
 * club's card in a search, a club's card itself, and the group as its page reads it. They share
 * the tile and the dots and differ in what the place needs — a list card names its Home club, a
 * search row says what the reader can do about it, the page carries the link.
 *
 * **Nothing here is computed on the phone.** The monogram's letters and colour are cut by the
 * backend so every client draws the same tile (§5); the sport dots are read when the group is
 * read (§6); the distance is the server's shown kilometres, or absent for a reader with no
 * Location area. This file holds what came, in the app's spelling.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { GroupRelation, JoinPolicy, ReadAs } from './vocabulary';

/**
 * The group's tile: two letters **as typed** — never re-cased — and a colour **key** from 0 to 7
 * that is fixed for the group for ever. The key is mapped to a hue on this side (`MONOGRAM_HUES`);
 * the backend never names a colour.
 */
export interface Monogram {
  readonly letters: string;
  readonly colourKey: number;
}

/** A group's Home club, as the line under its name. */
export interface ClubName {
  readonly id: string;
  readonly name: string;
}

/** **A card on the reader's Groups list** (play mock 38). The list comes newest joined first. */
export interface MyGroup {
  readonly id: string;
  readonly name: string;
  readonly monogram: Monogram;
  /** The sport dots: each sport at least two members are rated in, in the registry's order. */
  readonly sports: readonly Sport[];
  readonly memberCount: number;
  readonly homeClub: ClubName;
}

/** **A group inside a club's card**, with what it is to the reader (play mocks 9, 35–37). */
export interface GroupAtClub {
  readonly id: string;
  readonly name: string;
  readonly monogram: Monogram;
  readonly sports: readonly Sport[];
  readonly memberCount: number;
  readonly joinPolicy: JoinPolicy;
  /**
   * Who answers a request — the Owner's **whole Name**, never cut to a first name (ADR-0171 §4).
   * `null` for an account that can no longer be named.
   */
  readonly ownerName: string | null;
  readonly relation: GroupRelation;
}

/**
 * **One club, as a search draws it** — a header that is context rather than a choice, and the
 * groups inside it. `distanceKm` is `null` for a reader with no Location area, and then nothing
 * pretends to know how far away the club is.
 */
export interface SearchedClub {
  readonly id: string;
  readonly name: string;
  readonly district: string;
  readonly distanceKm: number | null;
  readonly sports: readonly Sport[];
  readonly groups: readonly GroupAtClub[];
}

/**
 * **One answered search** — the text it answered, the clubs it found, where the next page is,
 * and what the text was read as. The text travels with the answer so that *No match for "…"*
 * quotes what was searched for, never what has been typed since.
 */
export interface ClubSearch {
  readonly text: string;
  readonly clubs: readonly SearchedClub[];
  readonly nextPage: number | null;
  /** Home-club search reads everything as text; only join search recognises a link. */
  readonly readAs: ReadAs;
}

/** **A group, as one of its members opens it** — the page's header reads this (play mock 40). */
export interface Group {
  readonly id: string;
  readonly name: string;
  readonly monogram: Monogram;
  readonly sports: readonly Sport[];
  readonly memberCount: number;
  readonly homeClub: ClubName;
  /** The Group link — it never changes. */
  readonly link: string;
  readonly joinPolicy: JoinPolicy;
  readonly isOwner: boolean;
}

/** A group's name is 1–40 characters once trimmed (ADR-0183 §3). The field stops at 40. */
export const GROUP_NAME_MAX = 40;

/** **A Player group to create** — the New group form, checked (`schemas/newGroupForm`). */
export interface NewGroup {
  readonly name: string;
  readonly homeClubId: string;
  readonly joinPolicy: JoinPolicy;
}
