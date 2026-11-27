import 'server-only';

import { cookies } from 'next/headers';

import { cookieOptions } from './seal';

/**
 * **What this browser has already been told**, so a line meant once is said once: today, only
 * Overview's *You're live* (the screens B2). A plain cookie, `rakieta_club_told_live`, holding no
 * token and nothing anybody could use, with the session's attributes. Per browser, because the
 * backend keeps no such fact: a club can go live while nobody is looking (Stripe says so later),
 * so no save could carry the news to Overview instead.
 */

export const TOLD_LIVE_COOKIE = 'rakieta_club_told_live';

/** Long enough to outlast any club's setup; a club live a year ago needs no reminding. */
const YEAR_SECONDS = 365 * 24 * 60 * 60;

export async function readToldLive(): Promise<boolean> {
  return (await cookies()).has(TOLD_LIVE_COOKIE);
}

/**
 * Server actions only. Told, the line is not said again; untold (the club stopped being live),
 * it is said the next time the club is.
 */
export async function saveToldLive(told: boolean): Promise<void> {
  const jar = await cookies();
  if (told) jar.set(TOLD_LIVE_COOKIE, '1', cookieOptions(YEAR_SECONDS));
  else jar.delete({ name: TOLD_LIVE_COOKIE, path: '/' });
}
