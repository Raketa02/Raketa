/**
 * **A request, onto the wire** (#753) — where it was asked from, the group and the sport the screen
 * showed. The relation the routes answer needs no mapping: it is spelled as the wire spells it, and
 * `wireVocabulary.ts` holds the two equal.
 */

import { toWireSport } from '@/features/onboarding/types';
import type { components } from '@/generated/schema';

import type { AskedWhere } from '../domain/friendship';

type Schemas = components['schemas'];

/** `POST /friends/requests`'s body — the group and the sport only where the screen showed them. */
export function toAskRequest(
  playerId: string,
  where: AskedWhere,
): Schemas['AskToBeFriendsRequest'] {
  return {
    player_id: playerId,
    made_from: where.from,
    ...(where.groupId === undefined ? {} : { group_id: where.groupId }),
    ...(where.sport === undefined ? {} : { sport: toWireSport(where.sport) }),
  };
}
