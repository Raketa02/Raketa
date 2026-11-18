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

import type { FriendRelation } from '@/features/friends/types';
import type { ReliabilityBand } from '@/features/player_record/types';
import type { Sport } from '@/shared/vocabulary/sport';

import type { GroupKind, GroupRelation, HeatTag, JoinPolicy, ReadAs } from './vocabulary';

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
  /** An official group's card draws the official mark beside its name, as its page does. */
  readonly kind: GroupKind;
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
   * Who answers a request — the Owner's **whole nickname**, never cut and never with an @
   * (ADR-0199 §1). `null` for an account that can no longer be named, and always on an official
   * group, which has no Owner.
   */
  readonly ownerName: string | null;
  /**
   * **An official group's** answerer — the Administrator running it now, by their nickname, and by
   * the name their club typed until they have one (ADR-0199 §4): an Administrator who has never
   * played has no nickname, and the line must still say who runs it. Cut by nobody. `null` while it
   * **needs an administrator** (ADR-0183 §3), and always on a player group.
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
 * **A member's face** — a nickname and a photograph, and nothing else. `name` is what the member
 * is called — their whole nickname (ADR-0199 §1) — and `null` for an account that can no longer
 * be named: the member keeps their seat. `photoUrl` is
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
   * **Who runs an official group now** — its Administrator by their whole nickname, the one their
   * admin-tagged Members row says, or by the name their club typed until they have one
   * (ADR-0199 §4), cut by nobody. `null` while the group **needs an
   * administrator** (ADR-0183 §3), and always on a player group, whose Owner is one of its members.
   * Members names them apart from the list wherever the list does not (`runnerApart`).
   */
  readonly administratorName: string | null;
  /** Whether **the reader** runs this official group. Always `false` on a player group. */
  readonly isAdministrator: boolean;
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
   * **Info's members row** (#514): up to five faces of everybody **but the reader**, in
   * the Members list's order — the Owner, then newest joined first. A block hides nobody here
   * (ADR-0193 §2). Empty for a reader alone.
   */
  readonly memberFaces: readonly GroupPerson[];
}

/**
 * **One row of Members, for one sport** (play 61; #514) — *Padel 2,71* and a score tag. Only members
 * rated in the sport are listed, so `level` is always there; and so is `playerScore`, their Player
 * reliability in points — everyone starts at 100 (ADR-0195 §1, #660). The **admin** tag is drawn
 * on a player group's Owner and on an official group's Administrator who joined it as a player
 * (`adminTagged`).
 */
export interface GroupMember extends GroupPerson {
  readonly level: number;
  /** Player reliability, 0 to 100 — the figure on the tag. */
  readonly playerScore: number;
  /**
   * The band the server put that figure in — the tag's tint and its spoken word. **Absent only
   * where this build cannot name the served code**: the figure is then drawn untinted and said
   * alone, never banded by this phone.
   */
  readonly reliabilityBand?: ReliabilityBand;
  readonly isOwner: boolean;
  /** Whether they run this official group and joined it as a player. Always `false` on a player group. */
  readonly isAdministrator: boolean;
  /**
   * **Where the reader stands with them** (#753; ADR-0202 §1) — the pill or the tag on the row's
   * right: **+ Add**, *request sent*, **Accept**, *friend*. `NONE` on the reader's own row, which
   * draws neither, and the administrator's view draws none at all.
   */
  readonly relation: FriendRelation;
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

/**
 * **One card of Home's *Hottest groups*** ([#800](https://github.com/Raketa02/Raketa/issues/800);
 * ADR-0204 §3; the Home rows mechanics §5) — and **everything its group sheet shows**, so tapping the
 * card needs no second read. Drawn for any reader, **whether they are in the group or not**; the
 * group's page stays members-only.
 *
 * Every figure is the server's: the heat, its share, the tag, the order, which faces and how many
 * friends. The phone draws them.
 */
export interface HottestGroup {
  readonly id: string;
  readonly kind: GroupKind;
  readonly name: string;
  readonly monogram: Monogram;
  /** The sport dots, in the registry's order. */
  readonly sports: readonly Sport[];
  /** Every member, today — the card's *11 players*. */
  readonly memberCount: number;
  /** *Open group* (Anyone) or *Closed group* (People I approve) on the sheet. */
  readonly joinPolicy: JoinPolicy;
  /**
   * The sheet's *run by* — **an official group's club**, by its name, or **a player group's Owner**,
   * by their whole nickname. `null` only for an Owner who can no longer be named, and the sheet then
   * says nobody runs it rather than a name it does not have.
   */
  readonly runBy: string | null;
  /** The club it plays at. */
  readonly club: ClubName;
  /** Games with court time in the last 7 days, none called off — *14 games this week*. */
  readonly gamesThisWeek: number;
  /**
   * Members who joined in the last 30 days and stayed — the group sheet's green *+3*, above nought.
   * The card drew it as *+3 this month* until #821. The read's `heat_share` is left on the wire: the
   * heat bar it filled is drawn nowhere since #821.
   */
  readonly newThisMonth: number;
  readonly tag: HeatTag | null;
  /** Up to six members' faces — the sheet's six, the card's first four; never the reader's. */
  readonly faces: readonly GroupPerson[];
  /** The reader's friends in it now — *7 of your friends play here*. */
  readonly friendsCount: number;
  readonly relation: GroupRelation;
  /** Whether the reader runs this official group — their chip is *Join*, whatever the policy. */
  readonly isAdministrator: boolean;
}

/**
 * **Home's Hottest groups, as read** — the six cards, and **how many groups there are to look
 * through** ([#822](https://github.com/Raketa02/Raketa/issues/822); ADR-0205 §6): every group with 3
 * or more players, the reader's own included, counted up to 100 — the line's count. The server's
 * figure, refreshed only by the next read.
 */
export interface HottestRow {
  readonly groups: readonly HottestGroup[];
  readonly total: number;
}

/** A group's name is 1–40 characters once trimmed (ADR-0183 §3). The field stops at 40. */
export const GROUP_NAME_MAX = 40;

/** **A Player group to create** — the New group form, checked (`schemas/newGroupForm`). */
export interface NewGroup {
  readonly name: string;
  readonly homeClubId: string;
  readonly joinPolicy: JoinPolicy;
}
