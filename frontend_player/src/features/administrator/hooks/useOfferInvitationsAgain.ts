/**
 * **Offer the account's invitations again, now** — what a link opened by the account it was sent to
 * asks of the invitation sheet ([#520](https://github.com/Raketa02/Raketa/issues/520)).
 *
 * The sheet offers whatever `/users/me` lists that this launch has not set aside, so *again* is two
 * moves: take back what *Not now* set aside, and read the account again — a link can arrive for an
 * invitation the club sent after the account was last read. The sheet does the rest, as it does on
 * launch.
 *
 * **An invitation's link takes back only its own club's** (`clubName`): *Not now* hides the sheet
 * until the next launch (PRD #500 story 119), and a link about one club is no answer about another.
 * **The app's bare address takes back all of them** — it is the button of the club's email to an
 * account that already exists, which names no club.
 */

import { useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';

import { authKeys, useCurrentUser } from '@/features/auth/types';

import { useInvitationsSetAside } from '../store/invitationsSetAside.store';

export function useOfferInvitationsAgain(): (clubName?: string) => void {
  const client = useQueryClient();
  const user = useCurrentUser();
  const takeBack = useInvitationsSetAside((state) => state.takeBack);
  const pending = user.data?.profiles.pendingInvitations;

  return useCallback(
    (clubName?: string) => {
      takeBack(
        clubName === undefined
          ? undefined
          : (pending ?? [])
              .filter((invitation) => invitation.clubName === clubName)
              .map((invitation) => invitation.administratorId),
      );
      void client.invalidateQueries({ queryKey: authKeys.currentUser() });
    },
    [client, pending, takeBack],
  );
}
