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
 * phone has, and no `hitSlop` closes a 2,6pt-per-cell deficit against neighbours 6pt apart.
 * Turned the other way a cell is 44 tall by its own geometry and, with the label column at
 * its cap, 65,5pt wide on that same phone — the first control in the app that reaches the
 * touch minimum without being granted anything. `profileControlGeometry.test.ts` pins that
 * arithmetic, because it is the kind that holds on the phone an agent tests on and fails on
 * the one a player owns.
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
 * ## Selection is a fill inversion **and** a tick
 *
 * Inverting to `ink` is a 17,50:1 luminance change rather than a change of hue, so it
 * survives colour blindness on its own — but a cell is a bare rectangle, and twenty-one of
 * them differing only in lightness is a texture. The tick is the shape Part 13 asks for,
 * and it is what makes a ticked week read as a pattern rather than as a stain. Round cap and
 * join: at 2pt, butt caps make a tick read as two bars meeting at a corner.
 *
 * ## Every word is the caller's
 *
 * This file holds no copy. The heads, the day labels, each cell's accessible name and the
 * footnote all arrive as props, because the onboarding step that collects a week and the
 * profile editor that will change one do not say the same things.
 */

import { Pressable, StyleSheet, Text, View } from 'react-native';

import { theme } from './theme';
import { Tick } from './Tick';

const grid = theme.size.availability;

export interface AvailabilityGridCell {
  readonly key: string;
  /** Drawn ink-filled with a tick, and announced as checked. Owned by the caller. */
  readonly selected: boolean;
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

export interface AvailabilityGridProps {
  /** One per column, in the order the cells run. Decoration to assistive technology. */
  readonly columnHeads: readonly string[];
  readonly rows: readonly AvailabilityGridRow[];
  /**
   * At most two lines under the grid, and **its height is reserved whether or not it has
   * anything in it**: the moment a player is most likely to tick a second cell is
   * immediately after ticking the first, and a grid that jumped upward under a finger
   * mid-tap would select the wrong one.
   */
  readonly footnote?: string;
}

export function AvailabilityGrid({ columnHeads, rows, footnote }: AvailabilityGridProps) {
  return (
    <View>
      <View style={s.grid}>
        {/* Content-sized so Dynamic Type grows it, capped by `labelMaxRatio` so it cannot
            grow into the cells' 44pt. */}
        <View style={s.labels}>
          {rows.map((row) => (
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

          {rows.map((row) => (
            <View key={row.key} style={s.cellRow}>
              {row.cells.map((cell) => (
                <Cell key={cell.key} cell={cell} />
              ))}
            </View>
          ))}
        </View>
      </View>

      <View style={s.footnote}>
        {/* Two lines is a ceiling as well as a floor (6.8): a third line would push the
            grid, which is the movement the reserved slot exists to prevent. */}
        {footnote === undefined ? null : (
          <Text style={s.footnoteText} numberOfLines={2}>
            {footnote}
          </Text>
        )}
      </View>
    </View>
  );
}

/**
 * One cell — 44 tall by its own geometry, with no `hitSlop` to grant.
 *
 * `checkbox` rather than `button` because the state is the point and the role is what
 * carries it: twenty-one buttons announce twenty-one identical actions, where twenty-one
 * checkboxes announce twenty-one answers. `checked` is always present, never omitted when
 * false, or *not ticked* would be indistinguishable from *not a choice*.
 *
 * There is **no disabled cell and no fourth state**: every cell toggles, always, in both
 * directions, and a greyed one would be the screen claiming a constraint the domain does
 * not have.
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
    </Pressable>
  );
}

const s = StyleSheet.create({
  // Bottom-aligned, so the labels line up with their rows however tall the heads grow.
  grid: { flexDirection: 'row', alignItems: 'flex-end', gap: grid.labelGutter },
  labels: { maxWidth: `${grid.labelMaxRatio * 100}%`, gap: grid.gap },
  labelBox: { height: grid.cellHeight, justifyContent: 'center' },
  // `flab`, not the eyebrow role: it labels cells a player is about to OPERATE, and 3.3
  // says the two are not interchangeable.
  label: { ...theme.type.flab, color: theme.color.ink, textTransform: 'uppercase' },
  cells: { flex: 1, gap: grid.gap },
  heads: { flexDirection: 'row', gap: grid.gap },
  // The eyebrow role: these label a region being READ, and nothing here is pressable.
  head: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    flex: 1,
    textAlign: 'center',
    textTransform: 'uppercase',
  },
  cellRow: { flexDirection: 'row', gap: grid.gap },
  cell: {
    flex: 1,
    height: grid.cellHeight,
    borderRadius: theme.radius.availabilityCell,
    borderWidth: 1,
    borderColor: theme.color.line,
    backgroundColor: theme.color.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cellSelected: { backgroundColor: theme.color.ink, borderColor: theme.color.ink },
  cellPressed: { opacity: 0.7 },
  // Two lines of `tiny`, laid out whether or not anything is in them.
  footnote: { minHeight: grid.footnoteMinHeight, marginTop: theme.space.xs },
  footnoteText: { ...theme.type.tiny, color: theme.color.muted },
});
