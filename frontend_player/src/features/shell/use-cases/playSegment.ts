/**
 * **Reading and keeping the Play segment** — the phone-preferences store's first value
 * ([ADR-0188](../../../../../docs/adr/0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)
 * §2), per account.
 *
 * The store hands back a string it has not judged; `playSegmentFrom` is the judgement (§4), so a
 * value this build does not recognise opens on Groups rather than failing. Neither function
 * throws — the store never does — so a phone whose storage cannot be read opens on the default.
 */

import { readPhonePreference, savePhonePreference } from '@/shared/lib/preferences';

import { playSegmentFrom, type PlaySegment } from '../domain/playSegment';

export async function readPlaySegment(account: string): Promise<PlaySegment> {
  return playSegmentFrom(await readPhonePreference(account, 'playSegment'));
}

export function keepPlaySegment(account: string, segment: PlaySegment): Promise<void> {
  return savePhonePreference(account, 'playSegment', segment);
}
