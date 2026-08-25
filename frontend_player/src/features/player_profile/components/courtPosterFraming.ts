/**
 * What a player with no photo has instead of an empty box: a court, framed by their own id.
 *
 * The drawing is the design system's (`CourtPoster`, 6.9) and so is the space it is drawn
 * in — `COURT_POSTER_SPACE`, which every window below lies inside and a test holds them to. **Determinism is this feature's**, exactly as the confidence ring's ceiling belongs
 * to the engine and not to `theme.ts`: the design system's contract is that the same player
 * id produces the same poster, and choosing *which* poster is what this file does.
 *
 * ## Same id, same poster, forever
 *
 * A poster is derived from the player id and from nothing else — no random seed, no
 * timestamp, no counter — so it survives a reinstall, a new phone and a cold cache without
 * anything being stored anywhere. That is the whole reason it is a hash rather than a
 * picked value: a stored choice is a choice that can be lost, and a player whose poster
 * changed would reasonably think their profile had.
 *
 * ## It varies in geometry and never in colour
 *
 * Nothing here returns a colour, and there is nowhere for one to go. Every colour in this
 * palette already means something, so a player-coloured poster would be assigning meaning
 * to a hash — and the four sport colours in particular would have it claim a sport the
 * player may not play (6.9).
 *
 * ## It sits beside the copy, not in `domain/`
 *
 * There is no rule here a profile could break. What a player id maps to is a fact about how
 * the poster is *drawn* — expressed in the design system's own coordinate space — which is
 * the same kind of thing as the label a tag id maps to, and it lives in the same layer for
 * the same reason. `domain/` holds what the product refuses and requires; this refuses
 * nothing.
 *
 * ## The framings are crops, not drawings
 *
 * Each one is a window onto the same court. Cropping is what makes eight visibly different
 * posters out of one drawing, and it is also what keeps this file from becoming a second
 * place the court is described — the moment there were two, they would drift.
 */

import { type CourtPosterFraming } from '@/shared/ui';

/**
 * The windows onto the court, in its own units.
 *
 * Eight, and eight rather than four because the ball position multiplies them: a player
 * meeting another player's poster should not think the two are the same picture. They
 * range from the whole court down to a corner of it, so the set varies in scale as well as
 * in position — two crops of the same size at different offsets look like one drawing that
 * slid, which is a weaker difference than it sounds.
 */
const FRAMINGS: readonly CourtPosterFraming['view'][] = [
  { x: 0, y: 0, width: 100, height: 140 },
  { x: 6, y: 4, width: 74, height: 104 },
  { x: 20, y: 30, width: 72, height: 101 },
  { x: 0, y: 46, width: 66, height: 92 },
  { x: 28, y: 8, width: 60, height: 84 },
  { x: 10, y: 20, width: 84, height: 118 },
  { x: 34, y: 52, width: 56, height: 78 },
  { x: 2, y: 10, width: 90, height: 126 },
];

/**
 * Where the ball sits, as a fraction of the chosen window.
 *
 * Fractions rather than court coordinates, so the ball is inside the frame whichever
 * framing was drawn — a mark that fell outside the crop would be a poster with nothing on
 * it, on some ids and not others. None of them is centred: a ball in the middle of the
 * frame reads as a target rather than as a ball in play.
 */
const BALL_POSITIONS: readonly { readonly x: number; readonly y: number }[] = [
  { x: 0.27, y: 0.22 },
  { x: 0.72, y: 0.31 },
  { x: 0.38, y: 0.68 },
  { x: 0.66, y: 0.74 },
  { x: 0.21, y: 0.55 },
  { x: 0.79, y: 0.58 },
];

/**
 * FNV-1a, 32-bit, over the id's code units.
 *
 * A hash and not a cryptographic one, deliberately: what is wanted is *the same id lands
 * in the same place every time*, spread evenly enough that two players rarely share a
 * poster. Nothing here is a secret and nothing is being authenticated — a player id is
 * public to the player whose it is, and the poster it produces is shown to everyone.
 */
function hashOf(playerId: string): number {
  const OFFSET_BASIS = 2166136261;
  const PRIME = 16777619;

  let hash = OFFSET_BASIS;
  for (let at = 0; at < playerId.length; at += 1) {
    hash ^= playerId.charCodeAt(at);
    // `Math.imul` keeps the multiply in 32 bits; a plain `*` loses the low bits to
    // floating point at this magnitude and the hash stops spreading.
    hash = Math.imul(hash, PRIME);
  }
  return hash >>> 0;
}

/**
 * The poster this player has, and will still have on their next phone.
 *
 * The framing and the ball are taken from **different halves of the hash**, so the two
 * choices move independently — dividing one number twice by two small sets would tie them
 * together and cut the poster count from forty-eight to eight.
 */
export function courtPosterFor(playerId: string): CourtPosterFraming {
  const hash = hashOf(playerId);

  const view = FRAMINGS[hash % FRAMINGS.length] as CourtPosterFraming['view'];
  const spot = BALL_POSITIONS[(hash >>> 16) % BALL_POSITIONS.length] as (typeof BALL_POSITIONS)[0];

  return {
    view,
    ball: { x: view.x + spot.x * view.width, y: view.y + spot.y * view.height },
  };
}

/** How many distinct posters exist. Tested, so that shrinking either set is a decision. */
export const COURT_POSTER_COUNT = FRAMINGS.length * BALL_POSITIONS.length;

/** Every window this file will hand out, so a test can hold them against the court's bounds. */
export const COURT_POSTER_FRAMINGS = FRAMINGS;
