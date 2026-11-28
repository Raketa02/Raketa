/**
 * **Where every address the operating system opens the app with arrives** — expo-router's
 * `redirectSystemPath`, which `src/app/+native-intent.ts` hands straight to this
 * ([#520](https://github.com/Rakieta02/Rakieta/issues/520), docs/architecture.md Part 2).
 *
 * Not a component: expo-router calls it before it routes anything, at a cold start before a
 * component exists. It is the adapter between that call and the feature — who is signed in, which
 * domain is set, the link held, and the path answered — as `shell`'s `shellNavigation` is the one
 * between a tab press and the router. What a link is and where it lands is `receiveLink`'s.
 *
 * **One of the links is held, and anything else is ignored** — a malformed link, a link from another
 * host, the path of any screen in the app. *Ignored* is exactly that: at a cold start the app opens
 * where it would have with no link at all (`/`, where the gate decides), and while it is running
 * nothing moves. Every route stays reachable only by the app's own navigation.
 *
 * **It never throws.** Whatever goes wrong reading an address is an address that is not a link, and
 * expo-router's own guidance is that a throw here can crash the app.
 */

import { loadEnv } from '@/shared/config/env';
import { getSessionStatus, type SessionStatus } from '@/shared/lib/auth';

import type { LinkSession } from '../domain/linkRules';
import { holdLink } from '../hooks/heldLink';
import { receiveLink } from '../use-cases/receiveLink';

import { linkScreenPath } from './linkRoutes';

export interface SystemPath {
  /** The address as the operating system handed it — `rakieta://…`, `https://…`, or a path. */
  readonly path: string;
  /** Whether it is the address the app was launched with, rather than one opened while running. */
  readonly initial: boolean;
}

/**
 * **The path to route to, or `''` for no move at all.** A cold start always routes somewhere — `/`
 * when there is nothing else — because the app has to open on something.
 */
export function redirectSystemPath({ path, initial }: SystemPath): string {
  const nowhere = initial ? '/' : '';

  try {
    const received = receiveLink({
      address: path,
      initial,
      session: sessionOf(getSessionStatus()),
      domain: linkDomain(),
    });
    if (received === undefined) return nowhere;

    holdLink(received.link);
    return received.landing.kind === 'its-screen' ? linkScreenPath(received.landing.link) : nowhere;
  } catch {
    return nowhere;
  }
}

/**
 * The web domain, from the one validated read of the configuration. At a cold start this runs
 * before bootstrap validates it; a configuration that does not validate is refused on bootstrap's
 * own screen, and until then only the app's scheme is read.
 */
function linkDomain(): string | null {
  try {
    return loadEnv().linkDomain;
  } catch {
    return null;
  }
}

function sessionOf(status: SessionStatus): LinkSession {
  switch (status) {
    case 'authenticated':
      return 'signed-in';
    case 'unauthenticated':
      return 'signed-out';
    case 'bootstrapping':
      return 'unknown';
  }
}
