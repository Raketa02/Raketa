/**
 * The swipe row's three rules, held to the numbers a build session could quietly move.
 *
 * **Which touch is a swipe** is the load-bearing one: a list scrolls vertically and a row reveals
 * horizontally, and the same finger begins both. The rule is asked on every move until one answers
 * yes, so a rule that answered yes to a diagonal would take the list's scroll for a gesture the
 * player did not mean, and one that never answered would leave the control unreachable by touch.
 *
 * The other two are where the card sits under the finger and where it settles when the finger
 * lifts. Both are asserted against the served width rather than against a copy of it, because the
 * width is the theme's to change and the rules are not.
 */

import { claimsTheSwipe, settlesTo, shifted } from './swipeRowGeometry';
import { theme } from './theme';

const { reveal: REVEAL, intent: INTENT } = theme.size.swipeRow;

describe('which touch is a swipe', () => {
  it('claims a move to the left once it has travelled the intent distance', () => {
    expect(claimsTheSwipe({ dx: -INTENT, dy: 0 }, 'closed')).toBe(true);
    expect(claimsTheSwipe({ dx: -INTENT - 20, dy: 3 }, 'closed')).toBe(true);
  });

  it('claims nothing short of the intent distance, so a tap stays a tap', () => {
    expect(claimsTheSwipe({ dx: -INTENT + 1, dy: 0 }, 'closed')).toBe(false);
    expect(claimsTheSwipe({ dx: 0, dy: 0 }, 'closed')).toBe(false);
  });

  /** The list's own gesture: down the screen, with the sideways drift every thumb has. */
  it('leaves a move down or up the screen to the list, whatever it drifts sideways', () => {
    expect(claimsTheSwipe({ dx: -INTENT, dy: INTENT + 1 }, 'closed')).toBe(false);
    expect(claimsTheSwipe({ dx: -INTENT, dy: -(INTENT + 1) }, 'closed')).toBe(false);
    expect(claimsTheSwipe({ dx: -4, dy: 40 }, 'closed')).toBe(false);
  });

  it('claims a diagonal only while it is more across than down', () => {
    expect(claimsTheSwipe({ dx: -30, dy: 29 }, 'closed')).toBe(true);
    expect(claimsTheSwipe({ dx: -30, dy: 30 }, 'closed')).toBe(false);
  });

  /** A closed row has nothing to the right of it, so a move that way is not a swipe on it. */
  it('leaves a move to the right alone while the row is closed', () => {
    expect(claimsTheSwipe({ dx: INTENT + 20, dy: 0 }, 'closed')).toBe(false);
  });

  /** A revealed row closes by the opposite move, so that one is a swipe on it too. */
  it('claims a move to the right once the row is revealed', () => {
    expect(claimsTheSwipe({ dx: INTENT, dy: 0 }, 'revealed')).toBe(true);
    expect(claimsTheSwipe({ dx: -INTENT, dy: 0 }, 'revealed')).toBe(true);
  });
});

describe('where the card sits under the finger', () => {
  it('follows the finger left, as far as the control behind it is wide', () => {
    expect(shifted(-30)).toBe(-30);
    expect(shifted(-REVEAL)).toBe(-REVEAL);
    expect(shifted(-REVEAL - 50)).toBe(-REVEAL);
  });

  it('never goes right of where it started', () => {
    expect(shifted(0)).toBe(0);
    expect(shifted(25)).toBe(0);
  });
});

describe('where the card settles when the finger lifts', () => {
  it('reveals once it has been dragged half the control’s width', () => {
    expect(settlesTo(-REVEAL / 2)).toBe('revealed');
    expect(settlesTo(-REVEAL)).toBe('revealed');
  });

  it('closes short of that, so a nudge reveals nothing', () => {
    expect(settlesTo(-REVEAL / 2 + 1)).toBe('closed');
    expect(settlesTo(0)).toBe('closed');
    expect(settlesTo(15)).toBe('closed');
  });
});
