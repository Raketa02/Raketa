/**
 * The sports the picker offers.
 *
 * **Reference data**, so it overrides the 30-second default: the registry is a closed set
 * that changes with a backend release, and refetching it because a player came back to
 * the screen spends their data plan on an answer that cannot have moved.
 */

import { useQuery } from "@tanstack/react-query";

import type { AppError } from "@/shared/errors";

import type { Sport } from "../domain/Sport";
import { listSports } from "../use-cases/listSports";

import { onboardingKeys } from "./onboardingKeys";

const REFERENCE_DATA_STALE_MS = 24 * 60 * 60 * 1000;

export function useSports() {
  return useQuery<readonly Sport[], AppError>({
    queryKey: onboardingKeys.sports(),
    queryFn: ({ signal }) => listSports({ signal }),
    staleTime: REFERENCE_DATA_STALE_MS,
  });
}
