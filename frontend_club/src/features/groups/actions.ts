'use server';

import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';

import { writeAsClub } from '@/server/club';
import type { RefusalAbout } from '@/ui/forms';

import { readAnswer, readHandOver } from './schemas';

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

export interface AnswerState {
  /** What the backend refused, and about whom. */
  readonly refusal: RefusalAbout | null;
}

/**
 * **Approve** or **Decline** somebody asking to join (ADR-0191 §1), and draw the page and the
 * table again: the queue is shorter and the count moved. A 404 means the page was out of date
 * (whoever runs the group answered first, or the group is none of the club's), so it is drawn
 * again with the truth and says so; a backend that did not answer leaves the page as it was.
 */
export async function answerJoinRequest(
  _previous: AnswerState,
  form: FormData,
): Promise<AnswerState> {
  const { groupId, playerId, answer, name } = readAnswer(form);
  if (answer === null) return { refusal: { code: 'request_invalid', name } };
  if (groupId === null) return { refusal: { code: 'group_not_found', name } };
  if (playerId === null) return { refusal: { code: 'join_request_not_found', name } };

  const path = { params: { path: { group_id: groupId, player_id: playerId } } };
  const outcome = await writeAsClub((api, auth) =>
    answer === 'approve'
      ? api.POST('/api/v1/club/groups/{group_id}/requests/{player_id}/approve', {
          ...auth,
          ...path,
        })
      : api.POST('/api/v1/club/groups/{group_id}/requests/{player_id}/decline', {
          ...auth,
          ...path,
        }),
  );
  if (!outcome.ok) {
    if (outcome.error.status === 404) revalidatePath(TABLE, 'layout');
    return { refusal: { code: outcome.error.code, name } };
  }

  // The page's queue and the table's count changed.
  revalidatePath(TABLE, 'layout');
  return { refusal: null };
}
