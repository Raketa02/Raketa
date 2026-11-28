/**
 * **The friends card and *Find a court*, off the wire** — and the card's question onto it
 * ([#757](https://github.com/Rakieta02/Rakieta/issues/757), over #750's two reads). Generated types
 * stop here and in `api/`.
 *
 * The deck's narrowings, borrowed whole: a club with no name, a forecast the server could not
 * read, a For-fun card's Social vibe — none from an older server, which sends no `vibe` — and an
 * overlap whose game cell names no weekday (`toClub`, `toForecast`, `toVibe`, `toOverlap`). A
 * `null` becomes a field left off — *no court in the next 14 days* is a card with no `court`.
 * **Two fields stay on the wire**: a row's `free_count`, which the busy list already says, and the
 * card's `cut_off`, which is the send sheet's (#759).
 */

import { toWireSport } from '@/features/onboarding/types';
import type { components } from '@/generated/schema';
import type { Sport } from '@/shared/vocabulary/sport';

import type {
  FriendsCard,
  FriendsCardAsk,
  FriendsCourt,
  FriendsCourts,
} from '../domain/friendsCard';

import { toClub, toForecast, toKind, toOverlap, toVibe, toWireKind } from './deckMappers';

type Schemas = components['schemas'];

/** One court the line-up could take. */
export function toFriendsCourt(wire: Schemas['FriendsCourtSchema']): FriendsCourt {
  return {
    startsAt: wire.starts_at,
    club: toClub(wire.club),
    courtId: wire.court_id,
    courtName: wire.court_name,
    indoor: wire.indoor,
    shareGrosze: wire.share_grosze,
    homeClubFull: wire.home_club_full,
    busy: [...wire.busy],
  };
}

export function toFriendsCard(wire: Schemas['FriendsCardResponse']): FriendsCard {
  const overlap = wire.overlap === null ? undefined : toOverlap(wire.overlap);
  return {
    kind: toKind(wire.kind),
    homeClub: toClub(wire.home_club),
    sides: { yours: [...wire.sides.yours], theirs: [...wire.sides.theirs] },
    ...toForecast(wire.forecast),
    ...toVibe(wire.vibe),
    ...(wire.court === null ? {} : { court: toFriendsCourt(wire.court) }),
    ...(overlap === undefined ? {} : { overlap }),
    ...(wire.cut_off === null ? {} : { cutOff: wire.cut_off }),
  };
}

export function toFriendsCourts(wire: Schemas['FriendsCourtsResponse']): FriendsCourts {
  return { homeClub: toClub(wire.home_club), courts: wire.courts.map(toFriendsCourt) };
}

/** `friend_ids` once per friend, in the order seated — the query both reads share. */
function friendsQuery(sport: Sport, friendIds: readonly string[]): URLSearchParams {
  const query = new URLSearchParams({ sport: toWireSport(sport) });
  for (const id of friendIds) query.append('friend_ids', id);
  return query;
}

/** **The card's question** — the line-up, and the sides and the court once chosen. */
export function toFriendsCardQuery(sport: Sport, ask: FriendsCardAsk): string {
  const query = friendsQuery(sport, ask.friendIds);
  query.append('kind', toWireKind(ask.kind));
  if (ask.partnerId !== undefined) query.append('partner_id', ask.partnerId);
  if (ask.court !== undefined) {
    query.append('court_id', ask.court.courtId);
    query.append('starts_at', ask.court.startsAt);
  }
  return query.toString();
}

/** ***Find a court*'s question** — the sport and the friends, nothing else. */
export function toFriendsCourtsQuery(sport: Sport, friendIds: readonly string[]): string {
  return friendsQuery(sport, friendIds).toString();
}
