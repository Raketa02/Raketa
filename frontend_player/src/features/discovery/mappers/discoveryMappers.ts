/**
 * **New in Raketa's wire, read** ([#801](https://github.com/Raketa02/Raketa/issues/801); #793's
 * `NewInRaketaPlayerSchema`) — the wire boundary: the generated types stop here and in `api/`.
 *
 * **A sport this build cannot name is left off with its level**, as every list of sports in the app
 * leaves one off: the tile still says who joined and when. The relation is `friends`' own four, held
 * equal to the wire's in that feature's `wireVocabulary.ts`.
 */

import { toSport } from '@/features/onboarding/types';
import type { components } from '@/generated/schema';
import type { Sport } from '@/shared/vocabulary/sport';

import type { Joiner, JoinerPage, JoinerSport } from '../domain/joiner';

type Schemas = components['schemas'];

export function toJoiner(wire: Schemas['NewInRaketaPlayerSchema']): Joiner {
  return {
    playerId: wire.player_id,
    nickname: wire.nickname,
    ...(wire.photo_url === null ? {} : { photoUrl: wire.photo_url }),
    daysSinceJoined: wire.days_since_joined,
    sports: wire.sports.flatMap((held): JoinerSport[] => {
      const sport = toSport(held.sport);
      return sport === undefined ? [] : [{ sport, level: held.level }];
    }),
    relation: wire.relation,
  };
}

export function toJoinerPage(wire: Schemas['NewInRaketaPageResponse']): JoinerPage {
  return {
    joiners: wire.players.map(toJoiner),
    ...(wire.next === null ? {} : { next: wire.next }),
    sports: wire.sports.flatMap((served): Sport[] => {
      const sport = toSport(served);
      return sport === undefined ? [] : [sport];
    }),
  };
}
