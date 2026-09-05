/**
 * The one rule over what's at stake, and it is a rule about the **sport**.
 *
 * Three states reach the card and only one of them is a decision. Two are absences the
 * contract already made — for fun, and a pair where somebody holds no rating — and they arrive
 * as no field. The third is the interesting one: the figures are real, the server sent them,
 * and a **doubles** card must not print them, because a win against one named person is not a
 * thing that exists until the other three seats are known
 * ([#312](https://github.com/Raketa02/Raketa/issues/312)).
 */

import { courtSeatCount } from '@/shared/ui';

import { stakeOnACard } from './atStake';
import type { AtStake } from './candidate';
import { isDoubles } from './lineup';

/** `win_delta > 0 > loss_delta` — the server's invariant, and neither figure is ever zero. */
const AT_STAKE: AtStake = { winDelta: 0.08, lossDelta: -0.05 };

describe('what the card may print', () => {
  it('is the pair as served on a court that seats two', () => {
    expect(stakeOnACard({ atStake: AT_STAKE, seats: courtSeatCount('tennis') })).toBe(AT_STAKE);
  });

  it('is nothing on a doubles seat, though the figures are real', () => {
    // A refusal to draw rather than an absence: the server prices the pairing anyway, because
    // a matcher may compare candidates by it.
    expect(stakeOnACard({ atStake: AT_STAKE, seats: courtSeatCount('padel') })).toBeUndefined();
  });

  it('is nothing where the field never crossed, whichever court it is', () => {
    for (const sport of ['tennis', 'padel'] as const) {
      expect(stakeOnACard({ seats: courtSeatCount(sport) })).toBeUndefined();
    }
  });
});

describe('the boundary it is keyed off', () => {
  it('is `isDoubles` and never a second reading of the same seat count', () => {
    // One predicate for the whole feature — the court entry card's wording, the builder's
    // title, the pool's *add* sentence and this rule all read it. A local `seats === 2` here
    // would be a third answer to a settled question.
    for (const sport of ['tennis', 'squash', 'padel', 'badminton'] as const) {
      const drawn = stakeOnACard({ atStake: AT_STAKE, seats: courtSeatCount(sport) });

      expect(drawn === undefined).toBe(isDoubles(courtSeatCount(sport)));
    }
  });

  it('reads the count off the court, so a fifth sport arrives with coordinates', () => {
    // Tennis and squash seat two today, and the day that changes it changes in the drawing
    // that decides it rather than in a list here.
    expect([courtSeatCount('tennis'), courtSeatCount('squash')]).toEqual([2, 2]);
    expect([courtSeatCount('padel'), courtSeatCount('badminton')]).toEqual([4, 4]);
  });
});
