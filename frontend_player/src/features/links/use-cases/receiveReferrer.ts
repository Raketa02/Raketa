/**
 * **The link an Android install carried, arriving** ([#756](https://github.com/Rakieta02/Rakieta/issues/756),
 * the friends mechanics §4.3) — `receiveLink`'s twin for the one address no tap hands the app. The
 * reading is `schemas/`' (`readReferrerLink`); holding it is the caller's.
 *
 * **It only fills an empty hand.** A link the phone was opened with, or opened while Google Play was
 * being asked, is what the person tapped now; the referrer is the link they tapped before installing.
 * Either way it is held as a tap would be: a group link and a friend link are always held
 * (`landingOf`), so there is no screen of its own to open.
 */

import type { IncomingLink } from '../domain/incomingLink';
import { readReferrerLink } from '../schemas/incomingLinkUrl';

/** The link to hold, or `undefined` — no referrer, none that is a link, or a link already held. */
export function receiveReferrer(
  referrer: string | null,
  held: IncomingLink | null,
): IncomingLink | undefined {
  if (referrer === null || held !== null) return undefined;
  return readReferrerLink(referrer);
}
