/**
 * **A game still filling, in detail** — `GET /proposals/{id}` (#542), the details a card's **i**, a
 * *You’re in* row and a live yes open ([#557](https://github.com/Rakieta02/Rakieta/issues/557)).
 *
 * | | |
 * | --- | --- |
 * | `useProposal` | the read — the app's defaults: thirty seconds fresh, read again on focus |
 * | `useLeaveWhileWaiting` | *Leave the game* while one payment is awaited — the yes withdrawn |
 *
 * Every answer re-reads it (`reread`), so the details draw the server's view of the game the moment
 * an answer has landed, with no copy of their own held in between.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { ProposalDetails } from '../domain/details';
import { LEAVING_WHILE_WAITING } from '../domain/home';
import type { LeavingKind } from '../domain/vocabulary';
import { withdrawYes } from '../use-cases/answers';
import { readProposal } from '../use-cases/details';

import { proposalKeys } from './proposalKeys';
import { rereadAfterWithdrawing } from './useGroupDeck';

/** `null` is a game in a sport this build cannot name — read, and nothing to draw. */
export function useProposal(proposalId: string) {
  return useQuery<ProposalDetails | null, AppError>({
    queryKey: proposalKeys.proposal(proposalId),
    queryFn: ({ signal }) => readProposal(proposalId, { signal }),
  });
}

/**
 * **Leave the game while it waits for one payment** (the mechanics §13; #625) — sent as the
 * withdrawal, `DELETE /proposals/{id}/yes`: nobody had paid, and the leaver's hold is let go. The
 * game leaves the leaver's Home and stays on the others' as *Seat open*, filling again (Q106), and
 * Home, the decks, the details and the live yeses are read again (`rereadAfterWithdrawing`).
 */
export function useLeaveWhileWaiting(groupId: string, proposalId: string) {
  const client = useQueryClient();

  return useMutation<LeavingKind, AppError, void>({
    mutationFn: async () => {
      await withdrawYes(proposalId);
      return LEAVING_WHILE_WAITING.kind;
    },
    onSettled: () => rereadAfterWithdrawing(client, groupId),
  });
}
