/**
 * **How many of a Same vibe tile's chips are drawn whole** ([#803](https://github.com/Rakieta02/Rakieta/issues/803);
 * the Home rows screens §6.2; the README's override 8) — as many as fit in **three lines**, the last
 * place a dashed *+N more* when more remain, on Home's tile and in See all alike.
 *
 * **Measured, never guessed**: every width here is one the screen laid out — each chip's, each *+N
 * more*'s for the count it would say, and the line's — so a long tag, a narrow column or a larger
 * text size each fit what they fit. Geometry and nothing else, beside the component that measures
 * for it (`SharedTags`), as `shared/ui`'s `*Geometry.ts` files sit beside theirs.
 */

/**
 * **How many lines a run of chips takes** — laid left to right, `gap` apart, a chip that does not fit
 * beside the one before it starting the next line. A chip wider than the line takes a line of its
 * own, cut to it by its own ellipsis.
 */
export function linesTaken(widths: readonly number[], lineWidth: number, gap: number): number {
  let lines = 0;
  let used = 0;
  for (const raw of widths) {
    const width = Math.min(raw, lineWidth);
    if (lines > 0 && used + gap + width <= lineWidth) {
      used += gap + width;
    } else {
      lines += 1;
      used = width;
    }
  }
  return lines;
}

export interface TagFit {
  /** Each chip's laid-out width, in the order drawn. */
  readonly widths: readonly number[];
  /** *+N more*'s laid-out width for each count it can say, from one: `moreWidths[n - 1]`. */
  readonly moreWidths: readonly number[];
  readonly lineWidth: number;
  /** Between chips, both ways. */
  readonly gap: number;
  /** The cap — three on the tile. */
  readonly lines: number;
}

/**
 * **How many chips are drawn whole**; the rest are *+N more*. Every chip when they all fit. Otherwise
 * the most that still leave *+N more* — for the count it would then say — room within the cap; none,
 * at worst, beside it alone.
 */
export function tagsThatFit({ widths, moreWidths, lineWidth, gap, lines }: TagFit): number {
  if (linesTaken(widths, lineWidth, gap) <= lines) return widths.length;
  for (let drawn = widths.length - 1; drawn > 0; drawn -= 1) {
    const more = moreWidths[widths.length - drawn - 1] ?? 0;
    if (linesTaken([...widths.slice(0, drawn), more], lineWidth, gap) <= lines) return drawn;
  }
  return 0;
}
