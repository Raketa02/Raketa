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

/**
 * The group page's four tabs, each drawn for a sport (Q125: Info is the group's own screen, opened
 * from the header): **Games · Fill in · You’re in · Friends** — the rescues and the reader's own live
 * yeses a tab each since #847 (PRD #844, split mock 3), where Fill in had stacked both. It always
 * opens on Games (ADR-0188 §5: which tab is not kept). A route naming a tab not in this list is
 * dropped, and the page opens as it always does (`groupRouteParams`).
 */
export const GROUP_TABS = ['games', 'fillIn', 'youreIn', 'friends'] as const;

export type GroupTab = (typeof GROUP_TABS)[number];

export const OPENING_TAB: GroupTab = 'games';

/** The Friends tab's switch — held in memory while the app is open, never on the phone (§5). */
export type GameIntent = 'competitive' | 'forFun';

/** The two, in the switch's order — what a route param naming one is checked against. */
export const GAME_INTENTS = ['competitive', 'forFun'] as const satisfies readonly GameIntent[];

/**
 * **The filter's sports** — only the ones the reader is rated in, in the registry's order
 * (padel › tennis › squash › badminton). A player group's dots are not the list: a player rated in
 * a sport nobody else here plays can still open it, and a dot they are not rated in is a sport they
 * cannot play.
 *
 * **An official group plays what it declares** (story 56, #519), so `declared` — its declared sports —
 * narrows the list to the rated ones among them. `undefined` for a player group, which plays
 * whatever its members are rated in.
 */
export function filterSports(
  rated: readonly Sport[],
  declared?: readonly Sport[],
): readonly Sport[] {
  return SPORTS.filter(
    (sport) => rated.includes(sport) && (declared === undefined || declared.includes(sport)),
  );
}

/**
 * **The sport the page opens on** — the one last picked anywhere in Play, while it is still on the
 * filter; otherwise the filter's first sport in the registry's order (ADR-0188 §2). A saved value
 * that is no longer a rated sport — or a sport this official group does not play, or never was a
 * sport — is the default, never an error (§4). `undefined` only for a reader the filter lists
 * nothing for, who has no sport to open.
 *
 * **A notice opens the page in its card's sport** (#559; the screens A9), `wanted`, ahead of the one
 * picked last — while the filter lists it. Opening is not picking: the saved value is untouched.
 */
export function openingSport(
  rated: readonly Sport[],
  saved: string | undefined,
  declared?: readonly Sport[],
  wanted?: Sport,
): Sport | undefined {
  const sports = filterSports(rated, declared);
  return (
    sports.find((sport) => sport === wanted) ?? sports.find((sport) => sport === saved) ?? sports[0]
  );
}

/**
 * **The sport the deck last showed** (#775) — a player group's filter opening on the sport last
 * picked while the reader is still rated in it, else the first they are rated in (`openingSport`):
 * what Rankings and Home's Top 10 open on when the trophy names no sport. `null` for a reader rated in
 * nothing, whose deck shows no sport; `undefined` while either read is out — the ratings, or the
 * phone's saved sport, where `null` is a phone that answered *nothing saved*. The hook's answer and
 * the launch's off the cache (#874) are this one.
 */
export function deckSport(
  rated: readonly Sport[] | undefined,
  saved: string | null | undefined,
): Sport | null | undefined {
  if (rated === undefined || saved === undefined) return undefined;
  return openingSport(rated, saved ?? undefined) ?? null;
}

/**
 * **The sports a reader must add to see an official group's games** (story 57, #519) — every sport
 * it plays, in the registry's order, for a reader rated in none of them; nothing once they are
 * rated in one, and nothing for a player group, which plays whatever its members are rated in.
 */
export function sportsToAdd(
  rated: readonly Sport[],
  declared?: readonly Sport[],
): readonly Sport[] {
  if (declared === undefined || filterSports(rated, declared).length > 0) return [];
  return SPORTS.filter((sport) => declared.includes(sport));
}

/**
 * **Whether the reader meets the door where play begins** — *Get your level*, in place of a player
 * group's Games, Fill in and Friends, its *Post a game* and its Members
 * ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §2,
 * [#730](https://github.com/Raketa02/Raketa/issues/730)). A player group plays whatever its members
 * are rated in, so a reader rated in nothing has no sport for any of them. **Never an official
 * group's reader**: it plays what it declares, and offers those sports on its own card
 * (`sportsToAdd`, §3).
 */
export function needsALevel(rated: readonly Sport[], declared?: readonly Sport[]): boolean {
  return declared === undefined && filterSports(rated).length === 0;
}

/**
 * **What *+ Another sport* offers** — the sports the reader is unrated in, in the registry's order,
 * that the picker it opens lists ([ADR-0200](../../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md)
 * §4, [#731](https://github.com/Raketa02/Raketa/issues/731)). A player group plays whatever its
 * members are rated in, so it offers every one of them; **an official group plays what it declares**,
 * so it offers only its own sports she is missing — never a sport the group does not play.
 *
 * **Nothing while the chip is not drawn**: it ends the chip, and the chip appears only once there is
 * a rating to list. A reader rated in nothing here meets the door, or the official group's own card
 * (`needsALevel`, `sportsToAdd`), which asks the same question. And nothing once she is rated in
 * everything there is to offer, so she is never offered nothing.
 */
export function sportsToOffer(
  rated: readonly Sport[],
  declared?: readonly Sport[],
): readonly Sport[] {
  if (filterSports(rated, declared).length === 0) return [];
  return SPORTS.filter(
    (sport) => !rated.includes(sport) && (declared === undefined || declared.includes(sport)),
  );
}

/**
 * **Whether Home asks for a level** — *Get your level — your groups can't deal you games until you
 * have one.* (ADR-0200 §7, #731): a member of at least one group, player or official, who holds no
 * rating in any sport. For a player who never opens a group, it says why nothing is happening.
 * **Nobody in no group**: a level unlocks nothing there yet, and joining one is what Play is for.
 *
 * **Whether or not a friend asked her for a level** (#816, ADR-0205 §4, Q13). The ask waits in
 * Needs your answer, behind the envelope, and is never drawn in this card's place: #765's hand-off,
 * which left the card out while ASKED FOR A LEVEL was on Home, went with that row.
 */
export function homeAsksForALevel(groups: number, rated: readonly Sport[]): boolean {
  return groups > 0 && rated.length === 0;
}

/**
 * **Whether the reads Home's level card answers from have finished** (#871) — what Home's reveal
 * waits on for the card: **the ratings first, and your groups only for a reader rated in nothing**,
 * since a rated reader is asked nothing by it (`useHomeAsksForALevel`). `ratedInNothing` is
 * `undefined` while the ratings hold nothing — refused, held, retrying — and then the card is not
 * drawn, so it waits on nothing more.
 */
export function levelCardReadsFinished({
  ratingsFinished,
  ratedInNothing,
  groupsFinished,
}: {
  readonly ratingsFinished: boolean;
  readonly ratedInNothing: boolean | undefined;
  readonly groupsFinished: boolean;
}): boolean {
  return ratingsFinished && (ratedInNothing !== true || groupsFinished);
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
