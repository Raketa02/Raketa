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
  it('is drawn whole, because the engine serves it with its decimals on', () => {
    render(<FitPill fit={78} />);
    expect(screen.getByText('78')).toBeTruthy();
    screen.unmount();

    render(<FitPill fit={78.42131} />);
    expect(screen.getByText('78')).toBeTruthy();
    expect(screen.queryByText('78.42131')).toBeNull();
  });

  /**
   * **The fill reads the figure that is printed**, not the one that arrived.
   *
   * A pill drawn `hi` beside an 89 — because 89,6 crossed a line the reader cannot see — is
   * Part 13's *never colour alone* failing in the one direction the word cannot rescue: the
   * word here **is** the number.
   */
  it('rounds once, so the threshold and the figure are two views of one value', () => {
    expect(drawn(FIT_HIGH - 0.6).pill?.backgroundColor).toBe(theme.color.night);
    expect(screen.getByText(String(FIT_HIGH - 1))).toBeTruthy();
    screen.unmount();

    expect(drawn(FIT_HIGH - 0.5).pill?.backgroundColor).toBe(theme.color.coral);
    expect(screen.getByText(String(FIT_HIGH))).toBeTruthy();
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
  /**
   * **The word is a drawing and never a name.** §20.3 merges the pill into whatever names it —
   * a card body on three surfaces, a control's own label on the fourth — so a label prop that
   * started announcing itself would be the figure read twice on every card that has one.
   */
  it('draws the optional word before the glyph, and announces nothing', () => {
    render(<FitPill fit={80} label="Player fit" />);

    expect(screen.getByText('Player fit')).toBeTruthy();
    expect(screen.queryByLabelText('Player fit')).toBeNull();
    expect(screen.queryByRole('button')).toBeNull();
  });

  /** Without one the pill is exactly what the four surfaces that never wanted a word draw. */
  it('draws no word at all when it is given none', () => {
    render(<FitPill fit={80} />);

    expect(screen.queryByText('Player fit')).toBeNull();
  });

  it('is the height every call site drew, rather than the default none of them used', () => {
    expect(drawn(78).pill?.height).toBe(theme.size.fit);
    expect(theme.size.fit).toBe(26);
  });
});
