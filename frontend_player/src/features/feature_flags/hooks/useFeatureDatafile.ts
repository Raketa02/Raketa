/**
 * **Keep the datafile current** — the launch-time half of the feature-flag seam.
 *
 * Called once, from the signed-in app's layout, for as long as the app is open: it reads the
 * datafile saved on the device and fetches a fresh one, and because it keeps both reads observed,
 * every return to the foreground fetches again (ADR-0206 §6). It returns nothing, because nothing
 * renders from it; a gate looks the answer up when it mounts.
 *
 * **Never a bootstrap step.** The splash does not wait for it and no route does either: it starts
 * alongside the first screen, and whatever it has not answered by the time a gate mounts, that gate
 * answers from the next rung down.
 */

import { useQuery } from '@tanstack/react-query';

import { getEnv } from '@/shared/config/env';

import { freshDatafileQuery, savedDatafileQuery } from './datafileQueries';

/** `active` is the caller's moment: the datafiles are read while it is true. */
export function useFeatureDatafile(active: boolean): void {
  const { environment } = getEnv();

  useQuery({ ...savedDatafileQuery(environment), enabled: active });
  useQuery({ ...freshDatafileQuery(environment), enabled: active });
}
