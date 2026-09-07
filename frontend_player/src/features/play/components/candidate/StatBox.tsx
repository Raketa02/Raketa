/**
 * One recessed box on the competitive card — a name, and the fact under it
 * ([#312](https://github.com/Raketa02/Raketa/issues/312)).
 *
 * The shape [7.13](../../../../../docs/design-system.md#713-the-record-block) and
 * [7.14](../../../../../docs/design-system.md#714-the-stake-box) share. Three of them across
 * the card are the record; two are what is at stake. They are one component because they are
 * one object: a `paper2` box with a `rlLabel` over a figure, and the two rows differ in what
 * the figure is and in nothing else. Written twice, the second copy is where the padding stops
 * matching.
 *
 * ## Why a box at all, when the card already has `FactRow`
 *
 * A `FactRow` is a label opposite a value on one line, and it is the shape for a fact the card
 * **states** — the level row, the meta line. These are five figures the reader **compares**:
 * three across, then two across, each under its own name. A row apiece would be five more
 * lines on a card that is already a panel, a name, a pill, a band and a tag row, and the three
 * record figures would stop reading as one thing.
 *
 * **The ground is the argument, not decoration.** `paper2` is this system's recessed surface
 * inside a card ([6.8](../../../../../docs/design-system.md#68-the-availability-grid)'s
 * unticked cell, `DeclarationStanding`'s line), and recessing is what keeps *Player Score 74*
 * from reading as a second rating beside the Level printed hugely on the panel: it is what the
 * platform watched, held apart from what the player published. `muted` on `paper2` is 4,49 and
 * [2.5](../../../../../docs/design-system.md#25-contrast--computed) licenses it **at 11pt and
 * above**, which `rlLabel`'s 11,5 clears; the figure is `ink` at 14,57.
 *
 * ## It announces nothing
 *
 * §20.1 merges an actionless element into the nearest action above it, which here is the card
 * body — so the label and the figure are plain `Text`, exactly as `FactRow`'s are, and every
 * box drawn is a clause of `candidateCardLabel` instead. That is the rule the Social tag row
 * shipped with, read on a box: *do not draw one the label does not speak*.
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme } from '@/shared/ui';

import type { ReactNode } from 'react';

export interface StatBoxProps {
  /** The block's own name — *Player Score*, *Last 5*, *Counted*, *Win, counted*. */
  readonly label: string;
  /**
   * The fact, already drawn.
   *
   * A node rather than a string because one of the five is not one: the run of form is five
   * squares. A `value?: string | ReactNode` would be the same thing with a branch in it.
   */
  readonly children: ReactNode;
}

export function StatBox({ label, children }: StatBoxProps) {
  return (
    <View style={s.box}>
      {/* One line, hard. Four of the five names are two words and the fifth is *Counted*; a
          box whose name wrapped would be a box a third taller than the two beside it, and the
          row's whole point is that the figures line up. */}
      <Text style={s.label} numberOfLines={1}>
        {label}
      </Text>
      {children}
    </View>
  );
}

/** The figure in a box, for the four boxes whose fact is one. */
export function StatFigure({ children }: { readonly children: string }) {
  return <Text style={s.figure}>{children}</Text>;
}

/**
 * The row the boxes sit in — **equal thirds, or equal halves, or equal whatever is left**.
 *
 * `flex: 1` on the box rather than a width, because a block is hidden when its fact is absent
 * and the two that remain then fill the card. A fixed third would leave a hole where a block
 * stood down, which is *blank* rather than *hidden* drawn in negative space.
 */
export function StatRow({ children }: { readonly children: ReactNode }) {
  return <View style={s.row}>{children}</View>;
}

const s = StyleSheet.create({
  row: { flexDirection: 'row', gap: theme.space.xs },
  box: {
    flex: 1,
    gap: theme.space.xxs,
    backgroundColor: theme.color.paper2,
    borderRadius: theme.radius.note,
    paddingVertical: theme.space.xs,
    paddingHorizontal: theme.space.sm,
  },
  label: { ...theme.type.rlLabel, color: theme.color.muted },
  // `num.s` and not a step larger: the panel prints a Level at `num.xl` and the band prints
  // two more, and a record figure that competed with them would read as a third rating.
  figure: { ...theme.num.s, ...theme.tabular, color: theme.color.ink },
});
