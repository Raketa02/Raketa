/**
 * **What a tapped push carried, checked before anything is opened** (#559; `docs/architecture.md`
 * Part 13: *payloads are untrusted, deep-link targets are validated*).
 *
 * The backend pushes seven keys about a game (`notifications/application/pushing.py`), and all seven
 * are read: where it opens and the ids it opens by; its kind, because a Fill in alert opens somewhere
 * its `opens` alone does not say (`domain/notice.ts`); and the notice's own id, because the banner it
 * is drawn as is the list's too and is drawn once. The ids must be ids and where it opens one of the
 * four places a game is — the fourth a booked game's result screen (#664). **A notice about no game
 * pushes three** — its id, its kind and Home (#727) — and is read as nothing more (#731): a game's
 * keys on a push that opens Home are left on the wire, and a game's push with none of them is not a
 * notice. The kinds — the notice's, the sport, the game's — are narrowed where the wire is read
 * (`mappers/`), since a code this build cannot name is a notice still told and nowhere to open.
 * **A friend's notice** (#753) pushes the person it names as `player_id`: *You're friends* opens
 * their record (`RECORD`) and is nothing to open without a well-formed id; a friend request opens
 * Home, where its card is, and is read as any notice that opens Home.
 */

import { z } from 'zod';

import { GAME_OPENS, type Opens } from '../domain/vocabulary';

/** What every push carries: the notice, and its kind. */
const Pushed = z.object({ notice_id: z.string().uuid(), kind: z.string() });

const AboutNoGame = Pushed.extend({ opens: z.literal('HOME') });

/** *You're friends* (#753): the person it names, whose record a tap opens — an id, or nothing. */
const AboutAPerson = Pushed.extend({ opens: z.literal('RECORD'), player_id: z.string().uuid() });

const AboutAGame = Pushed.extend({
  opens: z.enum(GAME_OPENS),
  game_id: z.string().uuid(),
  pool_id: z.string().uuid(),
  sport: z.string(),
  game_kind: z.string(),
});

const PushNoticeData = z.union([AboutNoGame, AboutAPerson, AboutAGame]);

/**
 * A notice's facts as the backend sent them — a push's payload, or a listed row's. One about no game
 * carries no game's facts (#727), whichever way it arrived.
 */
export interface SentFacts {
  readonly kind: string;
  readonly opens: Opens;
  readonly gameId: string | null;
  readonly poolId: string | null;
  readonly sport: string | null;
  readonly gameKind: string | null;
  /**
   * The person a notice about no game names — on *You're friends*, whose record it opens (#753).
   * Absent or `null` on every notice that opens by a game or opens Home.
   */
  readonly playerId?: string | null;
}

/** A pushed notice: its id and its facts. */
export interface PushedNotice extends SentFacts {
  readonly noticeId: string;
}

/** The notice, or `undefined` for a payload that is not a notice's. */
export function parsePushNotice(data: unknown): PushedNotice | undefined {
  const parsed = PushNoticeData.safeParse(data);
  if (!parsed.success) return undefined;
  const pushed = parsed.data;
  const noGame = { gameId: null, poolId: null, sport: null, gameKind: null };
  const about =
    pushed.opens === 'HOME'
      ? noGame
      : pushed.opens === 'RECORD'
        ? { ...noGame, playerId: pushed.player_id }
        : {
            gameId: pushed.game_id,
            poolId: pushed.pool_id,
            sport: pushed.sport,
            gameKind: pushed.game_kind,
          };
  return { noticeId: pushed.notice_id, kind: pushed.kind, opens: pushed.opens, ...about };
}
