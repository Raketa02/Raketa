'use server';

import { redirect } from 'next/navigation';

import { appRoute, type AppRoute } from '@/features/get-the-app/mappers';
import { fromBackend, type PublicApi } from '@/server/backend';
import type { FetchResult } from '@/server/outcome';
import { formText, placeRefusal } from '@/ui/forms';

import {
  checkNewPassword,
  isAToken,
  JUST_SET,
  PASSWORD_FIELDS,
  type PasswordFormState,
} from './schemas';

/**
 * **Setting a password by a link**, from the invitation page and the reset page. Each checks what
 * it can before anything leaves, then posts the link's token and the password, and **signs nobody
 * in**: the site holds no session (ADR-0187 §4), so the page then says to sign in to the app.
 *
 * The token is the one the page was opened with, bound on the server (`.bind(null, token)`), and
 * checked again here because a bound argument comes back from the browser.
 */

/** Refusals that mean the link itself no longer works: the page says what it is now. */
const SPENT: ReadonlySet<string> = new Set([
  'credential_expired',
  'credential_used',
  'credential_locked',
  'credential_not_found',
]);

interface ByLink {
  /** The link's page: the invitation's or the reset's. */
  readonly route: Extract<AppRoute, 'invitation' | 'reset'>;
  readonly send: (
    api: PublicApi,
    body: { token: string; password: string },
  ) => Promise<FetchResult<unknown>>;
}

async function setByLink(way: ByLink, linkToken: unknown, form: FormData) {
  // Nothing to redraw: a token that could be nobody's is never put into an address.
  if (!isAToken(linkToken)) return { refusals: {}, formRefusal: 'credential_not_found' };
  const password = formText(form, 'password');
  const refusals = checkNewPassword(password, formText(form, 'repeat'));
  if (Object.keys(refusals).length > 0) return { refusals, formRefusal: null };

  const outcome = await fromBackend((api) => way.send(api, { token: linkToken, password }));
  const page = `/${appRoute(way.route, linkToken)}`;
  if (outcome.ok) redirect(`${page}?${JUST_SET.param}=${JUST_SET.value}`);
  // Spent since the page was drawn: draw it again, which says what the link is now.
  if (SPENT.has(outcome.error.code)) redirect(page);
  return placeRefusal(outcome.error, PASSWORD_FIELDS);
}

/** *Set your password here*, on the invitation page. */
export async function setInvitationPassword(
  linkToken: string,
  _previous: PasswordFormState,
  form: FormData,
): Promise<PasswordFormState> {
  return setByLink(
    {
      route: 'invitation',
      send: (api, body) => api.POST('/api/v1/public/invitations/password', { body }),
    },
    linkToken,
    form,
  );
}

/** *Set a new password*, on the reset page. It signs the account out everywhere. */
export async function setResetPassword(
  linkToken: string,
  _previous: PasswordFormState,
  form: FormData,
): Promise<PasswordFormState> {
  return setByLink(
    {
      route: 'reset',
      send: (api, body) => api.POST('/api/v1/public/password-resets/password', { body }),
    },
    linkToken,
    form,
  );
}
