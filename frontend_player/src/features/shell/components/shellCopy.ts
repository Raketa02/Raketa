/**
 * The sentences the shell writes for the tabs it composes — Home and Play.
 *
 * **These are citations, not filler**, and there is no placeholder among them any more. For
 * as long as a tab was unbuilt its line was one sentence naming what the tab would be plus
 * that it was not built ([#227](https://github.com/Raketa02/Raketa/issues/227)); every tab has
 * left that table and none of them was deleted. You's own words are in `youCopy`.
 *
 * **No sentence here may say "nothing is happening."** It began as Now's refusal — Now is where a
 * game lands, so a placeholder asserting emptiness would be lying one tap after one was booked —
 * and it now governs every empty state the shell writes. Naming what a tab **is** is true in both
 * states, which is the test each line has to pass and the test `shellCopy.test.ts` holds them to.
 */

import { countFigure } from '@/shared/formatting/countFigure';

/**
 * **The Home tab's own sentences** — its title, and what it says when it holds no games
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §22.7).
 *
 * **Home is today's Now, renamed** ([#550](https://github.com/Raketa02/Raketa/issues/550),
 * [the mechanics §3](../../../../../docs/specs/games-and-fill-in/the-mechanics.md#3-where-everything-lives)):
 * the title is the bar's word. The two lines below are still true of the tab — every game you are
 * in shows up here — and they are here rather than in `features/proposals` for §1's reason: the
 * heading over the rail is that feature's because it names its own content, and these are about
 * the **tab**.
 *
 * **The first says what Home is**, in the present tense and true whether or not anything is on it;
 * **the second names the act**, which is 10.1's empty-state rule.
 *
 * **The bolt is not drawn.** §22.7 writes the second line as `⚡ Play finds you one.`, and 10.2 is
 * explicit that *"the ⚡ is `zap` and never the character"*: `U+26A1` carries
 * `Emoji_Presentation=Yes`, so a bare one in a muted sentence renders as a colour emoji that this
 * app's `color` has nothing to apply to. The tab's own drawn name is `Play`, and that is the word
 * this sentence points at.
 */
export const HOME_COPY = {
  title: 'Home',
  empty: {
    line:
      'Every game you arrange shows up here — what is agreed, what is today, and what still ' +
      'needs a score.',
    act: 'Play finds you one.',
  },
  /** **FOR YOU** — the eyebrow over the five folding lines, drawn uppercase (#820, ADR-0205 §5). */
  forYou: 'For you',
} as const;

/**
 * **Needs your answer** — the envelope on Home's header and the sheet it opens
 * ([#816](https://github.com/Raketa02/Raketa/issues/816), ADR-0205 §1–§2; the words §32).
 *
 * The shell's because the header and the sheet are: each section under the title is its feature's,
 * with its own heading. The envelope is named by what it opens, as the bell is; its count, *, 2
 * new*, is #819's.
 */
export const NEEDS_YOUR_ANSWER_COPY = {
  /** The sheet's title, and the envelope's spoken name. */
  title: 'Needs your answer',
  /** The sheet's ✕ — never just *Close* (`CloseControl`). */
  close: 'Close Needs your answer',
} as const;

/**
 * **The envelope's badge** (#819): what is new since Needs your answer was last closed, as the
 * server counts it — the bell's count mark and the bell's rule, the figure up to 99, *99+* above it
 * (every count's cap, `countFigure`; ADR-0205 §2), and nothing at nought.
 */
export function envelopeFigure(count: number): string | undefined {
  return count <= 0 ? undefined : countFigure(count);
}

/**
 * The envelope's name, with its badge: *Needs your answer, 2 new*. Exact above 99, as the bell's —
 * the cap is the drawing's room, and a listener is not short of it.
 */
export function envelopeSpoken(count: number): string {
  return count <= 0
    ? NEEDS_YOUR_ANSWER_COPY.title
    : `${NEEDS_YOUR_ANSWER_COPY.title}, ${count} new`;
}

/**
 * **The Play tab's own words** — the two segments it opens on
 * ([#512](https://github.com/Raketa02/Raketa/issues/512), play mocks 1 and 3).
 *
 * The shell's rather than `groups`' because the segment is the *tab*: it names the two ways the
 * tab finds a player games, and each segment's page owns its own sentences under it. Explore draws
 * nothing yet, so it has nothing here but its name.
 */
export const PLAY_COPY = {
  segment: {
    groups: 'Groups',
    explore: 'Explore',
  },
} as const;
