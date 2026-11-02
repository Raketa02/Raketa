/**
 * 10.3's header, on the two things [#401](https://github.com/Raketa02/Raketa/issues/401) added
 * to it — a **sub-line** under the title, and a spoken name that may differ from the drawn one —
 * and on the one **control** in it, and the two things the amendment fixed about that.
 *
 * The first two are asserted the way a listener meets them — by role and name — because the
 * whole point of a spoken name is that what is drawn and what is spoken are two different
 * strings, and only one of them is the element's name.
 *
 * The chevron's two are asserted against the **drawing**, which is the declared exception: a
 * chevron in `muted` and one in `ink` are the same control to every query a screen can run, and
 * a mark centred by its 24pt line box and one centred by its own 19pt glyph are the same element
 * at two different heights. Neither difference is reachable any other way, and the design system
 * now states both.
 *
 * What the rest of the header does — which line survives on a given screen — is asserted where a
 * player meets it, on the screens that draw one.
 */

import { fireEvent, render, screen, within } from '@testing-library/react-native';
import { Pressable, StyleSheet, Text, View, type TextStyle } from 'react-native';

import { ScreenHeader } from './ScreenHeader';
import { theme } from './theme';

const noop = () => {};

/** The mark's own style, found by the glyph rather than by position in the tree. */
function chevron() {
  render(<ScreenHeader title="Your line-up" onBack={noop} />);
  return StyleSheet.flatten(screen.getByText('‹').props.style as TextStyle);
}

describe('the title and its sub-line', () => {
  it('draws the sub-line under the title, inside the one element the title is', () => {
    render(<ScreenHeader title="tomek, ola" subline="Padel · planning" />);

    const header = screen.getByRole('header');

    expect(within(header).getByText('tomek, ola')).toBeTruthy();
    expect(within(header).getByText('Padel · planning')).toBeTruthy();
  });

  /** The eyebrow labels a region above; the sub-line qualifies the title below. Both may exist. */
  it('keeps the eyebrow above and outside the element the title is', () => {
    render(<ScreenHeader eyebrow="Play" title="Find a game" subline="one search" />);

    const header = screen.getByRole('header');

    expect(within(header).getByText('Find a game')).toBeTruthy();
    expect(within(header).queryByText('Play')).toBeNull();
    expect(screen.getByText('Play')).toBeTruthy();
  });

  /**
   * Named by its own words and **not labelled with them**: a header carrying its title as a label
   * would answer for it in every `getByLabelText` that means the control beside it — Play's
   * segment is called *Match me* under a header saying *Match me*.
   */
  it('is one element named by the title alone where there is no sub-line, with no label of its own', () => {
    render(<ScreenHeader title="Find a game" />);

    expect(screen.getByRole('header', { name: 'Find a game' })).toBeTruthy();
    expect(screen.queryByLabelText('Find a game')).toBeNull();
  });
});

describe('a header with no title', () => {
  /**
   * **The eyebrow is the heading where there is no h1.** The game screen's plan lead draws
   * `DOUBLES · COUNTED` and nothing under it ([#414](https://github.com/Raketa02/Raketa/issues/414)),
   * so a listener's first stop has to be that line rather than an element with a role and no
   * words in it — and it is named by its own words, never labelled with them, for the reason the
   * title is not.
   */
  it('is named by the eyebrow, which becomes the one element the header is', () => {
    render(<ScreenHeader eyebrow="Doubles · Counted" />);

    expect(screen.getByRole('header', { name: 'Doubles · Counted' })).toBeTruthy();
    expect(screen.queryByLabelText('Doubles · Counted')).toBeNull();
  });

  /**
   * **And with no eyebrow either, there is no heading element at all.** The Players tab's header
   * is its *Deck | Radar* toggle and nothing written
   * ([ADR-0169](../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
   * §1), so what fills the row is the lead — and an element carrying a role and no words would be
   * a stop a listener lands on and hears nothing from.
   */
  it('draws no heading where there is nothing to head it with, and the lead is the row', () => {
    render(<ScreenHeader lead={<Text>Deck</Text>} />);

    expect(screen.queryByRole('header')).toBeNull();
    expect(screen.getByText('Deck')).toBeTruthy();
  });
});

describe('what the header is called', () => {
  /**
   * §20.4: *the visible label truncates, the spoken one never does*. The conversation draws the
   * handles' stems and speaks them whole, and this is the slot that lets it.
   */
  it('takes a spoken name that differs from the drawn line, and speaks only that', () => {
    render(
      <ScreenHeader
        title="tomek, ola"
        subline="Padel · planning"
        titleLabel="tomek.p and ola.k, Padel, planning"
      />,
    );

    const header = screen.getByRole('header', { name: 'tomek.p and ola.k, Padel, planning' });

    expect(within(header).getByText('tomek, ola')).toBeTruthy();
    expect(within(header).getByText('Padel · planning')).toBeTruthy();
    // The name is the label and only the label: what a listener hears, not what is drawn — so
    // it is found the way every other named thing in this app is, and the drawn line is not.
    expect(screen.getByLabelText('tomek.p and ola.k, Padel, planning')).toBe(header);
    expect(screen.queryByLabelText('tomek, ola')).toBeNull();
  });
});

describe('a header that is a button', () => {
  /**
   * A group's page opens its Info from its header (Q125): the tile, the name and the line under
   * it are one door, and what a listener lands on says that it does something rather than only
   * what the screen is.
   */
  function drawPressable(onPress: () => void, onBack = noop, onPill = noop) {
    render(
      <ScreenHeader
        compact
        title="Kazimierz crew"
        subline="8 members · Centrum Ruchu"
        lead={<View testID="tile" />}
        onBack={onBack}
        backLabel="Back to Groups"
        right={
          <Pressable accessibilityRole="button" accessibilityLabel="Sport: Padel" onPress={onPill}>
            <Text>Padel</Text>
          </Pressable>
        }
        onPress={onPress}
        pressHint="Opens Info"
      />,
    );
  }

  it('is one button, named by its words, with what it opens as its hint', () => {
    drawPressable(noop);

    const named = screen.getByRole('button', { name: /^Kazimierz crew/ });
    expect(named.props.accessibilityHint).toBe('Opens Info');
    expect(within(named).getByText('8 members · Centrum Ruchu')).toBeTruthy();
    expect(screen.queryByRole('header')).toBeNull();
  });

  it('is pressed from the lead, the title or the sub-line alike', () => {
    const onPress = jest.fn();
    drawPressable(onPress);

    fireEvent.press(screen.getByTestId('tile'));
    fireEvent.press(screen.getByText('Kazimierz crew'));
    fireEvent.press(screen.getByText('8 members · Centrum Ruchu'));

    expect(onPress).toHaveBeenCalledTimes(3);
  });

  it('leaves the back control and the right slot their own presses', () => {
    const onPress = jest.fn();
    const onBack = jest.fn();
    const onPill = jest.fn();
    drawPressable(onPress, onBack, onPill);

    fireEvent.press(screen.getByRole('button', { name: 'Back to Groups' }));
    fireEvent.press(screen.getByRole('button', { name: 'Sport: Padel' }));

    expect(onBack).toHaveBeenCalledTimes(1);
    expect(onPill).toHaveBeenCalledTimes(1);
    expect(onPress).not.toHaveBeenCalled();
  });

  it('is a heading, and no button, where the screen gives it nothing to open', () => {
    render(<ScreenHeader compact title="Kazimierz crew" subline="8 members · Centrum Ruchu" />);

    expect(screen.getByRole('header', { name: /^Kazimierz crew/ })).toBeTruthy();
    expect(screen.queryByRole('button')).toBeNull();
  });
});

describe('the back chevron', () => {
  it('is ink, because it is the one thing in the header that is pressed', () => {
    // It was `muted` — the eyebrow's own colour — which left the control quieter than the
    // text beside it. Nothing else moved: same role, same weight, same target.
    expect(chevron()?.color).toBe(theme.color.ink);
    expect(chevron()?.fontSize).toBe(theme.type.h1.fontSize);
  });

  it('takes a line box the size of the mark, so the row centres the glyph and not a gap', () => {
    // Part 4's rule for a drawn figure, read against a drawn mark. h1's own 24pt line around a
    // 19pt chevron is 5pt of nothing that the header's `alignItems: 'center'` centres instead.
    expect(chevron()?.lineHeight).toBe(theme.type.h1.fontSize);
  });

  it('is drawn only where a screen says it has somewhere to go', () => {
    // 10.3's opt-in, which is the reason the header does not point at whatever the router
    // happened to be holding.
    render(<ScreenHeader title="Your line-up" />);

    expect(screen.queryByText('‹')).toBeNull();
  });
});

describe('what the header announces', () => {
  it('names the screen with its title and never with the eyebrow above it', () => {
    render(<ScreenHeader title="Pick players" eyebrow="Padel · doubles · for fun" />);

    expect(screen.getByRole('header', { name: 'Pick players' })).toBeTruthy();
    expect(screen.queryByRole('header', { name: 'Padel · doubles · for fun' })).toBeNull();
  });

  it('names the back control by where it goes, where the screen says so', () => {
    render(<ScreenHeader title="Your court" onBack={noop} backLabel="Back to Find a game" />);

    expect(screen.getByLabelText('Back to Find a game')).toBeTruthy();
  });
});
