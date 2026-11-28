/**
 * **What an invitation's link opens**, read before *Set your password* is drawn — the address its
 * email box is locked to, and whether the link still works
 * ([#518](https://github.com/Rakieta02/Rakieta/issues/518), ADR-0184 §2).
 *
 * **Not retried unattended**, though a read is safe to repeat: while it is out the screen draws its
 * title and nothing else, and three retries with backoff would hold it so for seconds over a failure
 * the screen offers to read again with one tap. **Never kept**: `gcTime: 0` drops it with the screen,
 * because the answer is about one moment of one link — a link read *valid* an hour ago may be used
 * by now, and the set's own refusal is the authority either way.
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { InvitationLink } from '../domain/invitation';
import { readInvitationLink } from '../use-cases/readInvitationLink';

import { authKeys } from './authKeys';

export function useInvitationLink(token: string) {
  return useQuery<InvitationLink, AppError>({
    queryKey: authKeys.invitationLink(token),
    queryFn: ({ signal }) => readInvitationLink(token, { signal }),
    retry: false,
    gcTime: 0,
    staleTime: Infinity,
    refetchOnWindowFocus: false,
  });
}
