/**
 * **What a tapped push carried, checked before anything is opened** (#559; `docs/architecture.md`
 * Part 13: *payloads are untrusted, deep-link targets are validated*).
 *
 * The backend pushes seven keys (`notifications/application/pushing.py`), and all seven are read:
 * where it opens and the ids it opens by; its kind, because a Fill in alert opens somewhere its
 * `opens` alone does not say (`domain/notice.ts`); and the notice's own id, because the banner it is
 * drawn as is the list's too and is drawn once. The ids must be ids and where it opens one of the
 * five places — the fourth a booked game's result screen (#664), the fifth Home (#727), whose push
 * carries no game and is not read by this build (#731). The kinds — the notice's, the
 * sport, the game's — are narrowed where the wire is read (`mappers/`), since a code this build
 * cannot name is a notice still told and nowhere to open.
 */

import { z } from 'zod';

import { OPENS, type Opens } from '../domain/vocabulary';

const PushNoticeData = z.object({
  notice_id: z.string().uuid(),
  kind: z.string(),
  opens: z.enum(OPENS),
  game_id: z.string().uuid(),
  pool_id: z.string().uuid(),
  sport: z.string(),
  game_kind: z.string(),
});

/**
 * A notice's facts as the backend sent them — a push's payload, or a listed row's. A listed row
 * about no game carries no game's facts (#727); a push this build reads always does.
 */
export interface SentFacts {
  readonly kind: string;
  readonly opens: Opens;
  readonly gameId: string | null;
  readonly poolId: string | null;
  readonly sport: string | null;
  readonly gameKind: string | null;
}

/** A pushed notice: its id and its facts. */
export interface PushedNotice extends SentFacts {
  readonly noticeId: string;
}

/** The notice, or `undefined` for a payload that is not a notice's. */
export function parsePushNotice(data: unknown): PushedNotice | undefined {
  const parsed = PushNoticeData.safeParse(data);
  if (!parsed.success) return undefined;
  return {
    noticeId: parsed.data.notice_id,
    kind: parsed.data.kind,
    opens: parsed.data.opens,
    gameId: parsed.data.game_id,
    poolId: parsed.data.pool_id,
    sport: parsed.data.sport,
    gameKind: parsed.data.game_kind,
  };
}
