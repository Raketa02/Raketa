/**
 * **The group page's rules** — which sports its fast filter lists, which one it opens on, and
 * what the Games tab's card says for the sport chosen
 * ([#513](https://github.com/Raketa02/Raketa/issues/513), PRD #500 stories 51–63,
 * [ADR-0183](../../../../../docs/adr/0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md)
 * §13, [ADR-0188](../../../../../docs/adr/0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)
 * §2, §4).
 *
 * Pure: the ratings, the saved value and the roster are read elsewhere, and how many people stand
 * on a court is **handed in** — it is drawn knowledge (`courtSeatCount`, `shared/ui`), the room's
 * own rule, and a second table of seats here would be a second answer to it.
 */

import { SPORTS, type Sport } from '@/shared/vocabulary/sport';

import type { Group, GroupPerson, SportRoster } from './group';

/** The group page's four tabs. It always opens on Games (ADR-0188 §5: which tab is not kept). */
export const GROUP_TABS = ['games', 'fillIn', 'friends', 'info'] as const;

export type GroupTab = (typeof GROUP_TABS)[number];

export const OPENING_TAB: GroupTab = 'games';

/** The Friends tab's switch — held in memory while the app is open, never on the phone (§5). */
export type GameIntent = 'competitive' | 'forFun';

/**
 * **The filter's sports** — only the ones the reader is rated in, in the registry's order
 * (padel › tennis › squash › badminton). A group's dots are not the list: a player rated in a
 * sport nobody else here plays can still open it, and a dot they are not rated in is a sport they
 * cannot play.
 */
export function filterSports(rated: readonly Sport[]): readonly Sport[] {
  return SPORTS.filter((sport) => rated.includes(sport));
}

/**
 * **The sport the page opens on** — the one last picked anywhere in Play, while the reader is
 * still rated in it; otherwise the first rated sport in the registry's order (ADR-0188 §2). A
 * saved value that is no longer a rated sport — or never was a sport — is the default, never an
 * error (§4). `undefined` only for a reader rated in nothing, who has no sport to open.
 */
export function openingSport(
  rated: readonly Sport[],
  saved: string | undefined,
): Sport | undefined {
  const sports = filterSports(rated);
  return sports.find((sport) => sport === saved) ?? sports[0];
}

/** **One sport's roster** — `undefined` for a sport the group's read did not carry. */
export function rosterFor(
  group: Pick<Group, 'ratedBySport'>,
  sport: Sport,
): SportRoster | undefined {
  return group.ratedBySport.find((roster) => roster.sport === sport);
}

/**
 * **Somebody's face among a sport's first rated** — `undefined` for anybody who joined after the
 * group already had a court's worth rated in it, since the roster carries no more than that.
 */
export function faceIn(
  roster: SportRoster | undefined,
  playerId: string | undefined,
): GroupPerson | undefined {
  return roster?.firstRated.find((person) => person.playerId === playerId);
}

/**
 * **What the Games tab's dark card says** (stories 60–63) — for the sport chosen, from how many
 * members are rated in it against how many the court seats:
 *
 * | | |
 * | --- | --- |
 * | `just-you` | nobody but the reader rated in it yet — *Just you so far* |
 * | `filling` | others are in, not yet enough for a court — *3 of 4* |
 * | `nothing-picked` | the seats could be filled — *Nothing picked right now*, the honest line while a group cannot pick games (ADR-0183 §13) |
 *
 * `faces` are the first to join who are rated in it, **never more than the court seats**; the
 * rest of the seats are drawn empty.
 */
export interface GamesCard {
  readonly kind: 'just-you' | 'filling' | 'nothing-picked';
  readonly rated: number;
  readonly seats: number;
  readonly faces: readonly GroupPerson[];
}

export function gamesCard(roster: SportRoster | undefined, seats: number): GamesCard {
  const rated = roster?.ratedCount ?? 0;
  const faces = (roster?.firstRated ?? []).slice(0, seats);
  const kind = rated >= seats ? 'nothing-picked' : rated > 1 ? 'filling' : 'just-you';
  return { kind, rated, seats, faces };
}
