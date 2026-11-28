/**
 * **Play's two segments** — Groups and Explore, and which one the tab opens on
 * ([#512](https://github.com/Rakieta02/Rakieta/issues/512), PRD #500 stories 2–4).
 *
 * Groups is the crowd a player already plays with; Explore is where the rebuilt Find a game will
 * grow, and is a blank page until it does. The segment is the first value the phone-preferences
 * store keeps
 * ([ADR-0188](../../../../../docs/adr/0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)
 * §2), so Play reopens where the player left it.
 *
 * Pure: the store hands back a string it has not judged, and this is the judgement.
 */

export const PLAY_SEGMENTS = ['groups', 'explore'] as const;

export type PlaySegment = (typeof PLAY_SEGMENTS)[number];

/** ADR-0188 §2's default: a player who has never chosen lands on Groups. */
export const DEFAULT_PLAY_SEGMENT: PlaySegment = 'groups';

/**
 * The segment a saved value opens on. **Anything this build does not recognise is the default**
 * (§4) — a value written by a newer build, or by a build that had a third segment, is not an
 * error a player should meet.
 */
export function playSegmentFrom(saved: string | undefined): PlaySegment {
  return PLAY_SEGMENTS.find((segment) => segment === saved) ?? DEFAULT_PLAY_SEGMENT;
}
