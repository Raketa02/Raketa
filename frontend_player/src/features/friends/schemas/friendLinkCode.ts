/**
 * **A friend link's code, read** ([#756](https://github.com/Rakieta02/Rakieta/issues/756), the friends
 * mechanics §4.1) — what follows `/f/` in `<public site>/f/<code>`.
 *
 * It arrives in somebody else's text — a WhatsApp message, a QR code, a Play install referrer — so
 * it is checked before it is sent anywhere: **eight letters and digits, a group code's shape**,
 * read lower case, the case every code is minted in. The server stays the judge of whether a code
 * is anybody's link (`friend_link_not_found`).
 *
 * Spelled here rather than borrowed from `groups`' `GroupCodeSchema`: the shapes agree today
 * because the mechanics chose them to, and `groups` draws this feature's pills, so this feature
 * reading `groups` back would be a dependency both ways.
 */

import { z } from 'zod';

const FriendLinkCodeSchema = z
  .string()
  .regex(/^[0-9A-Za-z]{8}$/)
  .transform((code) => code.toLowerCase());

/** The code, lower case, or `undefined` for anything that cannot be one. */
export function parseFriendLinkCode(value: unknown): string | undefined {
  const parsed = FriendLinkCodeSchema.safeParse(value);
  return parsed.success ? parsed.data : undefined;
}
