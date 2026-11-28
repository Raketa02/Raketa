/**
 * **Reading and keeping the Rankings view** ([#777](https://github.com/Rakieta02/Rakieta/issues/777)) —
 * *General* or *Friends*, the view last looked at, per account on the phone
 * ([ADR-0203](../../../../../docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md) §5, its fourth
 * value under [ADR-0188](../../../../../docs/adr/0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)).
 *
 * The store hands back a string it has not judged; `rankingViewFrom` is the judgement (§4), so a
 * value this build does not recognise opens on General. Neither function throws — the store never
 * does — so a phone whose storage cannot be read opens on General.
 */

import { readPhonePreference, savePhonePreference } from '@/shared/lib/preferences';

import { rankingViewFrom } from '../domain/ranking';
import type { RankingView } from '../domain/vocabulary';

export async function readRankingView(account: string): Promise<RankingView> {
  return rankingViewFrom(await readPhonePreference(account, 'rankingView'));
}

export function keepRankingView(account: string, view: RankingView): Promise<void> {
  return savePhonePreference(account, 'rankingView', view);
}
