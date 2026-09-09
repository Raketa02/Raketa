/**
 * The conversation row's budget, and the one thing that makes it different from the challenge
 * row's.
 *
 * The character it is measured in is `shared/formatting/handleList.ts`'s and is derived against
 * the real face there. What is checked here is this row's own furniture: the same face and the
 * same cluster, and **no trailing reserve**, because there is no stripe on a conversation row.
 */

import { theme } from '@/shared/ui';
import { NARROWEST_SCREEN } from '@/test-support/fontMetrics';

import { FACE_OVERLAP, ROW_FACE, faceClusterWidth, handleBudget } from './conversationRowGeometry';

describe('the budget the row spends', () => {
  /**
   * The whole of the difference between the two Chats rows. It is asserted as arithmetic rather
   * than against the challenge row's module, because the two are deliberately spelled apart —
   * a test that imported the other one would be the coupling the duplication was chosen over.
   */
  it('keeps nothing for a trailing edge, because nothing is drawn there', () => {
    const column =
      NARROWEST_SCREEN -
      2 * theme.size.gutter -
      2 * theme.space.md -
      faceClusterWidth(1) -
      theme.space.md;

    expect(handleBudget(NARROWEST_SCREEN, 1)).toBe(
      Math.floor(column / (theme.type.cardTitle.fontSize * 1.01)),
    );
  });

  it('never goes under one character, because a row always names somebody', () => {
    expect(handleBudget(0, 3)).toBe(1);
  });

  it('shrinks as the room grows, because the faces are drawn beside the words', () => {
    expect(handleBudget(NARROWEST_SCREEN, 3)).toBeLessThan(handleBudget(NARROWEST_SCREEN, 1));
  });
});

describe('the row as a target', () => {
  /** 6.5's floor, reached by the row's own geometry rather than by `hitSlop`. */
  it('clears 44pt on the face and the card’s padding alone', () => {
    expect(ROW_FACE + 2 * theme.space.md).toBeGreaterThanOrEqual(theme.size.minTouch);
  });
});

describe('the cluster', () => {
  /** A room grows one acceptance at a time, so a two-member doubles room draws one face here. */
  it('is one face wide for one other person, and overlaps every face after it', () => {
    expect(faceClusterWidth(0)).toBe(0);
    expect(faceClusterWidth(1)).toBe(ROW_FACE);
    expect(faceClusterWidth(3)).toBeCloseTo(ROW_FACE * (1 + 2 * (1 - FACE_OVERLAP)), 5);
  });
});
