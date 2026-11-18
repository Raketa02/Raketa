/**
 * **The sport pill on a Home line** ([#805](https://github.com/Raketa02/Raketa/issues/805); the Home
 * rows screens §7.3; home rows 27; design-system 7.36) — the deck's pill (#774) standing in a folding
 * line's footer since [#820](https://github.com/Raketa02/Raketa/issues/820), before the line's link,
 * and the bar it unfolds into **sliding over the footer**: Top 10's sport, *● Padel ‹* beside
 * *Rankings ›*. (Its direction, and *Open the rankings ›*, are #821's.)
 *
 * `SportPillFrame` is the same control held on a **page**: its bar ends at the page's right edge,
 * where a header's pill stands. On a line the pill stands left of the link, and the link stays where
 * it is with the bar open (home rows 27), so the bar must end where **the pill** ends — which this
 * measures, and the frame does not.
 *
 * ```
 *                        ● Padel ‹   Rankings ›      ← folded: the pill is the footer's control
 * ┌ ● Tennis  ● Squash  ● Badminton [● Padel ›]┐ Rankings ›   ← open: over the footer, ending
 * └────────────────────────────────────────────┘                  where the pill ended
 * ```
 *
 * **The line draws both halves** (`FoldingLineFooter`'s `control` and `over`): the pill in the footer,
 * and — while it is open — a layer over the whole footer with a backdrop that folds it and the bar on
 * the pill's own line. **The pill stands directly in the footer, and the footer's box is the layer's**,
 * so the pill's layout is where the bar must stand.
 *
 * **What folds it** is the frame's: a tap on the current sport or anywhere else on the footer,
 * Android's back, and the screen losing focus (`FoldAway`). A tap elsewhere on the screen does not —
 * the backdrop is the footer's — and leaves the bar open over a footer the reader may scroll past.
 *
 * Never a `Modal`: the bar is a layer of the line (ADR-0178).
 */

import { useState, type ReactNode } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import type { Sport } from '@/shared/vocabulary/sport';

import { SportBar, SportPill, type SportChoice, type SportPillWords } from './SportPill';
import { FoldAway } from './SportPillFrame';
import { theme } from './theme';

/** The bar's inset round its pills — the current sport stands this far in from the bar's right end. */
const PAD = theme.size.groupPage.filterPad;

interface PillBox {
  readonly x: number;
  readonly y: number;
  readonly width: number;
  readonly height: number;
}

export interface RowSportPillProps<S extends SportChoice = Sport> {
  /** **The sports to offer**, in the order the bar lists them — `undefined` until the row knows. */
  readonly sports: readonly S[] | undefined;
  /** The sport the row is on — `undefined` until it is known. No pill is drawn until both are. */
  readonly sport: S | undefined;
  /** **Another sport was picked** — never the current one, which only folds the bar. */
  readonly onPick: (sport: S) => void;
  readonly words: SportPillWords<S>;
  /**
   * The line: `pill` for its footer (`FoldingLineFooter`'s `control`) — `undefined` until there is a
   * sport — and `over`, the open bar with its backdrop (the footer's `over`), `undefined` while folded.
   */
  readonly children: (pill: ReactNode | undefined, over: ReactNode | undefined) => ReactNode;
}

export function RowSportPill<S extends SportChoice = Sport>({
  sports,
  sport,
  onPick,
  words,
  children,
}: RowSportPillProps<S>) {
  const [unfolded, setUnfolded] = useState(false);
  const [box, setBox] = useState<PillBox>();
  const fold = () => setUnfolded(false);

  function choose(chosen: S) {
    if (chosen !== sport) onPick(chosen);
    fold();
  }

  const known = sports !== undefined && sport !== undefined;

  const pill = known ? (
    <View testID="row-sport-pill" onLayout={(event) => setBox(event.nativeEvent.layout)}>
      <SportPill sports={sports} sport={sport} words={words} onUnfold={() => setUnfolded(true)} />
    </View>
  ) : undefined;

  const over =
    known && unfolded ? (
      <View style={StyleSheet.absoluteFill} pointerEvents="box-none">
        <FoldAway onFold={fold} />
        <Pressable
          testID="sport-filter-backdrop"
          onPress={fold}
          accessible={false}
          importantForAccessibility="no"
          style={StyleSheet.absoluteFill}
        />
        <View
          testID="row-sport-bar-slot"
          pointerEvents="box-none"
          style={[
            s.barSlot,
            box === undefined
              ? undefined
              : { top: box.y, height: box.height, width: box.x + box.width + PAD },
          ]}
        >
          <SportBar sports={sports} sport={sport} words={words} onChoose={choose} />
        </View>
      </View>
    ) : undefined;

  return <>{children(pill, over)}</>;
}

const s = StyleSheet.create({
  // From the footer's left edge to the pill's right end and the bar's inset past it, on the pill's own
  // line: the bar grows leftwards from there, over the footer, and its current sport stands exactly
  // where the pill stood.
  barSlot: {
    position: 'absolute',
    left: 0,
    justifyContent: 'center',
    alignItems: 'flex-end',
  },
});
