import { render, screen } from '@testing-library/react-native';
import { StyleSheet, type ViewStyle } from 'react-native';

import { ComparisonBar, type ComparisonBarProps } from './ComparisonBar';
import { theme } from './theme';

const NAMES = {
  new: 'New',
  developing: 'Developing',
  established: 'Established',
  advanced: 'Advanced',
};
const HIDDEN = { includeHiddenElements: true } as const;

const draw = (props: Partial<ComparisonBarProps> = {}) =>
  render(
    <ComparisonBar
      yours={2.71}
      theirs={2.69}
      band="established"
      bandNames={NAMES}
      markLabel="YOU"
      variant="onDark"
      accessibilityLabel="You 2,71 · zofia.b 2,69"
      {...props}
    />,
  );
const styleOf = (testID: string) =>
  StyleSheet.flatten(screen.getByTestId(testID, HIDDEN).props.style as ViewStyle);

describe('ComparisonBar (7.33)', () => {
  it('is one element, named for the two levels', () => {
    draw();
    expect(screen.getByLabelText('You 2,71 · zofia.b 2,69')).toBeTruthy();
  });

  it('fills to their level and marks the reader’s, on the passport’s 1,00–5,00', () => {
    draw({ yours: 3, theirs: 2 });
    expect(styleOf('comparison-fill').width).toBe('25%');
    expect(styleOf('comparison-mark').left).toBe('50%');
  });

  it('holds a level off the scale at its end', () => {
    draw({ yours: 0.5, theirs: 6 });
    expect(styleOf('comparison-fill').width).toBe('100%');
    expect(styleOf('comparison-mark').left).toBe('0%');
  });

  it('labels the mark, and names all four bands with the reader’s in bold', () => {
    draw({ band: 'developing' });
    expect(screen.getByText('YOU', HIDDEN)).toBeTruthy();
    for (const name of Object.values(NAMES)) expect(screen.getByText(name, HIDDEN)).toBeTruthy();
    const bold = (name: string) =>
      StyleSheet.flatten(screen.getByText(name, HIDDEN).props.style).fontFamily;
    expect(bold('Developing')).toBe(theme.font.sans[800]);
    expect(bold('Established')).toBe(theme.font.sans[600]);
  });

  it('fills in volt with a white mark on dark', () => {
    draw();
    expect(styleOf('comparison-fill').backgroundColor).toBe(theme.color.volt);
    expect(styleOf('comparison-mark').backgroundColor).toBe(theme.color.surface);
  });

  it('fills in mint with an ink mark on light', () => {
    draw({ variant: 'base' });
    expect(styleOf('comparison-fill').backgroundColor).toBe(theme.color.mint);
    expect(styleOf('comparison-mark').backgroundColor).toBe(theme.color.ink);
  });
});
