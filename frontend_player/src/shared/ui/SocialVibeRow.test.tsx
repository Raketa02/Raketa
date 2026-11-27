import { render, screen } from '@testing-library/react-native';
import { StyleSheet, type TextStyle, type ViewStyle } from 'react-native';

import { SOCIAL_VIBE_ON_DARK, SocialVibeRow } from './SocialVibeRow';
import { theme } from './theme';

const HIDDEN = { includeHiddenElements: true } as const;

const styleOf = (testID: string) =>
  StyleSheet.flatten(screen.getByTestId(testID, HIDDEN).props.style as ViewStyle);
const figureColour = (text: string) =>
  StyleSheet.flatten(screen.getByText(text, HIDDEN).props.style as TextStyle).color;

describe('SocialVibeRow (7.38)', () => {
  it('is one element, named by the name, the figure and the band’s word', () => {
    render(<SocialVibeRow pct={82} />);
    expect(screen.getByRole('image', { name: 'Social vibe, 82 percent, Great vibe' })).toBeTruthy();
  });

  it('prints the figure and fills the bar to the same value, 0 to 100', () => {
    render(<SocialVibeRow pct={67} />);
    expect(screen.getByText('67%', HIDDEN)).toBeTruthy();
    expect(styleOf('social-vibe-fill').width).toBe('67%');
  });

  it('holds a figure off the scale at its end, and draws no fill at nought', () => {
    render(<SocialVibeRow pct={0} />);
    expect(screen.queryByTestId('social-vibe-fill', HIDDEN)).toBeNull();
    screen.rerender(<SocialVibeRow pct={130} />);
    expect(screen.getByText('100%', HIDDEN)).toBeTruthy();
    expect(styleOf('social-vibe-fill').width).toBe('100%');
    expect(
      screen.getByRole('image', { name: 'Social vibe, 100 percent, Great vibe' }),
    ).toBeTruthy();
  });

  it('draws, says and words one number — the figure as printed', () => {
    render(<SocialVibeRow pct={69.6} />);
    expect(screen.getByText('70%', HIDDEN)).toBeTruthy();
    expect(styleOf('social-vibe-fill').width).toBe('70%');
    expect(screen.getByRole('image', { name: 'Social vibe, 70 percent, Great vibe' })).toBeTruthy();
  });

  it.each([
    [82, theme.color.volt],
    [60, theme.color.volt],
    [35, theme.color.gameVoltDim],
    [10, theme.color.gameGrey],
  ])('colours %i%% and its fill by the band', (pct, colour) => {
    render(<SocialVibeRow pct={pct} />);
    expect(figureColour(`${pct}%`)).toBe(colour);
    expect(styleOf('social-vibe-fill').backgroundColor).toBe(colour);
  });

  it('never draws the forecast’s green, amber or red', () => {
    const forecast: readonly string[] = [
      theme.color.gameGreen,
      theme.color.gameAmber,
      theme.color.gameRed,
    ];
    for (const colour of Object.values(SOCIAL_VIBE_ON_DARK)) expect(forecast).not.toContain(colour);
  });

  it('says Social vibe inside the bar twice — light on the track, ink on the fill', () => {
    render(<SocialVibeRow pct={10} />);
    const names = screen.getAllByText('Social vibe', HIDDEN);
    expect(names).toHaveLength(2);
    const colours = names.map((name) => StyleSheet.flatten(name.props.style as TextStyle).color);
    expect(colours).toEqual([theme.color.surface, theme.color.ink]);
  });

  it('lays the ink copy over the bar’s whole width, so it meets the light one letter for letter', () => {
    render(<SocialVibeRow pct={25} />);
    // The fill is a quarter of the bar, so the copy inside it is four fills wide: the bar's width.
    expect(styleOf('social-vibe-on-fill').width).toBe('400%');
  });

  it('slants the name as an italic, since no italic face is loaded', () => {
    render(<SocialVibeRow pct={50} />);
    for (const name of screen.getAllByText('Social vibe', HIDDEN)) {
      expect(StyleSheet.flatten(name.props.style as TextStyle).transform).toEqual([
        { skewX: `${theme.size.socialVibe.lean}deg` },
      ]);
    }
  });
});
