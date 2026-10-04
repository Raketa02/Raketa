/**
 * **The screens a link opens on its own** — *Set your password* and *Set a new password*, `auth`'s,
 * at the paths their emails name (`invite/<token>`, `reset/<token>`). Spelled from `auth`'s own
 * route table rather than again here: a path spelled twice is the one that goes stale.
 *
 * A group link has no screen of its own to land on as it arrives — Join a group is inside the
 * player's app, reached once the account is (`linkRules`' `landingOf`).
 */

import { INVITATION_ROUTES, RESET_ROUTES } from '@/features/auth/types';

import type { CredentialLink } from '../domain/incomingLink';

/** The screen as a typed href, for the moves made inside the app. */
export function linkScreenHref(link: CredentialLink) {
  const pathname = link.kind === 'invite' ? INVITATION_ROUTES.link : RESET_ROUTES.link;
  return { pathname, params: { token: link.token } } as const;
}

/** The same screen's path, filled in — what expo-router is answered with as a link arrives. */
export function linkScreenPath(link: CredentialLink): string {
  const { pathname, params } = linkScreenHref(link);
  return pathname.replace('[token]', params.token);
}
