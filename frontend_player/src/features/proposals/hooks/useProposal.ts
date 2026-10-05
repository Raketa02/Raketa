/**
 * **A game still filling, in detail** — `GET /proposals/{id}` (#542), the details a card's **i**, a
 * *You're In* row and a live yes open ([#557](https://github.com/Raketa02/Raketa/issues/557)).
 *
 * | | |
 * | --- | --- |
 * | `useProposal` | the read — the app's defaults: thirty seconds fresh, read again on focus |
 * | `useLeaveWhileWaiting` | *Leave the game* while an On request club decides — the yes withdrawn |
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
import { reread } from './useGroupDeck';

/** `null` is a game in a sport this build cannot name — read, and nothing to draw. */
export function useProposal(proposalId: string) {
  return useQuery<ProposalDetails | null, AppError>({
    queryKey: proposalKeys.proposal(proposalId),
    queryFn: ({ signal }) => readProposal(proposalId, { signal }),
  });
}

/**
 * **Leave the game while the club decides** (the mechanics §13; #543) — sent as the withdrawal,
 * `DELETE /proposals/{id}/yes`, which also calls off the request to the club: nobody had paid. The
 * game leaves Home (it was waiting there), the people still In find it filling again, and the decks,
 * the details and the live yeses are read again.
 */
export function useLeaveWhileWaiting(groupId: string, proposalId: string) {
  const client = useQueryClient();

  return useMutation<LeavingKind, AppError, void>({
    mutationFn: async () => {
      await withdrawYes(proposalId);
      return LEAVING_WHILE_WAITING.kind;
    },
    onSettled: () =>
      Promise.all([
        reread(client, groupId, { yeses: true }),
        client.invalidateQueries({ queryKey: proposalKeys.home() }),
      ]),
  });
}
