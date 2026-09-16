/**
 * The location moves on a cold start — silently, after a day in the background, never on a
 * plain foreground ([ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §6).
 *
 * A location was written once, at the end of onboarding, and nothing moved it: a radar that
 * draws people where onboarding left them draws a city as it was. So once a player is signed
 * in and past onboarding, the app reads one fix through the same port the location step used
 * — foreground only, balanced accuracy — coarsens it on arrival and puts the cell. A trip is a
 * trip: a cold start in Lisbon moves the player to Lisbon for everyone, and the next cold
 * start at home moves them back.
 *
 * ## It never asks
 *
 * `getPermission()` only, never `requestPermission()`. Onboarding asked, at the moment the
 * player had read the sentence that earns a yes; a launch is not a press, and a permission
 * revoked in Settings since then means nothing happens and nothing is said — the stored cell
 * stays. That is the same rule `useLocationStep` applies to its own silent re-reads.
 *
 * ## Once on the way in, and then only after a day
 *
 * The cold start is the **mount**: the `(app)` tree mounts once per launch for a signed-in
 * player, and once more after a sign-in, and either is the moment the ADR names. Every
 * return from the background after that is measured against the last attempt by
 * `foregroundRefreshDue`, so a player who flips to Messages and back is not read — which
 * the author refused as tracking — and one back from two days away is. The instant is a
 * `ref`: a per-device convenience that nothing else reads, held for the life of this tree
 * and gone with the process, which is exactly what makes the next launch a cold start.
 *
 * ## Nothing resets
 *
 * The deck's held deal is not thrown away and the radar's held reading refetches on its own
 * rule; what is invalidated is the profile surface, so *In your area* follows the projection
 * the moment a surface reads it. A failed write is left in silence — nobody pressed anything,
 * so there is nothing to report, and the next cold start writes again.
 */

import { useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useRef } from 'react';

import { useLocation, useOnForeground } from '@/shared/lib/platform';

import { areaAround } from '../domain/locationArea';
import { foregroundRefreshDue } from '../domain/locationRefresh';
import { changeLocation } from '../use-cases/changeLocation';

import { playerProfileKeys } from './playerProfileKeys';

/**
 * @param inTheApp whether the player is signed in and past onboarding — the entry gate's own
 *   answer, handed in rather than re-derived, so a player still on the location step is never
 *   read by two things at once.
 */
export function useLocationRefresh(inTheApp: boolean): void {
  const location = useLocation();
  const client = useQueryClient();
  /** When the phone was last asked, on this device's clock. `undefined` until the cold start. */
  const lastRefreshAt = useRef<number | undefined>(undefined);

  const refresh = useCallback(async () => {
    // Stamped at the attempt, whatever comes of it: a refused permission or an empty fix is
    // still the phone having been asked, and asking again on the next foreground would be
    // the tracking the day was chosen against.
    lastRefreshAt.current = Date.now();

    if ((await location.getPermission()) !== 'granted') return;
    const fix = await location.readFix();
    if (fix === null) return;
    // The reading is coarsened here and the fix goes out of scope with this function.
    const area = areaAround(fix.latitude, fix.longitude);

    try {
      await changeLocation(area);
    } catch {
      // Silence: nobody pressed anything, and the next cold start writes again.
      return;
    }
    await client.invalidateQueries({ queryKey: playerProfileKeys.surface() });
  }, [location, client]);

  useEffect(() => {
    if (!inTheApp || lastRefreshAt.current !== undefined) return;
    void refresh();
  }, [inTheApp, refresh]);

  useOnForeground(() => {
    const last = lastRefreshAt.current;
    // Not yet in the app, so not yet read: a foreground on the sign-in screen is nobody's.
    if (last === undefined) return;
    if (foregroundRefreshDue(last, Date.now())) void refresh();
  });
}
