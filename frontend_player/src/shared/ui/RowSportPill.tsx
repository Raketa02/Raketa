/**
 * **The sport switcher on a Home line** ([#805](https://github.com/Raketa02/Raketa/issues/805); the
 * Home rows screens §7.3; design-system 7.36, 7.37) — the deck's pill (#774) standing in a folding
 * line's footer since [#820](https://github.com/Raketa02/Raketa/issues/820), and the bar it unfolds
 * into **sliding over the footer**. Since [#821](https://github.com/Raketa02/Raketa/issues/821)
 * (ADR-0205 §5, Q19, Q37; home refactor 12, 13) it stands **first, at the footer's left**, reading
 * *● Padel ›*, with *Open the rankings ›* at the right, and **opens to the right** (`SportBar`'s
 * `opens`): the current sport at the bar's left end where the pill stood, the others after it.
 *
 * `SportPillFrame` is the same control held on a **page**: its bar ends at the page's right edge,
 * where a header's pill stands, and grows leftwards. On a line the bar must **start** where the pill
 * starts — which this measures, and the frame does not — and runs across the footer, over the link,
 * to the footer's right edge. **Measured in Archivo, the open bar is about 322pt** (304 of pills):
 * inside the line with every sport in reach from a 375pt phone up; on a 360pt one its round end meets
 * the line's inner edge and the last sport's far ~6pt stand past the footer, out of Android's reach;
 * on a 320pt one it is cut by about 40pt (`rowSportBarFit.test.ts`). The leftward bar it replaces,
 * ending at the pill left of *Rankings ›*, was cut on a 360pt phone too (#820).
 *
 * ```
 * ● Padel ›                     Open the rankings ›   ← folded: the pill at the left, the link right
 * ┌[● Padel ‹] ● Tennis  ● Squash  ● Badminton┐ ›    ← open: over the footer, from where the
 * └───────────────────────────────────────────┘          pill started, rightwards
 * ```
 *
 * **The line draws both halves** (`FoldingLineFooter`'s `control` and `over`): the pill in the footer,
 * and — while it is open — a layer over the whole footer with a backdrop that folds it and the bar on
 * the pill's own line. **The pill stands directly in the footer, and the footer's box is the layer's**,
 * so the pill's layout is where the bar must stand. **A tap on the link while the bar is open folds
 * the bar** — the backdrop is over it — and leaves Home where it is.
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

/** The bar's inset round its pills — the current sport stands this far in from the bar's left end. */
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
      <SportPill
        sports={sports}
        sport={sport}
        words={words}
        onUnfold={() => setUnfolded(true)}
        opens="right"
      />
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
            box === undefined ? undefined : { top: box.y, height: box.height, left: box.x - PAD },
          ]}
        >
          <SportBar sports={sports} sport={sport} words={words} onChoose={choose} opens="right" />
        </View>
      </View>
    ) : undefined;

  return <>{children(pill, over)}</>;
}

const s = StyleSheet.create({
  // From the bar's inset before the pill's left end to the footer's right edge, on the pill's own
  // line: the bar grows rightwards from there, over the footer and its link, and its current sport
  // stands exactly where the pill stood. Until the pill is measured, it is taken at the footer's left.
  barSlot: {
    position: 'absolute',
    left: -PAD,
    right: 0,
    justifyContent: 'center',
    alignItems: 'flex-start',
  },
});
