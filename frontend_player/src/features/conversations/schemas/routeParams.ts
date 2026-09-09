/**
 * The two routes in this feature carry one param between them, validated before anything reads it.
 *
 * A route param is attacker-controlled and expo-router hands it over as
 * `string | string[] | undefined` whatever the route declared, so it is checked first — the rule
 * `features/challenges/schemas/routeParams.ts` states, and worth as much here: this string becomes
 * the path of a read that serves other people's photographs and their words, and then the path of
 * a `POST` that says something in their room.
 *
 * A link that does not survive this has no room behind it, which is the same answer as a link to a
 * room that is not yours. The two are deliberately not told apart, because the server refuses to
 * tell them apart for a reason: separating *it does not exist* from *you are not in it* would
 * answer *is this id real* about a stranger's evening.
 */

import { z } from 'zod';

export const conversationRouteParams = z.object({
  /** The room this screen is about. Read from `GET /conversations/{id}`, which serves only yours. */
  conversationId: z.string().uuid(),
});

export type ConversationRouteParams = z.infer<typeof conversationRouteParams>;

/** `undefined` when the link cannot be trusted. The route decides what that looks like. */
export function parseConversationRouteParams(
  params: Record<string, string | string[] | undefined>,
): ConversationRouteParams | undefined {
  const result = conversationRouteParams.safeParse(params);
  return result.success ? result.data : undefined;
}
