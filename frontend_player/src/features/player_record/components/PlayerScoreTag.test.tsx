/**
 * **The score tag, band by band** — which tint each figure is drawn on, read off the band the
 * server served and never off the figure (#660, ADR-0195 §1), and the arithmetic that chose the
 * inks.
 *
 * The second block is the one that matters later. The mocks spelled the top band in `mint` and
 * the amber one in amber's retired value; both are below 4,5:1 on their own tints at the
 * tag's size, so the tag draws the palette's text-safe inks instead. Derived here, so a repaint
 * that goes back to the mark colours goes red rather than going unread.
 */

import { render, screen } from '@testing-library/react-native';
import { StyleSheet, Text, View, type TextStyle, type ViewStyle } from 'react-native';

import { contrast, parse } from '@/test-support/contrast';
import { theme } from '@/shared/ui';

import type { ReliabilityBand } from '../domain/playerRecord';

import { PlayerScoreTag } from './PlayerScoreTag';

const ratio = (a: string, b: string) => contrast(parse(a).rgb, parse(b).rgb);

/** WCAG 2.1: 4.5:1 for text below the large-text threshold. */
const AA = 4.5;

function drawn(score: number, band?: ReliabilityBand) {
  render(<PlayerScoreTag score={score} {...(band === undefined ? {} : { band })} />);
  const pill = StyleSheet.flatten(screen.UNSAFE_getAllByType(View)[0]?.props.style as ViewStyle);
  const figure = StyleSheet.flatten(screen.UNSAFE_getByType(Text).props.style as TextStyle);
  return { background: pill.backgroundColor, ink: figure.color };
}

describe('the score tag', () => {
  it.each([
    [100, 'VERY_HIGH', theme.color.mintSoft, theme.color.mintInk],
    [92, 'VERY_HIGH', theme.color.mintSoft, theme.color.mintInk],
    [87, 'HIGH', theme.color.line2, theme.color.ink],
    [75, 'HIGH', theme.color.line2, theme.color.ink],
    [74, 'MEDIUM', theme.color.amberSoft, theme.color.amber],
    [50, 'MEDIUM', theme.color.amberSoft, theme.color.amber],
    [48, 'LOW', theme.color.redSoft, theme.color.red],
    [0, 'LOW', theme.color.redSoft, theme.color.red],
  ] as const)('draws %i in the %s band', (score, band, background, ink) => {
    expect(drawn(score, band)).toEqual({ background, ink });
    expect(screen.getByTestId(`score-tag-${band}`)).toBeTruthy();
    expect(screen.getByText(String(score))).toBeTruthy();
  });

  /**
   * **The band is the server's, so the figure never picks the tint.** A 74 served as *High* — a
   * floor the backend moved — is drawn as High: a phone holding its own thresholds is the
   * disagreement this tag was rebuilt to remove.
   */
  it('tints by the served band, whatever the figure', () => {
    expect(drawn(74, 'HIGH')).toEqual({ background: theme.color.line2, ink: theme.color.ink });
  });

  /** A band this build cannot name claims nothing: the neutral tint, and the figure. */
  it('draws a band it cannot name on the neutral tint', () => {
    expect(drawn(61)).toEqual({ background: theme.color.line2, ink: theme.color.ink });
    expect(screen.getByTestId('score-tag')).toBeTruthy();
  });

  it('hides the spark from a screen reader — the figure is the fact', () => {
    render(<PlayerScoreTag score={92} band="VERY_HIGH" />);
    expect(screen.getByText('92')).toBeTruthy();
    expect(screen.UNSAFE_getAllByType(View)[1]?.props.accessibilityElementsHidden).toBe(true);
  });
});

describe('the inks the tag is drawn in', () => {
  it.each([
    ['VERY_HIGH', theme.color.mintInk, theme.color.mintSoft],
    ['HIGH', theme.color.ink, theme.color.line2],
    ['MEDIUM', theme.color.amber, theme.color.amberSoft],
    ['LOW', theme.color.red, theme.color.redSoft],
  ])('clear AA for text on the %s tint', (_band, ink, tint) => {
    expect(ratio(ink, tint)).toBeGreaterThanOrEqual(AA);
  });

  // The mocks' amber, `#9A6A0B`, is the value the palette retired for this shortfall (theme.ts);
  // it is no longer a token, so only the mint half can be read off the theme.
  it('is not the mark colour the mocks typed, which falls short on the same tint', () => {
    expect(ratio(theme.color.mint, theme.color.mintSoft)).toBeLessThan(AA);
  });
});
