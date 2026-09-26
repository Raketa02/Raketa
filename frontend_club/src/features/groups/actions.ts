'use server';

import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';

import { writeAsClub } from '@/server/club';
import type { RefusalAbout } from '@/ui/forms';

import { readHandOver } from './schemas';

const TABLE = '/groups';

export interface HandOverState {
  /** What the backend refused, and about whom. */
  readonly refusal: RefusalAbout | null;
}

/**
 * **Hand over**, once the desk confirmed (ADR-0183 §8): the group goes to the one chosen, and
 * the desk goes back to the table, which now names them. A 409 means the page was out of date
 * (the one chosen was removed meanwhile), so it is drawn again with the truth. A 404 says only
 * that the group is none of the club's, which an official group never stops being, so the page
 * stays and says so; so does one the backend never answered.
 */
export async function handOverGroup(
  _previous: HandOverState,
  form: FormData,
): Promise<HandOverState> {
  const { groupId, administratorId, name } = readHandOver(form);
  if (groupId === null) return { refusal: { code: 'group_not_found', name } };
  if (administratorId === null) return { refusal: { code: 'administrator_not_active', name } };

  const outcome = await writeAsClub((api, auth) =>
    api.PUT('/api/v1/club/groups/{group_id}/administrator', {
      ...auth,
      params: { path: { group_id: groupId } },
      body: { administrator_id: administratorId },
    }),
  );
  if (!outcome.ok) {
    if (outcome.error.status === 409) revalidatePath(`${TABLE}/${groupId}`);
    return { refusal: { code: outcome.error.code, name } };
  }

  // The table and every Hand over page changed, and so did the Administrators table, which
  // names the groups each person runs.
  revalidatePath(TABLE, 'layout');
  revalidatePath('/administrators');
  redirect(TABLE);
}
