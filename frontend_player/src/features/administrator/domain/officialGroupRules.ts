/**
 * **The four things the administrator area works out on the phone** — everything else about an
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
 * - **Whether the settings say what the group already says** — *Saved*, settled, in place of *Save*
 *   (#517), so a save that would record nothing is never a round trip.
 */

import { platformDay } from '@/shared/date/platformZone';

import type { OfficialGroup, OfficialGroupSettings } from './officialGroup';

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

/**
 * **Whether the settings as the form holds them are the group's own** — the four fields, the sports
 * compared in the registry's order both sides are in. The name is compared as the form trims it;
 * one the server would collapse to the same is a save that records nothing, which the server
 * admits.
 */
export function settingsUnchanged(
  settings: OfficialGroupSettings,
  group: Pick<OfficialGroup, 'name' | 'joinPolicy' | 'whatsAppSize' | 'sports'>,
): boolean {
  return (
    settings.name === group.name &&
    settings.joinPolicy === group.joinPolicy &&
    settings.whatsAppSize === group.whatsAppSize &&
    settings.sports.length === group.sports.length &&
    settings.sports.every((sport, at) => group.sports[at] === sport)
  );
}
