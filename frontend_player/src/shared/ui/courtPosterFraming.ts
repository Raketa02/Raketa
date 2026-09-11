/**
 * What a player with no photo has instead of an empty box: a hue and a pose, framed by their
 * own id.
 *
 * The drawing is `CourtPoster` (6.9) and both sets it chooses from are the theme's —
 * `POSTER_HUES` and `COURT_POSTER_POSES`. **The choice sits beside them**: the design system's
 * contract is that the same player id produces the same poster, and choosing *which* poster is
 * what this file does.
 *
 * ## It left `player_profile/` on the third-caller rule
 *
 * It was that feature's, saying *determinism is this feature's*, while `features/play` was
 * already importing it across a feature boundary through `player_profile`'s public surface.
 * `recoveryMessage.ts` states the rule as a count of **copies** — *"a third copy is the signal
 * to move it"* — and this file's own previous docblock refused the move on exactly that
 * reading: *"there is no second copy."* True, and the wrong test. The third and fourth callers
 * arrive with the Chats rows and the conversation header
 * ([`the-loop-components.md`](../../../../docs/specs/the-loop/the-loop-components.md) §5), and
 * a hash four features deep in cross-boundary imports is one somebody copies rather than
 * reaches — so a copy is what the move now prevents rather than what it waits to count.
 * **One person being two colours on two screens is precisely the drift the seam rule exists
 * for**, and it is drift no type could have caught: two correct hashes that disagree are two
 * correct posters.
 *
 * A promotion and never a copy — there is exactly one implementation of the hash, and every
 * surface that draws somebody's poster reaches it through `@/shared/ui`.
 *
 * ## Same id, same poster, forever
 *
 * A poster is derived from the player id and from nothing else — no random seed, no
 * timestamp, no counter, and **no stored identity hue or pose index**. It survives a
 * reinstall, a new phone and a cold cache without anything being stored anywhere. That is the
 * whole reason it is a hash rather than a picked value: a stored choice is a choice that can
 * be lost, and a player whose poster changed would reasonably think their profile had. It is
 * also why this changes no contract — the client already has the player id, and a pure
 * function of it is the whole input.
 *
 * ## Neither half is a fact
 *
 * A player whose pose is `serve` is not a server; a player whose poster is green plays no
 * particular Sport, which is what the 25° bound on `POSTER_HUES` guarantees rather than
 * hopes. A poster is shown and never read: no engine, no term and no gate may take an input
 * from what this returns.
 *
 * ## It sits in `shared/ui`, beside the drawing it frames
 *
 * There is no rule here a profile could break. What a player id maps to is a fact about how
 * the poster is *drawn* — expressed in the design system's own vocabulary — so it holds no
 * domain rule and belongs to no feature. It began in `player_profile/components/`, because the
 * photos step was the only surface that had met a poster; `PlayerPhoto` is the second and the
 * **record sheet's header is the third**
 * ([#384](https://github.com/Raketa02/Raketa/issues/384)), and a component below every feature
 * cannot reach a function inside one. The design system's own contract — *one player id, one
 * poster, forever* — is what makes this the design system's to keep, and it is why it moved
 * rather than being re-exported through a third feature's barrel.
 *
 * ## The crops are gone, and the colour is what replaced them
 *
 * This file used to hand back a window onto one court, and conceded the case against its own
 * mechanism in doing so: *two crops of the same size at different offsets look like one
 * drawing that slid, which is a weaker difference than it sounds.* Eight windows by six ball
 * positions was that weakness multiplied, not answered — a deck of forty-eight crops of one
 * court is a deck where every card is the same picture, and at a 27pt avatar a crop of a court
 * is four hairlines carrying no identity whatever. Colour is the difference geometry was
 * standing in for, and a fixed composition is what a window would have sliced.
 */

import { COURT_POSTER_POSES, type CourtPosterLook, type CourtPosterPose } from './CourtPoster';
import { POSTER_HUES, type PosterHue } from './theme';

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
 * The hue and the pose are taken from **different parts of the hash**, so the two choices
 * move independently — dividing one number twice by two small sets would tie them together
 * and cut the poster count from forty-eight to sixteen.
 */
export function courtPosterFor(playerId: string): CourtPosterLook {
  const hash = hashOf(playerId);

  return {
    hue: POSTER_HUES[hash % POSTER_HUES.length] as PosterHue,
    pose: COURT_POSTER_POSES[(hash >>> 16) % COURT_POSTER_POSES.length] as CourtPosterPose,
  };
}

/** How many distinct posters exist. Tested, so that shrinking either set is a decision. */
export const COURT_POSTER_COUNT = POSTER_HUES.length * COURT_POSTER_POSES.length;
