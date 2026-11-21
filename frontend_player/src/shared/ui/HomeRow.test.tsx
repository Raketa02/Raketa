/**
 * **The Home row frame** — one heading and one rail, for every row in Needs your answer and *Your
 * games*, and the rail FOR YOU's open lines draw on ([#798](https://github.com/Raketa02/Raketa/issues/798),
 * [#820](https://github.com/Raketa02/Raketa/issues/820); the Home rows screens §2).
 *
 * The rows that sit on it keep their own tests; they say what each row does, and the geometry the rows
 * used to copy is held here, once: the heading, the bleed, the gap, every rail's widths and the paging
 * rail's snap and dots, a rail inside a folding line's bounds, and a rail that is never remounted, so
 * it keeps its scroll position. *See all ›* and Top 10's pill left the heading for the line's footer
 * (`FoldingLine.test.tsx`). That nothing moved on a device is a look, owed.
 */

import { act, fireEvent, render, screen } from '@testing-library/react-native';
import {
  Dimensions,
  ScrollView,
  StyleSheet,
  View,
  type TextStyle,
  type ViewStyle,
} from 'react-native';

import {
  HomeRow,
  HomeRowRail,
  RailBoundsContext,
  RailDrawsAll,
  cardsDrawnFirst,
  type HomeRowProps,
  type HomeRowRailProps,
} from './HomeRow';
import { PageOnScreen, followable, type Span } from './onScreen';
import { theme } from './theme';

/** Content width — the screen less the gutter each side (Part 4). */
const content = () => Dimensions.get('window').width - 2 * theme.size.gutter;

/** A rail of `count` cards, each a box at the width the rail hands it. */
function Row({
  count,
  heading = 'Friend requests · 2',
  ...rest
}: { readonly count: number } & Partial<Omit<HomeRowProps, 'children'>> &
  Pick<HomeRowRailProps<number>, 'geometry' | 'snap' | 'dotsAlone'>) {
  const { geometry, snap, dotsAlone, ...row } = rest;
  return (
    <HomeRow heading={heading} testID="row" {...row}>
      <HomeRowRail
        cards={Array.from({ length: count }, (_, at) => at)}
        {...(geometry === undefined ? {} : { geometry })}
        {...(snap === undefined ? {} : { snap })}
        {...(dotsAlone === undefined ? {} : { dotsAlone })}
      >
        {(at, width) => <View key={at} testID={`card-${at}`} style={{ width }} />}
      </HomeRowRail>
    </HomeRow>
  );
}

const flat = (style: unknown) => StyleSheet.flatten(style as ViewStyle);
const widthOf = (testID: string) => flat(screen.getByTestId(testID).props.style).width;
const rail = () => screen.UNSAFE_getByType(ScrollView);

describe('the Home row frame', () => {
  describe('the heading', () => {
    /** 3.3 as amended: a section heading is `eyebrow` / `muted` / uppercase, as Home's rows draw it. */
    it('is the eyebrow, uppercase in muted, and the header the row is named by', () => {
      render(<Row count={2} />);

      const heading = screen.getByRole('header', { name: 'Friend requests · 2' });
      expect(StyleSheet.flatten(heading.props.style as TextStyle)).toMatchObject({
        ...theme.type.eyebrow,
        color: theme.color.muted,
        textTransform: 'uppercase',
      });
    });

    it('stands `space.lg` under the row above, and `space.sm` over its rail', () => {
      render(<Row count={2} />);

      expect(flat(screen.getByTestId('row').props.style)).toMatchObject({
        marginTop: theme.space.lg,
        gap: theme.space.sm,
      });
    });
  });

  describe('the peeking rail', () => {
    /** 7.7: the next card showing by about a quarter is the whole affordance. */
    it('draws each card at 0.74 of the content width, so the next one peeks', () => {
      render(<Row count={3} />);

      expect(widthOf('card-0')).toBeCloseTo(content() * theme.size.railCardRatio);
      expect(widthOf('card-2')).toBeCloseTo(content() * theme.size.railCardRatio);
    });

    it('draws a lone card at the content width — there is nothing to peek at', () => {
      render(<Row count={1} />);

      expect(widthOf('card-0')).toBe(content());
    });

    /** Part 8's Strip: the negative margin bleeds the rail while its cards keep to the gutter. */
    it('bleeds to the screen edge, its cards 9 apart on the gutter', () => {
      render(<Row count={2} />);

      expect(flat(rail().props.style)).toMatchObject({ marginHorizontal: -theme.size.gutter });
      expect(flat(rail().props.contentContainerStyle)).toMatchObject({
        paddingHorizontal: theme.size.gutter,
        gap: theme.space.sm,
      });
      expect(rail().props.showsHorizontalScrollIndicator).toBe(false);
    });

    it('scrolls freely, unless the row asks it to snap a card at a time', () => {
      render(<Row count={2} />);
      expect(rail().props.snapToInterval).toBeUndefined();

      screen.rerender(<Row count={2} snap />);
      expect(rail().props.snapToInterval).toBeCloseTo(
        content() * theme.size.railCardRatio + theme.space.sm,
      );
      expect(rail().props.decelerationRate).toBe('fast');
    });

    it('draws no dots — the peek is the affordance', () => {
      render(<Row count={3} />);

      expect(screen.queryByTestId('pager-dots', { includeHiddenElements: true })).toBeNull();
    });
  });

  /** Needs your answer's request and ask tiles (#816; home refactor 2): wider, the next one peeking. */
  describe('the wide rail', () => {
    it('draws each card at the request card’s share of the content width, so the next one peeks', () => {
      render(<Row count={3} geometry="wide" />);

      expect(widthOf('card-0')).toBeCloseTo(content() * theme.size.requestCardRatio);
      expect(widthOf('card-2')).toBeCloseTo(content() * theme.size.requestCardRatio);
      expect(theme.size.requestCardRatio).toBeGreaterThan(theme.size.railCardRatio);
    });

    it('draws a lone card at the content width — there is nothing to peek at', () => {
      render(<Row count={1} geometry="wide" />);

      expect(widthOf('card-0')).toBe(content());
    });

    /** So a tile's buttons, held at its foot, sit level with the next tile's (Q3). */
    it('stands every card as tall as the tallest', () => {
      render(<Row count={2} geometry="wide" />);

      expect(flat(rail().props.contentContainerStyle)).toMatchObject({ alignItems: 'stretch' });
    });

    it('scrolls freely and draws no dots', () => {
      render(<Row count={3} geometry="wide" />);

      expect(rail().props.snapToInterval).toBeUndefined();
      expect(screen.queryByTestId('pager-dots', { includeHiddenElements: true })).toBeNull();
    });
  });

  /** New in Raketa's portrait tiles (#801; home rows 17): narrow, several on screen, the last cut. */
  describe('the tiles rail', () => {
    it('draws each tile at its share of the content width — a lone one too', () => {
      render(<Row count={3} geometry="tiles" />);
      expect(widthOf('card-0')).toBeCloseTo(content() * theme.size.portraitTile.railRatio);

      screen.rerender(<Row count={1} geometry="tiles" />);
      expect(widthOf('card-0')).toBeCloseTo(content() * theme.size.portraitTile.railRatio);
    });

    it('scrolls freely and draws no dots', () => {
      render(<Row count={4} geometry="tiles" />);

      expect(rail().props.snapToInterval).toBeUndefined();
      expect(screen.queryByTestId('pager-dots', { includeHiddenElements: true })).toBeNull();
    });
  });

  describe('the numbered rail', () => {
    /** Top 10 (#805): each card narrower than a tile, its numeral standing beside it. */
    it('hands each card its share of the content width — a lone one too', () => {
      render(<Row count={3} geometry="numbered" />);
      expect(widthOf('card-0')).toBeCloseTo(content() * theme.size.topTen.railRatio);

      screen.rerender(<Row count={1} geometry="numbered" />);
      expect(widthOf('card-0')).toBeCloseTo(content() * theme.size.topTen.railRatio);
    });

    it('scrolls freely and draws no dots', () => {
      render(<Row count={4} geometry="numbered" />);

      expect(rail().props.snapToInterval).toBeUndefined();
      expect(screen.queryByTestId('pager-dots', { includeHiddenElements: true })).toBeNull();
    });
  });

  describe('the paging rail', () => {
    /** 7.7: a card that needs the width takes it, and takes the dots always. */
    it('draws every card at the content width and snaps one at a time', () => {
      render(<Row count={3} geometry="paging" />);

      expect(widthOf('card-0')).toBe(content());
      expect(rail().props.snapToInterval).toBe(content() + theme.space.sm);
      expect(rail().props.decelerationRate).toBe('fast');
    });

    /** 7.18: the dots track the scroll — a page indicator that did not move is a picture. */
    it('moves its dots with the card on screen', () => {
      render(<Row count={3} geometry="paging" />);
      const dots = () =>
        screen.getByTestId('pager-dots', { includeHiddenElements: true }).children as {
          props: { style: unknown };
        }[];
      const current = () =>
        dots().findIndex((dot) => flat(dot.props.style).width === theme.size.pagerDotActive);

      expect(current()).toBe(0);
      fireEvent.scroll(rail(), {
        nativeEvent: { contentOffset: { x: 2 * (content() + theme.space.sm), y: 0 } },
      });
      expect(current()).toBe(2);
    });

    const dotsDrawn = () => screen.queryByTestId('pager-dots', { includeHiddenElements: true });

    /** 7.18: a rail of one draws its one dot — the affordance before a second card arrives. */
    it('draws one dot for a lone card', () => {
      render(<Row count={1} geometry="paging" />);
      expect(dotsDrawn()).not.toBeNull();
    });

    /** 7.18 as amended (#817, Q46): Needs your answer's FRIENDS GAME draws its dots from two. */
    it('draws its dots from two for a row that asks so', () => {
      render(<Row count={1} geometry="paging" dotsAlone={false} />);
      expect(dotsDrawn()).toBeNull();

      screen.rerender(<Row count={2} geometry="paging" dotsAlone={false} />);
      expect(dotsDrawn()).not.toBeNull();
    });
  });

  /**
   * **Inside a folding line** (#820): a tile's share is of the line's content, the rail bleeds to the
   * line's inner edge, and every rail settles on its tiles' edges (the brief).
   */
  describe('inside a folding line', () => {
    const LINE = { content: 300, bleed: 15, snaps: true } as const;
    const inLine = (geometry?: 'tiles' | 'numbered', itemWidth?: (card: number) => number) =>
      render(
        <RailBoundsContext.Provider value={LINE}>
          <HomeRowRail
            cards={[0, 1, 2]}
            {...(geometry === undefined ? {} : { geometry })}
            {...(itemWidth === undefined ? {} : { itemWidth })}
          >
            {(at, width) => <View key={at} testID={`card-${at}`} style={{ width }} />}
          </HomeRowRail>
        </RailBoundsContext.Provider>,
      );

    it('takes its shares of the line’s content, and bleeds to its inner edge', () => {
      inLine();

      expect(widthOf('card-0')).toBeCloseTo(300 * theme.size.railCardRatio);
      expect(flat(rail().props.style)).toMatchObject({ marginHorizontal: -15 });
      expect(flat(rail().props.contentContainerStyle)).toMatchObject({ paddingHorizontal: 15 });
    });

    it('snaps to its cards’ edges, a peeking rail and a tiles rail alike', () => {
      inLine();
      expect(rail().props.snapToInterval).toBeCloseTo(300 * theme.size.railCardRatio + 9);
      expect(rail().props.decelerationRate).toBe('fast');

      screen.rerender(
        <RailBoundsContext.Provider value={LINE}>
          <HomeRowRail cards={[0, 1, 2]} geometry="tiles">
            {(at, width) => <View key={at} testID={`card-${at}`} style={{ width }} />}
          </HomeRowRail>
        </RailBoundsContext.Provider>,
      );
      expect(rail().props.snapToInterval).toBeCloseTo(300 * theme.size.portraitTile.railRatio + 9);
    });

    /** Top 10's numeral stands beside its card, so an item is wider than the width handed (#805). */
    it('steps by an item’s width when the row says it is wider than its card', () => {
      inLine('numbered', (card) => card + 40);

      expect(widthOf('card-0')).toBeCloseTo(300 * theme.size.topTen.railRatio);
      expect(rail().props.snapToInterval).toBeCloseTo(300 * theme.size.topTen.railRatio + 40 + 9);
    });
  });

  /**
   * **Scroll position must survive a re-render** (Part 8): in React Native that is never remounting
   * the rail. A rail swapped for a new one starts again at its first card — the bug a row whose
   * cards come and go, or whose heading counts them, would otherwise ship.
   */
  it('keeps the same rail, and so its scroll position, across a re-render', () => {
    render(<Row count={2} />);
    const first = rail();

    screen.rerender(<Row count={3} heading="Friend requests · 3" />);
    expect(rail()).toBe(first);

    screen.rerender(<Row count={1} heading="Friend requests · 1" />);
    expect(rail()).toBe(first);
  });
});

/**
 * **A rail that watches what is on screen** (#804) — the page's band handed in as a page would, the
 * section and the rail laid out as a device reports them: the section 1000 down the page, the rail 30
 * into it and 240 tall, the phone's width wide.
 */
describe('a rail told what is on screen', () => {
  const width = () => Dimensions.get('window').width;
  const step = () => content() * theme.size.railCardRatio + theme.space.sm;
  const layout = (y: number, height: number) => ({
    nativeEvent: { layout: { x: 0, y, width: width(), height } },
  });

  function watching(page: ReturnType<typeof followable<Span>> | undefined, geometry?: 'paging') {
    const told: number[][] = [];
    const row = (
      <HomeRow heading="Same competitive level players" testID="row">
        <HomeRowRail
          cards={[0, 1, 2, 3]}
          {...(geometry === undefined ? {} : { geometry })}
          onScreen={(cards) => told.push([...cards])}
        >
          {(at, cardWidth) => <View key={at} testID={`card-${at}`} style={{ width: cardWidth }} />}
        </HomeRowRail>
      </HomeRow>
    );
    render(
      page === undefined ? row : <PageOnScreen.Provider value={page}>{row}</PageOnScreen.Provider>,
    );
    act(() => {
      fireEvent(screen.getByTestId('row'), 'layout', layout(1000, 300));
      fireEvent(rail(), 'layout', layout(30, 240));
    });
    return told;
  }

  const scrollRail = (x: number) =>
    act(() => {
      fireEvent.scroll(rail(), { nativeEvent: { contentOffset: { x, y: 0 } } });
    });

  it('says nothing while the page is below the row, and the cards in view once it reaches it', () => {
    const page = followable<Span>();
    const told = watching(page);
    act(() => page.set({ from: 0, size: 700 }));
    expect(told).toEqual([]);

    act(() => page.set({ from: 1030, size: 700 }));
    expect(told).toEqual([[0]]);
  });

  it('says the card the rail is scrolled to, with the page where it was', () => {
    const page = followable<Span>();
    const told = watching(page);
    act(() => page.set({ from: 1030, size: 700 }));

    scrollRail(2 * step());
    expect(told.at(-1)).toEqual([2]);
  });

  it('says nothing while the page is out of view, and what is in view when it is back', () => {
    const page = followable<Span>();
    const told = watching(page);
    scrollRail(step());
    expect(told).toEqual([]);

    act(() => page.set({ from: 1030, size: 700 }));
    expect(told).toEqual([[1]]);
  });

  it('is never measured on a page that does not watch', () => {
    const told = watching(undefined);
    scrollRail(step());

    expect(told).toEqual([]);
  });

  it('still moves a paging rail’s dots', () => {
    const page = followable<Span>();
    const told = watching(page, 'paging');
    act(() => page.set({ from: 1030, size: 700 }));
    const dots = () =>
      screen.getByTestId('pager-dots', { includeHiddenElements: true }).children as {
        props: { style: unknown };
      }[];
    const current = () =>
      dots().findIndex((dot) => flat(dot.props.style).width === theme.size.pagerDotActive);

    scrollRail(2 * (content() + theme.space.sm));
    expect(current()).toBe(2);
    expect(told.at(-1)).toEqual([2]);
  });
});

/**
 * **The first frame draws what can be seen, and the rest a moment later** — Home stands six rails of
 * up to ten cards, and drawing every card at once was most of what Home cost on a device.
 */
describe('what a rail draws first', () => {
  const screenWidth = () => Dimensions.get('window').width;
  const peekingStep = () => content() * theme.size.railCardRatio + theme.space.sm;

  it('is every card that can be on screen and the one past its edge', () => {
    // A peeking card is under three quarters of the content: one whole, the next peeking, one more.
    expect(cardsDrawnFirst({ count: 10, screen: 390, step: 0.74 * 360 + 9 })).toBe(3);
    // Top 10's narrow cards: four can stand on the screen at once.
    expect(cardsDrawnFirst({ count: 10, screen: 390, step: 0.29 * 360 + 9 })).toBe(5);
  });

  it('is all of them on a rail of fewer', () => {
    expect(cardsDrawnFirst({ count: 2, screen: 390, step: 0.74 * 360 + 9 })).toBe(2);
    expect(cardsDrawnFirst({ count: 0, screen: 390, step: 0.74 * 360 + 9 })).toBe(0);
  });

  it('draws those first, then every card — at the width it hands, in its place', () => {
    const drawing: number[] = [];
    const first = cardsDrawnFirst({ count: 10, screen: screenWidth(), step: peekingStep() });
    render(
      <HomeRowRail cards={Array.from({ length: 10 }, (_, at) => at)}>
        {(at, width) => {
          drawing.push(at);
          return <View key={at} testID={`card-${at}`} style={{ width }} />;
        }}
      </HomeRowRail>,
    );

    expect(first).toBeLessThan(10);
    // The first frame stops at the screen's edge; the next starts over from the first card.
    expect(drawing.slice(0, first)).toEqual(Array.from({ length: first }, (_, at) => at));
    expect(drawing[first]).toBe(0);
    for (let at = 0; at < 10; at += 1) {
      expect(widthOf(`card-${at}`)).toBeCloseTo(content() * theme.size.railCardRatio);
    }
  });
});

/**
 * **A rail draws a card again only when that card changes** (2026-11-21). A rail re-renders on its own
 * account — its folding line opening and closing hands it a page and takes it away — and it used to
 * draw every card anew each time: on a Galaxy A32, ten cards' posters, bars and friend buttons on
 * every open and every close of a FOR YOU line.
 */
describe('what a rail draws again', () => {
  const drawnTimes = new Map<number, number>();
  function Card({ at, width }: { readonly at: number; readonly width: number }) {
    drawnTimes.set(at, (drawnTimes.get(at) ?? 0) + 1);
    return <View testID={`card-${at}`} style={{ width }} />;
  }
  const drawCard = (at: number, width: number) => <Card key={at} at={at} width={width} />;
  const CARDS = [0, 1, 2];

  beforeEach(() => drawnTimes.clear());

  function railOn(page: ReturnType<typeof followable<Span>>, draw = drawCard) {
    return (
      <PageOnScreen.Provider value={page}>
        <HomeRowRail cards={CARDS} onScreen={() => undefined}>
          {draw}
        </HomeRowRail>
      </PageOnScreen.Provider>
    );
  }

  it('draws no card again when the rail re-renders on its own account', () => {
    render(railOn(followable<Span>()));
    const before = CARDS.map((at) => drawnTimes.get(at));

    // The page the rail is on comes and goes — its line opening, closing.
    screen.rerender(railOn(followable<Span>()));
    screen.rerender(railOn(followable<Span>()));

    expect(CARDS.map((at) => drawnTimes.get(at))).toEqual(before);
  });

  it('draws every card again when the row draws them another way — nothing is left behind', () => {
    const page = followable<Span>();
    render(railOn(page));
    const before = CARDS.map((at) => drawnTimes.get(at) ?? 0);

    screen.rerender(railOn(page, (at, width) => <Card key={at} at={at} width={width} />));

    expect(CARDS.map((at) => drawnTimes.get(at))).toEqual(before.map((times) => times + 1));
  });

  it('keeps each card where it was when the cards change order', () => {
    const page = followable<Span>();
    render(railOn(page));
    const first = screen.getByTestId('card-2');

    screen.rerender(
      <PageOnScreen.Provider value={page}>
        <HomeRowRail cards={[2, 0, 1]} onScreen={() => undefined}>
          {drawCard}
        </HomeRowRail>
      </PageOnScreen.Provider>,
    );

    // Keyed by the row's own key, as before: the same card, not the one at its old place.
    expect(screen.getByTestId('card-2')).toBe(first);
  });
});

/**
 * **In a folding line, the cards past the screen's edge wait for the unfold** (2026-11-21): drawn
 * during it, they held the JavaScript thread through the whole motion on a Galaxy A32.
 */
describe('a rail in a folding line', () => {
  const count = 10;
  const screenWidth = () => Dimensions.get('window').width;
  const peekingStep = () => content() * theme.size.railCardRatio + theme.space.sm;
  const drawnCards = () => screen.queryAllByTestId(/^card-/).length;

  function railIn({ unfolded }: { readonly unfolded: boolean }) {
    return (
      <RailDrawsAll.Provider value={unfolded}>
        <HomeRowRail cards={Array.from({ length: count }, (_, at) => at)}>
          {(at, width) => <View key={at} testID={`card-${at}`} style={{ width }} />}
        </HomeRowRail>
      </RailDrawsAll.Provider>
    );
  }

  it('draws only what can be on screen while the line unfolds, then every card', () => {
    const first = cardsDrawnFirst({ count, screen: screenWidth(), step: peekingStep() });
    render(railIn({ unfolded: false }));
    expect(drawnCards()).toBe(first);

    screen.rerender(railIn({ unfolded: true }));
    expect(drawnCards()).toBe(count);
  });
});
