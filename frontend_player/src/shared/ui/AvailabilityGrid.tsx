/**
 * The availability grid, per design-system 6.8 — seven days by three parts of the day.
 *
 * One cell is one standing preference, and the grid is the only place a time preference is
 * expressed anywhere in this product. It names no hour, no date and no court, and nothing
 * can be booked from it.
 *
 * **This is not the deleted 6.7 returning under a new number.** The slot squares that went
 * with the booking grid in the 2026-08-25 reset were four states deep because a court is
 * free, held, taken or yours. A cell here has two, and `radius.availabilityCell` is a fresh
 * token beside the dead `daySquare` for exactly that reason.
 *
 * ## Days are rows, and that is a touch decision
 *
 * Seven cells at the 44pt minimum want 308pt against the 290pt of content the narrowest
 * phone has, and no `hitSlop` closes a per-cell deficit against neighbours 6pt apart — nor
 * does the widest phone in the population close it, so it is a property of seven columns
 * rather than of one device. Turned this way a cell is 44 tall by its own geometry and, with
 * the card taken off and the label column at its cap, 59,5pt wide on that same phone — the
 * first control in the app that reaches the touch minimum in **both** axes without being
 * granted anything. `profileControlGeometry.test.ts` pins that arithmetic, because it is the
 * kind that holds on the phone an agent tests on and fails on the one a player owns.
 *
 * **The two columns are bottom-aligned**, which is what keeps each day label beside its own
 * row without anybody measuring anything: below the column heads both columns are the same
 * stack of 44pt boxes 6pt apart, so aligning their ends aligns every row in them. A fixed
 * height for the heads would have done it too, until the OS text size grew them.
 *
 * ## A cell is the only thing here that is pressable
 *
 * Not a day label, not a column head, not the row or the column they name — and there is no
 * bulk selection at all. That absence is the component's, not the caller's: a row tap would
 * be a claim about what players want, and describing an irregular week is the whole reason
 * the grid is twenty-one independent answers rather than three.
 *
 * ## Selection is a fill **and** a tick
 *
 * The fill goes `paper2` → `mint`: 3,39:1 between the two and a relative luminance of 0,824
 * against 0,208, so a reader who sees no hue at all sees a dark square in a field of pale
 * ones, which is what [Part 13](../../../docs/design-system.md#part-13--accessibility) asks
 * of a non-text graphical object. But a cell is a bare rectangle, and twenty-one of them
 * differing only in lightness is a texture: the tick is the shape Part 13 asks for, and it is
 * what makes a ticked week read as a pattern rather than as a stain. Round cap and join — at
 * 2pt, butt caps make a tick read as two bars meeting at a corner — in `surface` over the
 * fill, 4,07:1, which a 2pt graphical object clears and which is not the white **type** on
 * `mint` that Rule C refuses.
 *
 * `accessibilityState.checked` carries the same fact for whoever sees neither.
 *
 * ## One cell can also carry a mark it did not earn
 *
 * A times rung widens the searcher's own grid by one slot **for one search**, and the week the
 * player filled in disagrees with the search that ran until the grid says which cell that was
 * ([#283](https://github.com/Raketa02/Raketa/issues/283)). So an editor cell takes an optional
 * `addedForThisSearch`, drawn as a plus on the **unfilled** square.
 *
 * **It is a third fact and not a third state**: the cell is unselected, reports itself
 * unchecked, and toggles like every other, because pressing it is how a player makes that
 * widening their own ask. The bed is what forces a second plus in `Tick` — the diff's is volt
 * on `mint`, and this square is not filled.
 *
 * ## The card is the grid's own, and so is the footnote inside it
 *
 * 6.8 draws the week on a `surface` card with the footnote beneath a hairline **inside** it,
 * because the sentence is about the grid rather than about the screen: a count of slots
 * floating under a bare block of squares belonged to whatever came next on the page. The
 * hairline is drawn only when there are words to separate, and on the editor the slot's
 * height is reserved either way — the moment a player is most likely to tick a second cell is
 * immediately after ticking the first, and a grid that jumped upward under a finger mid-tap
 * would select the wrong one.
 *
 * **The diff grid reserves nothing**, and that is the same rule read rather than an exception
 * to it. What the reservation protects is a cell moving under a finger between two taps, and
 * nothing on the diff is pressable: it cannot gain a footnote, cannot lose one, and takes 44pt
 * of empty card for a message it has no way of being handed. Those 44 are worth having —
 * `SH.saveav` draws this grid above its two buttons inside a sheet that stops at 88% of the
 * screen.
 *
 * ## Every word is the caller's
 *
 * This file holds no copy. The heads, the row labels, each cell's accessible name and the
 * footnote all arrive as props, because the onboarding step that collects a week and the
 * profile editor that will change one do not say the same things.
 *
 * ## The diff variant is this grid, not a second one
 *
 * `SH.saveav` draws the same seven-by-three week with a **third fact** on each cell — the
 * slots this search added and the ones it dropped. `the-words.md` §20.7 calls it *"a
 * different control with a third fact … not interactive"*, which describes a second
 * accessibility tree and not a second file: it is this geometry **exactly**, and a second
 * copy of it is the drift `Tick` was extracted to prevent.
 *
 * **One component, two modes, two accessibility trees.** The editor's cells are twenty-one
 * `checkbox`es; the diff's are not interactive at all, so nothing there is pressable, nothing
 * carries `checked`, and a cell with nothing to say is hidden rather than announced empty.
 *
 * The prototype's scheme is **replaced rather than carried over**, because it is a
 * [Part 13](../../../docs/design-system.md#part-13--accessibility) violation twice: *new* was
 * a volt ring and *dropped* was 45% opacity — colour as the only signal, on a sheet whose own
 * body copy names the colour as the mechanism — and a volt ring drawn on paper is 1,3:1 and
 * simply not there. The three facts are three **shapes** instead, from `Tick`'s own family.
 */

import { type ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { theme } from './theme';
import { Dash, Plus, PlusOnSurface, Tick } from './Tick';

const grid = theme.size.availability;

export interface AvailabilityGridCell {
  readonly key: string;
  /** Drawn `mint`-filled, and announced as checked. Owned by the caller. */
  readonly selected: boolean;
  /**
   * A slot **this one search** added, which the player never ticked — drawn as a plus on the
   * unfilled cell ([#283](https://github.com/Raketa02/Raketa/issues/283)).
   *
   * It is a third *fact*, never a third state: the cell is not selected, reports itself
   * unticked, and presses like any other, because pressing it is how a player makes the
   * widening their own. What the mark adds is that the week on screen and the week the search
   * ran on can be told apart at all.
   */
  readonly addedForThisSearch?: boolean;
  /** Fires on every press, ticked or not. The cell reports; the caller decides. */
  readonly onPress: () => void;
  /**
   * Names **the day and the part of the day**, because a screen reader gets no help from
   * the row a cell is in or the column it is under.
   */
  readonly accessibilityLabel: string;
}

export interface AvailabilityGridRow {
  readonly key: string;
  /** The day, as short as the caller likes — the column is content-sized. */
  readonly label: string;
  readonly cells: readonly AvailabilityGridCell[];
}

/**
 * What a diff cell says about one slot, and the whole of it.
 *
 * `on` and `off` are this week as the search left it; `added` and `dropped` are the two
 * facts the editor has no room for. Each is a shape rather than a colour — `Tick`, `Plus`
 * and `Dash` — because the prototype's volt ring and 45% opacity are Part 13's prohibition
 * drawn twice.
 */
export type AvailabilityDiffState = 'on' | 'off' | 'added' | 'dropped';

export interface AvailabilityDiffCell {
  readonly key: string;
  readonly state: AvailabilityDiffState;
  /**
   * `{Day} {part}` · `{Day} {part}, newly added` · `{Day} {part}, dropped`
   * (`the-words.md` §20.7). **Omitted means hidden**, not announced empty: a slot that was
   * off and stayed off has nothing to tell a listener, and twenty-one of those between the
   * ones that do is the double announcement 6.8 hides its column heads to avoid.
   */
  readonly accessibilityLabel?: string;
}

export interface AvailabilityDiffRow {
  readonly key: string;
  readonly label: string;
  readonly cells: readonly AvailabilityDiffCell[];
}

interface GridChrome {
  /** One per column, in the order the cells run — the three parts of the day. Decoration to
   *  assistive technology. */
  readonly columnHeads: readonly string[];
  /**
   * At most two lines under the grid, inside the card and beneath a hairline.
   *
   * On the **editor** its height is reserved whether or not it has anything in it: the moment
   * a player is most likely to tick a second cell is immediately after ticking the first, and
   * a grid that jumped upward under a finger mid-tap would select the wrong one. The hairline
   * is drawn only when there is something to separate.
   *
   * On the **diff** there is no slot at all — see the module note.
   */
  readonly footnote?: string;
}

export interface AvailabilityGridEditorProps extends GridChrome {
  readonly variant?: 'editor';
  readonly rows: readonly AvailabilityGridRow[];
}

export interface AvailabilityGridDiffProps extends GridChrome {
  readonly variant: 'diff';
  readonly rows: readonly AvailabilityDiffRow[];
}

/** The two modes are a union rather than a flag, so a diff row can never reach the editor. */
export type AvailabilityGridProps = AvailabilityGridEditorProps | AvailabilityGridDiffProps;

export function AvailabilityGrid(props: AvailabilityGridProps) {
  const { columnHeads, footnote } = props;
  return (
    <View style={s.card}>
      <View style={s.grid}>
        {/* Content-sized so Dynamic Type grows it, capped by `labelMaxRatio` so it cannot
            grow into the cells' 44pt. */}
        <View style={s.labels}>
          {props.rows.map((row) => (
            <View key={row.key} style={s.labelBox}>
              {/* No `numberOfLines`: 6.8 has Dynamic Type *grow* these, and a truncated
                  `Tue` and `Thu` are the same three characters — the ambiguity the short
                  form was chosen to avoid. `labelMaxRatio` is what protects the cells. */}
              <Text style={s.label}>{row.label}</Text>
            </View>
          ))}
        </View>

        <View style={s.cells}>
          {/* Hidden from assistive technology: every cell already names its own column, so
              a head that was readable would be announced once per row it sits above. */}
          <View
            style={s.heads}
            accessibilityElementsHidden
            importantForAccessibility="no-hide-descendants"
          >
            {columnHeads.map((head) => (
              // Wraps rather than truncates, for the labels' reason: the widest head is
              // close to a cell's width on the narrowest phone, and a lost tail is worse
              // than a second line the bottom-aligned columns already absorb.
              <Text key={head} style={s.head}>
                {head}
              </Text>
            ))}
          </View>

          {cellRows(props).map((row) => (
            <View key={row.key} style={s.cellRow}>
              {row.cells}
            </View>
          ))}
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

/**
 * The rows, with their cells already drawn — the one place the two modes differ.
 *
 * The row wrapper is written once and the mode chooses only what goes in it, because the two
 * grids are the same seven-by-three geometry and a second copy of the loop is the second copy
 * of the geometry arriving as code.
 */
function cellRows(
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
 * One cell — 44 tall and 44 wide by its own geometry, with no `hitSlop` to grant.
 *
 * `checkbox` rather than `button` because the state is the point and the role is what
 * carries it: twenty-one buttons announce twenty-one identical actions, where twenty-one
 * checkboxes announce twenty-one answers. `checked` is always present, never omitted when
 * false, or *not ticked* would be indistinguishable from *not a choice*.
 *
 * There is **no disabled cell and no fourth state**: every cell toggles, always, in both
 * directions, and a greyed one would be the screen claiming a constraint the domain does
 * not have. `addedForThisSearch` does not make one — it is a mark on an unticked cell that
 * presses exactly like its neighbours, and `checked` stays what the *week* says rather than
 * what the search did.
 */
function Cell({ cell }: { readonly cell: AvailabilityGridCell }) {
  return (
    <Pressable
      accessibilityRole="checkbox"
      accessibilityLabel={cell.accessibilityLabel}
      accessibilityState={{ checked: cell.selected }}
      onPress={cell.onPress}
      // Touch has no hover, so the pressed appearance is declared rather than inherited
      // (6.6), and it sits over either of the two states.
      style={({ pressed }) => [
        s.cell,
        cell.selected ? s.cellSelected : undefined,
        pressed ? s.cellPressed : undefined,
      ]}
    >
      {cell.selected ? <Tick /> : null}
      {/* Never both: a cell the player has ticked is theirs, and the caller drops the mark
          on the tap that ticks it. */}
      {!cell.selected && cell.addedForThisSearch === true ? <PlusOnSurface /> : null}
    </Pressable>
  );
}

/**
 * One diff cell — the same 44pt box, and nothing that can be operated.
 *
 * Not a `Pressable` and not a `checkbox`: §20.7 records the diff grid as *"not interactive"*,
 * and a role that carried `checked` here would offer a state a reader could try to change.
 * The three drawn facts are three marks in one 12 × 12 box, so a reader who cannot separate
 * the fills still separates a tick from a plus from a dash.
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
  // `flab`, not the eyebrow role: it labels cells a player is about to OPERATE, and 3.3
  // says the two are not interchangeable.
  label: { ...theme.type.flab, color: theme.color.ink, textTransform: 'uppercase' },
  cells: { flex: 1, gap: grid.gap },
  heads: { flexDirection: 'row', gap: grid.gap },
  // `flab` as well, and for the same reason the day labels take it: a head sits directly
  // above cells a finger is going to land on, which is not a region being READ.
  head: {
    ...theme.type.flab,
    color: theme.color.ink,
    flex: 1,
    textAlign: 'center',
    textTransform: 'uppercase',
  },
  cellRow: { flexDirection: 'row', gap: grid.gap },
  cell: {
    flex: 1,
    height: grid.cellHeight,
    borderRadius: theme.radius.availabilityCell,
    // No border. The card bounds the grid; a line around each of twenty-one adjacent
    // squares is a fold drawn twenty-one times inside one thing.
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
