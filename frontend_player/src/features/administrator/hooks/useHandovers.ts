/**
 * **Saying the handover sheet was seen**
 * ([ADR-0192](../../../../../docs/adr/0192-a-handover-is-told-to-whom-it-was-handed-and-the-app-follows-the-account.md)
 * §1–§2): the groups on the sheet leave the cached account at once, so the sheet goes, and the
 * server is told so every phone agrees.
 *
 * **Retried, as no other write in this feature is**, because the route says so of itself: a group
 * already told about, handed on or not this account's is stepped over and still `204`, so a second
 * send changes nothing. A write that never lands leaves the server listing the groups; this launch
 * has closed them (`useHandoversClosed`), and the next launch tells them again.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';

import { authKeys, type AuthenticatedUser } from '@/features/auth/types';
import type { AppError } from '@/shared/errors';

import type { HandoverNotice } from '../domain/handovers';
import { noteHandoversSeen } from '../use-cases/officialGroups';

import { administratorKeys } from './administratorKeys';

/** How many more times a send is tried — safe, because the route is. */
const SEEN_RETRIES = 2;

export function useNoteHandoversSeen() {
  const client = useQueryClient();

  return useMutation<void, AppError, HandoverNotice>({
    mutationKey: administratorKeys.handoversSeen(),
    mutationFn: (notice) =>
      noteHandoversSeen(
        notice.clubId,
        notice.groups.map((group) => group.groupId),
      ),
    retry: SEEN_RETRIES,
    onMutate: async (notice) => {
      const told = notice.groups.map((group) => group.groupId);
      // A re-read in flight was asked before the sheet closed, and would put the groups back.
      await client.cancelQueries({ queryKey: authKeys.currentUser() });
      client.setQueryData<AuthenticatedUser>(authKeys.currentUser(), (user) =>
        user === undefined
          ? user
          : {
              ...user,
              profiles: {
                ...user.profiles,
                handovers: user.profiles.handovers.filter(
                  (handover) => !told.includes(handover.groupId),
                ),
              },
            },
      );
    },
  });
}
