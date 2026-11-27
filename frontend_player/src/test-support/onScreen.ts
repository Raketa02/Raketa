/**
 * **Home laid out and scrolled as a phone would** — the layout and scroll events a device reports on
 * its own, which the router harness never fires (#804; the Home rows mechanics §9.2).
 *
 * A line's cards are on screen by geometry: where the page is scrolled to and how tall it is, where
 * FOR YOU stands on it, where the line stands in FOR YOU and its fold under the line's header (#820),
 * where the rail stands in the fold, and where the rail is scrolled to. Under the harness nothing is
 * laid out, so nothing is ever on screen until a suite says where it is.
 *
 * The phone is the harness's window — `Dimensions`' width, so a rail's cards are the width the rail
 * draws them — and the page a fixed height below the header.
 */

import { act, fireEvent, screen, within } from 'expo-router/testing-library';
import { Dimensions, ScrollView } from 'react-native';

import { theme } from '@/shared/ui';

import { PLAYERS_BAR } from './tabBarReach';

/** `POST /on-screen` — the cards that came on screen in one row (#796). */
export const ON_SCREEN_PATH = '/api/v1/on-screen';

/** How tall Home's page shows between the header and the tab bar. */
export const PAGE_HEIGHT = 700;
/**
 * How tall its scroller measures — the page and the strip under the bar, since the bar floats over
 * the page's foot (#881). What shows is this less the bar's reach: `PAGE_HEIGHT`.
 */
const SCROLLER_HEIGHT = PAGE_HEIGHT + PLAYERS_BAR;
/** Where a line's rail stands under the line's top — its header's height, the fold's place. */
const RAIL_TOP = 30;
/** How tall a rail is — its cards' height. */
const RAIL_HEIGHT = 240;

const layout = (x: number, y: number, width: number, height: number) => ({
  nativeEvent: { layout: { x, y, width, height } },
});

/** A drawn node, as a query hands it back. */
type Node = ReturnType<typeof screen.getByTestId>;

/** The page a line stands on — the nearest scroller above it that is not a rail. */
function pageOf(line: Node): Node {
  let node = line.parent;
  while (node !== null && !(node.type === ScrollView && node.props.horizontal !== true)) {
    node = node.parent;
  }
  if (node === null) throw new Error('This line stands on no page.');
  return node;
}

/** The line's rail — its sideways scroller, drawn only while the line is open. */
function railOf(lineTestId: string): Node {
  const rail = within(screen.getByTestId(lineTestId))
    .UNSAFE_getAllByType(ScrollView)
    .find((node) => node.props.horizontal === true);
  if (rail === undefined) throw new Error(`The line ${lineTestId} draws no rail — is it open?`);
  return rail;
}

/**
 * **Home's parts laid out at the column's top** (#871): the skeleton's ground and each part's reveal
 * stand between the page's column and its sections, and each passes on where it stands on the page
 * — so a suite that lays a section out on the page lays these out too, at the top, which keeps a
 * section's own `y` its place on the page.
 */
export function layOutHomeParts(): void {
  const width = Dimensions.get('window').width;
  act(() => {
    for (const testId of ['home-parts', 'home-your-things', 'home-for-you']) {
      fireEvent(screen.getByTestId(testId), 'layout', layout(0, 0, width, 4000));
    }
  });
}

/**
 * **Lays Home out**: the page `PAGE_HEIGHT` tall, FOR YOU at the column's top, and each line named at
 * the top given — far enough down, and it is under the fold until the page is scrolled to it. An open
 * line's fold and rail are laid out under its header; a closed line has neither.
 */
export function layOutHome(lines: Readonly<Record<string, number>>): void {
  const width = Dimensions.get('window').width;
  // A rail bleeds to the line's inner edge: the column less the line's border each side.
  const inside = width - 2 * theme.size.gutter - 2 * theme.size.foldingLine.border;
  const first = Object.keys(lines)[0];
  if (first === undefined) return;
  layOutHomeParts();
  act(() => {
    fireEvent(pageOf(screen.getByTestId(first)), 'layout', layout(0, 0, width, SCROLLER_HEIGHT));
    fireEvent(screen.getByTestId('for-you'), 'layout', layout(theme.size.gutter, 0, width, 4000));
    for (const [testId, top] of Object.entries(lines)) {
      fireEvent(screen.getByTestId(testId), 'layout', layout(0, top, width, 300));
      const fold = screen.queryByTestId(`${testId}-fold`);
      if (fold === null) continue;
      // The fold stands in the line's clip, inside its border: RAIL_TOP under the line's top.
      fireEvent(
        fold,
        'layout',
        layout(0, RAIL_TOP - theme.size.foldingLine.border, width, RAIL_HEIGHT),
      );
      fireEvent(railOf(testId), 'layout', layout(0, 0, inside, RAIL_HEIGHT));
    }
  });
}

/** Scrolls Home's page so its top is `y` down the content. */
export function scrollHomeTo(lineTestId: string, y: number): void {
  const width = Dimensions.get('window').width;
  act(() => {
    fireEvent.scroll(pageOf(screen.getByTestId(lineTestId)), {
      nativeEvent: {
        contentOffset: { x: 0, y },
        layoutMeasurement: { width, height: SCROLLER_HEIGHT },
        contentSize: { width, height: 4000 },
      },
    });
  });
}

/** Where Home's page is scrolled to put a line's rail wholly on screen, at the page's top. */
export const pageAtRow = (top: number) => top + RAIL_TOP;

/**
 * Scrolls a peeking rail in an open line so its card `at` stands at the rail's start — wholly on
 * screen, the card before it gone and the one after it peeking, under half. A card is the line's
 * share (`lineCardRatio`) of the line's content, not the page's.
 */
export function scrollRowToCard(lineTestId: string, at: number): void {
  const width = Dimensions.get('window').width;
  const { border, pad } = theme.size.foldingLine;
  const content = width - 2 * theme.size.gutter - 2 * (border + pad);
  const step = content * theme.size.lineCardRatio + theme.space.sm;
  act(() => {
    fireEvent.scroll(railOf(lineTestId), {
      nativeEvent: {
        contentOffset: { x: at * step, y: 0 },
        layoutMeasurement: { width, height: RAIL_HEIGHT },
        contentSize: { width: 10 * step, height: RAIL_HEIGHT },
      },
    });
  });
}
