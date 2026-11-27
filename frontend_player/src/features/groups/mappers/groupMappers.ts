/**
 * **The wire boundary** — the group and club shapes the contract serves, in the app's spelling.
 * Generated types stop here and in `api/`.
 *
 * **A sport this build cannot name is dropped**, from a dot row and from a club's sports alike:
 * a dot with no sport behind it is a colour claiming something, and `toSport` is the one place
 * that decides what this build can name (`onboarding`'s mapper, as `player_record` uses it).
 * Everything else is carried as it came — the monogram's letters are never re-cased (ADR-0183 §5)
 * and the distance is the server's shown kilometres or `null`.
 */

import type { components } from '@/generated/schema';
import { toSport } from '@/features/onboarding/types';
import { toReliabilityBand } from '@/features/player_record/types';
import type { Sport } from '@/shared/vocabulary/sport';

import type {
  SearchedClub,
  ClubName,
  ClubSearch,
  EditedGroup,
  Group,
  GroupAtClub,
  GroupMember,
  GroupPerson,
  HottestGroup,
  HottestPage,
  HottestRow,
  JoinRequest,
  Monogram,
  MyGroup,
  SportLevel,
  SportRoster,
} from '../domain/group';

type Schemas = components['schemas'];

function toSports(wire: readonly Schemas['Sport'][]): readonly Sport[] {
  return wire.map(toSport).filter((sport): sport is Sport => sport !== undefined);
}

function toMonogram(wire: Schemas['MonogramSchema']): Monogram {
  return { letters: wire.letters, colourKey: wire.colour };
}

function toClubName(wire: Schemas['ClubNameSchema']): ClubName {
  return { id: wire.id, name: wire.name };
}

export function toMyGroup(wire: Schemas['MyGroupSchema']): MyGroup {
  return {
    id: wire.id,
    kind: wire.kind,
    name: wire.name,
    monogram: toMonogram(wire.monogram),
    sports: toSports(wire.sports),
    memberCount: wire.member_count,
    homeClub: toClubName(wire.home_club),
  };
}

export function toMyGroups(wire: Schemas['MyGroupsResponse']): readonly MyGroup[] {
  return wire.groups.map(toMyGroup);
}

export function toGroupAtClub(wire: Schemas['GroupAtClubSchema']): GroupAtClub {
  return {
    id: wire.id,
    kind: wire.kind,
    name: wire.name,
    monogram: toMonogram(wire.monogram),
    sports: toSports(wire.sports),
    memberCount: wire.member_count,
    joinPolicy: wire.join_policy,
    ownerName: wire.owner_nickname,
    administratorName: wire.administrator_nickname,
    isAdministrator: wire.is_administrator,
    relation: wire.relation,
  };
}

export function toClubCard(wire: Schemas['ClubCardSchema']): SearchedClub {
  return {
    id: wire.id,
    name: wire.name,
    district: wire.district,
    distanceKm: wire.distance_km,
    sports: toSports(wire.sports),
    groups: wire.groups.map(toGroupAtClub),
  };
}

/** Home-club search reads everything as text: it has no link to recognise. */
export function toHomeClubSearch(text: string, wire: Schemas['HomeClubPageResponse']): ClubSearch {
  return {
    text,
    clubs: wire.clubs.map(toClubCard),
    nextPage: wire.next_page,
    readAs: 'TEXT',
  };
}

export function toJoinSearch(text: string, wire: Schemas['JoinSearchResponse']): ClubSearch {
  return {
    text,
    clubs: wire.clubs.map(toClubCard),
    nextPage: wire.next_page,
    readAs: wire.read_as,
  };
}

/** A face: the photograph's link travels only when there is one — the poster stands in otherwise. */
function toGroupPerson(wire: Schemas['GroupPersonSchema']): GroupPerson {
  return { playerId: wire.player_id, name: wire.nickname, ...photoOf(wire) };
}

/** A photograph's link, where the wire carried one. */
function photoOf(wire: { readonly photo_url?: string }): { readonly photoUrl?: string } {
  return wire.photo_url === undefined ? {} : { photoUrl: wire.photo_url };
}

/** Every sport's roster this build can name — a count with no sport behind it claims nothing. */
function toRosters(wire: readonly Schemas['GroupSportSchema'][]): readonly SportRoster[] {
  return wire.flatMap((roster) => {
    const sport = toSport(roster.sport);
    if (sport === undefined) return [];
    return [
      {
        sport,
        ratedCount: roster.rated_count,
        firstRated: roster.first_rated.map(toGroupPerson),
      },
    ];
  });
}

/**
 * **What an official group plays**, where the build can name it. Only an official group declares
 * its sports; a player group carries nothing here. **A declared list this build can name none of
 * is carried as none at all** — an older build after a sport is added — so the page reads the
 * group as it reads a player group, rather than narrowing its filter to nothing with nothing it
 * could name for the reader to add.
 */
function declaredSportsOf(wire: Schemas['GroupResponse']): Pick<Group, 'declaredSports'> {
  const declared = toSports(wire.declared_sports ?? []);
  return declared.length === 0 ? {} : { declaredSports: declared };
}

export function toGroup(wire: Schemas['GroupResponse']): Group {
  return {
    id: wire.id,
    kind: wire.kind,
    name: wire.name,
    monogram: toMonogram(wire.monogram),
    sports: toSports(wire.sports),
    memberCount: wire.member_count,
    homeClub: toClubName(wire.home_club),
    link: wire.link,
    joinPolicy: wire.join_policy,
    isOwner: wire.is_owner,
    administratorName: wire.administrator_nickname,
    isAdministrator: wire.is_administrator,
    ...declaredSportsOf(wire),
    ratedBySport: toRosters(wire.rated_by_sport),
    memberFaces: wire.member_faces.map(toGroupPerson),
  };
}

/**
 * **Members, for one sport** — in the order served: the reader, the Owner, then newest joined
 * first. Every row carries its points and band since #659 (ADR-0195 §1); the band is narrowed by
 * `player_record`'s own reading of the code, so the list and the record it opens cannot read one
 * band two ways, and a band this build cannot name is dropped rather than guessed.
 */
export function toGroupMembers(wire: Schemas['GroupMembersResponse']): readonly GroupMember[] {
  return wire.members.map((member) => {
    const band = toReliabilityBand(member.reliability_band);
    return {
      playerId: member.player_id,
      name: member.nickname,
      ...photoOf(member),
      level: member.level,
      playerScore: member.player_score,
      ...(band === undefined ? {} : { reliabilityBand: band }),
      isOwner: member.is_owner,
      isAdministrator: member.is_administrator,
      // Spelled as the wire spells it — `friends`' vocabulary holds the two equal.
      relation: member.relation,
    };
  });
}

/** Every Level this build can name — a figure with no sport behind it claims nothing. */
function toLevels(wire: readonly Schemas['SportLevelSchema'][]): readonly SportLevel[] {
  return wire.flatMap((row) => {
    const sport = toSport(row.sport);
    return sport === undefined ? [] : [{ sport, level: row.level }];
  });
}

/** *Want to join · N* — everybody waiting, in the order they asked. */
export function toJoinRequests(wire: Schemas['JoinRequestsResponse']): readonly JoinRequest[] {
  return wire.requests.map((request) => ({
    playerId: request.player_id,
    name: request.nickname,
    ...photoOf(request),
    levels: toLevels(request.levels),
  }));
}

export function toEditedGroup(wire: Schemas['EditedGroupResponse']): EditedGroup {
  return { group: toGroup(wire.group), admitted: wire.admitted.map(toGroupPerson) };
}

/**
 * **Home's Hottest groups** (#800), in the row's order — the server's. Everything the card and its
 * sheet draw rides on the one read, so nothing here is worked out: the share, the tag and the six
 * faces are carried as they came. **The total is the server's too** (#822): every group of 3 or more,
 * up to 100, which the line draws as its count.
 */
export function toHottestRow(wire: Schemas['HottestGroupsResponse']): HottestRow {
  return { groups: wire.groups.map(toHottestGroup), total: wire.total };
}

/**
 * **A page of *Groups heating up*** (#823) — the row's cards, read whole for the page's 20, and the
 * cursor behind them; none on the last page. The first page's `total` is the line's count, already on
 * the row's read, and the page draws no count, so it is left on the wire.
 */
export function toHottestPage(wire: Schemas['HottestGroupsPageResponse']): HottestPage {
  const groups = wire.groups.map(toHottestGroup);
  return wire.next === null ? { groups } : { groups, next: wire.next };
}

function toHottestGroup(group: Schemas['HottestGroupSchema']): HottestGroup {
  return {
    id: group.id,
    kind: group.kind,
    name: group.name,
    monogram: toMonogram(group.monogram),
    sports: toSports(group.sports),
    memberCount: group.member_count,
    joinPolicy: group.join_policy,
    runBy: group.run_by,
    club: toClubName(group.club),
    gamesThisWeek: group.games_this_week,
    newThisMonth: group.new_this_month,
    tag: group.tag,
    faces: group.faces.map(toGroupPerson),
    friendsCount: group.friends_count,
    relation: group.relation,
    isAdministrator: group.is_administrator,
  };
}
