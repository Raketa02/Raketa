/**
 * Put a score on the table: enter one, correct her own side's, or counter theirs.
 *
 * **One use case for all three**, because they are one act at three moments and
 * which one a given score is depends on what is already on the table. Splitting
 * them here would mean this layer deciding it, which is `ADR-0048`'s cap living on
 * the phone — and the server would decide it again anyway, from the record.
 *
 * The refusal path is not here, and that is `ADR-0070`: a score that arrives after
 * the conversation moved on is a 200 carrying what a success carries. This
 * resolves; the screen redraws and she *sees* what is true now. The one exception
 * is a score no format of this sport could produce, which rejects — because it is
 * about what she typed rather than about what the match is doing, and a recomposed
 * screen would show her the same table and no reason at all.
 */

import { proposeScore as postScore } from '../api/resultApi';
import type { ResultAnswer } from '../domain/Result';
import { toResultAnswer } from '../mappers/resultMappers';

export interface ProposeScoreOptions {
  readonly matchId: string;
  readonly sets: readonly (readonly [number, number])[];
  readonly signal?: AbortSignal;
}

export function proposeScore({
  matchId,
  sets,
  signal,
}: ProposeScoreOptions): Promise<ResultAnswer> {
  return postScore({ matchId, sets, signal }).then(toResultAnswer);
}
