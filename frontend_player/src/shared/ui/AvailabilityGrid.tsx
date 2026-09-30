/**
 * The week grid, per design-system 6.8 — seven days across, sixteen hours down.
 *
 * One cell is one **weekly hour**: a standing preference about an ordinary week, and the only
 * place a time preference is expressed anywhere in this product. It names no date and no
 * court, and nothing can be booked from it
 * ([ADR-0189](../../../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) §5,
 * mock 36).
 *
 * ## Days are columns, and the cells are under the touch minimum on purpose
 *
 * The seven-by-three week had days as rows so a cell could reach 44pt by its own geometry.
 * Sixteen hours cannot: sixteen rows at 44pt are 704pt of grid, taller than any phone's page,
 * and a grid that scrolled under the finger painting it would paint the wrong hours. So the
 * week is drawn as mock 36 draws it — `MON … SUN` across, `07:00 … 22:00` down, every cell
 * `size.availability.cellHeight` tall and a seventh of the width — and fits a phone whole. The
 * minimum is met another way: **a press and drag paints a run**, so a week is drawn by a finger
 * rather than hit cell by cell, and each cell is granted half the gap on every side
 * (`hit.availabilityCell`), which the neighbour rule allows and which leaves no dead point
 * between two cells. 6.5 records the departure.
 *
 * **The two columns are bottom-aligned**, which is what keeps each hour label beside its own
 * row without anybody measuring anything: below the column heads both columns are the same
 * stack of cells the same gap apart, so aligning their ends aligns every row in them.
 *
 * ## A tap toggles one hour; a drag paints a run
 *
 * A cell is a `Pressable`, and a tap on it is an ordinary toggle — the caller's `onPress`. A
 * finger that moves `size.availability.paintIntent` instead claims the touch as a **paint**:
 * the cell it began on decides what the drag does — **it ticks, or it clears if that cell was
 * already ticked** — and every cell the finger then crosses gets the same. The pan is
 * `react-native-gesture-handler`'s, as the radar's is
 * ([ADR-0176](../../../../docs/adr/0176-the-radar-moves-on-the-ui-thread-and-draws-one-card.md)), because the
 * grid sits in a page that scrolls: a recogniser that claims the touch before the scroll view's
 * does is what keeps a drag down a column a paint rather than a scroll, and its claiming cancels
 * the press the cell under the finger had begun. The hour labels and the heads are not part of
 * the paint field, so a thumb on them still scrolls the page.
 *
 * **What is reported is the run so far, whole, every time** — `onPaint(run, on)` — never the
 * one cell that was just crossed. A screen draws the run from its own week, and a screen one
 * render behind the finger would otherwise drop the hours it had not drawn yet; painting the
 * same run twice is painting it once (`paintCells`). The arithmetic of which cell a finger is
 * over and which cells a fast drag jumped is `availabilityGridGeometry`'s.
 *
 * **Still no bulk selection.** No row tap, no column tap, no *weekends* shortcut: a shortcut is
 * a claim about what players want. A drag is a player drawing the week they mean.
 *
 * ## Selection is a fill **and** a tick
 *
 * `paper2` → `mint`: 3,39:1 between the two and a relative luminance of 0,824 against 0,208, so
 * a reader who sees no hue at all sees dark hours in a field of pale ones — the non-text contrast
 * Part 13 asks of a graphical object. **The tick is kept although mock 36 draws the fill
 * alone**: every state carries a word or a shape, never colour alone, and a lightness is still a
 * colour. The 12 × 12 tick fits the 20pt cell with room to spare, in `surface` over the fill at
 * 4,07:1, which a 2pt graphical object clears. `accessibilityState.checked` carries the same
 * fact for whoever sees neither.
 *
 * ## One cell can also carry a mark it did not earn
 *
 * A times rung widens the searcher's own week by one hour **for one search**, and the week the
 * player filled in disagrees with the search that ran until the grid says which hour that was
 * ([#283](https://github.com/Raketa02/Raketa/issues/283)). So an editor cell takes an optional
 * `addedForThisSearch`, drawn as a plus on the **unfilled** cell. **It is a third fact and not
 * a third state**: the cell is unselected, reports itself unchecked, and toggles like every
 * other, because pressing it is how a player makes that widening their own ask.
 *
 * ## The card is the grid's own, and so is the footnote inside it
 *
 * 6.8 draws the week on a `surface` card with the footnote beneath a hairline **inside** it,
 * because the sentence is about the grid rather than about the screen. On the editor the slot's
 * height is reserved either way — the moment a player is most likely to tick a second hour is
 * immediately after ticking the first, and a grid that jumped under a finger mid-tap would
 * select the wrong one. **The diff grid reserves nothing**: nothing on it is pressable, so there
 * is no finger for a reservation to protect, and `SH.saveav` draws it inside a sheet that stops
 * at 88% of the screen.
 *
 * ## Every word is the caller's
 *
 * This file holds no copy. The heads, the row labels, each cell's accessible name and the
 * footnote all arrive as props, because the onboarding step, the You tab and Play do not say
 * the same things.
 *
 * ## The diff variant is this grid, not a second one
 *
 * `SH.saveav` draws the same week with a **third fact** on each cell — the hours this search
 * added and the ones it dropped. `the-words.md` §20.7 calls it *"a different control with a
 * third fact … not interactive"*, which describes a second accessibility tree and not a second
 * file: it is this geometry **exactly**. Its cells are not pressable and carry no `checked`, a
 * cell with nothing to say is hidden rather than announced empty, and its three facts are three
 * **shapes** from `Tick`'s family — the tick, a plus on the fill, a dash on the paper.
 */

import { useMemo, useRef, type ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View, type LayoutChangeEvent } from 'react-native';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';

import {
  cellUnder,
  cellsCrossed,
  type FieldPoint,
  type GridPosition,
} from './availabilityGridGeometry';
import { theme } from './theme';
import { Dash, Plus, PlusOnSurface, Tick } from './Tick';

const grid = theme.size.availability;

/** The paint gesture, by the test id a suite finds it with — see `test-support/weekGridTouch`. */
export const AVAILABILITY_PAINT_GESTURE = 'availability-paint';

/** The field the paint gesture reads, by the test id a suite lays it out with. */
export const AVAILABILITY_PAINT_FIELD = 'availability-paint-field';

export interface AvailabilityGridCell {
  readonly key: string;
  /** Drawn `mint`-filled with a tick, and announced as checked. Owned by the caller. */
  readonly selected: boolean;
  /**
   * An hour **this one search** added, which the player never ticked — drawn as a plus on the
   * unfilled cell ([#283](https://github.com/Raketa02/Raketa/issues/283)).
   *
   * It is a third *fact*, never a third state: the cell is not selected, reports itself
   * unticked, and presses like any other, because pressing it is how a player makes the
   * widening their own.
   */
  readonly addedForThisSearch?: boolean;
  /** Fires on a tap, ticked or not. The cell reports; the caller decides. */
  readonly onPress: () => void;
  /**
   * Names **the day and the hour**, because a screen reader gets no help from the row a cell
   * is in or the column it is under.
   */
  readonly accessibilityLabel: string;
}

export interface AvailabilityGridRow {
  readonly key: string;
  /** The hour, as the caller writes it — the column is content-sized. */
  readonly label: string;
  readonly cells: readonly AvailabilityGridCell[];
}

/**
 * What a diff cell says about one hour, and the whole of it.
 *
 * `on` and `off` are this week as the search left it; `added` and `dropped` are the two facts
 * the editor has no room for. Each is a shape rather than a colour — `Tick`, `Plus` and `Dash`
 * — because the prototype's volt ring and 45% opacity are Part 13's prohibition drawn twice.
 */
export type AvailabilityDiffState = 'on' | 'off' | 'added' | 'dropped';

export interface AvailabilityDiffCell {
  readonly key: string;
  readonly state: AvailabilityDiffState;
  /**
   * `{Day} {hour}` · `{Day} {hour}, newly added` · `{Day} {hour}, dropped` (`the-words.md`
   * §20.7). **Omitted means hidden**, not announced empty: an hour that was off and stayed off
   * has nothing to tell a listener.
   */
  readonly accessibilityLabel?: string;
}

export interface AvailabilityDiffRow {
  readonly key: string;
  readonly label: string;
  readonly cells: readonly AvailabilityDiffCell[];
}

interface GridChrome {
  /** One per column, in the order the cells run — the seven days. Decoration to assistive
   *  technology. */
  readonly columnHeads: readonly string[];
  /**
   * At most two lines under the grid, inside the card and beneath a hairline. Reserved on the
   * **editor** whether or not it has anything in it; absent from the **diff** — see the module
   * note.
   */
  readonly footnote?: string;
}

export interface AvailabilityGridEditorProps extends GridChrome {
  readonly variant?: 'editor';
  readonly rows: readonly AvailabilityGridRow[];
  /**
   * A drag painted a run: **every cell it has crossed so far, whole**, the one it began on
   * first, and `on` — whether the run ticks (it began on an unticked cell) or clears. Reported
   * again, one cell longer, each time the finger reaches another cell.
   */
  readonly onPaint: (run: readonly GridPosition[], on: boolean) => void;
}

export interface AvailabilityGridDiffProps extends GridChrome {
  readonly variant: 'diff';
  readonly rows: readonly AvailabilityDiffRow[];
}

/** The two modes are a union rather than a flag, so a diff row can never reach the editor. */
export type AvailabilityGridProps = AvailabilityGridEditorProps | AvailabilityGridDiffProps;

export function AvailabilityGrid(props: AvailabilityGridProps) {
  const { columnHeads, footnote } = props;
  const cellRows = (
    <View style={s.cellRows}>
      {drawnRows(props).map((row) => (
        <View key={row.key} style={s.cellRow}>
          {row.cells}
        </View>
      ))}
    </View>
  );

  return (
    <View style={s.card}>
      <View style={s.grid}>
        {/* Content-sized so Dynamic Type grows it, capped by `labelMaxRatio` so it cannot
            grow into the cells. Not part of the paint field: a thumb here scrolls the page. */}
        <View style={s.labels}>
          {props.rows.map((row) => (
            <View key={row.key} style={s.labelBox}>
              <Text style={s.label} numberOfLines={1}>
                {row.label}
              </Text>
            </View>
          ))}
        </View>

        <View style={s.cells}>
          {/* Hidden from assistive technology: every cell already names its own day, so a
              head that was readable would be announced once per hour it sits above. */}
          <View
            style={s.heads}
            accessibilityElementsHidden
            importantForAccessibility="no-hide-descendants"
          >
            {columnHeads.map((head) => (
              <Text key={head} style={s.head} numberOfLines={1}>
                {head}
              </Text>
            ))}
          </View>

          {props.variant === 'diff' ? (
            cellRows
          ) : (
            <PaintField rows={props.rows} onPaint={props.onPaint}>
              {cellRows}
            </PaintField>
          )}
        </View>
      </View>

      {/* No slot at all on the diff: nothing there is pressable, so there is no tap for a
          reserved height to protect, and the sheet it is drawn in has no room to spare. */}
      {props.variant === 'diff' && footnote === undefined ? null : (
        <View style={s.footnote}>
          {/* Two lines is a ceiling as well as a floor (6.8): a third line would push the
              grid, which is the movement the reserved slot exists to prevent. */}
          {footnote === undefined ? null : (
            <>
              <View style={s.footnoteRule} />
              <Text style={s.footnoteText} numberOfLines={2}>
                {footnote}
              </Text>
            </>
          )}
        </View>
      )}
    </View>
  );
}

/** A drag in progress: what it does, every cell it has crossed, and the one it is on. */
interface Run {
  readonly on: boolean;
  readonly cells: readonly GridPosition[];
  readonly at: GridPosition;
}

/**
 * The cells area as a paint surface — the pan, and the size it reads positions against.
 *
 * The pan is built once, so it reads the rows and the callback through a ref rather than
 * closing over a render's: a drag reports against the week that is on screen now, not the one
 * that was there when the touch began — `RadiusSlider`'s rule, for the same reason.
 */
function PaintField({
  rows,
  onPaint,
  children,
}: {
  readonly rows: readonly AvailabilityGridRow[];
  readonly onPaint: AvailabilityGridEditorProps['onPaint'];
  readonly children: ReactNode;
}) {
  const size = useRef({ width: 0, height: 0 });
  const latest = useRef({ rows, onPaint });
  latest.current = { rows, onPaint };
  const run = useRef<Run | undefined>(undefined);

  const gesture = useMemo(() => {
    const under = (point: FieldPoint) =>
      cellUnder(point, {
        ...size.current,
        rows: latest.current.rows.length,
        columns: latest.current.rows[0]?.cells.length ?? 0,
        gap: grid.gap,
      });

    /** Carry the run to the cell under `point`, and report it if that crossed anything. */
    const reach = (point: FieldPoint) => {
      const held = run.current;
      const at = under(point);
      if (held === undefined || at === undefined) return;
      const crossed = cellsCrossed(held.at, at).filter(
        (cell) => !held.cells.some((painted) => samePosition(painted, cell)),
      );
      run.current = { ...held, cells: [...held.cells, ...crossed], at };
      if (crossed.length > 0) latest.current.onPaint(run.current.cells, held.on);
    };

    return (
      Gesture.Pan()
        .withTestId(AVAILABILITY_PAINT_GESTURE)
        // State updates on every cell, and no animation to keep off the JavaScript thread.
        .runOnJS(true)
        .minDistance(grid.paintIntent)
        .onStart((event) => {
          // Where the finger went down, which is where the claimed pan has travelled from.
          const first = under({ x: event.x - event.translationX, y: event.y - event.translationY });
          if (first === undefined) return;
          const on = latest.current.rows[first.row]?.cells[first.column]?.selected !== true;
          run.current = { on, cells: [first], at: first };
          latest.current.onPaint(run.current.cells, on);
          reach({ x: event.x, y: event.y });
        })
        .onUpdate((event) => reach({ x: event.x, y: event.y }))
        .onFinalize(() => {
          run.current = undefined;
        })
    );
  }, []);

  return (
    <GestureDetector gesture={gesture}>
      <View
        testID={AVAILABILITY_PAINT_FIELD}
        onLayout={(event: LayoutChangeEvent) => {
          const { width, height } = event.nativeEvent.layout;
          size.current = { width, height };
        }}
      >
        {children}
      </View>
    </GestureDetector>
  );
}

function samePosition(one: GridPosition, other: GridPosition): boolean {
  return one.row === other.row && one.column === other.column;
}

/**
 * The rows, with their cells already drawn — the one place the two modes differ.
 *
 * The row wrapper is written once and the mode chooses only what goes in it, because the two
 * grids are the same geometry and a second copy of the loop is the second copy of the geometry
 * arriving as code.
 */
function drawnRows(
  props: AvailabilityGridProps,
): readonly { readonly key: string; readonly cells: readonly ReactNode[] }[] {
  return props.variant === 'diff'
    ? props.rows.map((row) => ({
        key: row.key,
        cells: row.cells.map((cell) => <DiffCell key={cell.key} cell={cell} />),
      }))
    : props.rows.map((row) => ({
        key: row.key,
        cells: row.cells.map((cell) => <Cell key={cell.key} cell={cell} />),
      }));
}

/**
 * One cell — `size.availability.cellHeight` tall and a seventh of the field wide, reachable to
 * half the gap on every side.
 *
 * `checkbox` rather than `button` because the state is the point and the role is what carries
 * it: a hundred and twelve buttons announce identical actions, where a hundred and twelve
 * checkboxes announce answers. `checked` is always present, never omitted when false, or *not
 * ticked* would be indistinguishable from *not a choice*.
 *
 * There is **no disabled cell and no fourth state**: every cell toggles, always, in both
 * directions, and a greyed one would be the screen claiming a constraint the domain does not
 * have.
 */
function Cell({ cell }: { readonly cell: AvailabilityGridCell }) {
  return (
    <Pressable
      accessibilityRole="checkbox"
      accessibilityLabel={cell.accessibilityLabel}
      accessibilityState={{ checked: cell.selected }}
      onPress={cell.onPress}
      hitSlop={theme.hit.availabilityCell}
      // Touch has no hover, so the pressed appearance is declared rather than inherited
      // (6.6), and it sits over either of the two states.
      style={({ pressed }) => [
        s.cell,
        cell.selected ? s.cellSelected : undefined,
        pressed ? s.cellPressed : undefined,
      ]}
    >
      {cell.selected ? <Tick /> : null}
      {/* Never both: a cell the player has ticked is theirs, and the caller drops the mark on
          the press that ticks it. */}
      {!cell.selected && cell.addedForThisSearch === true ? <PlusOnSurface /> : null}
    </Pressable>
  );
}

/**
 * One diff cell — the same box, and nothing that can be operated.
 *
 * Not a `Pressable` and not a `checkbox`: §20.7 records the diff grid as *"not interactive"*,
 * and a role that carried `checked` here would offer a state a reader could try to change.
 */
function DiffCell({ cell }: { readonly cell: AvailabilityDiffCell }) {
  const hidden = cell.accessibilityLabel === undefined;
  return (
    <View
      accessible={!hidden}
      accessibilityLabel={cell.accessibilityLabel}
      accessibilityElementsHidden={hidden}
      importantForAccessibility={hidden ? 'no-hide-descendants' : 'auto'}
      style={[s.cell, FILLED.has(cell.state) ? s.cellSelected : undefined]}
    >
      {MARKS[cell.state]}
    </View>
  );
}

/** The two states drawn on the filled cell — this week as the search leaves it. */
const FILLED = new Set<AvailabilityDiffState>(['on', 'added']);

const MARKS: Readonly<Record<AvailabilityDiffState, ReactNode>> = {
  on: <Tick />,
  added: <Plus />,
  dropped: <Dash />,
  off: null,
};

const s = StyleSheet.create({
  // The week's own card — 6.8. The footnote lives inside it because the sentence is about
  // the grid rather than about whatever comes next on the page.
  card: {
    backgroundColor: theme.color.surface,
    borderRadius: theme.radius.card,
    borderWidth: 1,
    borderColor: theme.color.line,
    padding: grid.cardPadding,
  },
  // Bottom-aligned, so the labels line up with their rows however tall the heads grow.
  grid: { flexDirection: 'row', alignItems: 'flex-end', gap: grid.labelGutter },
  labels: { maxWidth: `${grid.labelMaxRatio * 100}%`, gap: grid.gap },
  labelBox: { height: grid.cellHeight, justifyContent: 'center' },
  // A column of clock figures read down the grid, so the mono role that keeps their colons
  // in line — mock 36's `07:00`.
  label: { ...theme.num.tiny, ...theme.tabular, color: theme.color.muted },
  cells: { flex: 1, gap: grid.gap },
  heads: { flexDirection: 'row', gap: grid.gap },
  // `flab`: a head sits directly above cells a finger is going to land on, which is not a
  // region being READ.
  head: {
    ...theme.type.flab,
    color: theme.color.muted,
    flex: 1,
    textAlign: 'center',
    textTransform: 'uppercase',
  },
  cellRows: { gap: grid.gap },
  cellRow: { flexDirection: 'row', gap: grid.gap },
  cell: {
    flex: 1,
    height: grid.cellHeight,
    borderRadius: theme.radius.availabilityCell,
    // No border. The card bounds the grid; a line around each of a hundred and twelve
    // adjacent cells is a fold drawn over and over inside one thing.
    backgroundColor: theme.color.paper2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cellSelected: { backgroundColor: theme.color.mint },
  cellPressed: { opacity: 0.7 },
  // Two lines of `rlLabel`, laid out whether or not anything is in them.
  footnote: { minHeight: grid.footnoteMinHeight, marginTop: theme.space.md },
  footnoteRule: {
    height: StyleSheet.hairlineWidth,
    backgroundColor: theme.color.line,
    marginBottom: theme.space.sm,
  },
  footnoteText: { ...theme.type.rlLabel, color: theme.color.muted },
});
