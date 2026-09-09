/**
 * `WIDEST_HANDLE_EM`, derived rather than chosen — and the budget it feeds.
 *
 * The handle line gives way by **dropping whole names**, which needs an answer to *how many
 * characters fit* on a screen no module can measure. Pick that by eye and it is a guess that
 * fails on one handle, on one phone, as an ellipsis inside somebody's nickname that nobody who
 * built the row will ever see. So it is **measured**: this file reads the advance widths out of
 * the Archivo Bold that ships in the bundle and checks that no character a handle can be
 * written in is wider than the share the row budgets for.
 *
 * **What makes it go red:** an Archivo release that redraws the letters, a different type role
 * on the handle line, or a repertoire that grows a wider character. Every one of those is a real
 * change to the answer, and none of them announces itself at 13pt.
 *
 * Font metrics come from `test-support/fontMetrics.ts`, which is where the tab bar's `cmap`
 * walk moved when a second surface needed the same measurement.
 */

import { theme } from '@/shared/ui';
import { NARROWEST_SCREEN, readFace, widthOf } from '@/test-support/fontMetrics';

import {
  FACE_OVERLAP,
  ROW_FACE,
  WIDEST_HANDLE_EM,
  faceClusterWidth,
  handleBudget,
} from './challengeRowGeometry';

/** The face the handle line is drawn in, built from the role's own family rather than named. */
const archivoBold = readFace(`@expo-google-fonts/archivo/${theme.type.cardTitle.fontFamily}.ttf`);

/**
 * Everything a nickname can be written in: printable ASCII, and the nine Polish letters this
 * platform's own players write their handles with.
 */
const REPERTOIRE = [
  ...Array.from({ length: 0x7f - 0x20 }, (_, at) => String.fromCodePoint(0x20 + at)),
  ...'ĄĆĘŁŃÓŚŹŻąćęłńóśźż',
];

describe('the widest character a handle may contain', () => {
  it('is drawn by the face the line is actually set in', () => {
    for (const character of REPERTOIRE) {
      expect(archivoBold.draws(character.codePointAt(0) ?? 0)).toBe(true);
    }
  });

  it('is inside the share the budget spends per character', () => {
    const size = theme.type.cardTitle.fontSize;
    const widest = Math.max(...REPERTOIRE.map((c) => widthOf(archivoBold, c, size)));

    expect(widest / size).toBeLessThanOrEqual(WIDEST_HANDLE_EM);
    // And not wildly under it, or the budget is throwing away room it could have spent.
    expect(widest / size).toBeGreaterThan(WIDEST_HANDLE_EM - 0.05);
  });
});

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
