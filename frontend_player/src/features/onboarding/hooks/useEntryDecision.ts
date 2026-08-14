/**
 * The entry gate, as a hook.
 *
 * **The two queries are fired in parallel**, which is not a performance preference: they
 * answer different questions — is a *run* unfinished, does a *rating* exist — and
 * sequencing them would make every cold launch pay for both round trips one after the
 * other before anything renders.
 *
 * Neither is part of `SessionStatus`. Making "has a rating" a session state would block
 * every cold launch on a network request, which is the opposite of what the bootstrap
 * sequence exists to avoid, and it would be a fourth state nothing else needs.
 */

import { useQuery } from "@tanstack/react-query";
import { useCallback } from "react";

import { useSessionStatus } from "@/shared/lib/auth";
import { networkUnavailable, type AppError } from "@/shared/errors";

import { entryDestination, type EntryDestination } from "../domain/entryDecision";
import { useDeferredRuns } from "../store/deferredRuns.store";
import { findRunInProgress } from "../use-cases/findRunInProgress";
import { listRatings } from "../use-cases/listRatings";

import { onboardingKeys } from "./onboardingKeys";

export type EntryDecision =
  /** Still asking. The caller renders nothing — not a spinner, and never a route tree. */
  | { readonly kind: "pending" }
  /**
   * The gate could not be read. There is no safe default: sending an unrated player into
   * the app skips onboarding, and sending a rated one into onboarding re-rates them. So
   * the player is told, and offered the retry.
   */
  | { readonly kind: "unavailable"; readonly error: AppError; readonly retry: () => void }
  | EntryDestination;

export function useEntryDecision(): EntryDecision {
  const status = useSessionStatus();
  // An unauthenticated launch must not fire authenticated requests that can only 401 —
  // and a 401 at launch is exactly what would make the token rotation chase a session
  // that never existed.
  const enabled = status === "authenticated";
  // Not server data and never mirrored from it: the run really is unfinished, and this
  // is the player's decision to leave it that way until the next launch.
  const deferredRunIds = useDeferredRuns((state) => state.deferred);

  const ratings = useQuery({
    queryKey: onboardingKeys.ratings(),
    queryFn: ({ signal }) => listRatings({ signal }),
    enabled,
  });

  const run = useQuery({
    queryKey: onboardingKeys.runInProgress(),
    // `?? null` is load-bearing. TanStack Query reserves `undefined` for "nothing
    // cached" and rejects it as data, so a query that answered "no run in progress" by
    // returning `undefined` would be recorded as a failed fetch — and the gate would sit
    // pending forever for the commonest player there is. `null` is the value that means
    // *asked, and there is none*.
    queryFn: ({ signal }) => findRunInProgress({ signal }).then((found) => found ?? null),
    enabled,
  });

  const refetchRatings = ratings.refetch;
  const refetchRun = run.refetch;
  const retry = useCallback(() => {
    void refetchRatings();
    void refetchRun();
  }, [refetchRatings, refetchRun]);

  const error = (ratings.error ?? run.error) as AppError | null;
  if (error !== null) return { kind: "unavailable", error, retry };

  // Offline, with nothing cached to decide from. `networkMode: 'online'` *pauses* a
  // query rather than failing it, so without this branch a launch on a dead connection
  // renders nothing at all — for as long as the connection stays dead. Saying so is the
  // difference between an app that is waiting and an app that looks broken.
  const paused = ratings.fetchStatus === "paused" || run.fetchStatus === "paused";
  if (paused && !(ratings.isSuccess && run.isSuccess)) {
    return { kind: "unavailable", error: networkUnavailable(), retry };
  }

  // `isSuccess`, not a truthiness check on the data: an empty ratings list and a `null`
  // run are both real answers, and both are falsy.
  if (!ratings.isSuccess || !run.isSuccess) return { kind: "pending" };

  return entryDestination({
    ratings: ratings.data,
    runInProgress: run.data ?? undefined,
    deferredRunIds,
  });
}
