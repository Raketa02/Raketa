/**
 * **Which of FOR YOU's lines is open** ([#820](https://github.com/Raketa02/Raketa/issues/820);
 * ADR-0205 §5; the Home rows screens §1, §2; Q10, Q12, Q21, Q38).
 *
 * Home's five discovery rows fold into five lines under *Your games*, and **one is open at a time**:
 *
 * - **a press on a closed line opens it**, and on the open line's header closes it;
 * - **a press on another line folds the open one first, then unfolds the second** — so for a moment
 *   the second is chosen and nothing is drawn open. **Whatever is pressed while a line folds waits
 *   for the fold** (a close, or the first half of a switch), so an unfold never runs beside a fold.
 *   The page says when the fold has run (`foldRan`); under Reduce motion nothing folds, and every
 *   press lands at once;
 * - **a line that is no longer shown closes** — its read emptied while it was open — and stays closed
 *   if it comes back;
 * - **every line starts closed**, but a page may name **a line it starts on**: Groups heating up, for
 *   a player in no group (`lineToStartOn`), opened as soon as it is shown and until the reader chooses
 *   anything — **opened by nobody's press**, so the page is not scrolled to it (`pressed`);
 * - **FOR YOU is shown while any line is** (`forYouShown`).
 *
 * Pure: the page says what is shown and what was pressed, and keeps the answer while it lives — never
 * across a restart (ADR-0205 §5).
 */

/** The five lines, in Home's order (ADR-0205 §5's table) — the rows' own names, not their titles. */
export const FOR_YOU_LINES = [
  'hottestGroups',
  'sameLevel',
  'newInRakieta',
  'sameVibe',
  'topTen',
] as const;

export type ForYouLine = (typeof FOR_YOU_LINES)[number];

export type LinesShown = Readonly<Record<ForYouLine, boolean>>;

export interface OpenLine {
  /**
   * **What the reader chose last** — a line, or none (`null`) after a close; `undefined` until the
   * first press, which is what lets a page's line to start on open by itself.
   */
  readonly chosen: ForYouLine | null | undefined;
  /** **The line drawn open now** — the one chosen, or none while a fold runs before it. */
  readonly drawn: ForYouLine | null;
  /** **Whether a line is folding now** — until the page says the fold has run (`foldRan`). */
  readonly folding: boolean;
  /** **Whether the reader pressed for what is open** — false for the line a page starts on. */
  readonly pressed: boolean;
}

export const ALL_CLOSED: OpenLine = {
  chosen: undefined,
  drawn: null,
  folding: false,
  pressed: false,
};

const opened = (line: ForYouLine, pressed: boolean): OpenLine => ({
  chosen: line,
  drawn: line,
  folding: false,
  pressed,
});

/** **FOR YOU is drawn while any of its lines is** — with all five hidden, it goes too (Q21). */
export function forYouShown(shown: LinesShown): boolean {
  return FOR_YOU_LINES.some((line) => shown[line]);
}

/** **The line Home starts on** — Groups heating up for a player in no group (Q38), else none. */
export function lineToStartOn({
  inNoGroup,
}: {
  readonly inNoGroup: boolean;
}): ForYouLine | undefined {
  return inNoGroup ? 'hottestGroups' : undefined;
}

/**
 * **A press on a line's header.** `folds` is false under Reduce motion, where every press is one step.
 */
export function pressLine(
  now: OpenLine,
  line: ForYouLine,
  { folds }: { readonly folds: boolean },
): OpenLine {
  if (!folds) {
    return now.drawn === line
      ? { chosen: null, drawn: null, folding: false, pressed: true }
      : opened(line, true);
  }
  if (now.folding) {
    return now.chosen === line ? now : { chosen: line, drawn: null, folding: true, pressed: true };
  }
  if (now.drawn === line) return { chosen: null, drawn: null, folding: true, pressed: true };
  if (now.drawn === null) return opened(line, true);
  return { chosen: line, drawn: null, folding: true, pressed: true };
}

/** **The fold has run**: the line chosen while it ran is drawn open, or none after a close. */
export function foldRan(now: OpenLine): OpenLine {
  if (!now.folding) return now;
  return now.chosen === null || now.chosen === undefined
    ? { ...now, drawn: null, folding: false }
    : opened(now.chosen, now.pressed);
}

/**
 * **What is shown settles the open line**: a line no longer shown is closed, and a page's line to
 * start on opens once it is shown, while nothing was ever chosen. The same object when nothing moves.
 */
export function settleLine(
  now: OpenLine,
  shown: LinesShown,
  startsOn: ForYouLine | undefined,
): OpenLine {
  if (now.chosen === undefined) {
    return startsOn !== undefined && shown[startsOn] ? opened(startsOn, false) : now;
  }
  const gone =
    (now.chosen !== null && !shown[now.chosen]) || (now.drawn !== null && !shown[now.drawn]);
  return gone ? { ...now, chosen: null, drawn: null } : now;
}
