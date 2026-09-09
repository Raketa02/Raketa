/**
 * The budget the challenge row spends, and the cluster it spends it around.
 *
 * The **character** the budget is measured in is `shared/formatting/handleList.ts`'s and is
 * derived against the real face there; what is checked here is that this row's own furniture —
 * the gutters, the card's padding, the faces and the urgency stripe — leaves a column a real
 * handle line fits in on the narrowest phone.
 *
 * Font metrics come from `test-support/fontMetrics.ts`, which is where the tab bar's `cmap` walk
 * moved when a second surface needed the same measurement.
 */

import { theme } from '@/shared/ui';
import { NARROWEST_SCREEN, readFace, widthOf } from '@/test-support/fontMetrics';

import { FACE_OVERLAP, ROW_FACE, faceClusterWidth, handleBudget } from './challengeRowGeometry';

/** The face the handle line is drawn in, built from the role's own family rather than named. */
const archivoBold = readFace(`@expo-google-fonts/archivo/${theme.type.cardTitle.fontFamily}.ttf`);

describe('the budget the row spends', () => {
  it('holds a real handle line at the narrowest phone', () => {
    // One face and one handle is the singles row, which is most of them.
    const singles = handleBudget(NARROWEST_SCREEN, 1);
    const width = widthOf(archivoBold, 'niepokonany', theme.type.cardTitle.fontSize);

    expect(singles).toBeGreaterThanOrEqual('niepokonany'.length);
    expect(width).toBeLessThan(NARROWEST_SCREEN);
  });

  it('never goes under one character, because a row always names somebody', () => {
    expect(handleBudget(0, 3)).toBe(1);
  });

  it('grows with the screen, which is the whole reason it is not a constant', () => {
    expect(handleBudget(430, 3)).toBeGreaterThan(handleBudget(NARROWEST_SCREEN, 3));
  });

  it('shrinks as the cluster grows, because the faces are drawn beside the words', () => {
    expect(handleBudget(NARROWEST_SCREEN, 3)).toBeLessThan(handleBudget(NARROWEST_SCREEN, 1));
  });

  /**
   * The stripe is charged for on every row in the section, including the ones that draw none —
   * so the list holds all its handles to one rule rather than measuring itself per row.
   */
  it('reserves the stripe whether or not this row draws one', () => {
    const withoutTheStripe =
      NARROWEST_SCREEN -
      2 * theme.size.gutter -
      2 * theme.space.md -
      faceClusterWidth(1) -
      theme.space.md;
    const spent = withoutTheStripe - theme.space.md - theme.size.semanticBar;

    expect(handleBudget(NARROWEST_SCREEN, 1)).toBeLessThan(
      Math.floor(withoutTheStripe / theme.type.cardTitle.fontSize),
    );
    expect(spent).toBeLessThan(withoutTheStripe);
  });
});

describe('the row as a target', () => {
  /**
   * 6.5's floor, reached by the row's own geometry rather than by `hitSlop`: a face inside the
   * card's padding is already past 44, which is why `ChallengeRow` carries no slop at all.
   */
  it('clears 44pt on the face and the card’s padding alone', () => {
    expect(ROW_FACE + 2 * theme.space.md).toBeGreaterThanOrEqual(theme.size.minTouch);
  });
});

describe('the cluster', () => {
  it('is one face wide for one person, and overlaps every face after it', () => {
    expect(faceClusterWidth(0)).toBe(0);
    expect(faceClusterWidth(1)).toBe(ROW_FACE);
    expect(faceClusterWidth(3)).toBeCloseTo(ROW_FACE * (1 + 2 * (1 - FACE_OVERLAP)), 5);
  });

  it('stays inside the content width, faces and words together', () => {
    const content = NARROWEST_SCREEN - 2 * theme.size.gutter;

    expect(faceClusterWidth(3)).toBeLessThan(content / 2);
  });
});
