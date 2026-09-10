/**
 * **The run of form** — one square per counted result, oldest to newest
 * ([7.13](../../../docs/design-system.md#713-the-record-block)).
 *
 * ```
 * ■ ■ ▨ ■
 *
 * (Four squares and not five: they have four counted results, and the fifth is a gap. ▨ is a
 * loss — a paler fill, never a different hue.)
 * ```
 *
 * ## The gap is the statement, so the run is never padded
 *
 * **Fewer than five is a real answer**: three squares means three results, and the space where
 * the other two would be is drawn as a gap, because padding it would claim two games nobody
 * played. The row is left-aligned for exactly that reason — the missing squares are missing at
 * the **end**, where the newest results are not yet.
 *
 * That is a rule about the drawing and not about the data, so this component pads nothing and
 * caps nothing. What it is handed is what it draws, and *how many* a caller was served is the
 * caller's own question — the candidate card's is `player_card.last_five`, which the wire omits
 * rather than sends as an empty list.
 *
 * ## Fill, and what a listener gets instead of it
 *
 * A win is `mint` and a loss is `muted`: 3,39 and 4,49 against the recessed ground they are
 * drawn on, so neither square can be mistaken for the **gap** at the end of a short run —
 * which is the ratio that keeps the run's *length* readable, and the run's length is its
 * whole statement.
 *
 * **The pair is now a hue step, and that is a change from the lightness step it was.** It was
 * `ink` against `muted`: 3,24:1 apart, clearing
 * [1.4.11](../../../docs/design-system.md#25-contrast--computed)'s 3:1 for a graphical object
 * by luminance alone, so the row survived being read in one colour. Green against grey is
 * **1,33:1**, and no green in this palette can do better — `mint` sits mid-luminance, so it
 * cannot be 3:1 from both a light ground and a partner that is also 3:1 from that ground; the
 * only fills that can are one near-black and one mid-grey, which is the pair that just left.
 *
 * So the sighted half of [Part 13](../../../docs/design-system.md#part-13--accessibility)'s
 * *never colour alone* now rests on hue, and a reader who cannot separate green from slate
 * reads five squares of one colour. The **count is still spoken** — *3 of the last 5 won* —
 * so nothing is lost to a listener. The cheap way back, if that matters more than the green:
 * draw the loss as a **hollow** square, which is a shape cue and costs no geometry.
 *
 * The ratios are derived in `recordSquares.test.ts`, off `RUN_OF_FORM_FILL` rather than off
 * the theme, so repainting a square here goes red.
 *
 * It does not survive being read aloud, which is the half
 * [Part 13](../../../docs/design-system.md#part-13--accessibility) is about: the squares carry
 * no words, so **this component announces nothing** and the whole row reaches a listener as one
 * clause counting them — *3 of the last 5 won*, against the run's own length — composed by
 * whichever surface draws it. §20.1 merges an actionless element into the nearest action above
 * it, and a square that named itself would be five states read like a table.
 *
 * ## Why this is `shared/ui` and not a card's own component
 *
 * It was the competitive candidate card's, inline in its record block
 * ([#312](https://github.com/Raketa02/Raketa/issues/312)). The record sheet draws the same run
 * for a resolved sport ([#373](https://github.com/Raketa02/Raketa/issues/373)), and a second
 * copy would be a second thing to keep in step with a **pinned** geometry test — the one shape
 * this system's Part 15 says never to let happen twice.
 */

import { StyleSheet, View } from 'react-native';

import type { GameResult } from '@/shared/vocabulary/gameResult';

import { theme } from './theme';

/**
 * The two fills, as one table rather than two style keys.
 *
 * Exported because the arithmetic that makes them legal is a test's, and a test parsing
 * `theme.color.ink` would pass the day this component started drawing something else. It is
 * `BALANCE_INK` / `FIT_HIGH`'s shape: the number a drawn object is held to comes off the drawn
 * object.
 */
export const RUN_OF_FORM_FILL: Readonly<Record<GameResult, string>> = {
  WIN: theme.color.mint,
  LOSS: theme.color.muted,
};

export interface RunOfFormProps {
  /**
   * The counted results, **oldest to newest**, exactly as many as there are.
   *
   * Never padded and never truncated here — see the module note. An empty list draws an empty
   * row of the run's own height, so a caller with nothing to show hides the block instead.
   */
  readonly results: readonly GameResult[];
}

export function RunOfForm({ results }: RunOfFormProps) {
  return (
    <View style={s.run}>
      {results.map((result, at) => (
        <View
          key={`result-${at}`}
          style={[s.square, { backgroundColor: RUN_OF_FORM_FILL[result] }]}
        />
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  run: {
    flexDirection: 'row',
    gap: theme.space.xxs,
    alignItems: 'center',
    // A figure's own line, so a box of squares stands exactly as tall as a box of digits —
    // 7.13's three boxes are one row and the run is one of the three. A caller wanting some
    // other height is asking for a different drawn object, which is a change to 7.13 rather
    // than a prop.
    height: theme.num.s.lineHeight,
  },
  square: {
    width: theme.size.recordSquare,
    height: theme.size.recordSquare,
    borderRadius: theme.radius.recordSquare,
  },
});
