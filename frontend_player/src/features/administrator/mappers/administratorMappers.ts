/**
 * **The wire boundary** — the administrator's official-group shapes, in the app's spelling.
 * Generated types stop here and in `api/`.
 *
 * `groups`' mapper's rules, applied to the shapes only an Administrator reads: **a sport this build
 * cannot name is dropped** — from the dots, from the club's sports and from a request's Levels —
 * because a dot or a Level with no sport behind it claims something (`toSport` decides what this
 * build can name); the monogram's letters are carried as typed and never re-cased (ADR-0183 §5);
 * and a photograph's link travels only where there is one.
 */

import type { components } from '@/generated/schema';
import { toSport, toWireSport } from '@/features/onboarding/types';
import type { JoinRequest, Monogram, SportLevel } from '@/features/groups/types';
import type { Sport } from '@/shared/vocabulary/sport';

import type {
  OfficialGroupsClub,
  AdministeredGroups,
  GroupPlayer,
  NewOfficialGroup,
  OfficialGroup,
  AdministeredGroup,
} from '../domain/officialGroup';

type Schemas = components['schemas'];

function toSports(wire: readonly Schemas['Sport'][]): readonly Sport[] {
  return wire.map(toSport).filter((sport): sport is Sport => sport !== undefined);
}

function toMonogram(wire: Schemas['MonogramSchema']): Monogram {
  return { letters: wire.letters, colourKey: wire.colour };
}

function photoOf(wire: { readonly photo_url?: string }): { readonly photoUrl?: string } {
  return wire.photo_url === undefined ? {} : { photoUrl: wire.photo_url };
}

function toClub(wire: Schemas['OfficialGroupClubSchema']): OfficialGroupsClub {
  return { id: wire.id, name: wire.name, sports: toSports(wire.sports) };
}

function toCard(wire: Schemas['AdministeredGroupCardSchema']): AdministeredGroup {
  return {
    id: wire.id,
    name: wire.name,
    monogram: toMonogram(wire.monogram),
    sports: toSports(wire.sports),
    memberCount: wire.member_count,
    waitingCount: wire.waiting_count,
    homeClub: { id: wire.home_club.id, name: wire.home_club.name },
  };
}

export function toAdministeredGroups(
  wire: Schemas['AdministeredGroupsResponse'],
): AdministeredGroups {
  return { club: toClub(wire.club), groups: wire.groups.map(toCard) };
}

function toLevels(wire: readonly Schemas['SportLevelSchema'][]): readonly SportLevel[] {
  return wire.flatMap((row) => {
    const sport = toSport(row.sport);
    return sport === undefined ? [] : [{ sport, level: row.level }];
  });
}

function toRequest(wire: Schemas['JoinRequestSchema']): JoinRequest {
  return {
    playerId: wire.player_id,
    name: wire.name,
    ...photoOf(wire),
    levels: toLevels(wire.levels),
  };
}

function toPlayer(wire: Schemas['GroupPlayerSchema']): GroupPlayer {
  return { playerId: wire.player_id, name: wire.name, ...photoOf(wire), joinedAt: wire.joined_at };
}

export function toOfficialGroup(wire: Schemas['AdministeredGroupResponse']): OfficialGroup {
  return {
    id: wire.id,
    name: wire.name,
    monogram: toMonogram(wire.monogram),
    sports: toSports(wire.sports),
    memberCount: wire.member_count,
    homeClub: toClub(wire.home_club),
    link: wire.link,
    joinPolicy: wire.join_policy,
    whatsAppSize: wire.whatsapp_size,
    players: wire.players.map(toPlayer),
    requests: wire.requests.map(toRequest),
  };
}

export function toCreateRequest(group: NewOfficialGroup): Schemas['CreateOfficialGroupRequest'] {
  return {
    name: group.name,
    join_policy: group.joinPolicy,
    whatsapp_size: group.whatsAppSize,
    sports: group.sports.map(toWireSport),
  };
}
