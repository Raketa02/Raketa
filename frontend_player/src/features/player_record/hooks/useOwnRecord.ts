/**
 * **Your own record, read for the You tab** — the header card, the reliability row, the
 * reliability screen and the passport's blocks all draw from it
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §1–§2).
 *
 * It is `usePlayerRecord` on `{ kind: 'me' }`, and not a fourth query: the tab's header opens
 * the record sheet, and the sheet reads exactly this entry — one read, shared between the card
 * that summarises it and the sheet that draws it whole. `useOwnFace` keeps its own entry for
 * its own reason (a URL, read once per open of a screen the sheet is never on); this is the
 * whole record, on the sheet's own defaults — every open a cold read, and nothing cached
 * between opens, because the gates are live.
 *
 * `playerId` is the signed-in player's, read off `GET /users/me`: the `/me` route never sends
 * an id back, and the header draws a generated poster for a player with no photograph, which
 * is a fact about an id.
 */

import { useCurrentUser } from '@/features/auth/types';
import type { Sport } from '@/shared/vocabulary/sport';

import type { RecordSubject } from '../domain/playerRecord';

import { usePlayerRecord } from './usePlayerRecord';

export function useOwnRecord(sport?: Sport) {
  const user = useCurrentUser();
  const playerId = user.data?.id;

  const record = usePlayerRecord({
    subject: { kind: 'me', playerId: playerId ?? '' },
    ...(sport === undefined ? {} : { sport }),
    enabled: playerId !== undefined,
  });

  return { record, playerId };
}

/** The subject the sheet is opened on, for the surfaces that open it from the tab. */
export function ownSubject(playerId: string): RecordSubject {
  return { kind: 'me', playerId };
}
