/**
 * The tick, which is the half of the selected state a screen reader and a colour-blind
 * player each get one of.
 *
 * **Asserted against the drawing, which is the declared exception to "assert what the
 * player can observe"** — the same exception `ConfidenceRing.test.tsx` makes, and for the
 * same reason. 6.8 says the selected state is a fill inversion *and* a tick, and that the
 * tick is the half that matters: twenty-one rectangles differing only in lightness are a
 * texture. A fill has no role, no name and no text, so a suite that only went through a
 * screen could not tell a grid that inverted a cell from one that also ticked it — and
 * "selection is not carried by colour alone" is precisely the claim that would slip.
 *
 * The reserved footnote slot is the second thing here for the same reason: when it is empty
 * it has no text, no role and no name, so *the height is still there* is unobservable from a
 * screen. Its **value** is not pinned — `profileControlGeometry.test.ts` owns the geometry
 * arithmetic and says outright that a derivation like two lines of `tiny` is not worth an
 * assertion that cannot fail.
 *
 * Everything else about the grid — what the cells are called, what pressing one does, what
 * the footnote says — is asserted where a player meets it, in
 * `features/player_profile/components/socialAvailabilityStep.test.tsx`.
 */

import { render, screen } from '@testing-library/react-native';
import { StyleSheet, View, type ViewStyle } from 'react-native';
import { Path } from 'react-native-svg';

import {
  AvailabilityGrid,
  type AvailabilityDiffRow,
  type AvailabilityDiffState,
  type AvailabilityGridRow,
} from './AvailabilityGrid';
import { theme } from './theme';

const grid = theme.size.availability;

const flatten = (style: unknown) => StyleSheet.flatten(style as ViewStyle);

const ticks = () => screen.UNSAFE_queryAllByType(Path);

/** Two days of three, which is enough to tell a cell's state from its neighbour's. */
function rows(selected: readonly string[]): readonly AvailabilityGridRow[] {
  return ['Mon', 'Tue'].map((day) => ({
    key: day,
    label: day,
    cells: ['morning', 'afternoon', 'evening'].map((part) => ({
      key: `${day} ${part}`,
      selected: selected.includes(`${day} ${part}`),
      onPress: () => undefined,
      accessibilityLabel: `${day} ${part}`,
    })),
  }));
}

describe('the selected cell', () => {
  it('carries a tick as well as the inverted fill', () => {
    render(<AvailabilityGrid columnHeads={['Morning']} rows={rows(['Mon morning'])} />);

    expect(ticks()).toHaveLength(1);
    expect(screen.getByRole('checkbox', { name: 'Mon morning' }).props.accessibilityState).toEqual(
      expect.objectContaining({ checked: true }),
    );
  });

  it('draws one per ticked cell and none anywhere else', () => {
    render(
      <AvailabilityGrid columnHeads={['Morning']} rows={rows(['Mon morning', 'Tue evening'])} />,
    );

    expect(ticks()).toHaveLength(2);
  });

  it('draws nothing at all on an empty week', () => {
    // The empty grid is a complete answer and is drawn as one: nothing greyed, nothing
    // pre-seeded, and no cell ticked on the player's behalf.
    render(<AvailabilityGrid columnHeads={['Morning']} rows={rows([])} />);

    expect(ticks()).toHaveLength(0);
  });
});

describe('the column heads', () => {
  it('are drawn, and hidden from assistive technology so no cell is announced twice', () => {
    render(<AvailabilityGrid columnHeads={['Morning', 'Afternoon']} rows={rows([])} />);

    // On screen for whoever is looking at it...
    expect(screen.getByText('Morning', { includeHiddenElements: true })).toBeTruthy();
    // ...and out of the way of whoever is not: a cell already names its own column, so a
    // readable head would be announced once for every row it sits above.
    expect(screen.queryByText('Morning')).toBeNull();
  });
});

describe('the footnote slot', () => {
  /** The reserved slot, found by the one thing that distinguishes it: its floor. */
  const reservedSlots = () =>
    screen
      .UNSAFE_queryAllByType(View)
      .filter((node) => flatten(node.props.style)?.minHeight === grid.footnoteMinHeight);

  it('is laid out whether or not it has anything in it', () => {
    // The moment a player is most likely to tick a second cell is immediately after
    // ticking the first, and a grid that jumped upward under a finger mid-tap would select
    // the wrong cell. So the slot's height is reserved, not conditional on the message.
    const { rerender } = render(
      <AvailabilityGrid columnHeads={['Morning']} rows={rows([])} footnote="Nothing ticked" />,
    );

    expect(screen.getByText('Nothing ticked')).toBeTruthy();
    expect(reservedSlots()).toHaveLength(1);

    rerender(<AvailabilityGrid columnHeads={['Morning']} rows={rows([])} />);

    expect(screen.queryByText('Nothing ticked')).toBeNull();
    expect(reservedSlots()).toHaveLength(1);
  });
});

/**
 * The diff variant — the same geometry with a third fact, and the fix for a Part 13 violation
 * nobody had claimed.
 *
 * The prototype drew *new* as a volt ring and *dropped* as 45% opacity: colour as the only
 * signal, twice, on a sheet whose own body copy names the colour as the mechanism — and a
 * volt ring on paper is 1,3:1 besides, so half of it was not there at all. Three shapes is
 * the fix, and a shape is exactly what no screen query can see.
 */
describe('the diff variant', () => {
  const diffRows = (states: readonly AvailabilityDiffState[]): readonly AvailabilityDiffRow[] => [
    {
      key: 'Mon',
      label: 'Mon',
      cells: states.map((state, index) => ({
        key: `Mon ${index}`,
        state,
        accessibilityLabel: state === 'off' ? undefined : `Mon ${index}`,
      })),
    },
  ];

  it('draws one mark per fact, so no two states differ by colour alone', () => {
    render(
      <AvailabilityGrid
        variant="diff"
        columnHeads={['Morning', 'Afternoon', 'Evening']}
        rows={diffRows(['on', 'added', 'dropped'])}
      />,
    );

    // A tick, a plus and a dash: three drawings, and the plus is two subpaths in one.
    expect(ticks().map((node) => node.props.d as string)).toEqual([
      'M 2.5 6.5 L 5 9 L 9.5 3.5',
      'M 6 2.5 V 9.5 M 2.5 6 H 9.5',
      'M 2.5 6 H 9.5',
    ]);
  });

  it('is not interactive, so nothing on it offers a state a reader could try to change', () => {
    render(
      <AvailabilityGrid
        variant="diff"
        columnHeads={['Morning']}
        rows={diffRows(['on', 'added', 'dropped'])}
      />,
    );

    expect(screen.queryAllByRole('checkbox')).toHaveLength(0);
    expect(screen.getByLabelText('Mon 1')).toBeTruthy();
  });

  it('hides a cell with nothing to say rather than announcing it empty', () => {
    render(
      <AvailabilityGrid
        variant="diff"
        columnHeads={['Morning']}
        rows={diffRows(['off', 'added'])}
      />,
    );

    // Twenty-one names between the ones that changed is the double announcement 6.8 hides
    // its column heads to avoid, arriving on a grid that cannot be operated at all.
    expect(screen.queryAllByLabelText(/^Mon/)).toHaveLength(1);
  });

  it('is 6.8 exactly — the same cell, at the same height, on the same inverted fill', () => {
    render(<AvailabilityGrid variant="diff" columnHeads={['Morning']} rows={diffRows(['on'])} />);
    const diffCell = flatten(screen.getByLabelText('Mon 0').props.style);
    screen.unmount();

    render(<AvailabilityGrid columnHeads={['Morning']} rows={rows(['Mon morning'])} />);
    const editorCell = flatten(screen.getByRole('checkbox', { name: 'Mon morning' }).props.style);

    expect(diffCell?.height).toBe(grid.cellHeight);
    expect(diffCell?.backgroundColor).toBe(editorCell?.backgroundColor);
    expect(diffCell?.borderRadius).toBe(editorCell?.borderRadius);
  });
});
