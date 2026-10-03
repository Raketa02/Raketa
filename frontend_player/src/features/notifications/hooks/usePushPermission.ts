/**
 * **May this phone show a notice — and asking it** (#559; the screens A7.2: *a line at the top
 * offers Allow notifications*).
 *
 * The answer is the phone's, read through the push port and held under the feature's keys, so the
 * screen that offers the question and the registration under the tabs read one answer — and the
 * moment it turns to *granted*, the phone is registered. It is re-read on every return to the
 * foreground (never fresh, `refetchOnWindowFocus`), because the remedy for a refusal is the Settings
 * app, and a player coming back from it has changed the answer outside the app.
 *
 * `networkMode: 'always'`: the phone answers with no connection at all. **Asking is just in time**
 * (`docs/architecture.md` Part 13): only *Allow notifications*, pressed, asks — never a launch.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { ensurePermission, usePush, type PermissionState } from '@/shared/lib/platform';

import { notificationKeys } from './notificationKeys';

export function usePushPermission() {
  const push = usePush();
  return useQuery<PermissionState>({
    queryKey: notificationKeys.permission(),
    queryFn: () => push.getPermission(),
    networkMode: 'always',
    staleTime: 0,
    retry: false,
  });
}

/** *Allow notifications*, pressed: the OS asks, and the answer is what the app reads from then on. */
export function useAllowNotifications() {
  const push = usePush();
  const client = useQueryClient();
  return useMutation<PermissionState, Error, void>({
    mutationFn: () => ensurePermission(push),
    networkMode: 'always',
    onSuccess: (state) => client.setQueryData(notificationKeys.permission(), state),
  });
}
