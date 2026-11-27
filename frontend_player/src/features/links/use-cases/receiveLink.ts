/**
 * **A link arriving** — the address the operating system opened the app with, read, and where it
 * lands decided ([#520](https://github.com/Raketa02/Raketa/issues/520)). Holding it and routing to
 * its screen are the caller's; the reading is `schemas/`', and the landing `domain/`'s.
 */

import type { IncomingLink } from '../domain/incomingLink';
import { landingOf, type Landing, type LinkSession } from '../domain/linkRules';
import { readIncomingLink } from '../schemas/incomingLinkUrl';

export interface LinkArrival {
  /** The address as the operating system handed it — `rakieta://…`, `https://…`, or a path. */
  readonly address: string;
  /** Whether it is the address the app was launched with, rather than one opened while running. */
  readonly initial: boolean;
  readonly session: LinkSession;
  /** The web domain the app's links live on, or `null` while none is set. */
  readonly domain: string | null;
}

export interface ReceivedLink {
  readonly link: IncomingLink;
  readonly landing: Landing;
}

/**
 * **The link in the address and where it lands**, or `undefined` when there is no link to answer.
 *
 * **The app's bare address is a link only while the app runs.** A launch from the home screen hands
 * the router the same address, so at a launch it asks nothing — the invitation sheet offers what is
 * open on every launch anyway.
 */
export function receiveLink({
  address,
  initial,
  session,
  domain,
}: LinkArrival): ReceivedLink | undefined {
  const link = readIncomingLink(address, domain);
  if (link === undefined || (link.kind === 'open' && initial)) return undefined;
  return { link, landing: landingOf(link, session) };
}
