/**
 * **The three things the administrator area works out on the phone** — everything else about an
 * official group is the server's.
 *
 * - **How much of the group has arrived** — the players over the WhatsApp group size, which the
 *   screens call the group size (#529). It may pass 100%, and says so: the size limits nothing
 *   (ADR-0183 §3).
 * - **Which faces the members card draws** — the five newest, and *+N* for the rest of the group's
 *   count, as Info's members row counts (#514).
 * - **Whether the settings say what the group already says** — *Saved*, settled, in place of *Save*
 *   (#517), so a save that would record nothing is never a round trip.
 *
 * A fourth — when a player joined, *this week* or *7 Sep* — went with the players list the card's
 * tap to Members replaced (#529).
 */

import type { OfficialGroup, OfficialGroupSettings } from './officialGroup';

/** **The share of the WhatsApp group that has arrived**, as a percentage — past 100 when it has. */
export function whatsAppShare(players: number, whatsAppSize: number): number {
  return (players / whatsAppSize) * 100;
}

/** At most this many faces on the members card, as Info's members row draws. */
const STACKED_FACES = 5;

/**
 * **The members card's faces and *+N***: the five newest players, and everybody else **in the
 * group's count**, which is the server's. With no face drawn there is no *+N*: it would only
 * repeat the count beside it.
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
