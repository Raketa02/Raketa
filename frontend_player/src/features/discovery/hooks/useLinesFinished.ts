/**
 * **Whether FOR YOU's three people lines have been read** (#871) — Players at your level, New in
 * Rakieta and Players with your vibe, each landed, refused, held for a connection, or failed once and
 * retrying: three of the reads FOR YOU waits on before Home reveals it whole. Read off the cache, so
 * it draws again only as it turns.
 */

import { useReadFinished } from '@/shared/lib/query-client';

import { discoveryKeys } from './discoveryKeys';

export function useDiscoveryLinesFinished(): boolean {
  const sameLevel = useReadFinished(discoveryKeys.sameLevel());
  const newInRakieta = useReadFinished(discoveryKeys.newInRakieta());
  const sameVibe = useReadFinished(discoveryKeys.sameVibe());
  return sameLevel && newInRakieta && sameVibe;
}
