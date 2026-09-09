/**
 * The rail's dots — 7.18, and the drawn object whose whole point is that it **moves**.
 *
 * 7.9's navigator *"indicates; it does not navigate"* and can afford to; a paging rail has no
 * elsewhere, so the dots are what a card with no peek has **instead** of a peek. Two of the three
 * assertions here are therefore about the state channel — that the current dot is wider as well as
 * darker, which is Part 13's *never colour alone* discharged by geometry — and the third is an
 * absence: this row says nothing, and an absence is exactly what stops being true by accident.
 */

import { render, screen } from '@testing-library/react-native';
import { StyleSheet, View, type ViewStyle } from 'react-native';

import { contrast, parse } from '@/test-support/contrast';

import { PagerDots } from './PagerDots';
import { theme } from './theme';

const flatten = (style: unknown) => StyleSheet.flatten(style as ViewStyle);

/** The row, then one view per dot. */
const parts = () => screen.UNSAFE_getAllByType(View);

describe("the rail's dots", () => {
  it('draws one dot per card', () => {
    render(<PagerDots count={4} current={0} />);

    expect(parts()).toHaveLength(5);
  });

  /**
   * **Always**, which is 7.7's own word: *a paging rail with neither peek nor dots says nothing at
   * all about there being a second card.* A row that appeared only once a second card existed
   * would be the affordance arriving after it was needed, so a rail of one draws one dot — and
   * only a rail of none draws nothing, because there is no rail.
   */
  it('draws for a rail of one, and nothing for a rail of none', () => {
    render(<PagerDots count={1} current={0} />);
    expect(parts()).toHaveLength(2);

    screen.rerender(<PagerDots count={0} current={0} />);
    expect(screen.UNSAFE_queryAllByType(View)).toHaveLength(0);
  });

  it("is Part 8's geometry, unmoved — 5 × 5 at the pill radius, `space.xxs` apart", () => {
    render(<PagerDots count={3} current={0} />);
    const [row, , second] = parts();

    expect(flatten(second?.props.style)).toMatchObject({
      width: theme.size.pagerDot,
      height: theme.size.pagerDot,
      borderRadius: theme.radius.pill,
      backgroundColor: theme.color.line,
    });
    expect(flatten(row?.props.style)).toMatchObject({ gap: theme.space.xxs });
  });

  it('marks the one you are on by width as well as by tone', () => {
    render(<PagerDots count={3} current={1} />);
    const [, first, current] = parts();

    expect(flatten(current?.props.style)).toMatchObject({
      width: theme.size.pagerDotActive,
      height: theme.size.pagerDot,
      backgroundColor: theme.color.ink,
    });
    // The shape channel is the half Part 13 requires, so the two must differ in width and not
    // only in fill — a tone-only difference is the failure 1.4.1 names.
    expect(flatten(first?.props.style).width).not.toBe(flatten(current?.props.style).width);
  });

  /** 2.5's own pair: `ink` on `line` is what makes the current dot legible beside a resting one. */
  it('reads against the dot beside it', () => {
    const ink = parse(theme.color.ink).rgb;
    const line = parse(theme.color.line).rgb;

    expect(contrast(ink, line)).toBeGreaterThanOrEqual(3);
  });

  /**
   * *The row is hidden, and there is no element per dot.* The rail under it is a list and the
   * count is on the heading above it, so a spoken position here would be the second spelling of a
   * fact the screen already carries.
   */
  it('says nothing, on both platforms', () => {
    render(<PagerDots count={3} current={0} />);
    const [row] = parts();

    expect(row?.props.accessibilityElementsHidden).toBe(true);
    expect(row?.props.importantForAccessibility).toBe('no-hide-descendants');
    expect(row?.props.accessibilityRole).toBeUndefined();
    expect(row?.props.accessibilityLabel).toBeUndefined();
  });
});
