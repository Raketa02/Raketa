/**
 * **The folding line** — FOR YOU's quiet lines, the section they stand in, and the footer an open one
 * ends with ([#820](https://github.com/Rakieta02/Rakieta/issues/820); ADR-0205 §5, §8, §9; home refactor
 * 3–13). Which line is open, and what each holds, are the shell's and the features' suites'; this is the
 * frame: the look closed and open, what a press reports, what is drawn and for how long, the rail's
 * bounds inside it, where it says it stands on the page, the page asked to show it, and the footer.
 * That it moves as the mocks mean is a look on a device, owed.
 */

import { act, fireEvent, render, screen } from '@testing-library/react-native';
import { useState } from 'react';
import { getAnimatedStyle } from 'react-native-reanimated';
import {
  Animated,
  Dimensions,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  type TextStyle,
  type ViewStyle,
} from 'react-native';

import { footerParts } from '@/test-support/forYou';

import {
  FoldingLine,
  FoldingLineFooter,
  FoldingLines,
  type FoldingLineFooterProps,
} from './FoldingLine';
import { HomeRowRail } from './HomeRow';
import { PageOnScreen, PageReveal, followable, type Span } from './onScreen';
import { ReducedMotionProvider } from './overlay';
import { theme } from './theme';

const flat = (style: unknown) => StyleSheet.flatten(style as ViewStyle);

const TITLE = 'Players at your level';

/** One line, its open state the test's, its header's presses counted. */
function Line({
  open,
  onHeader = jest.fn(),
  footer,
  onTile,
  count,
}: {
  readonly open: boolean;
  readonly onHeader?: () => void;
  readonly footer?: FoldingLineFooterProps;
  readonly onTile?: () => void;
  readonly count?: number;
}) {
  return (
    <FoldingLines heading="For you" folding={!open} testID="for-you">
      <FoldingLine
        title={TITLE}
        count={count}
        open={open}
        onHeader={onHeader}
        footer={footer === undefined ? undefined : <FoldingLineFooter {...footer} />}
        testID="line"
      >
        <Pressable accessibilityRole="button" accessibilityLabel="a tile" onPress={onTile}>
          <Text>the tiles</Text>
        </Pressable>
      </FoldingLine>
    </FoldingLines>
  );
}

const header = () => screen.getByRole('button', { name: TITLE });
const card = () => flat(screen.getByTestId('line').props.style);
/** The border as the UI thread draws it — the press and the open state, with no render. */
const drawnBorder = () =>
  (getAnimatedStyle(screen.getByTestId('line')) as { readonly borderColor?: string }).borderColor;
const chevronTurn = () =>
  // Hidden from a listener: the line's name says open or shut.
  (
    getAnimatedStyle(screen.getByTestId('line-chevron', { includeHiddenElements: true })) as {
      readonly transform?: readonly { readonly rotate?: string }[];
    }
  ).transform?.[0]?.rotate;
/** One frame, for a value set on the UI thread to be drawn. */
const nextFrame = () => act(() => jest.advanceTimersByTime(16));

beforeEach(() => jest.useFakeTimers());
afterEach(() => jest.useRealTimers());

describe('FOR YOU, the section', () => {
  /** 3.3 as amended: a section heading is `eyebrow` / `muted` / uppercase. */
  it('is headed by the eyebrow, uppercase in muted', () => {
    render(<Line open={false} />);

    const heading = screen.getByRole('header', { name: 'For you' });
    expect(StyleSheet.flatten(heading.props.style as TextStyle)).toMatchObject({
      ...theme.type.eyebrow,
      color: theme.color.muted,
      textTransform: 'uppercase',
    });
  });

  it('stands `space.lg` under the row above, its lines `space.sm` apart', () => {
    render(<Line open={false} />);

    expect(flat(screen.getByTestId('for-you').props.style)).toMatchObject({
      marginTop: theme.space.lg,
      gap: theme.space.sm,
    });
  });
});

describe('a closed line', () => {
  /** Home refactor 3, 4: a white card, its title, the chevron — and nothing else. */
  it('is a white card bounded by `line`, its title in h2, and draws nothing it holds', () => {
    render(<Line open={false} />);

    expect(card()).toMatchObject({
      backgroundColor: theme.color.surface,
      borderColor: theme.color.line,
      borderWidth: 1,
      borderRadius: theme.radius.card,
    });
    expect(card().shadowOpacity).toBeUndefined();
    expect(StyleSheet.flatten(screen.getByText(TITLE).props.style as TextStyle)).toMatchObject({
      ...theme.type.h2,
      color: theme.color.ink,
    });
    expect(screen.queryByText('the tiles')).toBeNull();
  });

  /** ADR-0205 §8: a button that says its title and whether it is open. */
  it('is a button named by its title, collapsed, at least 44 tall', () => {
    render(<Line open={false} />);

    expect(header().props.accessibilityState).toEqual({ expanded: false });
    expect(screen.getByRole('button', { name: TITLE, expanded: false })).toBeTruthy();
    expect(flat(header().props.style).minHeight).toBe(theme.size.minTouch);
  });

  it('reports a tap on it — the whole of it is its header', () => {
    const onHeader = jest.fn();
    render(<Line open={false} onHeader={onHeader} />);

    fireEvent.press(header());

    expect(onHeader).toHaveBeenCalledTimes(1);
  });

  /** 6.6: a card pressed is its border in coral — drawn on the UI thread, with no render for it. */
  it('draws its border coral while pressed', () => {
    render(<Line open={false} />);

    fireEvent(header(), 'pressIn');
    nextFrame();
    expect(drawnBorder()).toBe(theme.color.coral);

    fireEvent(header(), 'pressOut');
    nextFrame();
    expect(drawnBorder()).toBe(theme.color.line);
  });

  /**
   * 2026-11-21: nothing moved until the page drew the content — 350 ms after the finger on a Galaxy
   * A32. The header answers on its own, and the page's `open` lands on the same.
   */
  it('answers a press at once — the border ink, the chevron turning — before the page draws anything', () => {
    // The page never answers: whatever moves here, the header moved by itself.
    render(<Line open={false} />);

    fireEvent.press(header());
    nextFrame();
    expect(drawnBorder()).toBe(theme.color.ink);
    act(() => jest.advanceTimersByTime(theme.motion.lineUnfold));
    expect(chevronTurn()).toBe('90deg');
    // What it holds is still the page's to draw.
    expect(screen.queryByText('the tiles')).toBeNull();
  });
});

describe('an open line, pressed', () => {
  it('answers at once too — the border back to `line`, the chevron turning back', () => {
    render(<Line open />);
    nextFrame();
    expect(drawnBorder()).toBe(theme.color.ink);

    fireEvent.press(header());
    nextFrame();
    expect(drawnBorder()).toBe(theme.color.line);
    act(() => jest.advanceTimersByTime(theme.motion.lineFold));
    expect(chevronTurn()).toBe('0deg');
  });
});

describe('its count', () => {
  const pill = () => screen.getByTestId('line-count', { includeHiddenElements: true });
  const figure = () => screen.getByText(/^\d+\+?$/, { includeHiddenElements: true });

  /** What the header draws, left to right — the dev build's pressability overlay left out. */
  const headerParts = () =>
    (header().children as { props: Record<string, unknown> }[]).flatMap((part) => {
      if (part.props.children === TITLE) return ['title'];
      if (part.props.figure !== undefined) return ['count'];
      if (part.props.accessibilityElementsHidden === true) return ['chevron'];
      return [];
    });

  /** Home refactor 3, 4 (#822): the count stands between the title and the chevron. */
  it('stands between the title and the chevron, in a grey pill', () => {
    render(<Line open={false} count={14} />);

    expect(headerParts()).toEqual(['title', 'count', 'chevron']);
    expect(flat(pill().props.style)).toMatchObject({
      backgroundColor: theme.color.line2,
      borderRadius: theme.radius.pill,
      minHeight: theme.size.foldingLine.count,
      paddingHorizontal: theme.space.xs,
    });
    // It grows with its figure under a larger OS text size, rather than clipping it.
    expect(flat(pill().props.style).height).toBeUndefined();
  });

  /** 1.4: a number is mono and tabular; `muted` on `line2` is 4.62. */
  it('writes the served figure in muted mono', () => {
    render(<Line open={false} count={14} />);

    expect(figure().props.children).toBe('14');
    expect(StyleSheet.flatten(figure().props.style as TextStyle)).toMatchObject({
      ...theme.num.tiny,
      ...theme.tabular,
      color: theme.color.muted,
    });
  });

  /** ADR-0205 §6: the server stops at 100, *100 or more*. */
  it('writes 99+ past 99', () => {
    render(<Line open={false} count={100} />);

    expect(figure().props.children).toBe('99+');
  });

  /** ADR-0205 §5: the count pill stays when the line opens. */
  it('stays when the line opens', () => {
    render(<Line open count={14} />);

    expect(figure().props.children).toBe('14');
  });

  /** Top 10 has no count. */
  it('is not drawn without one', () => {
    render(<Line open={false} />);

    expect(screen.queryByTestId('line-count', { includeHiddenElements: true })).toBeNull();
    expect(headerParts()).toEqual(['title', 'chevron']);
  });

  /** #822: *Players at your level, 14, collapsed* — the figure as drawn, in the line's name. */
  it('joins the line’s name, as drawn, and is not read a second time', () => {
    render(<Line open={false} count={100} />);

    expect(screen.getByRole('button', { name: `${TITLE}, 99+`, expanded: false })).toBeTruthy();
    expect(pill().props.accessibilityElementsHidden).toBe(true);
    expect(pill().props.importantForAccessibility).toBe('no-hide-descendants');
  });
});

describe('an open line', () => {
  /** ADR-0205 §5, §9.1: an ink border and the seventh shadow. */
  it('has an ink border and the open line’s shadow, and says it is expanded', () => {
    render(<Line open />);

    expect(card()).toMatchObject({ borderColor: theme.color.ink, ...theme.shadow.openLine });
    expect(header().props.accessibilityState).toEqual({ expanded: true });
  });

  it('draws what it holds under its header', () => {
    render(<Line open />);

    expect(screen.getByText('the tiles')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'a tile' })).toBeTruthy();
  });

  /** Q12: only the header closes it — a tap inside is the content's own. */
  it('reports its header only: a tap inside never reaches it', () => {
    const onHeader = jest.fn();
    const onTile = jest.fn();
    render(<Line open onHeader={onHeader} onTile={onTile} />);

    fireEvent.press(screen.getByRole('button', { name: 'a tile' }));
    expect(onTile).toHaveBeenCalledTimes(1);
    expect(onHeader).not.toHaveBeenCalled();

    fireEvent.press(header());
    expect(onHeader).toHaveBeenCalledTimes(1);
  });
});

describe('closing', () => {
  /** The brief: it folds over a slightly shorter moment, and only then is the content let go. */
  it('folds for `motion.lineFold`, hidden and untouchable, then draws nothing', () => {
    render(<Line open />);

    screen.rerender(<Line open={false} />);
    // Folding away: still drawn, but a closed line is a closed line to a listener and to a finger.
    expect(screen.queryByText('the tiles')).toBeNull();
    expect(screen.getByText('the tiles', { includeHiddenElements: true })).toBeTruthy();

    act(() => jest.advanceTimersByTime(theme.motion.lineFold));
    expect(screen.queryByText('the tiles', { includeHiddenElements: true })).toBeNull();
  });

  /** ADR-0205 §8: under Reduce motion, everything is instant. */
  it('lets the content go at once under Reduce motion', () => {
    const tree = (open: boolean) => (
      <ReducedMotionProvider value>
        <Line open={open} />
      </ReducedMotionProvider>
    );
    render(tree(true));

    screen.rerender(tree(false));

    expect(screen.queryByText('the tiles', { includeHiddenElements: true })).toBeNull();
  });

  it('draws it again when it opens before the fold has run', () => {
    render(<Line open />);
    screen.rerender(<Line open={false} />);

    screen.rerender(<Line open />);
    act(() => jest.advanceTimersByTime(theme.motion.lineFold));

    expect(screen.getByText('the tiles')).toBeTruthy();
  });
});

/**
 * **The content's fade and slide are React Native's `Animated` on the native driver** (2026-11-21).
 * What went wrong under a Reanimated style lives in Fabric's `measure` and Reanimated's native commits,
 * which Jest draws neither of: a press inside a rail the line's content had scrolled was measured where
 * its card stood before the scroll, and dropped at the first move of a resting thumb (the module note).
 * So this holds the cure — no Reanimated style on the content, the motion on the native driver — and the
 * device holds the proof.
 */
describe('the content, moving', () => {
  const content = () => screen.getByTestId('line-content', { includeHiddenElements: true });

  let timing: jest.SpyInstance<Animated.CompositeAnimation, Parameters<typeof Animated.timing>>;
  beforeEach(() => {
    timing = jest.spyOn(Animated, 'timing');
  });
  afterEach(() => timing.mockRestore());
  /** The motions started since the last look, as far as this suite cares. */
  const motions = () => {
    const runs = timing.mock.calls.map(([, config]) => ({
      toValue: config.toValue,
      duration: config.duration,
      useNativeDriver: config.useNativeDriver,
    }));
    timing.mockClear();
    return runs;
  };

  it('fades and slides in on the native driver for `motion.lineUnfold`, and out for `motion.lineFold`', () => {
    render(<Line open={false} />);
    motions();

    screen.rerender(<Line open />);
    expect(motions()).toEqual([
      { toValue: 1, duration: theme.motion.lineUnfold, useNativeDriver: true },
    ]);

    screen.rerender(<Line open={false} />);
    expect(motions()).toEqual([
      { toValue: 0, duration: theme.motion.lineFold, useNativeDriver: true },
    ]);
  });

  it('carries no Reanimated style: nothing above a rail may', () => {
    render(<Line open={false} />);
    screen.rerender(<Line open />);

    expect(content().props.jestAnimatedStyle).toBeUndefined();
    expect(content().props.animatedStyle).toBeUndefined();
  });

  it('stands still under Reduce motion, drawn where it rests', () => {
    const tree = (open: boolean) => (
      <ReducedMotionProvider value>
        <Line open={open} />
      </ReducedMotionProvider>
    );
    render(tree(false));

    screen.rerender(tree(true));

    expect(motions()).toEqual([]);
    expect(flat(content().props.style)).toMatchObject({ opacity: 1 });
  });
});

describe('a rail inside it', () => {
  /**
   * Home refactor 6: the tile's share is of the line's content, the next one cut at its edge — the
   * line's card, a little wider than the page's (2026-11-26).
   */
  it('takes its shares of the line’s content, its first card at the line’s inset', () => {
    const lineContent =
      Dimensions.get('window').width -
      2 * theme.size.gutter -
      2 * (theme.size.foldingLine.border + theme.size.foldingLine.pad);
    render(
      <FoldingLine title={TITLE} open onHeader={jest.fn()}>
        <HomeRowRail cards={[0, 1]}>
          {(at, width) => <View key={at} testID={`card-${at}`} style={{ width }} />}
        </HomeRowRail>
      </FoldingLine>,
    );

    expect(flat(screen.getByTestId('card-0').props.style).width).toBeCloseTo(
      lineContent * theme.size.lineCardRatio,
    );
    const rail = screen.UNSAFE_getByType(ScrollView);
    expect(flat(rail.props.style)).toMatchObject({
      marginHorizontal: -theme.size.foldingLine.pad,
    });
    expect(rail.props.snapToInterval).toBeCloseTo(
      lineContent * theme.size.lineCardRatio + theme.space.sm,
    );
  });

  /**
   * #804 through #820: a rail in an open line is measured from the page through FOR YOU, the line and
   * the fold — each laid out in its parent, as a device reports it.
   */
  it('is measured on the page through FOR YOU, the line and the fold', () => {
    const page = followable<Span>();
    const told: number[][] = [];
    const width = Dimensions.get('window').width;
    render(
      <PageOnScreen.Provider value={page}>
        <FoldingLines heading="For you" folding={false} testID="for-you">
          <FoldingLine title={TITLE} open onHeader={jest.fn()} testID="line">
            <HomeRowRail cards={[0, 1, 2]} onScreen={(cards) => told.push([...cards])}>
              {(at, cardWidth) => <View key={at} style={{ width: cardWidth }} />}
            </HomeRowRail>
          </FoldingLine>
        </FoldingLines>
      </PageOnScreen.Provider>,
    );
    const layout = (y: number, height: number) => ({
      nativeEvent: { layout: { x: 0, y, width, height } },
    });
    act(() => {
      fireEvent(screen.getByTestId('for-you'), 'layout', layout(1000, 600));
      fireEvent(screen.getByTestId('line'), 'layout', layout(100, 300));
      // The fold, under the header, in the clip inside the line's 1pt border.
      fireEvent(screen.getByTestId('line-fold'), 'layout', layout(45, 250));
      fireEvent(screen.UNSAFE_getByType(ScrollView), 'layout', layout(0, 240));
    });

    // The rail stands 1146 down the page — FOR YOU 1000, the line 100, its border 1, the fold 45 — 240
    // tall: a page showing 0–1200 shows 54 of it, under half, though a rail measured from FOR YOU
    // alone, 100 higher, would be over half on it…
    act(() => page.set({ from: 0, size: 1200 }));
    expect(told).toEqual([]);
    // …and a page showing 0–1300 shows 154 of it, over half.
    act(() => page.set({ from: 0, size: 1300 }));
    expect(told.at(-1)).toEqual([0]);
  });

  /** ADR-0205 §5: a closed line draws no tile, so it reports nobody — folding away included. */
  it('is on no page while it folds away', () => {
    const page = followable<Span>();
    const told: number[][] = [];
    const tree = (open: boolean) => (
      <PageOnScreen.Provider value={page}>
        <FoldingLine title={TITLE} open={open} onHeader={jest.fn()} testID="line">
          <HomeRowRail cards={[0, 1, 2]} onScreen={(cards) => told.push([...cards])}>
            {(at, cardWidth) => <View key={at} style={{ width: cardWidth }} />}
          </HomeRowRail>
        </FoldingLine>
      </PageOnScreen.Provider>
    );
    render(tree(true));
    screen.rerender(tree(false));
    act(() => {
      fireEvent(screen.getByTestId('line'), 'layout', {
        nativeEvent: { layout: { x: 0, y: 0, width: 360, height: 300 } },
      });
      fireEvent(screen.UNSAFE_getByType(ScrollView), 'layout', {
        nativeEvent: { layout: { x: 0, y: 0, width: 360, height: 240 } },
      });
    });

    act(() => page.set({ from: 0, size: 700 }));

    expect(told).toEqual([]);
  });
});

describe('the page shown it', () => {
  /** The brief: if the opened content would be cut off, the page eases down just enough. */
  it('asks as it unfolds, for its whole height — and once per opening', () => {
    const reveal = jest.fn<void, [Span]>();
    function Toggled() {
      const [open, setOpen] = useState(false);
      return (
        <PageReveal.Provider value={reveal}>
          <FoldingLines heading="For you" folding={!open} testID="for-you">
            <FoldingLine
              title={TITLE}
              open={open}
              onHeader={() => setOpen((was) => !was)}
              testID="line"
            >
              <Text>the tiles</Text>
            </FoldingLine>
          </FoldingLines>
        </PageReveal.Provider>
      );
    }
    render(<Toggled />);
    const layout = (y: number, height: number) => ({
      nativeEvent: { layout: { x: 0, y, width: 360, height } },
    });
    act(() => {
      fireEvent(screen.getByTestId('for-you'), 'layout', layout(900, 400));
      fireEvent(screen.getByTestId('line'), 'layout', layout(60, 46));
      fireEvent(header(), 'layout', layout(0, 44));
    });

    fireEvent.press(header());
    expect(reveal).not.toHaveBeenCalled();
    act(() => {
      fireEvent(screen.getByTestId('line-content'), 'layout', layout(0, 230));
    });

    expect(reveal).toHaveBeenCalledTimes(1);
    expect(reveal).toHaveBeenCalledWith({ from: 960, size: 2 + 44 + 230 });

    // Measured again while it stays open: no second ask.
    act(() => {
      fireEvent(screen.getByTestId('line-content'), 'layout', layout(0, 260));
    });
    expect(reveal).toHaveBeenCalledTimes(1);
  });

  /** Q38: Groups heating up, open by itself for a player in no group, scrolls Home under nobody. */
  it('never asks for a line opened by nobody’s press', () => {
    const reveal = jest.fn<void, [Span]>();
    const tree = (open: boolean) => (
      <PageReveal.Provider value={reveal}>
        <FoldingLine title={TITLE} open={open} onHeader={jest.fn()} reveals={false} testID="line">
          <Text>the tiles</Text>
        </FoldingLine>
      </PageReveal.Provider>
    );
    render(tree(false));
    const layout = (y: number, height: number) => ({
      nativeEvent: { layout: { x: 0, y, width: 360, height } },
    });
    act(() => {
      fireEvent(screen.getByTestId('line'), 'layout', layout(600, 46));
      fireEvent(header(), 'layout', layout(0, 44));
    });

    screen.rerender(tree(true));
    act(() => {
      fireEvent(screen.getByTestId('line-content'), 'layout', layout(0, 230));
    });

    expect(reveal).not.toHaveBeenCalled();
  });
});

describe('its cards on the page', () => {
  /** Fading in at no height, a card is not seen: it is on the page once the line has unfolded. */
  it('are told nothing until the line has unfolded', () => {
    const page = followable<Span>();
    const told: number[][] = [];
    const tree = (open: boolean) => (
      <PageOnScreen.Provider value={page}>
        <FoldingLine title={TITLE} open={open} onHeader={jest.fn()} testID="line">
          <HomeRowRail cards={[0, 1, 2]} onScreen={(cards) => told.push([...cards])}>
            {(at, cardWidth) => <View key={at} style={{ width: cardWidth }} />}
          </HomeRowRail>
        </FoldingLine>
      </PageOnScreen.Provider>
    );
    render(tree(false));
    act(() => page.set({ from: 0, size: 700 }));

    screen.rerender(tree(true));
    act(() => {
      fireEvent(screen.getByTestId('line'), 'layout', {
        nativeEvent: { layout: { x: 0, y: 0, width: 360, height: 300 } },
      });
      fireEvent(screen.getByTestId('line-fold'), 'layout', {
        nativeEvent: { layout: { x: 0, y: 44, width: 360, height: 240 } },
      });
      fireEvent(screen.UNSAFE_getByType(ScrollView), 'layout', {
        nativeEvent: { layout: { x: 0, y: 0, width: 360, height: 240 } },
      });
    });
    expect(told).toEqual([]);

    act(() => jest.advanceTimersByTime(theme.motion.lineUnfold));
    expect(told.at(-1)).toEqual([0]);
  });
});

describe('the footer', () => {
  const SEE_ALL = { words: 'See all', label: 'See all players at your level' };

  it('opens what the line says it opens, named by the line', () => {
    const onPress = jest.fn();
    render(<Line open footer={{ link: { ...SEE_ALL, onPress } }} />);

    fireEvent.press(screen.getByRole('link', { name: SEE_ALL.label }));

    expect(onPress).toHaveBeenCalledTimes(1);
  });

  /** The chevron is a direction rather than a word: drawn, and not spoken after the name. */
  it('draws the words and a chevron, ink, and speaks the name alone', () => {
    render(<Line open footer={{ link: { ...SEE_ALL, onPress: jest.fn() } }} />);

    expect(
      StyleSheet.flatten(screen.getByText(SEE_ALL.words).props.style as TextStyle),
    ).toMatchObject({ ...theme.type.rlValue, color: theme.color.ink });
    const chevron = screen.getByText('›', { includeHiddenElements: true });
    expect(chevron.props.accessibilityElementsHidden).toBe(true);
    expect(chevron.props.importantForAccessibility).toBe('no');
  });

  /** ADR-0205 §8: targets are 44pt, and the press is drawn. */
  it('is a 44pt link at the bottom right, dimmed while pressed', () => {
    render(<Line open footer={{ link: { ...SEE_ALL, onPress: jest.fn() } }} />);

    const link = screen.getByRole('link', { name: SEE_ALL.label });
    expect(flat(link.props.style).minHeight).toBe(theme.size.minTouch);
    const row = flat(screen.getByTestId('folding-line-footer').props.style);
    expect(row).toMatchObject({ flexDirection: 'row', justifyContent: 'flex-end' });
  });

  /**
   * Top 10's switcher stands at the footer's left and *Open the rankings ›* at its right (#821, home
   * refactor 12, 13), and the switcher's open bar lies over the footer, last.
   */
  it('draws a control at the left end, the link at the right, and lays what it is handed over both', () => {
    render(
      <Line
        open
        footer={{
          control: <View testID="pill" />,
          link: {
            words: 'Open the rankings',
            label: 'Open the rankings in padel',
            onPress: jest.fn(),
          },
          over: <View testID="over" />,
        }}
      />,
    );

    const parts = footerParts(screen.getByTestId('folding-line-footer'), (part) =>
      String(part.props.testID),
    );
    expect(parts).toEqual(['pill', 'link', 'over']);
    // The link takes the room left over before it, so it ends the row whatever stands at the left.
    const link = screen.getByRole('link', { name: 'Open the rankings in padel' });
    expect(flat(link.props.style)).toMatchObject({ marginLeft: 'auto' });
  });

  it('is drawn only while the line is open', () => {
    render(<Line open={false} footer={{ link: { ...SEE_ALL, onPress: jest.fn() } }} />);

    expect(screen.queryByRole('link', { name: SEE_ALL.label })).toBeNull();
  });
});
