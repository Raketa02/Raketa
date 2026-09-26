/**
 * **An Official group, as the Administrator who runs it reads it** — the club's crowd from one
 * WhatsApp group, brought into the app
 * ([ADR-0183](../../../../../docs/adr/0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md),
 * [ADR-0184](../../../../../docs/adr/0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md),
 * the root glossary's **Groups** and **Administrators**).
 *
 * Three shapes, one per place the administrator area draws a group: a card on its Groups tab, the
 * group as its page reads it, and its settings — to create it, and to change it later. The tile, the dots and the request card are
 * the `groups` feature's own — an official group is a Group — and the shapes here add what only an
 * Administrator sees: *N waiting* on the card, the **WhatsApp group size**, the declared sports and
 * every player with the day they joined.
 *
 * **Nothing here is computed on the phone** but *this week*, the share of the WhatsApp group and
 * whether the settings changed, all in `officialGroupRules.ts`: the monogram, the dots, the counts and the order are the
 * server's.
 */

import type { GroupPerson, JoinPolicy, JoinRequest, Monogram } from '@/features/groups/types';
import type { Sport } from '@/shared/vocabulary/sport';

/**
 * **The club an Administrator runs groups for** — its name, and the sports it offers, which are
 * exactly the sports an official group may declare. An official group's Home club is this club,
 * fixed.
 */
export interface OfficialGroupsClub {
  readonly id: string;
  readonly name: string;
  readonly sports: readonly Sport[];
}

/**
 * **An official group this Administrator runs, as the Groups tab lists it** (club 17): the tile,
 * the name, *N waiting*, dots, *N members*, the club.
 */
export interface AdministeredGroup {
  readonly id: string;
  readonly name: string;
  readonly monogram: Monogram;
  /** The sports it declares, in the registry's order. */
  readonly sports: readonly Sport[];
  /** Every Group member — an Administrator who joined as a player included. */
  readonly memberCount: number;
  /** Join requests waiting on it — the amber *N waiting*; `0` draws nothing. */
  readonly waitingCount: number;
  readonly homeClub: { readonly id: string; readonly name: string };
}

/**
 * **The Groups tab's read** — the club, and the official groups this Administrator runs there,
 * **newest created first**, never a colleague's.
 */
export interface AdministeredGroups {
  readonly club: OfficialGroupsClub;
  readonly groups: readonly AdministeredGroup[];
}

/**
 * **A player of the group, with the day they joined** — this stay (club 18, 19). `name` is the
 * whole Name, `null` for an account that can no longer be named; `photoUrl` is signed for the one
 * answer it came on, absent where the poster stands in.
 */
export interface GroupPlayer {
  readonly playerId: string;
  readonly name: string | null;
  readonly photoUrl?: string;
  /** An instant. *this week* within seven days, the date after (`joinedWhen`). */
  readonly joinedAt: string;
}

/** **An official group, as its Administrator opens it** (club 11, 18, 19). */
export interface OfficialGroup {
  readonly id: string;
  readonly name: string;
  readonly monogram: Monogram;
  readonly sports: readonly Sport[];
  /** *N players* — the group's member count, which a block does not change. */
  readonly memberCount: number;
  readonly homeClub: OfficialGroupsClub;
  /** The Group link to post into the WhatsApp group. It never changes. */
  readonly link: string;
  readonly joinPolicy: JoinPolicy;
  readonly whatsAppSize: number;
  /** Every player, **newest joined first**; a blocked pair is left out, and the count is not. */
  readonly players: readonly GroupPlayer[];
  /** *Want to join · N*, in the order they asked — the request card everywhere (club 20). */
  readonly requests: readonly JoinRequest[];
}

/** **The WhatsApp group size's bounds** — a whole number from 2 to 1024 (ADR-0183 §3). */
export const WHATSAPP_SIZE = { min: 2, max: 1024 } as const;

/**
 * **An Official group to create** — the New official group form, checked
 * (`schemas/officialGroupForm`). Its Home club is the club in the route, so it is not here.
 */
export interface OfficialGroupSettings {
  readonly name: string;
  readonly joinPolicy: JoinPolicy;
  readonly whatsAppSize: number;
  /** At least one, and only the club's, in the registry's order. */
  readonly sports: readonly Sport[];
}

/**
 * **What a settings save answers** — the group as its settings left it, and who the save let in:
 * everybody waiting, in the order they asked, when it switched to *Anyone*; nobody otherwise.
 */
export interface SavedSettings {
  readonly group: OfficialGroup;
  readonly admitted: readonly GroupPerson[];
}
