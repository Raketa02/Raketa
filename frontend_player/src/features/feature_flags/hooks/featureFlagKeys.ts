/**
 * The feature's query keys, in one file.
 *
 * Two entries per environment, because the datafile has two sources with two lifetimes: the one
 * fetched this session, and the one saved on the device by an earlier one. Each is keyed by the
 * environment it was built for — the only parameter that changes either answer.
 */

import type { AppEnvironment } from '@/shared/config/env';

export const featureFlagKeys = {
  all: ['feature-flags'] as const,
  /** This environment's datafile, as the flags host served it this session. */
  fresh: (environment: AppEnvironment) => [...featureFlagKeys.all, 'fresh', environment] as const,
  /** The last readable datafile saved on the device, read back at launch. */
  saved: (environment: AppEnvironment) => [...featureFlagKeys.all, 'saved', environment] as const,
} as const;
