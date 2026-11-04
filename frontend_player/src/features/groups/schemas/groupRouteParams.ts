/**
 * **A group page's route params, checked before anything trusts them** — a route param is input
 * from outside the app (a link, a notification later), and an id that is not a UUID has no group
 * behind it.
 */

import { z } from 'zod';

import { SPORTS, type Sport } from '@/shared/vocabulary/sport';

import { GAME_INTENTS, GROUP_TABS, type GameIntent, type GroupTab } from '../domain/groupPage';

const GroupRouteParams = z.object({ groupId: z.string().uuid() });

/**
 * **A deck opened at a card** — what a notice's tap adds to the group's id (#559; the screens A9):
 * the sport and the kind the card was dealt in, and the card to put on top.
 */
const DeckArrivalParams = z.object({
  sport: z.enum(SPORTS),
  kind: z.enum(GAME_INTENTS),
  card: z.string().uuid(),
});

export interface DeckArrival {
  readonly sport: Sport;
  readonly kind: GameIntent;
  /** The card's id — the proposal it is. */
  readonly card: string;
}

/**
 * **A page a rating pass returns to** — what the app adds to the group's id when a pass begun on
 * the page ends (#729, ADR-0200 §5): the tab it began on, and the sport it rated last, which the
 * page stands on until the player picks another. No sport for a pass that rated nothing.
 */
const ReturningPassParams = z.object({
  tab: z.enum(GROUP_TABS),
  sport: z.enum(SPORTS).optional(),
});

export interface ReturningPass {
  readonly tab: GroupTab;
  readonly sport?: Sport;
}

export interface GroupRoute {
  readonly groupId: string;
  readonly arrival?: DeckArrival;
  readonly returning?: ReturningPass;
}

/**
 * The group id, the card a notice opened its deck at, and the tab a rating pass returns to — or
 * `undefined` for a group id this app cannot read. An arrival is all three of its params or none,
 * and a return its tab or nothing: one this build cannot read opens the page as the page always
 * opens, since the group id alone is a page to open.
 */
export function parseGroupRouteParams(params: unknown): GroupRoute | undefined {
  const parsed = GroupRouteParams.safeParse(params);
  if (!parsed.success) return undefined;
  const arrival = DeckArrivalParams.safeParse(params);
  const returning = ReturningPassParams.safeParse(params);
  return {
    ...parsed.data,
    ...(arrival.success ? { arrival: arrival.data } : {}),
    ...(returning.success ? { returning: returning.data } : {}),
  };
}

/**
 * **A group's tab, as the sports picker is opened from it** (#729, for the door #730 draws there):
 * the group and the tab a pass begun there returns to — or `undefined` for anything else, which is
 * the picker onboarding opens itself.
 */
const GroupPlaceParams = GroupRouteParams.extend({ tab: z.enum(GROUP_TABS) });

export function parseGroupPlace(
  params: unknown,
): { readonly groupId: string; readonly tab: GroupTab } | undefined {
  const parsed = GroupPlaceParams.safeParse(params);
  return parsed.success ? parsed.data : undefined;
}

/**
 * The Friends screen's: the group, and **the sport the court was drawn for** — the screen's
 * eyebrow counts that court's seats (play 54), so a sport this build cannot name is a screen with
 * nothing to count, and is refused like a group id that is not one.
 */
const FriendsRouteParams = GroupRouteParams.extend({ sport: z.enum(SPORTS) });

export function parseFriendsRouteParams(
  params: unknown,
): { readonly groupId: string; readonly sport: Sport } | undefined {
  const parsed = FriendsRouteParams.safeParse(params);
  return parsed.success ? parsed.data : undefined;
}

/**
 * **A group's code** — the eight letters and digits after `/join/` in its link. Read in lower case,
 * the case every code is minted in, so a link a keyboard capitalised names the same group; whether
 * the eight are any group's is the server's to say (ADR-0183 §4).
 */
export const GroupCodeSchema = z
  .string()
  .regex(/^[0-9A-Za-z]{8}$/)
  .transform((code) => code.toLowerCase());

const JoinRouteParams = z.object({ code: GroupCodeSchema });

/**
 * **Join a group opened by a group link** (#520): the code the link carried, or `undefined` —
 * Join a group opened from Play, or a code that cannot be one, either way an empty field.
 */
export function parseJoinRouteParams(params: unknown): { readonly code: string } | undefined {
  const parsed = JoinRouteParams.safeParse(params);
  return parsed.success ? parsed.data : undefined;
}
