/**
 * The two routes a record is read through, the one write beside them, and the only place their
 * paths are written down.
 *
 * One of the two layers allowed to read generated types.
 *
 * ## Two routes, because one of them is not gated
 *
 * `GET /players/{player_id}/record` is read **through a prior disclosure**: it opens for
 * somebody a search of yours returned, somebody you share an open challenge or a game with,
 * and for yourself. Everybody else — and anybody a live gate no longer admits — is `404`, in
 * one shape that names nothing.
 *
 * `GET /players/me/record` is the same sheet about yourself and **nothing gates it**. The gender
 * preference is mutual and has nothing to say about somebody reading their own record; a hold
 * does not reach it either, because this is the one screen a held player has for finding out how
 * they appear. The parameterised route would answer a healthy account asking about itself, which
 * is exactly why the two are not collapsed: the one player who most needs this screen is the one
 * the other route would refuse.
 *
 * ## `sport` selects what the sheet is about and never who may be seen
 *
 * Where the subject holds a rating in the sport asked for, that is the sport the skill card is
 * drawn for; otherwise the server falls back to the one they have played most. Admission is
 * decided in the partitions the platform already showed this person in, which is not something
 * a client sends — so omitting the parameter narrows nothing and widens nothing.
 *
 * ## The sport is a query parameter, spelled here and nowhere else
 *
 * It is the first query string in this app, so it is built with `URLSearchParams` rather than
 * interpolated: a sport is a closed four today and the encoding is what stops the second
 * parameter — a citation, when the chat and the games list open this sheet — arriving as a
 * hand-joined `&`.
 *
 * ## A `signal` on the reads and none on the write
 *
 * The asymmetry every api module in this app draws: a `GET` records nothing, so a sheet closed
 * while its request is in flight costs nobody a row. The filter's `PUT` is a setting the player
 * asked for, and a screen left mid-save does not take the asking back.
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type PlayerRecordResponse = components['schemas']['PlayerRecordResponse'];
type WireSport = components['schemas']['Sport'];
type SetReliabilityFilterRequest = components['schemas']['SetReliabilityFilterRequest'];

/** The read may be abandoned — see the module note. */
export interface Cancellable {
  readonly signal?: AbortSignal;
}

/** Which sport the reader arrived from, where they arrived from one at all. */
export interface RecordAsk extends Cancellable {
  readonly sport?: WireSport;
}

/**
 * **One player's record**, or the one refusal that names nothing.
 *
 * `404` carries `record_unavailable` for three causes — never disclosed, held or in a state that
 * may not be shown, and no such player — and the body is identical in all three. A block is not
 * one of them, either way round (ADR-0193 §2). The indistinguishability is the feature, so nothing
 * here branches on it.
 */
export function getPlayerRecord(
  playerId: string,
  { sport, signal }: RecordAsk = {},
): Promise<PlayerRecordResponse> {
  return httpRequest<PlayerRecordResponse>({
    method: 'GET',
    path: `/api/v1/players/${encodeURIComponent(playerId)}/record${askedSport(sport)}`,
    authenticated: true,
    signal,
  });
}

/** **Your own record** — how others see you, and the one read on this sheet nothing gates. */
export function getOwnRecord({ sport, signal }: RecordAsk = {}): Promise<PlayerRecordResponse> {
  return httpRequest<PlayerRecordResponse>({
    method: 'GET',
    path: `/api/v1/players/me/record${askedSport(sport)}`,
    authenticated: true,
    signal,
  });
}

/**
 * The one query string on this route, or nothing at all.
 *
 * Omitted rather than sent empty: the server's fallback — *the sport they have played most* —
 * is what an absent parameter asks for, and `?sport=` with nothing after it is a different
 * request that means the same thing badly.
 */
function askedSport(sport: WireSport | undefined): string {
  return sport === undefined ? '' : `?${new URLSearchParams({ sport }).toString()}`;
}

/**
 * **The reliability filter** — *Play only with players of at least High reliability*, *at least
 * Medium*, or `null` for off (ADR-0195 §6, #662). `204` and no body: what is saved is read back
 * on the own record, with how many players in the player's groups it hides. Unkeyed on purpose —
 * an unchanged value records nothing, so a repeat lands the same state. `404
 * player_profile_not_found` is a profile onboarding has not finished; `409
 * concurrent_modification` lost a race with another write to the profile.
 */
export function putReliabilityFilter(
  minimum: SetReliabilityFilterRequest['minimum'],
): Promise<void> {
  const body: SetReliabilityFilterRequest = { minimum };
  return httpRequest<void>({
    method: 'PUT',
    path: '/api/v1/players/me/reliability-filter',
    body,
    authenticated: true,
  });
}
