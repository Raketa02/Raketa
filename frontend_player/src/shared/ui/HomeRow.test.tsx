/**
 * **The Home row frame** — one heading, one link, one rail, for every row on Home
 * ([#798](https://github.com/Raketa02/Raketa/issues/798); the Home rows screens §2).
 *
 * The rows that sit on it — FRIENDS GAME, FRIEND REQUESTS, ASKED FOR A LEVEL, YOUR GAMES — keep their
 * own tests, which pass unchanged; they say what each row does, and the geometry the four rows used
 * to copy is held here, once: the heading, the bleed, the gap, both rails' widths and the paging
 * rail's snap and dots. And the three things no row today exercises: *See all ›* and its name, the
 * slot a row hands a control into, and a rail that is never remounted, so it keeps its scroll
 * position. That nothing moved on a device is a look, owed.
 */

import { fireEvent, render, screen } from '@testing-library/react-native';
import {
  Dimensions,
  ScrollView,
  StyleSheet,
  Text,
  View,
  type TextStyle,
  type ViewStyle,
} from 'react-native';

import { HomeRow, HomeRowRail, type HomeRowProps, type HomeRowRailProps } from './HomeRow';
import { theme } from './theme';

const SEE_ALL = {
  words: 'See all',
  label: 'See all same competitive level players',
};

/** Content width — the screen less the gutter each side (Part 4). */
const content = () => Dimensions.get('window').width - 2 * theme.size.gutter;

/** A rail of `count` cards, each a box at the width the rail hands it. */
function Row({
  count,
  heading = 'Friend requests · 2',
  ...rest
}: { readonly count: number } & Partial<Omit<HomeRowProps, 'children'>> &
  Pick<HomeRowRailProps<number>, 'geometry' | 'snap'>) {
  const { geometry, snap, ...row } = rest;
  return (
    <HomeRow heading={heading} testID="row" {...row}>
      <HomeRowRail
        cards={Array.from({ length: count }, (_, at) => at)}
        {...(geometry === undefined ? {} : { geometry })}
        {...(snap === undefined ? {} : { snap })}
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

  describe('See all', () => {
    it('opens what the row says it opens, named by the row', () => {
      const onPress = jest.fn();
      render(<Row count={2} link={{ ...SEE_ALL, onPress }} />);

      fireEvent.press(screen.getByRole('link', { name: SEE_ALL.label }));

      expect(onPress).toHaveBeenCalledTimes(1);
    });

    /** The chevron is a direction rather than a word: drawn, and not spoken after the name. */
    it('draws the words and a chevron, and speaks the name alone', () => {
      render(<Row count={2} link={{ ...SEE_ALL, onPress: jest.fn() }} />);

      expect(screen.getByText(SEE_ALL.words)).toBeTruthy();
      const chevron = screen.getByText('›', { includeHiddenElements: true });
      expect(chevron.props.accessibilityElementsHidden).toBe(true);
      expect(chevron.props.importantForAccessibility).toBe('no');
    });

    /** Ink on paper, as the sign-in screen's link (6.6's 44pt reached by its slop — 6.5). */
    it('is ink, and is reached past its words', () => {
      render(<Row count={2} link={{ ...SEE_ALL, onPress: jest.fn() }} />);

      const link = screen.getByRole('link', { name: SEE_ALL.label });
      expect(link.props.hitSlop).toEqual(theme.hit.rowLink);
      expect(
        StyleSheet.flatten(screen.getByText(SEE_ALL.words).props.style as TextStyle),
      ).toMatchObject({ ...theme.type.rlValue, color: theme.color.ink });
    });

    /**
     * Its 16pt line overhangs the eyebrow's 12 rather than growing the heading's line, so a row with
     * a link stands where a row without one does (home rows 1: the same spacing either way).
     */
    it('stands on the heading’s line without making it taller', () => {
      render(<Row count={2} link={{ ...SEE_ALL, onPress: jest.fn() }} />);

      const link = screen.getByRole('link', { name: SEE_ALL.label });
      const drawn = flat(link.props.style);
      expect(theme.type.rlValue.lineHeight + 2 * (drawn.marginVertical as number)).toBe(
        theme.type.eyebrow.lineHeight,
      );
    });

    it('is not there unless the row hands one in', () => {
      render(<Row count={2} />);

      expect(screen.queryByRole('link')).toBeNull();
      expect(screen.queryByText('›', { includeHiddenElements: true })).toBeNull();
    });
  });

  /** Top 10 hands in its sport pill here, beside *Rankings ›* (the screens §2). */
  it('draws the control a row hands in, on the heading’s line', () => {
    render(
      <Row
        count={2}
        control={<Text>Padel</Text>}
        link={{ words: 'Rankings', label: 'Rankings', onPress: jest.fn() }}
      />,
    );

    expect(screen.getByText('Padel')).toBeTruthy();
    expect(screen.getByRole('link', { name: 'Rankings' })).toBeTruthy();
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

    screen.rerender(
      <Row count={1} heading="Friend requests · 1" link={{ ...SEE_ALL, onPress: jest.fn() }} />,
    );
    expect(rail()).toBe(first);
  });
});
