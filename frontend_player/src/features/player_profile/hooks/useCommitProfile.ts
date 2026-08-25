/**
 * Finishing the part, as the last step sees it.
 *
 * **The decisions are elsewhere.** Where the part stands, and whether the finish may be
 * pressed, are `commitStanding`'s and `mayFinish`'s — pure rules with their own tests. What
 * the key is and how long it lives is the store's. Sending the body is the use case's. What
 * is left here is the sequencing none of those can express: one press, one request, and the
 * things that are true afterwards.
 *
 * ## The key is the defence and the disabled control is the courtesy
 *
 * A double tap sends the same key twice, because the key belongs to the part rather than to
 * the press — so the server creates one profile and answers the second call with it. The
 * control blocking while a commit is in flight is worth having and is not what makes this
 * safe: it is one render behind the finger, and a player on a slow connection tapping twice
 * is the ordinary case rather than the exotic one.
 *
 * **A retry after a failure is the same request.** Nothing is minted, nothing is rebuilt:
 * the draft is untouched and the key is the one the failed attempt carried, so a retry that
 * lands after a commit which actually succeeded replays it rather than making a second.
 *
 * ## What is true once the server has it
 *
 * Three things, and they are done here because this is the one place that knows the commit
 * landed:
 *
 * 1. **The player has a Player profile**, so the entry gate's fourth branch is answered.
 *    The auth feature owns that fact and owns the write — `markPlayerProfileCommitted` — so
 *    this one does not reach into another feature's cached entity to reshape it.
 * 2. **The part is over**, so the draft and its key go. A key that has produced a profile
 *    must never be sent again under a different set of answers.
 * 3. **Where the player goes next** is the caller's, passed to `finish`. This feature owns
 *    the profile, not the flow that collects it, and the screens on the other side of the
 *    commit are onboarding's.
 *
 * The failure is deliberately *not* one of them. A commit that did not land leaves the draft
 * exactly as it was, on the step it was pressed from, with the control that failed as the
 * retry — and nothing anywhere claiming the account was set up.
 */

import { useMutation } from '@tanstack/react-query';
import { useCallback } from 'react';

import { useMarkPlayerProfileCommitted } from '@/features/auth/types';
import type { AppError } from '@/shared/errors';

import {
  commitStanding,
  commitToSend,
  type CommitAttempt,
  type CommitStanding,
  type ProfileCommit,
} from '../domain/profileCommit';
import { useProfileDraft } from '../store/profileDraft.store';
import { commitProfile } from '../use-cases/commitProfile';

interface CommitInput {
  readonly commit: ProfileCommit;
  readonly idempotencyKey: string;
}

export interface ProfileCommitControl {
  readonly standing: CommitStanding;
  /**
   * Send it, and go wherever `onCommitted` says once the server has it.
   *
   * **A no-op on every standing `commitToSend` refuses** — a press that arrives while one is
   * in flight, after one has landed, or while an answer or a photo is outstanding starts
   * nothing. That guard is the rule's, not a second one written here.
   */
  readonly finish: (onCommitted: () => void) => void;
}

export function useCommitProfile(): ProfileCommitControl {
  const markCommitted = useMarkPlayerProfileCommitted();
  const draft = useProfileDraft((state) => state.draft);
  const photos = useProfileDraft((state) => state.photos);
  const commitKey = useProfileDraft((state) => state.commitKey);
  const reset = useProfileDraft((state) => state.reset);

  const commit = useMutation<void, AppError, CommitInput>({
    mutationFn: ({ commit: answers, idempotencyKey }) =>
      commitProfile({ commit: answers, idempotencyKey }),
    // Never unattended, even though the endpoint takes a key: *whether to send this again*
    // is the player's decision, on the control they already pressed once. The key is what
    // makes their decision safe, not a licence for the client to take it for them.
    retry: false,
    onSuccess: () => {
      markCommitted();
      reset();
    },
  });

  const standing = commitStanding(draft, photos, attemptOf(commit));
  const mutate = commit.mutate;

  const finish = useCallback(
    (onCommitted: () => void) => {
      // Both halves have to be there, and neither can be defaulted: `commitToSend` is the
      // rule about which standings may send at all, and no key means no part is running — a
      // commit made under a key invented here would be a write nothing could safely retry.
      const answers = commitToSend(standing);
      if (answers === undefined || commitKey === undefined) return;

      mutate(
        { commit: answers, idempotencyKey: commitKey },
        // Per call rather than on the mutation, so the departure is captured at the moment
        // the player pressed rather than read off whichever render happens to be current
        // when the server answers.
        { onSuccess: onCommitted },
      );
    },
    [standing, commitKey, mutate],
  );

  return { standing, finish };
}

/** The mutation's four states, in the words the rule takes. */
function attemptOf(commit: {
  isSuccess: boolean;
  isPending: boolean;
  error: AppError | null;
}): CommitAttempt {
  if (commit.isSuccess) return { kind: 'landed' };
  if (commit.isPending) return { kind: 'sending' };
  return commit.error === null ? { kind: 'idle' } : { kind: 'failed', error: commit.error };
}
