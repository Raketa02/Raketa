/**
 * One mark, one drawing: a drawn tick before the words at every placement — the two photo
 * panels and the deck card — and the placement's own treatment over the same two words.
 */

import { render, screen } from '@testing-library/react-native';
import { Text } from 'react-native';
import { Path } from 'react-native-svg';

import { ON_COURT_MARK, OnCourtMark, type OnCourtMarkPlacement } from './OnCourtMark';
import { TICK_PATH } from './Tick';
import { theme } from './theme';

const PLACEMENTS: readonly OnCourtMarkPlacement[] = ['card', 'record', 'deck'];

describe.each(PLACEMENTS)('the mark on the %s', (on) => {
  it('draws the tick before the words, as the tick family’s own path', () => {
    render(<OnCourtMark on={on} />);

    const [tick] = screen.UNSAFE_getAllByType(Path);
    expect(tick?.props.d).toBe(TICK_PATH);
    expect(screen.getByText(ON_COURT_MARK)).toBeTruthy();
  });

  it('draws the tick in the words’ own colour, so the two read as one line', () => {
    render(<OnCourtMark on={on} />);

    const [tick] = screen.UNSAFE_getAllByType(Path);
    const words = screen.UNSAFE_getAllByType(Text)[0];
    const colour = (words?.props.style as readonly { color?: string }[])
      .flat()
      .find((style) => style?.color !== undefined)?.color;

    expect(tick?.props.stroke).toBe(colour);
  });
});

describe('the placements’ treatments', () => {
  it('is mint over the panels’ scrim and white over the deck card’s photograph', () => {
    render(<OnCourtMark on="card" />);
    expect(screen.UNSAFE_getAllByType(Path)[0]?.props.stroke).toBe(theme.color.mintSoft);
    screen.unmount();

    render(<OnCourtMark on="deck" />);
    expect(screen.UNSAFE_getAllByType(Path)[0]?.props.stroke).toBe(theme.color.surface);
  });

  /** The panels' words are capped over what the corner leaves them; the deck card is not a fixed box. */
  it('caps the words on a panel and leaves them uncapped on the deck card', () => {
    render(<OnCourtMark on="record" />);
    expect(screen.getByText(ON_COURT_MARK).props.maxFontSizeMultiplier).toBe(1.6);
    screen.unmount();

    render(<OnCourtMark on="deck" />);
    expect(screen.getByText(ON_COURT_MARK).props.maxFontSizeMultiplier).toBeUndefined();
  });
});
