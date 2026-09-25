/**
 * **The wire boundary** — the five group and club shapes the contract serves, in the app's
 * spelling. Generated types stop here and in `api/`.
 *
 * **A sport this build cannot name is dropped**, from a dot row and from a club's sports alike:
 * a dot with no sport behind it is a colour claiming something, and `toSport` is the one place
 * that decides what this build can name (`onboarding`'s mapper, as `player_record` uses it).
 * Everything else is carried as it came — the monogram's letters are never re-cased (ADR-0183 §5)
 * and the distance is the server's shown kilometres or `null`.
 */

import type { components } from '@/generated/schema';
import { toSport } from '@/features/onboarding/types';
import type { Sport } from '@/shared/vocabulary/sport';

import type {
  SearchedClub,
  ClubName,
  ClubSearch,
  Group,
  GroupAtClub,
  Monogram,
  MyGroup,
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
    name: wire.name,
    monogram: toMonogram(wire.monogram),
    sports: toSports(wire.sports),
    memberCount: wire.member_count,
    joinPolicy: wire.join_policy,
    ownerName: wire.owner_name,
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

export function toGroup(wire: Schemas['GroupResponse']): Group {
  return {
    id: wire.id,
    name: wire.name,
    monogram: toMonogram(wire.monogram),
    sports: toSports(wire.sports),
    memberCount: wire.member_count,
    homeClub: toClubName(wire.home_club),
    link: wire.link,
    joinPolicy: wire.join_policy,
    isOwner: wire.is_owner,
  };
}
