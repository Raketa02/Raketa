import 'server-only';

import { readAsClub } from '@/server/club';

import {
  toGroupRow,
  toHandOver,
  toJoinRequests,
  type GroupPageView,
  type GroupRow,
} from './mappers';

/** The Groups table as the backend answers it; a page that cannot read it cannot be drawn. */
async function readGroups() {
  const outcome = await readAsClub((api, auth) => api.GET('/api/v1/club/groups', auth));
  if (!outcome.ok) throw new Error(`The club's groups could not be read: ${outcome.error.code}`);
  return outcome.data;
}

/** **The club's official groups**, by name, whoever runs them or nobody. */
export async function getGroups(): Promise<readonly GroupRow[]> {
  return (await readGroups()).groups.map(toGroupRow);
}

/**
 * **One group's page**, or `null` when the club has no such official group: who runs it, whom
 * it can be handed to, and who waits to join. The club surface reads its groups only as the
 * table, so the group is found there; its queue is read beside it.
 */
export async function getGroupPage(groupId: string): Promise<GroupPageView | null> {
  const [groups, administrators, requests] = await Promise.all([
    readGroups(),
    readAsClub((api, auth) => api.GET('/api/v1/club/administrators', auth)),
    readAsClub((api, auth) =>
      api.GET('/api/v1/club/groups/{group_id}/requests', {
        ...auth,
        params: { path: { group_id: groupId } },
      }),
    ),
  ]);
  if (!administrators.ok) {
    throw new Error(`The club's administrators could not be read: ${administrators.error.code}`);
  }
  const handOver = toHandOver(groupId, groups, administrators.data);
  if (handOver === null) return null;
  if (!requests.ok) {
    // None of the club's: gone between the two reads, as the table has it missing.
    if (requests.error.status === 404) return null;
    throw new Error(`The group's join requests could not be read: ${requests.error.code}`);
  }
  return { ...handOver, requests: toJoinRequests(requests.data) };
}
