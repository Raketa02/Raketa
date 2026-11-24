/**
 * **Where the tab's menu stands, and what its catcher covers** (9.5, #861; PRD #859) — pure numbers,
 * since Jest has no layout. The menu hangs from the tab that opens it, its start or its end edge on
 * the tab's, and never past the screen's gutters; its catcher covers the whole page but the tab bar,
 * so a press on another tab reaches the bar in one tap.
 */

import { TAB_REACH, catcherAround, tabMenuPlace, type MenuFrame } from './tabMenuGeometry';
import { theme } from './theme';

const GUTTER = theme.size.gutter;
const HANG = theme.size.tabMenu.hang;

/** The user's A32, 384 wide: a group page's tab bar between the gutters, 31 tall, under a header. */
const LAYER = 384;
const BAR: MenuFrame = { x: GUTTER, y: 62, width: LAYER - 2 * GUTTER, height: 31 };
/** Its Friends tab, the last, widened by the chevron's room — the track's 3pt padding inside. */
const FRIENDS: MenuFrame = { x: 252, y: 65, width: 114, height: 25 };
/** Its Games tab, the first. */
const GAMES: MenuFrame = { x: 18, y: 65, width: 76, height: 25 };

describe('the menu’s place', () => {
  it('hangs from the tab’s bottom edge', () => {
    expect(tabMenuPlace(FRIENDS, LAYER, 'end').top).toBe(FRIENDS.y + FRIENDS.height + HANG);
  });

  it('stands its end edge on the tab’s, aligned right — Friends', () => {
    const place = tabMenuPlace(FRIENDS, LAYER, 'end');

    expect(place.right).toBe(LAYER - (FRIENDS.x + FRIENDS.width));
    expect(place.left).toBeUndefined();
  });

  it('stands its start edge on the tab’s, aligned left — Games', () => {
    const place = tabMenuPlace(GAMES, LAYER, 'start');

    expect(place.left).toBe(GAMES.x);
    expect(place.right).toBeUndefined();
  });

  it('never stands past the gutter, at either end', () => {
    expect(tabMenuPlace({ ...GAMES, x: 4 }, LAYER, 'start').left).toBe(GUTTER);
    expect(tabMenuPlace({ ...FRIENDS, x: 280, width: 100 }, LAYER, 'end').right).toBe(GUTTER);
  });

  it('is never wider than the room from its edge to the far gutter', () => {
    const start = tabMenuPlace(GAMES, LAYER, 'start');
    const end = tabMenuPlace(FRIENDS, LAYER, 'end');

    expect(start.maxWidth).toBe(LAYER - GUTTER - GAMES.x);
    expect(end.maxWidth).toBe(LAYER - GUTTER - end.right!);
  });
});

describe('the catcher', () => {
  it('covers the page above the bar, below it, and each side of it — and leaves the bar', () => {
    expect(catcherAround(BAR, 0)).toEqual({
      above: { top: 0, left: 0, right: 0, height: BAR.y },
      below: { top: BAR.y + BAR.height, left: 0, right: 0, bottom: 0 },
      start: { top: BAR.y, height: BAR.height, left: 0, width: BAR.x },
      end: { top: BAR.y, height: BAR.height, left: BAR.x + BAR.width, right: 0 },
    });
  });

  /**
   * A tab answers a touch 9pt past its 25pt box (6.5's slop), 6 past the bar's 3pt padding; the
   * catcher leaves that reach too, above and below the bar, so a tab is still one tap away.
   */
  it('leaves the tabs’ reach above and below the bar, and covers the gutters beside it', () => {
    const reach = TAB_REACH;
    const boxes = catcherAround(BAR, reach);

    expect(boxes.above.height).toBe(BAR.y - reach);
    expect(boxes.below.top).toBe(BAR.y + BAR.height + reach);
    expect(boxes.start).toMatchObject({ top: BAR.y - reach, height: BAR.height + 2 * reach });
    expect(boxes.end).toMatchObject({ top: BAR.y - reach, height: BAR.height + 2 * reach });
  });

  it('takes the tabs’ reach from the segment’s slop, less the track’s padding', () => {
    expect(TAB_REACH).toBe(theme.hit.seg.top - theme.space.xxs);
    expect(theme.hit.seg.bottom).toBe(theme.hit.seg.top);
  });
});
