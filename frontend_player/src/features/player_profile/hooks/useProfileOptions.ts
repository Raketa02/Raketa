/**
 * What the profile steps offer, and the numbers they enforce.
 *
 * **Reference data**, so it overrides the 30-second default for the reason the sports
 * registry does: the vocabulary is a closed set that changes with a backend release, and
 * refetching it because a player walked back to step one spends their data plan on an
 * answer that cannot have moved. One fetch covers the whole part.
 */

import { useQuery } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { ProfileOptions } from '../domain/ProfileOptions';
import { loadProfileOptions } from '../use-cases/loadProfileOptions';

import { playerProfileKeys } from './playerProfileKeys';

const REFERENCE_DATA_STALE_MS = 24 * 60 * 60 * 1000;

export function useProfileOptions() {
  return useQuery<ProfileOptions, AppError>({
    queryKey: playerProfileKeys.options(),
    queryFn: ({ signal }) => loadProfileOptions({ signal }),
    staleTime: REFERENCE_DATA_STALE_MS,
  });
}
