/**
 * **The six group routes the Groups list, New group, Join a group and the group page read and
 * write** — one of the two layers allowed to read generated types, and the only place these
 * paths are written down.
 *
 * ## A `signal` on the reads and none on the writes
 *
 * The asymmetry `gamesApi` draws, for its reason: a `GET` records nothing, so an abandoned one
 * costs nobody a row — and the two searches are abandoned on **every keystroke**, because each
 * letter is a new question. A write appends an event to the group's stream, and a cancelled one
 * can leave a member or a request recorded with nobody holding the answer that says so.
 *
 * ## No `Idempotency-Key` on either write
 *
 * Joining twice changes nothing: the second `POST /membership` answers the relation the first one
 * made, *you're in* or *requested · waiting*. Creating twice **would** make two groups — names are
 * never unique — so the create is never retried, and the form's button is busy while it is in
 * flight (`useCreateGroup`).
 */

import type { components } from '@/generated/schema';
import { httpRequest } from '@/shared/lib/http';

type Schemas = components['schemas'];

/** The reads may be abandoned; a write may not. See the module note. */
export interface Cancellable {
  readonly signal?: AbortSignal;
}

/** The groups the reader belongs to, **newest joined first**. */
export function getMyGroups({ signal }: Cancellable = {}): Promise<Schemas['MyGroupsResponse']> {
  return httpRequest({ method: 'GET', path: '/api/v1/groups', authenticated: true, signal });
}

/** A group, for its members. `group_not_found` for no such group and for one the reader is not in. */
export function getGroup(
  groupId: string,
  { signal }: Cancellable = {},
): Promise<Schemas['GroupResponse']> {
  return httpRequest({
    method: 'GET',
    path: `/api/v1/groups/${encodeURIComponent(groupId)}`,
    authenticated: true,
    signal,
  });
}

/** Create a Player group — the reader becomes its Owner and first member. */
export function postGroup(
  body: Schemas['CreatePlayerGroupRequest'],
): Promise<Schemas['GroupResponse']> {
  return httpRequest({ method: 'POST', path: '/api/v1/groups', body, authenticated: true });
}

/**
 * **Join, or ask to** — one tap, and the answer's `relation` says which happened: `MEMBER` for an
 * Anyone group, `REQUESTED` for a People I approve one.
 */
export function postMembership(groupId: string): Promise<Schemas['GroupAtClubSchema']> {
  return httpRequest({
    method: 'POST',
    path: `/api/v1/groups/${encodeURIComponent(groupId)}/membership`,
    authenticated: true,
  });
}

function pageQuery(text: string, page: number): string {
  return `q=${encodeURIComponent(text)}&page=${page}`;
}

/** Every club in Raketa whose name or district holds `text`, nearest first, twenty to a page. */
export function getHomeClubs(
  text: string,
  page: number,
  { signal }: Cancellable = {},
): Promise<Schemas['HomeClubPageResponse']> {
  return httpRequest({
    method: 'GET',
    path: `/api/v1/home-clubs?${pageQuery(text, page)}`,
    authenticated: true,
    signal,
  });
}

/** Clubs, districts, group names or a group link — answered as club cards with groups inside. */
export function getJoinSearch(
  text: string,
  page: number,
  { signal }: Cancellable = {},
): Promise<Schemas['JoinSearchResponse']> {
  return httpRequest({
    method: 'GET',
    path: `/api/v1/join-search?${pageQuery(text, page)}`,
    authenticated: true,
    signal,
  });
}
