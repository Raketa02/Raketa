/**
 * The one route in this feature that carries a param, validated before anything reads it.
 *
 * A route param is attacker-controlled and expo-router hands it over as
 * `string | string[] | undefined` whatever the route declared, so it is checked first — the same
 * rule `features/games/schemas/routeParams.ts` and `features/play/schemas/routeParams.ts` state,
 * and worth as much here: this string becomes the path of a read that serves another person's
 * photograph and level, and then the path of a `POST` that accepts a game on somebody's behalf.
 *
 * A link that does not survive this has no challenge behind it, which is the same answer as a
 * link to a challenge that is not yours. The two are deliberately not told apart, because the
 * server refuses to tell them apart for a reason: separating *it does not exist* from *you are
 * not on its court* would answer *is this id real* about a stranger's evening.
 */

import { z } from 'zod';

export const challengeRouteParams = z.object({
  /** The challenge this screen is about. Read from `GET /challenges/{id}`, which serves only yours. */
  challengeId: z.string().uuid(),
});

export type ChallengeRouteParams = z.infer<typeof challengeRouteParams>;

/** `undefined` when the link cannot be trusted. The screen decides what that looks like. */
export function parseChallengeRouteParams(
  params: Record<string, string | string[] | undefined>,
): ChallengeRouteParams | undefined {
  const result = challengeRouteParams.safeParse(params);
  return result.success ? result.data : undefined;
}

/**
 * **The builder, under a challenge** — `features/play`'s own screen at a second route.
 *
 * One screen component and two routes, which is ADR-0149 §9's shape reused: each route lights
 * its own column, and *back* is correct in both directions **by construction** rather than
 * through a `from` parameter that would make `tabForPathname` impure
 * ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §0.2). Being
 * under `/chats` is what lights the Chats column, for free.
 *
 * Spelled beside the route's own check because a `/chats/…` path is this feature's to own —
 * `features/play` holds the paths under `/play/…` for the same reason, one tab over — and here
 * rather than on the challenge screen since [#419](https://github.com/Raketa02/Raketa/issues/419):
 * the game screen and the Now card push it too, through `FillTheSeat`.
 */
export const fillRoute = (challengeId: string) => `/chats/challenge/${challengeId}/fill` as const;

/**
 * **The yes screen, under the challenge it is about** — `…/yes?which=challenge`
 * ([ADR-0166](../../../../../docs/adr/0166-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
 * §1, [#433](https://github.com/Raketa02/Raketa/issues/433)).
 *
 * Keyed by the challenge id — both entries end in a challenge, so the screen reads everything
 * it draws from the one the cache holds — with one parameter saying **which yes** it is, which
 * decides the word, the picture and where *Later* lands. A route param is not app state, so
 * the parameter is a closed union and a value outside it is a link this app cannot read: the
 * route leaves rather than drawing a screen about nothing.
 *
 * `challenge` is the one member today. `mutual` — the deck's *Let's play* come back mutual and
 * naming a chat — is [#434](https://github.com/Raketa02/Raketa/issues/434)'s, and widening the
 * union is where that ticket starts.
 */
export const WHICH_YES = ['challenge'] as const;

export type WhichYes = (typeof WHICH_YES)[number];

export const yesRouteParams = challengeRouteParams.extend({
  which: z.enum(WHICH_YES),
});

export type YesRouteParams = z.infer<typeof yesRouteParams>;

/** `undefined` when the link cannot be trusted. The route decides what that looks like. */
export function parseYesRouteParams(
  params: Record<string, string | string[] | undefined>,
): YesRouteParams | undefined {
  const result = yesRouteParams.safeParse(params);
  return result.success ? result.data : undefined;
}

/** Where a yes lands, spelled once for the one surface that pushes it today and the second to come. */
export const yesRoute = (challengeId: string, which: WhichYes) =>
  ({ pathname: `/chats/challenge/${challengeId}/yes`, params: { which } }) as const;

/**
 * **The Chats list** — where the yes screen's *Later* lands, and what the room is opened over.
 *
 * The shell's `SHELL_TAB_ROOT.chats`, spelled here for the same reason `fillRoute` is: every
 * `/chats/challenge/…` path is this feature's, and a pop to their parent is this feature's move
 * — a `dismissTo` down the stack rather than the shell's reset, which lays a stack down and
 * ends a Play session on the way. The two route files under it already redirect a bad link
 * here by the same literal.
 */
export const CHATS_LIST_ROUTE = '/chats' as const;
