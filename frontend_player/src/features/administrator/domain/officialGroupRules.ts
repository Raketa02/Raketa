/**
 * **The three things the administrator area works out on the phone** — everything else about an
 * official group is the server's.
 *
 * - **When a player joined**, as the players list says it: *this week* within seven days, the date
 *   after (club 18, 19). The seven days are **rolling** — seven times twenty-four hours back from
 *   the read — as the club website's *this week* is (#523), so the two surfaces a club and its
 *   Administrator look at never disagree about one player. The date is the day **in the platform's
 *   zone**, never the phone's (`shared/date/platformZone`), so a player who joined at half past
 *   midnight in Kraków joined on that day wherever the phone is.
 * - **How much of the WhatsApp group has arrived** — the players over the WhatsApp group size. It
 *   may pass 100%, and says so: the size limits nothing (ADR-0183 §3).
 * - **Which faces the players card draws** — the five newest, and *+N* for the rest of the group's
 *   count, as Info's members row counts (#514).
 */

import { platformDay } from '@/shared/date/platformZone';

/** Seven days, rolling — *this week*. */
const WEEK_MS = 7 * 24 * 60 * 60 * 1000;

export type JoinedWhen =
  /** Within seven days of the read — and a moment the phone's clock has not reached yet. */
  | { readonly kind: 'this-week' }
  /** Earlier: the calendar day, `YYYY-MM-DD`, in the platform's zone. */
  | { readonly kind: 'day'; readonly day: string };

/**
 * When a player joined, read at `readAt` — the instant the group was read, in milliseconds, so
 * every row of one answer is judged against the same moment. Nothing for a value that is not an
 * instant: there is no day to name.
 */
export function joinedWhen(joinedAt: string, readAt: number): JoinedWhen | undefined {
  const at = Date.parse(joinedAt);
  if (Number.isNaN(at)) return undefined;
  if (readAt - at < WEEK_MS) return { kind: 'this-week' };

  const day = platformDay(joinedAt);
  return day === undefined ? undefined : { kind: 'day', day };
}

/** **The share of the WhatsApp group that has arrived**, as a percentage — past 100 when it has. */
export function whatsAppShare(players: number, whatsAppSize: number): number {
  return (players / whatsAppSize) * 100;
}

/** At most this many faces on the players card, as Info's members row draws. */
const STACKED_FACES = 5;

/**
 * **The players card's faces and *+N***: the five newest players, and everybody else **in the
 * group's count** — which a block does not change, so somebody hidden from this reader is still
 * counted. With no face drawn there is no *+N*: it would only repeat the count beside it.
 */
export function playersStack<Player>(
  players: readonly Player[],
  memberCount: number,
): { readonly faces: readonly Player[]; readonly more: number } {
  const faces = players.slice(0, STACKED_FACES);
  return { faces, more: faces.length === 0 ? 0 : Math.max(0, memberCount - faces.length) };
}
