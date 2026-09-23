/**
 * Answer the proposals question again, from the profile — the You tab's press on either
 * answer (ADR-0179 §2, §8).
 *
 * **Every press records**, the same answer included. Consent is evidenced, not asserted
 * (`CONTEXT.md`), so *asked again against these words and said yes again* is a fact the stream
 * keeps rather than a no-op to skip — which is why this is the one write on the profile
 * surface that is not idempotent, and why nothing here compares the answer to the one held.
 *
 * It takes the answer **with the words it was given against**, always together: the version
 * is the screen's fact and nobody else's, because the file that drew the sentences is the only
 * one that can honestly name them. And it answers with **the record the route made** — the
 * answer, its moment, its words and its surface (`PROFILE`, the route's own and never the
 * body's) — which is what the screen then draws, never the press it sent.
 */

import { answerProposalsOptIn as putProposalsOptIn } from '../api/playerProfileApi';
import type { ProposalsOptIn } from '../domain/ProfileDraft';
import type { RecordedProposalsOptIn } from '../domain/proposalsOptIn';
import { toRecordedProposalsOptIn } from '../mappers/playerProfileMappers';

export function answerProposalsOptIn(answer: ProposalsOptIn): Promise<RecordedProposalsOptIn> {
  return putProposalsOptIn({ accepted: answer.accepted, copyVersion: answer.copyVersion }).then(
    toRecordedProposalsOptIn,
  );
}
