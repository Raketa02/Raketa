/**
 * **Home laid out and scrolled as a phone would** — the layout and scroll events a device reports on
 * its own, which the router harness never fires (#804; the Home rows mechanics §9.2).
 *
 * A row's cards are on screen by geometry: where the page is scrolled to and how tall it is, where
 * the row stands on it, where its rail stands in the row, and where the rail is scrolled to. Under
 * the harness nothing is laid out, so nothing is ever on screen until a suite says where it is.
 *
 * The phone is the harness's window — `Dimensions`' width, so a rail's cards are the width the rail
 * draws them — and the page a fixed height below the header.
 */

import { act, fireEvent, screen, within } from 'expo-router/testing-library';
import { Dimensions, ScrollView } from 'react-native';

import { theme } from '@/shared/ui';

/** `POST /on-screen` — the cards that came on screen in one row (#796). */
export const ON_SCREEN_PATH = '/api/v1/on-screen';

/** How tall Home's page is between the header and the tab bar. */
export const PAGE_HEIGHT = 700;
/** Where a row's rail stands in its section — under the heading. */
const RAIL_TOP = 30;
/** How tall a rail is — its cards' height. */
const RAIL_HEIGHT = 240;

const layout = (x: number, y: number, width: number, height: number) => ({
  nativeEvent: { layout: { x, y, width, height } },
});

/** A drawn node, as a query hands it back. */
type Node = ReturnType<typeof screen.getByTestId>;

/** The page a row stands on — the nearest scroller above it that is not a rail. */
function pageOf(row: Node): Node {
  let node = row.parent;
  while (node !== null && !(node.type === ScrollView && node.props.horizontal !== true)) {
    node = node.parent;
  }
  if (node === null) throw new Error('This row stands on no page.');
  return node;
}

/** The row's rail — its sideways scroller. */
function railOf(rowTestId: string): Node {
  const rail = within(screen.getByTestId(rowTestId))
    .UNSAFE_getAllByType(ScrollView)
    .find((node) => node.props.horizontal === true);
  if (rail === undefined) throw new Error(`The row ${rowTestId} draws no rail.`);
  return rail;
}

/**
 * **Lays Home out**: the page `PAGE_HEIGHT` tall, and each row named at the top given — far enough
 * down, and it is under the fold until the page is scrolled to it.
 */
export function layOutHome(rows: Readonly<Record<string, number>>): void {
  const width = Dimensions.get('window').width;
  const first = Object.keys(rows)[0];
  if (first === undefined) return;
  act(() => {
    fireEvent(pageOf(screen.getByTestId(first)), 'layout', layout(0, 0, width, PAGE_HEIGHT));
    for (const [testId, top] of Object.entries(rows)) {
      fireEvent(screen.getByTestId(testId), 'layout', layout(theme.size.gutter, top, width, 300));
      fireEvent(railOf(testId), 'layout', layout(-theme.size.gutter, RAIL_TOP, width, RAIL_HEIGHT));
    }
  });
}

/** Scrolls Home's page so its top is `y` down the content. */
export function scrollHomeTo(rowTestId: string, y: number): void {
  const width = Dimensions.get('window').width;
  act(() => {
    fireEvent.scroll(pageOf(screen.getByTestId(rowTestId)), {
      nativeEvent: {
        contentOffset: { x: 0, y },
        layoutMeasurement: { width, height: PAGE_HEIGHT },
        contentSize: { width, height: 4000 },
      },
    });
  });
}

/** Where Home's page is scrolled to put a row's rail wholly on screen, at the page's top. */
export const pageAtRow = (top: number) => top + RAIL_TOP;

/**
 * Scrolls a peeking rail so its card `at` stands at the rail's start — wholly on screen, the card
 * before it gone and the one after it peeking, under half.
 */
export function scrollRowToCard(rowTestId: string, at: number): void {
  const width = Dimensions.get('window').width;
  const step = (width - 2 * theme.size.gutter) * theme.size.railCardRatio + theme.space.sm;
  act(() => {
    fireEvent.scroll(railOf(rowTestId), {
      nativeEvent: {
        contentOffset: { x: at * step, y: 0 },
        layoutMeasurement: { width, height: RAIL_HEIGHT },
        contentSize: { width: 10 * step, height: RAIL_HEIGHT },
      },
    });
  });
}
