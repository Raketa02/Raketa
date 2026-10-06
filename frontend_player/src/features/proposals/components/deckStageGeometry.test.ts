/**
 * The drag's arithmetic, as numbers: which move claims the touch, where the stamp is full and a
 * release commits, which answer a direction is, how far a card turns, and where the cards
 * behind stand.
 */

import { theme } from '@/shared/ui/theme';

import {
  COMMIT,
  STACK,
  claimsTheDrag,
  committed,
  crossedThreshold,
  stackLift,
  stackOpacity,
  stackScale,
  stampOpacity,
  tilt,
  wayOf,
} from './deckStageGeometry';

const { commit, intent, tilt: TILT } = theme.size.deckSwipe;

describe('claiming the touch', () => {
  /** Never on the press: the card is a door to the record on a long press, and a tap has to reach it. */
  it('claims a move that has travelled the intent distance across, either way', () => {
    expect(claimsTheDrag({ dx: intent, dy: 0 })).toBe(true);
    expect(claimsTheDrag({ dx: -intent, dy: 0 })).toBe(true);
    expect(claimsTheDrag({ dx: intent - 1, dy: 0 })).toBe(false);
  });

  /** A drift down the screen is the scroller's, and a tie goes to the gesture worse to steal. */
  it('leaves a move further down than across to the page', () => {
    expect(claimsTheDrag({ dx: intent, dy: intent })).toBe(false);
    expect(claimsTheDrag({ dx: intent + 1, dy: intent })).toBe(true);
  });

  it('reads the swipe row’s intent, because it is the same finger', () => {
    expect(intent).toBe(theme.size.swipeRow.intent);
  });
});

describe('the threshold', () => {
  it('is the mock’s 95, read from the theme', () => {
    expect(COMMIT).toBe(95);
    expect(COMMIT).toBe(commit);
  });

  it('commits in the drag’s direction from the threshold on, and not before', () => {
    expect(committed(commit)).toBe('yes');
    expect(committed(-commit)).toBe('no');
    expect(committed(commit - 1)).toBeUndefined();
    expect(committed(-(commit - 1))).toBeUndefined();
    expect(committed(0)).toBeUndefined();
  });

  it('is crossed at the same point, either way', () => {
    expect(crossedThreshold(commit)).toBe(true);
    expect(crossedThreshold(-commit)).toBe(true);
    expect(crossedThreshold(commit - 1)).toBe(false);
  });

  /** A yes goes right and a pass goes left — the two buttons' own order — and the sign says so. */
  it('gives each answer its way off the stage', () => {
    expect(wayOf('yes')).toBe(1);
    expect(wayOf('no')).toBe(-1);
  });
});

describe('the stamps', () => {
  it('fade in with the drag and are full at the threshold', () => {
    expect(stampOpacity('yes').inputRange).toEqual([0, commit]);
    expect(stampOpacity('yes').outputRange).toEqual([0, 1]);
    expect(stampOpacity('no').inputRange).toEqual([-commit, 0]);
    expect(stampOpacity('no').outputRange).toEqual([1, 0]);
  });
});

describe('the turn', () => {
  it('reaches the full tilt at twice the threshold, in the drag’s direction', () => {
    expect(tilt().inputRange).toEqual([-2 * commit, 0, 2 * commit]);
    expect(tilt().outputRange).toEqual([`-${TILT}deg`, '0deg', `${TILT}deg`]);
  });
});

describe('the stack', () => {
  /** The top card arrives from where the card behind it stood, and comes to rest in its own place. */
  it('draws the top card one step back while it is arriving, and at rest once it has', () => {
    expect(stackLift(0).inputRange).toEqual([0, 1]);
    expect(stackLift(0).outputRange).toEqual([STACK.step, 0]);
    expect(stackScale(0).outputRange).toEqual([1 - STACK.shrink, 1]);
  });

  /** Every card behind comes forward on the same beat — a card at depth two arrives from three. */
  it('draws every card behind one step further back while the top card is arriving', () => {
    expect(stackLift(1).outputRange).toEqual([2 * STACK.step, STACK.step]);
    expect(stackLift(2).outputRange).toEqual([3 * STACK.step, 2 * STACK.step]);
    expect(stackScale(1).outputRange).toEqual([1 - 2 * STACK.shrink, 1 - STACK.shrink]);
    expect(stackScale(2).outputRange).toEqual([1 - 3 * STACK.shrink, 1 - 2 * STACK.shrink]);
  });

  /** #553, Q90: the cards peeking behind fade as well as shrink, on the same beat. */
  it('draws each card behind one fade fainter, and brightens the card coming forward', () => {
    expect(stackOpacity(0).outputRange).toEqual([1 - STACK.fade, 1]);
    expect(stackOpacity(1).outputRange).toEqual([1 - 2 * STACK.fade, 1 - STACK.fade]);
    expect(stackOpacity(2).outputRange).toEqual([1 - 3 * STACK.fade, 1 - 2 * STACK.fade]);
    // The farthest card still shows: 0,4 at rest.
    expect(stackOpacity(2).outputRange[1]).toBeGreaterThan(0);
  });

  it('steps by the small space, so the stack peeks out and does not sprawl', () => {
    expect(STACK.step).toBe(theme.space.sm);
  });
});
