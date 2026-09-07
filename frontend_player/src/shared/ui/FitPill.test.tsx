/**
 * The threshold, and the pairing Rule C refuses.
 *
 * Part 17 warns that the deleted 7.1's *"90 threshold named a scale the deleted engine
 * defined"* and says outright that rebuilding one of those sections is an amendment rather
 * than a restoration. So the two things this file holds are the two the warning is about: the
 * scale the number is against, and the step in it.
 *
 * The fill is asserted against the drawing — the declared exception — because `ink` on coral
 * and `#fff` on coral are the same pill to every query a screen can run, and the prototype
 * drew the second one at 3,89:1.
 */

import { render, screen } from '@testing-library/react-native';
import { StyleSheet, Text, View, type TextStyle, type ViewStyle } from 'react-native';

import { FIT_HIGH, FIT_SCALE, FitPill } from './FitPill';
import { theme } from './theme';

const flatten = <T,>(style: unknown) => StyleSheet.flatten(style as T);

function drawn(fit: number) {
  render(<FitPill fit={fit} />);
  const pill = flatten<ViewStyle>(screen.UNSAFE_getByType(View).props.style);
  const label = flatten<TextStyle>(screen.UNSAFE_getAllByType(Text)[1]?.props.style);
  return { pill, label };
}

describe('the scale', () => {
  it('is a hundred, stated here rather than inherited from a deleted engine', () => {
    expect(FIT_SCALE).toBe(100);
  });

  it('puts the step at the top tenth of it', () => {
    expect(FIT_HIGH).toBe(FIT_SCALE * 0.9);
  });
});

describe('the fill', () => {
  it('is night below the step and coral at it', () => {
    expect(drawn(FIT_HIGH - 1).pill?.backgroundColor).toBe(theme.color.night);
    screen.unmount();
    expect(drawn(FIT_HIGH).pill?.backgroundColor).toBe(theme.color.coral);
  });

  /** Rule C: white on coral is 3,89:1 and is refused outright. `ink` is 4,50:1. */
  it('carries ink on the coral and white on the night, never the other way round', () => {
    expect(drawn(FIT_HIGH).label?.color).toBe(theme.color.ink);
    screen.unmount();
    expect(drawn(FIT_HIGH - 1).label?.color).toBe(theme.color.surface);
  });
});

describe('the number', () => {
  it('is drawn as served, with nothing here rounding or rescaling it', () => {
    render(<FitPill fit={78} />);

    expect(screen.getByText('78')).toBeTruthy();
  });

  /** Twenty of these scroll past one another; a 78 wider than a 90 is a column that breathes. */
  it('is mono and tabular, which is the rule for every number in this app', () => {
    const label = drawn(78).label;

    expect(label?.fontFamily).toBe(theme.num.xs.fontFamily);
    expect(label?.fontVariant).toEqual(theme.tabular.fontVariant);
  });
});

describe('the pill', () => {
  /** UI §G1: the class defaults were overridden inline at all five call sites. */
  it('is the height every call site drew, rather than the default none of them used', () => {
    expect(drawn(78).pill?.height).toBe(theme.size.fit);
    expect(theme.size.fit).toBe(26);
  });
});
