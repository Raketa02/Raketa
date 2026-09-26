import 'server-only';

import { readAsClub } from '@/server/club';

import { toGroupRow, toHandOver, type GroupRow, type HandOverView } from './mappers';

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
 * **One group's Hand over page**, or `null` when the club has no such official group. The club
 * surface reads its groups only as the table, so the group is found there.
 */
export async function getHandOver(groupId: string): Promise<HandOverView | null> {
  const [groups, administrators] = await Promise.all([
    readGroups(),
    readAsClub((api, auth) => api.GET('/api/v1/club/administrators', auth)),
  ]);
  if (!administrators.ok) {
    throw new Error(`The club's administrators could not be read: ${administrators.error.code}`);
  }
  return toHandOver(groupId, groups, administrators.data);
}
