/**
 * **This phone is pushed the signed-in player's notices** — registered once a session, again when
 * the system replaces its token, and again on a foreground after a registration failed (#559; the
 * screens A9; `docs/architecture.md` Part 13: *token rotation is supported and synchronized with the
 * backend*).
 *
 * Mounted by `NoticesHost` under the tabs, so it runs exactly while a player is in the app:
 * once after a cold start, once after a sign-in — the next player on this phone takes it over, as
 * the backend moves a phone to whoever registers it last — and never on a sign-in screen.
 *
 * ## It never asks
 *
 * The permission is read, never requested (`useLocationRefresh`'s rule): a launch is not a press.
 * Until the player allows notifications on the Notifications screen, nothing is registered, and the
 * moment they do the shared answer turns to *granted* and this registers.
 *
 * ## Once per token, and the write is a mutation
 *
 * `POST /players/me/devices` is the same answer twice, so a repeat would be harmless — but it is
 * still sent once per token per session (`registered`), because every launch and every foreground
 * asking would be traffic for nothing. A failure forgets the token, so the next foreground sends it
 * again; it is a mutation for `useLocationRefresh`'s reason — held while offline and sent on
 * reconnect — and a failure is said to nobody, because nobody pressed anything.
 */

import { useMutation } from '@tanstack/react-query';
import { useCallback, useEffect, useRef, useState } from 'react';

import type { AppError } from '@/shared/errors';
import { useOnForeground, usePush } from '@/shared/lib/platform';

import { registerPhone } from '../use-cases/notifications';

import { usePushPermission } from './usePushPermission';

/**
 * @returns whether this phone is being pushed the player's notices — a registration has landed
 *   this session — which is what the banner's other source, re-reading the list, waits on.
 */
export function usePushRegistration(): boolean {
  const push = usePush();
  const permission = usePushPermission().data;
  /** The token this session registered — or is registering. */
  const registered = useRef<string | undefined>(undefined);
  const [pushed, setPushed] = useState(false);

  const { mutate: register } = useMutation<void, AppError, string>({
    mutationFn: registerPhone,
    onSuccess: () => setPushed(true),
    // On the mutation rather than the call: a later `mutate` drops an earlier call's callbacks.
    onError: (_error, token) => {
      if (registered.current === token) registered.current = undefined;
    },
  });

  const sync = useCallback(async () => {
    if (permission !== 'granted') return;
    const token = await push.readToken();
    if (token === null || token === registered.current) return;
    registered.current = token;
    register(token);
  }, [permission, push, register]);

  // On the way in, and the moment the permission turns to granted.
  useEffect(() => {
    void sync();
  }, [sync]);

  const latest = useRef(sync);
  latest.current = sync;

  // A registration that failed, or a token Expo could not mint, is tried again on the way back.
  useOnForeground(() => void latest.current());

  // The system replaced the token: the old one stops working, so the new one is registered.
  useEffect(() => push.onTokenChange(() => void latest.current()), [push]);

  // A phone that may no longer show anything is not being pushed, whatever was registered.
  return pushed && permission === 'granted';
}
