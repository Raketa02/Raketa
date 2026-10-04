import { NextResponse, type NextRequest } from 'next/server';

import { PATH_HEADER } from '@/server/club';
import { refreshOnce } from '@/server/refresh';
import { SESSION_COOKIE, sealSession, sessionCookieOptions, unsealSession } from '@/server/session';

/**
 * **Keeps the session's access token fresh, ahead of every page and every action.**
 *
 * A server component cannot set a cookie, so a render cannot keep a rotated pair. The proxy can:
 * when the access token is within {@link RENEW_AHEAD_MS} of lapsing, it renews the pair through
 * the single flight and hands the new cookie both to the browser and to the render behind it,
 * which then reads a token that works.
 *
 * It decides nothing else. Whether a page needs a session is the page's question, answered by
 * `src/server/club.ts`, because a proxy is skipped by any path its matcher misses.
 */

const RENEW_AHEAD_MS = 30_000;

/**
 * Forward the request with its own path stamped on it, so a render that must hand itself to
 * `/session/renew` knows where to come back to. The stamp always overwrites: a browser cannot
 * choose where a renewal returns. `sealed` is the session to forward: unchanged (`undefined`),
 * renewed (a new seal), or gone (`null`).
 */
function forward(request: NextRequest, sealed?: string | null): NextResponse {
  const { pathname, search } = request.nextUrl;
  if (sealed === null) request.cookies.delete(SESSION_COOKIE);
  else if (sealed !== undefined) request.cookies.set(SESSION_COOKIE, sealed);
  const forwarded = new Headers(request.headers);
  forwarded.set(PATH_HEADER, `${pathname}${search}`);

  const response = NextResponse.next({ request: { headers: forwarded } });
  if (sealed === null) response.cookies.delete({ name: SESSION_COOKIE, path: '/' });
  else if (sealed !== undefined)
    response.cookies.set(SESSION_COOKIE, sealed, sessionCookieOptions());
  return response;
}

export async function proxy(request: NextRequest): Promise<NextResponse> {
  const sealed = request.cookies.get(SESSION_COOKIE)?.value;
  if (sealed === undefined) return forward(request);

  const session = await unsealSession(sealed);
  if (session === null) return forward(request, null);
  if (session.expiresAt - Date.now() > RENEW_AHEAD_MS) return forward(request);

  const refreshed = await refreshOnce(session.refreshToken);
  switch (refreshed.kind) {
    case 'renewed':
      return forward(request, await sealSession(refreshed.session));
    case 'refused':
      return forward(request, null);
    case 'unreachable':
      return forward(request);
  }
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|icon.svg).*)'],
};
