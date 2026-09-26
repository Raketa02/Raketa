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

import type { GroupKind, GroupRelation, JoinPolicy, ReadAs } from './vocabulary';

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
  readonly kind: GroupKind;
  readonly name: string;
  readonly monogram: Monogram;
  readonly sports: readonly Sport[];
  readonly memberCount: number;
  readonly joinPolicy: JoinPolicy;
  /**
   * Who answers a request — the Owner's **whole Name**, never cut to a first name (ADR-0171 §4).
   * `null` for an account that can no longer be named, and always on an official group, which has
   * no Owner.
   */
  readonly ownerName: string | null;
  /**
   * **An official group's** answerer — the whole name of the Administrator running it now, cut by
   * nobody. `null` while it **needs an administrator** (ADR-0183 §3), and always on a player group.
   */
  readonly administratorName: string | null;
  /**
   * Whether **the reader** runs this official group — then their tap is *Join* whatever the policy
   * says, because they would otherwise be asking themselves (ADR-0183 §7).
   */
  readonly isAdministrator: boolean;
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

/**
 * **A member's face** — a name and a photograph, and nothing else. `name` is the whole Name, and
 * `null` for an account that can no longer be named: the member keeps their seat. `photoUrl` is
 * a link signed for the one answer it came on, absent when they have none — the poster stands in.
 */
export interface GroupPerson {
  readonly playerId: string;
  readonly name: string | null;
  readonly photoUrl?: string;
}

/**
 * **One sport's *N of M***, for the Games tab (ADR-0183 §13): how many members hold a Skill
 * rating in it, and the first of them to join, in joining order — at most as many as the sport
 * seats, which are the faces that fill its seats.
 */
export interface SportRoster {
  readonly sport: Sport;
  readonly ratedCount: number;
  readonly firstRated: readonly GroupPerson[];
}

/** **A group, as one of its members opens it** — the page reads this (play mocks 14–17, 39–55). */
export interface Group {
  readonly id: string;
  readonly kind: GroupKind;
  readonly name: string;
  readonly monogram: Monogram;
  readonly sports: readonly Sport[];
  readonly memberCount: number;
  readonly homeClub: ClubName;
  /** The Group link — it never changes. */
  readonly link: string;
  readonly joinPolicy: JoinPolicy;
  /** Always `false` on an official group, which has no Owner. */
  readonly isOwner: boolean;
  /**
   * **What an official group plays** — the sports it declares, in the registry's order: the fast
   * filter narrows to the ones the reader is rated in among these, and a reader rated in none of
   * them is shown what to add (#519). **Absent on a player group**, which plays whatever its
   * members are rated in.
   */
  readonly declaredSports?: readonly Sport[];
  /**
   * **Every sport's roster**, the ones the group has no dot for too — the reader may be rated in
   * a sport only they play here, and open it.
   */
  readonly ratedBySport: readonly SportRoster[];
  /**
   * **The Info tab's members row** (#514): up to five faces of everybody **but the reader**, in
   * the Members list's order — the Owner, then newest joined first — with a blocked pair left
   * out, either way round. Empty for a reader alone, and for one a block hides everybody from.
   */
  readonly memberFaces: readonly GroupPerson[];
}

/**
 * **One row of Members, for one sport** (play 61; #514) — *Padel 2,71 · score 92*. Only members
 * rated in the sport are listed, so `level` is always there; `playerScore` is **absent** for
 * somebody the platform has watched nothing of — no record is not a bad one, and never `0`.
 * The **admin** tag is drawn on a player group's Owner and on an official group's Administrator who
 * joined it as a player (`adminTagged`).
 */
export interface GroupMember extends GroupPerson {
  readonly level: number;
  readonly playerScore?: number;
  readonly isOwner: boolean;
  /** Whether they run this official group and joined it as a player. Always `false` on a player group. */
  readonly isAdministrator: boolean;
}

/** One sport a person is rated in, with its Level — *Padel 2,44*. */
export interface SportLevel {
  readonly sport: Sport;
  readonly level: number;
}

/**
 * **A Join request, as its Owner sees it** (club 20, the request card everywhere): who is asking
 * and **every sport they are rated in**, in the registry's order. No Player Score — club 20
 * replaces play 62 by name.
 */
export interface JoinRequest extends GroupPerson {
  readonly levels: readonly SportLevel[];
}

/** **What Edit group saves** — the New group form's Name and Who can join; the home club never changes. */
export interface GroupDetails {
  readonly name: string;
  readonly joinPolicy: JoinPolicy;
}

/**
 * **An edit's answer**: the group as the save left it, and **who the switch to Anyone let in**,
 * in the order they asked — empty for every other save.
 */
export interface EditedGroup {
  readonly group: Group;
  readonly admitted: readonly GroupPerson[];
}

/** A group's name is 1–40 characters once trimmed (ADR-0183 §3). The field stops at 40. */
export const GROUP_NAME_MAX = 40;

/** **A Player group to create** — the New group form, checked (`schemas/newGroupForm`). */
export interface NewGroup {
  readonly name: string;
  readonly homeClubId: string;
  readonly joinPolicy: JoinPolicy;
}
