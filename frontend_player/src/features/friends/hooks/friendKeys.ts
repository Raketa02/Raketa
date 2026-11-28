/**
 * **The friends feature's query keys** ([#754](https://github.com/Rakieta02/Rakieta/issues/754)) —
 * the Friends page's three reads and the Add friends sheet's two, which the You tab's row shares.
 *
 * **Every friends write re-reads them all** (`useFriendWrites`' `settle`): an accept on Home moves
 * *Asked you* and *Friends*, a request from Members moves *You asked* and a group's *to add*, and
 * whichever screen pressed it, the page under it or the row on You says so when the player comes
 * back. They are this feature's own, so naming them costs no other feature a dependency. **One
 * other feature reads them**: `notifications` marks them stale as *Level got* opens the picker
 * (#758) — the friend's Level arrived — and this feature imports nothing of `notifications`'.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { RequestDirection } from '../domain/vocabulary';

export const friendKeys = {
  all: ['friends'] as const,
  /** `GET /friends` — your friends, by nickname. */
  list: () => [...friendKeys.all, 'list'] as const,
  /** `GET /friends?sport=` — a group's picker (#757): one sport's Level each, highest first. */
  listIn: (sport: Sport) => [...friendKeys.all, 'list', sport] as const,
  /** `GET /friends/requests?direction=` — *Asked you* or *You asked*. */
  requests: (direction: RequestDirection) => [...friendKeys.all, 'requests', direction] as const,
  /** `GET /friends/groups` — the Add friends sheet's groups. */
  groups: () => [...friendKeys.all, 'groups'] as const,
  /** `GET /friends/link` — your friend link, the sheet's *Not on Rakieta yet?* card (#756). */
  link: () => [...friendKeys.all, 'link'] as const,
};
