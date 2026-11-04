/**
 * **The club's official groups, wire to view.** The only file in this feature that imports a
 * generated type (ADR-0187 §6); everything else reads the {@link GroupRow} it makes.
 */

import type { Sport } from '@/features/club-details/mappers';
import type { components } from '@/generated/schema';

type WireGroup = components['schemas']['ClubGroupSchema'];
type WireGroups = components['schemas']['ClubGroupsResponse'];
type WireAdministrators = components['schemas']['AdministratorListResponse'];
type WireJoinRequests = components['schemas']['ClubJoinRequestsResponse'];

/** Who runs a group: the name the club gave them, as its Administrators table prints it. */
export interface GroupAdministrator {
  readonly id: string;
  readonly name: string;
}

/** One row of the Groups table (club mocks 15–16). */
export interface GroupRow {
  readonly id: string;
  readonly name: string;
  /** `null` while it needs an administrator: the club removed whoever ran it (ADR-0183 §8). */
  readonly administrator: GroupAdministrator | null;
  /** Every Group member, an Administrator who joined it as a player included. */
  readonly players: number;
  /** Join requests waiting for an answer. */
  readonly waiting: number;
  /**
   * *From original group*: the players, of the size of the group it mirrors (a WhatsApp group,
   * say; the wire still calls it that). The percent is the backend's,
   * rounded half up and never capped (*52 of 48 · 108%*), and is never worked out again here.
   */
  readonly whatsApp: { readonly size: number; readonly percent: number };
  /** Games booked in the group: every game its deck filled into a booking at a court. */
  readonly games: number;
}

export function toGroupRow(wire: WireGroup): GroupRow {
  return {
    id: wire.id,
    name: wire.name,
    administrator:
      wire.administrator === null
        ? null
        : { id: wire.administrator.id, name: wire.administrator.name },
    players: wire.member_count,
    waiting: wire.waiting_count,
    whatsApp: { size: wire.whatsapp_size, percent: wire.whatsapp_percent },
    games: wire.games,
  };
}

/** Somebody a group can be handed to: an active Administrator of the club. */
export interface Choice {
  readonly id: string;
  readonly name: string;
  readonly email: string;
}

/** **The Hand over page**: the group, and whom the club can give it to. */
export interface HandOverView {
  readonly group: GroupRow;
  /**
   * The club's **active** administrators, by name, but for whoever runs the group already:
   * handing it to them would change nothing. Somebody invited or expired can't take a group
   * (ADR-0183 §8).
   */
  readonly choices: readonly Choice[];
}

/** The Hand over page for one group, or `null` when it is none of the club's official groups. */
export function toHandOver(
  groupId: string,
  groups: WireGroups,
  administrators: WireAdministrators,
): HandOverView | null {
  const wire = groups.groups.find((group) => group.id === groupId);
  if (wire === undefined) return null;
  const group = toGroupRow(wire);
  return {
    group,
    choices: administrators.administrators
      .filter((each) => each.status === 'ACTIVE' && each.id !== group.administrator?.id)
      .map((each) => ({ id: each.id, name: each.name, email: each.email })),
  };
}

/** One sport somebody is rated in, and their Level in it. */
export interface SportLevel {
  readonly sport: Sport;
  readonly level: number;
}

/** **Somebody asking to join** one of the club's official groups (club mock 20, ADR-0191 §1). */
export interface JoinRequest {
  /** The player's id: whom the club approves or declines. */
  readonly id: string;
  /**
   * Their whole nickname (ADR-0199 §5), or `null` for an account that can no longer be named.
   */
  readonly nickname: string | null;
  /** Every sport they are rated in, in the registry's order, each with its Level. */
  readonly levels: readonly SportLevel[];
}

/** Everybody waiting on a group, in the order they asked. */
export function toJoinRequests(wire: WireJoinRequests): readonly JoinRequest[] {
  return wire.requests.map((request) => ({
    id: request.player_id,
    nickname: request.nickname,
    levels: request.levels.map(({ sport, level }) => ({ sport, level })),
  }));
}

/**
 * **A group's page**: who runs it and whom it can be handed to, and everybody waiting to join,
 * whom the club answers whoever runs it (ADR-0191 §1).
 */
export interface GroupPageView extends HandOverView {
  readonly requests: readonly JoinRequest[];
}
