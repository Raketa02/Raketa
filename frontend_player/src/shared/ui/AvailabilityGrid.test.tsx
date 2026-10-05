/**
 * The tick, the fills, and the reserved footnote slot — what the grid draws that no screen
 * query can see.
 *
 * **Asserted against the drawing, which is the declared exception to "assert what the
 * player can observe"** — the same exception `ConfidenceRing.test.tsx` makes, and for the
 * same reason. 6.8 says the selected state is a fill *and* a tick — every state carries a
 * shape, never colour alone, and mock 36's plain fill does not change that. A fill has no
 * role, no name and no text, so a suite that only went through a screen could not tell
 * a grid that filled a cell from one that also ticked it — and "selection is not carried by
 * colour alone" is precisely the claim that would slip. The fills are pinned beside it,
 * because `paper2` → `mint` is what makes the fill legal on its own (3,39:1) and is one
 * careless token from not being.
 *
 * The reserved footnote slot is the third thing here for the same reason: when it is empty
 * it has no text, no role and no name, so *the height is still there* is unobservable from a
 * screen. Its **value** is not pinned — `profileControlGeometry.test.ts` owns the geometry
 * arithmetic and says outright that a derivation like two lines of `rlLabel` is not worth an
 * assertion that cannot fail.
 *
 * Everything else about the grid — what the cells are called, what a tap and a drag do, what
 * the footnote says — is asserted where a player meets it, in
 * `features/player_profile/components/socialAvailabilityStep.test.tsx` and the You tab's
 * `youProfileScreens.test.tsx`; which cell a finger is over is `availabilityGridGeometry`'s.
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

const marks = () => screen.UNSAFE_queryAllByType(Path);

const fillOf = (name: string) =>
  flatten(screen.getByRole('checkbox', { name }).props.style)?.backgroundColor;

/** Two hours of three days, which is enough to tell a cell's state from its neighbour's. */
function rows(selected: readonly string[]): readonly AvailabilityGridRow[] {
  return ['09:00', '19:00'].map((hour) => ({
    key: hour,
    label: hour,
    cells: ['Mon', 'Tue', 'Wed'].map((day) => ({
      key: `${day} ${hour}`,
      selected: selected.includes(`${day} ${hour}`),
      onPress: () => undefined,
      accessibilityLabel: `${day} ${hour}`,
    })),
  }));
}

/** The drag's report, which nothing here drives — a drawing is what is under test. */
const noPaint = () => undefined;

describe('the selected cell', () => {
  it('carries a tick as well as the fill', () => {
    render(<AvailabilityGrid onPaint={noPaint} columnHeads={['Mon']} rows={rows(['Mon 09:00'])} />);

    expect(marks()).toHaveLength(1);
    expect(fillOf('Mon 09:00')).toBe(theme.color.mint);
    expect(screen.getByRole('checkbox', { name: 'Mon 09:00' }).props.accessibilityState).toEqual(
      expect.objectContaining({ checked: true }),
    );
  });

  it('draws one per ticked cell and none anywhere else', () => {
    render(
      <AvailabilityGrid
        onPaint={noPaint}
        columnHeads={['Mon']}
        rows={rows(['Mon 09:00', 'Tue 19:00'])}
      />,
    );

    expect(marks()).toHaveLength(2);
    expect(fillOf('Tue 19:00')).toBe(theme.color.mint);
    expect(fillOf('Tue 09:00')).toBe(theme.color.paper2);
  });

  it('draws nothing at all on an empty week', () => {
    // The empty grid is a complete answer and is drawn as one: nothing greyed, nothing
    // pre-seeded, and no cell ticked on the player's behalf.
    render(<AvailabilityGrid onPaint={noPaint} columnHeads={['Mon']} rows={rows([])} />);

    expect(marks()).toHaveLength(0);
    expect(fillOf('Mon 09:00')).toBe(theme.color.paper2);
  });

  /**
   * The fills are the half of the state a colour-blind player gets, and 6.8 publishes the
   * ratio between them. Pinned as the two tokens rather than as the number: a hex is not
   * reachable from a component, and the ratio is derived from the palette in the section.
   */
  it('separates its two states by a fill a reader of no hue can still tell apart', () => {
    render(<AvailabilityGrid onPaint={noPaint} columnHeads={['Mon']} rows={rows(['Mon 09:00'])} />);

    expect(fillOf('Mon 09:00')).toBe(theme.color.mint);
    expect(fillOf('Tue 09:00')).toBe(theme.color.paper2);
    // The cells carry no border: the card bounds the grid, and a line around each of a
    // hundred and twelve adjacent cells is a fold drawn over and over inside one thing.
    expect(
      flatten(screen.getByRole('checkbox', { name: 'Mon 09:00' }).props.style)?.borderWidth,
    ).toBeUndefined();
  });
});

/**
 * The third fact on an editor cell — a slot **this search** added, which the player never
 * ticked.
 *
 * It is drawn rather than announced-only for the reason the tick is: a cell is a bare
 * rectangle, and the mark is the whole of what separates a square that is part of the ask from
 * one that a rung widened for one search
 * ([#283](https://github.com/Raketa02/Raketa/issues/283)). The bed is the argument for the
 * second plus: `Plus` is volt on the filled cell, and this one is **not** filled — it is not
 * part of the week, and a filled one would read as ticked under a finger that is about to
 * tick it.
 */
describe('the cell a rung added for this search', () => {
  const added = (): readonly AvailabilityGridRow[] =>
    rows([]).map((row) => ({
      ...row,
      cells: row.cells.map((cell) =>
        cell.key === 'Mon 09:00' ? { ...cell, addedForThisSearch: true } : cell,
      ),
    }));

  it('draws the plus, on the unfilled cell, and never the tick', () => {
    render(<AvailabilityGrid onPaint={noPaint} columnHeads={['Mon']} rows={added()} />);

    expect(marks().map((node) => node.props.d as string)).toEqual(['M 6 2.5 V 9.5 M 2.5 6 H 9.5']);
    expect(fillOf('Mon 09:00')).toBe(theme.color.paper2);
  });

  /**
   * The mark says what the *search* did; `checked` says what the *week* holds, and the week
   * does not hold this cell. A cell reported as checked would be one a player unticks by
   * pressing — which is the opposite of what the press does.
   */
  it('is still a cell to press, and reports itself unticked', () => {
    render(<AvailabilityGrid onPaint={noPaint} columnHeads={['Mon']} rows={added()} />);

    expect(screen.getByRole('checkbox', { name: 'Mon 09:00' }).props.accessibilityState).toEqual(
      expect.objectContaining({ checked: false }),
    );
  });
});

describe('the column heads', () => {
  it('are drawn, and hidden from assistive technology so no cell is announced twice', () => {
    render(<AvailabilityGrid onPaint={noPaint} columnHeads={['Mon', 'Tue']} rows={rows([])} />);

    // On screen for whoever is looking at it...
    expect(screen.getByText('Mon', { includeHiddenElements: true })).toBeTruthy();
    // ...and out of the way of whoever is not: a cell already names its own column, so a
    // readable head would be announced once for every row it sits above.
    expect(screen.queryByText('Mon')).toBeNull();
  });
});

/** One row of a diff grid — the states are the whole of what a diff cell carries. */
const diffRows = (states: readonly AvailabilityDiffState[]): readonly AvailabilityDiffRow[] => [
  {
    key: '09:00',
    label: '09:00',
    cells: states.map((state, index) => ({
      key: `Mon ${index}`,
      state,
      accessibilityLabel: state === 'off' ? undefined : `Mon ${index}`,
    })),
  },
];

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
      <AvailabilityGrid
        onPaint={noPaint}
        columnHeads={['Mon']}
        rows={rows([])}
        footnote="Nothing ticked"
      />,
    );

    expect(screen.getByText('Nothing ticked')).toBeTruthy();
    expect(reservedSlots()).toHaveLength(1);

    rerender(<AvailabilityGrid onPaint={noPaint} columnHeads={['Mon']} rows={rows([])} />);

    expect(screen.queryByText('Nothing ticked')).toBeNull();
    expect(reservedSlots()).toHaveLength(1);
  });

  /**
   * And the diff reserves nothing, which is the same rule read rather than an exception to
   * it: what the reservation protects is a cell moving between two taps, and nothing on the
   * diff grid can be tapped. The 44pt it gives back is room `SH.saveav`'s sheet needs — it
   * draws this grid above two buttons inside a sheet that stops at 88% of the screen.
   */
  it('is not reserved on the diff, which has no tap to protect and no room to spare', () => {
    render(<AvailabilityGrid variant="diff" columnHeads={['Mon']} rows={diffRows(['on'])} />);

    expect(reservedSlots()).toHaveLength(0);
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
  it('draws one mark per fact, so no two states differ by colour alone', () => {
    render(
      <AvailabilityGrid
        variant="diff"
        columnHeads={['Mon', 'Tue', 'Wed']}
        rows={diffRows(['on', 'added', 'dropped'])}
      />,
    );

    // A tick, a plus and a dash: three drawings, and the plus is two subpaths in one.
    expect(marks().map((node) => node.props.d as string)).toEqual([
      'M 2.5 6.5 L 5 9 L 9.5 3.5',
      'M 6 2.5 V 9.5 M 2.5 6 H 9.5',
      'M 2.5 6 H 9.5',
    ]);
  });

  it('is not interactive, so nothing on it offers a state a reader could try to change', () => {
    render(
      <AvailabilityGrid
        variant="diff"
        columnHeads={['Mon', 'Tue', 'Wed']}
        rows={diffRows(['on', 'added', 'dropped'])}
      />,
    );

    expect(screen.queryAllByRole('checkbox')).toHaveLength(0);
    expect(screen.getByLabelText('Mon 1')).toBeTruthy();
  });

  it('hides a cell with nothing to say rather than announcing it empty', () => {
    render(
      <AvailabilityGrid variant="diff" columnHeads={['Mon']} rows={diffRows(['off', 'added'])} />,
    );

    // A hundred names between the ones that changed is the double announcement 6.8 hides
    // its column heads to avoid, arriving on a grid that cannot be operated at all.
    expect(screen.queryAllByLabelText(/^Mon/)).toHaveLength(1);
  });

  it('is 6.8 exactly — the same cell, at the same height, on the same fill', () => {
    render(<AvailabilityGrid variant="diff" columnHeads={['Mon']} rows={diffRows(['on'])} />);
    const diffCell = flatten(screen.getByLabelText('Mon 0').props.style);
    screen.unmount();

    render(<AvailabilityGrid onPaint={noPaint} columnHeads={['Mon']} rows={rows(['Mon 09:00'])} />);
    const editorCell = flatten(screen.getByRole('checkbox', { name: 'Mon 09:00' }).props.style);

    expect(diffCell?.height).toBe(grid.cellHeight);
    expect(diffCell?.backgroundColor).toBe(editorCell?.backgroundColor);
    expect(diffCell?.borderRadius).toBe(editorCell?.borderRadius);
  });
});
