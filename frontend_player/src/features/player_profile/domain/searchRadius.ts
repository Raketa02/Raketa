/**
 * The **Search radius**: how far out a player asks to look, and the arithmetic that keeps
 * whatever they do to a slider inside what the commit will accept.
 *
 * The radius is *"a filter when the player searches, and a weight when the engine
 * proposes"* (`CONTEXT.md`) — the same number answering two questions, because who *you*
 * asked to see and who the platform *offers* you are different acts. Nothing consumes it
 * yet; this module owns the range a player may choose from and where a finger on a track
 * lands inside it.
 *
 * ## The four numbers are not here, and their absence is the point
 *
 * The minimum, the maximum, the step and the default are served by
 * `GET /player-profile/options`, re-validated on the write path, and product's to retune
 * without an app-store release. So every function below **takes** them, and none of this
 * file knows what they are — the same shape `socialTagSelection` has for the same reason.
 * A module that shipped `1` and `50` compiled in would be a second, staler copy of a rule
 * the server already owns, in builds already on phones.
 *
 * ## Whole steps, counted from the minimum
 *
 * The backend accepts a radius that is inside the range **and** on a step boundary, and it
 * counts those boundaries from the minimum rather than from zero. Everything here counts
 * them the same way, because a control that can only be operated into a refusal is worse
 * than no control.
 *
 * ## No renderer, no store, no served response
 *
 * The onboarding step is the first screen to obey these rules and the profile editor will
 * be the second — the same four numbers, the same snapping, a different screen. So the
 * rules are functions of a value and its bounds, which is also what makes them testable
 * without mounting anything.
 */

/** The served range, in whole kilometres. Both ends included, subject to the step. */
export interface SearchRadiusBounds {
  readonly minimumKm: number;
  readonly maximumKm: number;
  /** The granularity — whole kilometres today, and never zero. */
  readonly stepKm: number;
  /** What the control opens at, so the step can be passed without a decision. */
  readonly defaultKm: number;
}

/** Which way one accessibility action moves the value. */
export type RadiusStepDirection = 'increment' | 'decrement';

/**
 * The largest radius the track's far end may produce.
 *
 * Usually the served maximum, and **not** when the step does not divide the range: with a
 * minimum of 2 and a step of 5, a maximum of 21 is inside the range and off the step, so
 * the last value a player may actually hold is 17. The end of the track has to be a value
 * the commit accepts — otherwise the one place on the control a player is most likely to
 * press is the one place that cannot be committed.
 */
export function topOfScale(bounds: SearchRadiusBounds): number {
  const span = bounds.maximumKm - bounds.minimumKm;
  return bounds.minimumKm + Math.floor(span / bounds.stepKm) * bounds.stepKm;
}

/**
 * What the step opens at: what the player already said, or the served default.
 *
 * The held value wins, always. Walking back to this step to check something and finding it
 * reset to the default would be the part quietly discarding an answer — which is the one
 * thing the client-held draft exists to make impossible.
 */
export function openingRadius(held: number | undefined, bounds: SearchRadiusBounds): number {
  return held ?? bounds.defaultKm;
}

/**
 * The radius a press at `fraction` along the track means.
 *
 * `fraction` is where the finger is, 0 at the start of the track and 1 at its end. It is
 * allowed to arrive outside that: the **row** is the control, not the track, so a press
 * past either end is an ordinary press meaning that end — and a pan that leaves the row
 * sideways keeps the value it was dragging rather than jumping.
 *
 * A row that has not been laid out has no width, and a fraction divided out of it is not a
 * number. That answers the minimum rather than propagating a `NaN` into the draft.
 */
export function radiusAtFraction(fraction: number, bounds: SearchRadiusBounds): number {
  if (!Number.isFinite(fraction)) return bounds.minimumKm;

  const top = topOfScale(bounds);
  const alongTheTrack = clampToTrack(fraction);
  return snapped(bounds.minimumKm + alongTheTrack * (top - bounds.minimumKm), bounds);
}

/**
 * Where the thumb sits for a radius, on the **full served scale**.
 *
 * Always the whole range, exactly as the confidence ring's scale is always 0–100: the same
 * radius lands in the same place on this step and in the profile editor that later reads
 * it. Clamped at both ends because a radius recorded under bounds that have since been
 * narrowed is still a fact about the player — the backend's fold accepts what its write
 * path refuses — and a thumb drawn off the end of its own track is not a reading.
 */
export function radiusFraction(radiusKm: number, bounds: SearchRadiusBounds): number {
  const travel = topOfScale(bounds) - bounds.minimumKm;
  if (travel <= 0) return 0;
  return clampToTrack((radiusKm - bounds.minimumKm) / travel);
}

/**
 * One step up or down — what an `increment` or `decrement` action does.
 *
 * Defined as *the next step boundary in that direction* rather than as `value ± step`, so
 * that a value which is not on a boundary lands on one instead of carrying its offset
 * along. Both ends hold: there is nowhere past them to go, and going nowhere is not the
 * same as going outside the bounds.
 */
export function steppedRadius(
  radiusKm: number,
  bounds: SearchRadiusBounds,
  direction: RadiusStepDirection,
): number {
  const steps = (radiusKm - bounds.minimumKm) / bounds.stepKm;
  const next = direction === 'increment' ? Math.floor(steps) + 1 : Math.ceil(steps) - 1;
  return clampToScale(bounds.minimumKm + next * bounds.stepKm, bounds);
}

/** Onto the track: 0 at its start, 1 at its end, and nothing outside either. */
function clampToTrack(fraction: number): number {
  return Math.min(Math.max(fraction, 0), 1);
}

/** The nearest step boundary, held inside the scale. */
function snapped(radiusKm: number, bounds: SearchRadiusBounds): number {
  const steps = Math.round((radiusKm - bounds.minimumKm) / bounds.stepKm);
  return clampToScale(bounds.minimumKm + steps * bounds.stepKm, bounds);
}

function clampToScale(radiusKm: number, bounds: SearchRadiusBounds): number {
  return Math.min(Math.max(radiusKm, bounds.minimumKm), topOfScale(bounds));
}
