/**
 * What the conversation is doing, asked fresh every time the screen opens.
 *
 * **`staleTime: 0`, against the app's 30-second default**, and the default's own
 * comment invites exactly this: *"data classes that differ (slow reference data,
 * live availability) override it in their own feature hook."* This is the live
 * class. Everything on this screen turns on clocks the phone does not hold — a
 * proposal can land, settle, or be countered between two visits — and a screen that
 * offered *accept* against a score somebody has already replaced would be asking
 * her to agree with a number that is no longer on the table.
 *
 * It is still not a promise that what is on screen stays true, and nothing here
 * pretends otherwise: a write made against a conversation that moved on comes back
 * as the conversation as it is now, which is the correction that matters.
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { Result } from '../domain/Result';
import { readResult } from '../use-cases/readResult';

import { resultKeys } from './resultKeys';

export function useResult(matchId: string) {
  return useQuery<Result, AppError>({
    queryKey: resultKeys.screen(matchId),
    queryFn: ({ signal }) => readResult({ matchId, signal }),
    staleTime: 0,
  });
}
