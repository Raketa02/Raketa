/**
 * **Reading a link the phone hands the app** — the address the operating system opened Raketa with,
 * turned into one of the three links or into nothing
 * ([#520](https://github.com/Raketa02/Raketa/issues/520), docs/architecture.md Part 2 *Deep links are
 * untrusted input*, ADR-0187 §7).
 *
 * **Everything here is somebody else's text.** Anybody can make a page, a message or a QR code that
 * opens `raketa://` with any path and any query, so the reading is a list of what is accepted and
 * nothing more:
 *
 * - **where from** — the app's own scheme, the web domain once one is set (`https`, that host, no
 *   port or user), or a path the router already holds. Nothing else: another host, `http`, Expo Go's
 *   `exp://`, a `javascript:` URL.
 * - **which page** — exactly two path segments, `join`, `invite` or `reset` and its value, so
 *   `play/join/<code>` or the path of any screen in the app is no link. Or **the scheme and nothing
 *   after it**, `raketa://` — the button of the club's email to an account that already exists, which
 *   carries no token.
 * - **what value** — a group's code by `groups`' own shape, a token by `auth`'s, both the shapes
 *   those features' routes already read their params with. The server stays the judge of whether a
 *   code is a group's or a token was sent.
 *
 * **The query and the fragment are dropped, never read**, and what comes out is rebuilt from the
 * checked parts — so no link can carry an address, a flag or a host into the app, and none can
 * repoint the backend: the API's address is configuration read once at launch, and nothing a link
 * holds reaches it.
 */

import { parseInvitationLinkParams, parseResetLinkParams } from '@/features/auth/types';
import { parseJoinRouteParams } from '@/features/groups/types';
import { APP_SCHEME, LINK_PAGES, type LinkPage } from '@/shared/config/appLinks';

import type { IncomingLink } from '../domain/incomingLink';

/** Far past any link the three pages make — the longest is a 256-character token. */
const LONGEST = 2048;

/** The app's scheme, then any number of slashes: `raketa://join/…` and `raketa:///join/…` alike. */
const OWN_SCHEME = new RegExp(`^${APP_SCHEME}:/*`, 'i');

/** `https://<host><path>` — the host up to the first slash, so a port or a user stays in it. */
const WEB = /^https:\/\/([^/]*)(\/.*)?$/i;

/**
 * **The link in an address**, or `undefined` for anything that is not exactly one of the three.
 *
 * @param domain the web domain the app's links live on, or `null` while none is set — when an
 *   `https` address is no link at all.
 */
export function readIncomingLink(url: string, domain: string | null): IncomingLink | undefined {
  if (url.length > LONGEST) return undefined;

  const address = url.split(/[?#]/, 1)[0] ?? '';
  if (OWN_SCHEME.test(address) && address.replace(OWN_SCHEME, '') === '') return { kind: 'open' };

  const path = pathIn(address, domain);
  if (path === undefined) return undefined;

  const segments = path.split('/').filter((segment) => segment !== '');
  if (segments.length !== 2) return undefined;

  const [page, value] = segments as [string, string];
  return isLinkPage(page) ? linkTo(page, value) : undefined;
}

/** The path an address names, if it comes from somewhere the app takes links from. */
function pathIn(address: string, domain: string | null): string | undefined {
  if (address.startsWith('/')) return address;
  if (OWN_SCHEME.test(address)) return `/${address.replace(OWN_SCHEME, '')}`;

  const web = WEB.exec(address);
  if (web === null || domain === null) return undefined;
  return web[1]?.toLowerCase() === domain ? (web[2] ?? '/') : undefined;
}

function isLinkPage(segment: string): segment is LinkPage {
  return (LINK_PAGES as readonly string[]).includes(segment);
}

function linkTo(page: LinkPage, value: string): IncomingLink | undefined {
  switch (page) {
    case 'join': {
      const parsed = parseJoinRouteParams({ code: value });
      return parsed === undefined ? undefined : { kind: 'join', code: parsed.code };
    }
    case 'invite': {
      const parsed = parseInvitationLinkParams({ token: value });
      return parsed === undefined ? undefined : { kind: 'invite', token: parsed.token };
    }
    case 'reset': {
      const parsed = parseResetLinkParams({ token: value });
      return parsed === undefined ? undefined : { kind: 'reset', token: parsed.token };
    }
  }
}
