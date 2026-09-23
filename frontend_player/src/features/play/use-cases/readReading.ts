/**
 * Read the radar — **one request, and the whole of what the pane asks for.**
 *
 * A sport, and nothing else: no radius (it is the profile's, resolved server-side), no mode
 * (there is none — the radar scores every pairing under one ruler, as the deck does), no
 * position (the server holds the viewer's cell). `POST /radar` answers with every player the
 * radar may draw for the viewer in that sport, each at a distance and a bearing
 * ([ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §1, [`the-radar.md`](../../../../../docs/specs/matchmaking/the-radar.md) §2).
 *
 * A pass-through in the uniform-strict sense: the rule about what a reading *is* lives in
 * `domain/reading` and the narrowings in `mappers/readingMappers`; what is here is the one
 * seam a hook calls, so the wire's sport spelling is decided in one place.
 */

import { toWireSport } from '@/features/onboarding/types';
import type { Sport } from '@/shared/vocabulary/sport';

import { readRadar } from '../api/radarApi';
import type { Reading } from '../domain/reading';
import { toReading } from '../mappers/readingMappers';

export async function readReading(sport: Sport): Promise<Reading> {
  return toReading(await readRadar({ sport: toWireSport(sport) }));
}
