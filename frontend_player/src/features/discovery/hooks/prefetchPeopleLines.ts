/**
 * **FOR YOU's three people lines, set out before Home is drawn** (#874; ADR-0209 §2, amended
 * 2026-11-24) — Players at your level, New in Raketa and Players with your vibe, read during the
 * splash by the launch's warm-up under the very definitions their hooks observe (`sameLevelRow`,
 * `newInRaketaRow`, `sameVibeRow`), so Home finds them fresh when it mounts and asks nothing twice.
 */

import type { QueryClient } from '@tanstack/react-query';

import { newInRaketaRow } from './useNewInRaketa';
import { sameLevelRow } from './useSameLevel';
import { sameVibeRow } from './useSameVibe';

export function prefetchPeopleLines(client: QueryClient): Promise<unknown> {
  return Promise.all([
    client.prefetchQuery(sameLevelRow),
    client.prefetchQuery(newInRaketaRow),
    client.prefetchQuery(sameVibeRow),
  ]);
}
