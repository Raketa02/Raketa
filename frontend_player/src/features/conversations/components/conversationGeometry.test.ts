/**
 * The conversation's two budgets — the row's, and the header's over the same face.
 *
 * The character both are measured in is `shared/formatting/handleList.ts`'s and is derived
 * against the real face there. What is checked here is each surface's own furniture: the row
 * keeps **no trailing reserve**, because there is no stripe on a conversation row; the header
 * keeps one for the `Details` control on every room, drawn or not.
 */

import { charactersThatFit } from '@/shared/formatting/handleList';
import { theme } from '@/shared/ui';
import { NARROWEST_SCREEN } from '@/test-support/fontMetrics';

import {
  DETAILS_WIDTH,
  FACE_OVERLAP,
  ROW_FACE,
  faceClusterWidth,
  handleBudget,
  headerHandleBudget,
} from './conversationGeometry';

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
  /** A room draws the members it has, so a two-member doubles room draws one face here. */
  it('is one face wide for one other person, and overlaps every face after it', () => {
    expect(faceClusterWidth(0)).toBe(0);
    expect(faceClusterWidth(1)).toBe(ROW_FACE);
    expect(faceClusterWidth(3)).toBeCloseTo(ROW_FACE * (1 + 2 * (1 - FACE_OVERLAP)), 5);
  });
});

describe('the budget the header spends', () => {
  /**
   * The `Details` control is charged for on **every** room, drawn or not — so a header does not
   * reflow its handles the moment a line-up completes and a game appears.
   */
  it('reserves the Details control whether or not there is a game to open', () => {
    // The signature is the assertion: there is no *has a game* argument to reserve against, so
    // the number cannot move when one appears. What is checked is that it is reserved at all —
    // the header holds fewer characters than the row, over the same face and the same words.
    expect(headerHandleBudget(NARROWEST_SCREEN, 1)).toBeLessThan(handleBudget(NARROWEST_SCREEN, 1));
  });

  it('shrinks as the room grows, because the same cluster is drawn beside the words', () => {
    expect(headerHandleBudget(NARROWEST_SCREEN, 3)).toBeLessThan(
      headerHandleBudget(NARROWEST_SCREEN, 1),
    );
  });

  it('never goes under one character, because a header always names somebody', () => {
    expect(headerHandleBudget(0, 3)).toBe(1);
  });

  /**
   * **Counted in the role the header draws.** The title is `h1`, and until #401 the budget was
   * counted at the rows' `cardTitle` — a line six points smaller — so a header could be told a
   * line fitted that then wrapped onto a second line, which is what the dropping exists to
   * prevent. Re-derived the way the row's own test above re-derives its column, which is this
   * file's precedent for asserting arithmetic.
   */
  it('counts its characters at h1, which is what the title is set in', () => {
    const column =
      NARROWEST_SCREEN -
      2 * theme.size.gutter -
      theme.type.h1.fontSize -
      theme.space.sm -
      faceClusterWidth(1) -
      theme.space.sm -
      DETAILS_WIDTH -
      theme.space.sm;

    expect(headerHandleBudget(NARROWEST_SCREEN, 1)).toBe(charactersThatFit(column, theme.type.h1));
    expect(headerHandleBudget(NARROWEST_SCREEN, 1)).toBeLessThan(charactersThatFit(column));
  });

  /** One face size in this feature: a person is not two sizes two taps apart. */
  it('draws the row’s own face', () => {
    expect(ROW_FACE).toBe(38);
  });
});
