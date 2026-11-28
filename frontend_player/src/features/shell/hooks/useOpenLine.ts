/**
 * **Which of FOR YOU's lines is open, kept while Home lives** ([#820](https://github.com/Rakieta02/Rakieta/issues/820);
 * ADR-0205 §5; Q10, Q38).
 *
 * The rules are `forYou`'s; this keeps the answer and runs the one clock they ask for: **once a fold
 * starts, `motion.lineFold` later it has run** (`foldRan`), and whatever was pressed meanwhile unfolds
 * then. Under Reduce motion nothing folds, so nothing waits (ADR-0205 §8).
 *
 * **Home's own state**, never a store: Home stays mounted under every tab (`TAB_STACK`, #809), so the
 * open line outlives a tab switch, and goes with Home — at a restart or a sign-out — so it is never
 * kept (ADR-0205 §5: *never across a restart*).
 */

import { useEffect, useRef, useState } from 'react';

import { theme, useReducedMotion } from '@/shared/ui';

import {
  ALL_CLOSED,
  foldRan,
  pressLine,
  settleLine,
  type ForYouLine,
  type LinesShown,
  type OpenLine,
} from '../domain/forYou';

export interface OpenLineState {
  /** The line drawn open — none while every line is closed, or a fold runs before the next. */
  readonly open: ForYouLine | null;
  /** Whether a line is folding now — what the lines below slide by. */
  readonly folding: boolean;
  /** Whether the open line was opened by the reader's press — the page shows only those. */
  readonly pressed: boolean;
  /** A press on a line's header. */
  readonly press: (line: ForYouLine) => void;
}

export function useOpenLine(shown: LinesShown, startsOn: ForYouLine | undefined): OpenLineState {
  const reduced = useReducedMotion();
  const [kept, setKept] = useState<OpenLine>(ALL_CLOSED);
  const timer = useRef<ReturnType<typeof setTimeout>>();

  // Derived state, as `useTopTen` keeps its pick: what is shown settles the line at once.
  const now = settleLine(kept, shown, startsOn);
  if (now !== kept) setKept(now);

  useEffect(() => () => clearTimeout(timer.current), []);

  return {
    open: now.drawn,
    folding: now.folding,
    pressed: now.pressed,
    press: (line) => {
      const next = pressLine(now, line, { folds: !reduced });
      setKept(next);
      // A fold just started: it runs for its own beat, whatever is pressed while it does.
      if (next.folding && !now.folding) {
        timer.current = setTimeout(() => setKept(foldRan), theme.motion.lineFold);
      }
    },
  };
}
