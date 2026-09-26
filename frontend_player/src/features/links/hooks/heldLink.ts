/**
 * **The held link, for the places that answer it** — held as it arrives, read by the hosts in the
 * player's app and the administrator area, let go of by whichever answers it
 * ([#520](https://github.com/Raketa02/Raketa/issues/520)).
 *
 * `holdLink` and `letGoOf` are not hooks: a link arrives before any component exists. They live here
 * because this is the layer that reaches the store — and because holding a link is more than storing
 * it.
 *
 * **A held link belongs to the session it arrived in** — or to the next one, when it arrived with
 * nobody signed in: the invitation opened signed out is answered by the sign-in it leads to. **When a
 * session ends, the link is let go of**, so an invitation's or a reset's token — or a group somebody
 * tapped — is never handed to the next person who signs in on the phone (the logout rule: *reset
 * sensitive UI state*). A sheet's own *Sign out* ends a session too; it leads to the link's screen by
 * the token in that screen's path, and needs nothing held.
 */

import { useEffect } from 'react';

import { getSessionStatus, subscribeToSession } from '@/shared/lib/auth';

import type { IncomingLink } from '../domain/incomingLink';
import { useHeldLinkStore } from '../store/heldLink.store';

/** The link being held, or `null`. */
export function useHeldLink(): IncomingLink | null {
  return useHeldLinkStore((state) => state.link);
}

/** Watching the session for the one held link — replaced with it, stopped when it is let go of. */
let stopWatching: (() => void) | undefined;

/** A link arrived: hold it, in place of any other, until it is answered or its session ends. */
export function holdLink(link: IncomingLink): void {
  useHeldLinkStore.getState().hold(link);
  stopWatching?.();
  stopWatching = letGoWhenTheSessionEnds(link);
}

/** A link was answered: let go of it, unless a newer one has taken its place. */
export function letGoOf(link: IncomingLink): void {
  useHeldLinkStore.getState().letGo(link);
  if (useHeldLinkStore.getState().link === null) {
    stopWatching?.();
    stopWatching = undefined;
  }
}

/**
 * The session machine notifies on every move; **only signed in → signed out is an end**. A cold
 * start's restore (bootstrapping → signed in) and a sign-in after a link opened signed out keep it.
 */
function letGoWhenTheSessionEnds(link: IncomingLink): () => void {
  let before = getSessionStatus();
  return subscribeToSession(() => {
    const now = getSessionStatus();
    if (before === 'authenticated' && now === 'unauthenticated') letGoOf(link);
    before = now;
  });
}

/**
 * **A reset link's own screen is up** — *Set a new password*, signed out — so nothing more is owed to
 * the link. Let go of here, or the password it sets would begin a session the held link then met as
 * a signed-in phone, and asked to sign out of.
 *
 * An invitation's link is not let go of on its screen: an account that already exists signs in from
 * there, and the held link is what has the sheet offer it the invitation.
 */
export function useResetLinkOpened(token: string | undefined): void {
  useEffect(() => {
    if (token !== undefined) letGoOf({ kind: 'reset', token });
  }, [token]);
}
