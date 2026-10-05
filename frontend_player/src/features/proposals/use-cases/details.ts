/**
 * **A game still filling, read** (#542, #557) — a pass-through: who is In, the status and what the
 * reader may do are the server's projection, and nothing about them is decided on the way in.
 */

import { getProposal, type Cancellable } from '../api/proposalsApi';
import type { ProposalDetails } from '../domain/details';
import { toProposalDetails } from '../mappers/detailsMappers';

/** One game's details — or nothing, for a game in a sport this build cannot name. */
export async function readProposal(
  proposalId: string,
  options: Cancellable = {},
): Promise<ProposalDetails | null> {
  return toProposalDetails(await getProposal(proposalId, options)) ?? null;
}
