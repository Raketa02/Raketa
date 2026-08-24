/**
 * Agree with the score on the table.
 *
 * It carries nothing, which is why it has its own address rather than a flag on the
 * other one: an endpoint whose meaning turned on whether a field was present is the
 * *not there / there and empty* confusion the result block is itself shaped to
 * avoid.
 *
 * A **stale accept** — the result settled while her screen was open, or a counter
 * beat her to it — comes back as the counter's situation with `mayAccept` false,
 * which is `ADR-0074`'s own named case. So this resolves and the screen redraws;
 * nothing here tells the two apart, because the screen she gets back does.
 */

import { acceptResult as postAcceptance } from '../api/resultApi';
import type { ResultAnswer } from '../domain/Result';
import { toResultAnswer } from '../mappers/resultMappers';

export interface AcceptResultOptions {
  readonly matchId: string;
  readonly signal?: AbortSignal;
}

export function acceptResult({ matchId, signal }: AcceptResultOptions): Promise<ResultAnswer> {
  return postAcceptance({ matchId, signal }).then(toResultAnswer);
}
