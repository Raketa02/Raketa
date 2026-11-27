/**
 * **Discovery's wire, read** — New in Rakieta ([#801](https://github.com/Raketa02/Raketa/issues/801);
 * #793's `NewInRakietaPlayerSchema`), Same competitive level
 * ([#802](https://github.com/Raketa02/Raketa/issues/802); #794's `SameLevelPlayerSchema`) and Same
 * vibe ([#803](https://github.com/Raketa02/Raketa/issues/803); #795's `SameVibePlayerSchema`). The
 * wire boundary: the generated types stop here and in `api/`.
 *
 * **A sport this build cannot name is left off with its level**, as every list of sports in the app
 * leaves one off: the tile still says who joined and when. The relation is `friends`' own four, held
 * equal to the wire's in that feature's `wireVocabulary.ts`.
 */

import { toSport, toWireSport } from '@/features/onboarding/types';
import type { components } from '@/generated/schema';
import { toSocialTagId } from '@/shared/vocabulary/socialTags';
import type { Sport } from '@/shared/vocabulary/sport';

import type { Joiner, JoinerPage, JoinerSport } from '../domain/joiner';
import type { RestingRow } from '../domain/onScreen';
import type { PeopleRow } from '../domain/peopleRow';
import type { LevelComparison, SameLevelPlayer } from '../domain/sameLevel';
import type { SameVibePlayer } from '../domain/sameVibe';
import type { PageAsked } from '../api/discoveryApi';
import type { SeeAllAsk, SeeAllPage } from '../domain/seeAll';

type Schemas = components['schemas'];

export function toJoiner(wire: Schemas['NewInRakietaPlayerSchema']): Joiner {
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

/** **Home's New in Rakieta** — the ten newest in the server's order, and its total (#822). */
export function toNewInRakietaRow(wire: Schemas['NewInRakietaResponse']): PeopleRow<Joiner> {
  return { people: wire.players.map(toJoiner), total: wire.total };
}

export function toJoinerPage(wire: Schemas['NewInRakietaPageResponse']): JoinerPage {
  return {
    people: wire.players.map(toJoiner),
    ...(wire.next === null ? {} : { next: wire.next }),
    sports: toSports(wire.sports),
  };
}

/**
 * **A Same competitive level card** (#802; #794's `SameLevelPlayerSchema`). **A card whose own sport
 * this build cannot name is left out**: its % and its bar are that sport's, and there is no word or
 * colour to draw them with. A shared sport it cannot name is left off the sheet's blocks.
 */
export function toSameLevelPlayer(
  wire: Schemas['SameLevelPlayerSchema'],
): SameLevelPlayer | undefined {
  const shown = toComparison(wire.shown);
  if (shown === undefined) return undefined;
  return {
    playerId: wire.player_id,
    nickname: wire.nickname,
    ...(wire.photo_url === null ? {} : { photoUrl: wire.photo_url }),
    shown,
    sports: wire.sports.flatMap((each): LevelComparison[] => {
      const comparison = toComparison(each);
      return comparison === undefined ? [] : [comparison];
    }),
    relation: wire.relation,
  };
}

/** Home's row, or a page's players — the cards this build can draw, in the order served. */
export function toSameLevelPlayers(
  players: readonly Schemas['SameLevelPlayerSchema'][],
): readonly SameLevelPlayer[] {
  return players.flatMap((wire): SameLevelPlayer[] => {
    const player = toSameLevelPlayer(wire);
    return player === undefined ? [] : [player];
  });
}

/**
 * **Home's Same competitive level** — the cards this build can draw, and the total as served (#822):
 * the pool counts a card this build leaves out, as it counts everybody the row does not show.
 */
export function toSameLevelRow(wire: Schemas['SameLevelResponse']): PeopleRow<SameLevelPlayer> {
  return { people: toSameLevelPlayers(wire.players), total: wire.total };
}

export function toSameLevelPage(
  wire: Schemas['SameLevelPageResponse'],
): SeeAllPage<SameLevelPlayer> {
  return {
    people: toSameLevelPlayers(wire.players),
    ...(wire.next === null ? {} : { next: wire.next }),
    sports: toSports(wire.sports),
  };
}

function toComparison(wire: Schemas['SameLevelSportSchema']): LevelComparison | undefined {
  const sport = toSport(wire.sport);
  if (sport === undefined) return undefined;
  return {
    sport,
    yourLevel: wire.your_level,
    theirLevel: wire.their_level,
    percentEven: wire.percent_even,
    levelGap: wire.level_gap,
    yourBand: wire.your_band.name,
  };
}

/**
 * **A Same vibe tile** (#803; #795's `SameVibePlayerSchema`). **A shared tag this build cannot name is
 * left off the chips** — a chip with no words is no chip — and the count stays the server's: *3 things
 * in common* is still true of the two of them.
 */
export function toSameVibePlayer(wire: Schemas['SameVibePlayerSchema']): SameVibePlayer {
  return {
    playerId: wire.player_id,
    nickname: wire.nickname,
    ...(wire.photo_url === null ? {} : { photoUrl: wire.photo_url }),
    vibePercent: wire.vibe_percent,
    inCommon: wire.in_common,
    sharedTags: wire.shared_tags.flatMap((served) => toSocialTagId(served) ?? []),
    relation: wire.relation,
  };
}

/** **Home's Same vibe** — the ten in the server's order, and its total (#822). */
export function toSameVibeRow(wire: Schemas['SameVibeResponse']): PeopleRow<SameVibePlayer> {
  return { people: wire.players.map(toSameVibePlayer), total: wire.total };
}

export function toSameVibePage(wire: Schemas['SameVibePageResponse']): SeeAllPage<SameVibePlayer> {
  return {
    people: wire.players.map(toSameVibePlayer),
    ...(wire.next === null ? {} : { next: wire.next }),
    sports: toSports(wire.sports),
  };
}

/** **A See all page, as the route asks for it** — `sport` and `after` only where there is one. */
export function toPageAsked(page: SeeAllAsk): PageAsked {
  return {
    ...(page.sport === undefined ? {} : { sport: toWireSport(page.sport) }),
    ...(page.after === undefined ? {} : { after: page.after }),
  };
}

/** The pill's sports, leaving off one this build cannot name. */
function toSports(served: readonly Schemas['Sport'][]): Sport[] {
  return served.flatMap((each): Sport[] => {
    const sport = toSport(each);
    return sport === undefined ? [] : [sport];
  });
}

/**
 * **A report of the cards on screen** in one row (#804; #796's `OnScreenRequest`). The wire's
 * `OnScreenRow` holds this feature's `RestingRow` by this return type: a row the wire drops fails to
 * compile here, and one it adds is a row this build never reports.
 */
export function toOnScreenReport(
  row: RestingRow,
  playerIds: readonly string[],
): Schemas['OnScreenRequest'] {
  return { row, player_ids: [...playerIds] };
}
