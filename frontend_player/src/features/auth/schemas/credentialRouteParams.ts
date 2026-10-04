/**
 * **The recovery and invitation screens' route params, checked before anything trusts them.** A route param is
 * input from outside the app — the reset link arrives from an email (#520 wires it), and any of
 * these paths can be opened by a link somebody made up.
 *
 * Two kinds of value travel. An **email** only pre-fills a box the person can read and change, so
 * one that does not parse opens the box empty rather than refusing the screen. A **token** or a
 * **ticket** opens the way to a new password, so one that does not parse has no screen behind it
 * and the route redirects. Both are the server's `secrets.token_urlsafe` — URL-safe base64 — and
 * the bound is the server's own cap on what a request may carry; the server stays the judge of
 * whether one is real.
 */

import { z } from 'zod';

/** RFC 5321's longest path, well past any address a person types. */
const EMAIL_PARAM = z.object({ email: z.string().max(320) });

const SECRET = z.string().regex(/^[A-Za-z0-9_-]{1,256}$/);

/** The email a screen opens with — what was typed on the screen before, or nothing. */
export function parseEmailParam(params: unknown): string {
  const parsed = EMAIL_PARAM.safeParse(params);
  return parsed.success ? parsed.data.email : '';
}

/** The token from the email's link, or `undefined` for a link this app cannot read. */
export function parseResetLinkParams(params: unknown): { readonly token: string } | undefined {
  const parsed = z.object({ token: SECRET }).safeParse(params);
  return parsed.success ? parsed.data : undefined;
}

/** The ticket a right code was exchanged for, or `undefined` for one that cannot be one. */
export function parseResetTicketParams(params: unknown): { readonly ticket: string } | undefined {
  const parsed = z.object({ ticket: SECRET }).safeParse(params);
  return parsed.success ? parsed.data : undefined;
}

/**
 * **An invitation's two secrets** (#518) — the token from its email's link and the ticket a right
 * code bought. The same machinery mints them (ADR-0184 §4), so the same shape reads them; named
 * apart so a route file says which door it is.
 */
export const parseInvitationLinkParams = parseResetLinkParams;
export const parseInvitationTicketParams = parseResetTicketParams;
