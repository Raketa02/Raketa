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
 * player, once more after a sign-in, and once on the way out of onboarding — a sibling route
 * group, so finishing the second part mounts this tree too. The third is a read of the cell
 * the commit stored seconds earlier, and it is left alone rather than special-cased: a fix
 * that rounds to the stored cell records nothing and answers `204`, which is what makes a
 * write on every launch free. Every return from the background after the mount is measured
 * against the last attempt by `foregroundRefreshDue`, so a player who flips to Messages and
 * back is not read — which the author refused as tracking — and one whose last read is more
 * than a day old is. The instant is a `ref`: a per-device convenience that nothing else
 * reads, held for the life of this tree and gone with the process, which is exactly what
 * makes the next launch a cold start.
 *
 * ## Nothing resets, and the write is a mutation
 *
 * The deck's held deal is not thrown away — its cards' *In your area* is the envelope's
 * `my_area_code`, and the next hand's envelope carries the new cell — and the radar's held
 * reading refetches on its own rule. What is invalidated is the profile surface: the read
 * carries no area today, and this is what makes it follow the moment the profile read grows
 * the field, which the contract books for the day *You* is built.
 *
 * The write goes through `useMutation` as the feature's three other writes do, and for the
 * query client's own reason: paused while offline and resumed on reconnect. A cold start on a
 * dead connection — the trip case — is then a write that lands when the phone does, rather
 * than one dropped until the next launch. `retry: false` is the app's default and right here.
 * A failed write is left in silence — nobody pressed anything, so there is nothing to report,
 * and the next cold start writes again.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useRef } from 'react';

import type { AppError } from '@/shared/errors';
import { useLocation, useOnForeground } from '@/shared/lib/platform';

import { areaAround } from '../domain/locationArea';
import { foregroundRefreshDue } from '../domain/locationRefresh';
import type { LocationArea } from '../domain/ProfileDraft';
import { changeLocation } from '../use-cases/changeLocation';

import { LOCATION_WRITES, playerProfileKeys } from './playerProfileKeys';

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

  // No `onError`: `mutate` reports a failure to nobody, which is the silence the ADR asks for.
  const { mutate: move } = useMutation<void, AppError, LocationArea>({
    // Always a reading: a refresh only ever has the phone's cell to send, and once permission
    // exists it replaces a club picked by hand (ADR-0200 §10).
    mutationFn: (area) => changeLocation({ kind: 'reading', area }),
    scope: LOCATION_WRITES,
    onSuccess: () => client.invalidateQueries({ queryKey: playerProfileKeys.surface() }),
  });

  const refresh = useCallback(async () => {
    // Stamped at the attempt, whatever comes of it: a refused permission or an empty fix is
    // still the phone having been asked, and asking again on the next foreground would be
    // the tracking the day was chosen against.
    lastRefreshAt.current = Date.now();

    if ((await location.getPermission()) !== 'granted') return;
    const fix = await location.readFix();
    if (fix === null) return;
    // The reading is coarsened here and the fix goes out of scope with this function.
    move(areaAround(fix.latitude, fix.longitude));
  }, [location, move]);

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
