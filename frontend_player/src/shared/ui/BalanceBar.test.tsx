/**
 * One scale, one clamp, and the three tones white is allowed to sit on.
 *
 * The prototype computed the fold one way and clamped it three ways — 22–78 on the forecast
 * card, 20–80 on the pool header and the candidate card — so the same gap landed in a
 * different place on two screens. That is the defect 7.5 and 7.8 exist to prevent, and it is
 * unobservable from a screen: a bar has no role, no name and no text under it, and two bars
 * that disagree by two points look identical to every query.
 */

import { render, screen } from '@testing-library/react-native';
import { StyleSheet, Text, View, type ViewStyle } from 'react-native';

import { BALANCE_SCALE, BalanceBar, balanceShare, type BalanceBarTone } from './BalanceBar';
import { theme } from './theme';

const flatten = (style: unknown) => StyleSheet.flatten(style as ViewStyle);

/** The two segments, yours first — the only Views carrying a percentage width. */
function segments() {
  return screen
    .UNSAFE_queryAllByType(View)
    .map((node) => flatten(node.props.style))
    .filter((style) => typeof style?.width === 'string');
}

describe('the scale', () => {
  it('is one mapping, one constant and one clamp', () => {
    expect(BALANCE_SCALE).toEqual({ centre: 50, amplification: 34, min: 20, max: 80 });
  });

  it('puts an even game in the middle', () => {
    expect(balanceShare(0)).toBe(BALANCE_SCALE.centre);
  });

  it('amplifies, which is the whole reason a fixed scale was worth arguing for', () => {
    // 2,71 against 2,83 drawn honestly is 48,9 against 51,1 — a difference nobody can see.
    expect(balanceShare(-0.12)).toBeCloseTo(45.92, 2);
  });

  it('clamps at 20 and 80 in both directions, and at one pair of numbers', () => {
    expect(balanceShare(-5)).toBe(BALANCE_SCALE.min);
    expect(balanceShare(5)).toBe(BALANCE_SCALE.max);
  });
});

describe('the bar', () => {
  it('draws the fold where the scale puts it, and the rest is theirs', () => {
    render(<BalanceBar advantage={0.5} tone="ok" accessibilityLabel="Fairly even, 74%" />);

    const [yours, theirs] = segments();
    expect(yours?.width).toBe(`${balanceShare(0.5)}%`);
    expect(theirs?.width).toBe(`${100 - balanceShare(0.5)}%`);
  });

  /** Rule C: white on `mint` is 4,07:1. Every tone here is an ink one white may sit on. */
  it.each([
    ['ok', theme.color.mintInk],
    ['warn', theme.color.amber],
    ['bad', theme.color.red],
  ] as const)('paints their side in %s with a value white reads on', (tone, expected) => {
    render(
      <BalanceBar
        advantage={0}
        tone={tone as BalanceBarTone}
        accessibilityLabel="Very even, 91%"
      />,
    );

    expect(segments()[1]?.backgroundColor).toBe(expected);
  });

  it('swaps which side is the dark one on a dark card, because the card is the other one', () => {
    render(<BalanceBar advantage={0} tone="ok" variant="onDark" accessibilityLabel="Very even" />);

    expect(segments()[0]?.backgroundColor).toBe(theme.color.surface);
  });
});

describe('the labels', () => {
  it('are drawn at the two sizes with room for them', () => {
    render(
      <BalanceBar
        advantage={0}
        tone="ok"
        size="md"
        labels={['you', 'them']}
        accessibilityLabel="x"
      />,
    );

    expect(screen.getByText('you')).toBeTruthy();
    expect(screen.getByText('them')).toBeTruthy();
  });

  /** #219 B4 put the type floor at 9,5pt, so the smallest bar draws none rather than a 8pt one. */
  it('are absent at the smallest size rather than drawn under the floor', () => {
    render(
      <BalanceBar
        advantage={0}
        tone="ok"
        size="sm"
        labels={['you', 'them']}
        accessibilityLabel="x"
      />,
    );

    expect(screen.UNSAFE_queryAllByType(Text)).toHaveLength(0);
  });
});

describe('what it announces', () => {
  /**
   * `the-words.md` §20.4: one `image`, named with the balance word and its figure. The word
   * is the point, because the bar itself is a colour — which Part 13 forbids being the only
   * signal.
   */
  it('is one element carrying the word, never the two segments', () => {
    render(<BalanceBar advantage={0.2} tone="warn" accessibilityLabel="One side favoured, 62%" />);

    expect(screen.getByRole('image', { name: 'One side favoured, 62%' })).toBeTruthy();
  });
});
