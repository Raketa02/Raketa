/**
 * The four questions a search may raise — **codes, never sentences**.
 *
 * *"`Keep 15 km?` is one phrasing of `KEEP_THIS_RADIUS` in one language, and a backend that
 * shipped it would own the copy for every client that ever exists."* Each prompt rides on a
 * search response ([#226](https://github.com/Raketa02/Raketa/issues/226)), so *"it never
 * blocks"* is true by construction
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §12).
 *
 * **Every value quoted is `RaisedPrompt`'s own payload** — the value already in play, never a
 * value the engine picked. This module writes no number of its own, and the payload rides in
 * on the union below so a prompt cannot be drawn without the facts its sentence quotes.
 *
 * **One `switch` over the `Prompt` union, exhaustive.** Two of the four titles and two of the
 * four bodies quote a value, so a flat `Readonly<Record<Prompt, string>>` cannot hold them —
 * this is §1's second shape for the same reason the evidence renderers are: the sentence
 * quotes its payload. What the table shape bought is kept regardless, because a fifth prompt
 * with no arm does not compile.
 *
 * ## The closer, and the one prompt with no suppression
 *
 * All four close with §F2's *"Either way the search runs now."* Three then say that declining
 * is remembered for thirty days
 * ([#237](https://github.com/Raketa02/Raketa/issues/237)): a decline writes no value, so it
 * is the one answer nothing else would record, and a thirty-day silence nobody is told about
 * is a hidden mechanism.
 *
 * `KEEP_THESE_TIMES`'s blank is a **typed absence** rather than a string somebody forgot — it
 * is the one prompt with no suppression at all, because a grid legitimately differs per search
 * where a radius, a declaration and a described week do not.
 *
 * **`REFRESH_YOUR_TIMES` keeps §F2 #9 verbatim.** It is one of the ten strings that define
 * the voice, and this is the prompt it was written for — a copy edit there is an edit to the
 * voice, not to a screen.
 */

import { counted } from '@/shared/formatting/counted';

import type { Prompt, SearchMode } from '../domain/vocabulary';

import { modeWord } from './searchPresentation';

/** §F2's closer, on all four. It is what makes a prompt an offer rather than a gate. */
export const PROMPT_CLOSER = 'Either way the search runs now.';

/**
 * A prompt as it was raised, with the value it is asking about.
 *
 * `sportName` is passed in rather than resolved here: what a sport is called is
 * `sportPresentation`'s, and it lives in the feature that first drew one. A copy deck quoting
 * a name is not a second table of names.
 */
export type RaisedPrompt =
  | { readonly prompt: 'KEEP_THESE_TIMES'; readonly slotsNow: number; readonly slotsWas: number }
  | { readonly prompt: 'KEEP_THIS_RADIUS'; readonly radiusKm: number }
  | { readonly prompt: 'UPDATE_PLAY_INTENT'; readonly sportName: string; readonly mode: SearchMode }
  | { readonly prompt: 'REFRESH_YOUR_TIMES' };

/** What the sheet draws: the question, what saying yes buys, and what *not now* costs. */
export interface PromptCopy {
  readonly title: string;
  readonly body: string;
  /** The closer, on every prompt. Separate from the body because it is one sentence, shared. */
  readonly closer: string;
  /** Absent on the one prompt a decline does not suppress. */
  readonly suppression?: string;
}

/**
 * What *not now* costs, where it costs anything.
 *
 * §F1 rule 4's fact·mechanism shape with **no agent**, which is what keeps rule 6 — no *we*,
 * no *Raketa*, no passive.
 */
const SUPPRESSION: Readonly<Record<Prompt, string | null>> = {
  KEEP_THESE_TIMES: null,
  KEEP_THIS_RADIUS: 'Not now means not for a month.',
  UPDATE_PLAY_INTENT: 'Not now means not for a month.',
  REFRESH_YOUR_TIMES: 'Not now means not for a month.',
};

export function promptSuppression(prompt: Prompt): string | undefined {
  return SUPPRESSION[prompt] ?? undefined;
}

/**
 * §F2 #9, **verbatim**. One of the ten strings that define the voice, exported so a test can
 * hold it against the deck without going through a payload.
 */
export const REFRESH_YOUR_TIMES_BODY =
  'The matcher reads this grid every time it looks for anybody — for you and for the people ' +
  'it puts in front of you. A grid that is three months old quietly ruins every match it ' +
  'touches, so it is worth keeping honest.';

/**
 * Everything one prompt says.
 *
 * **A copy edit is booked against `KEEP_THESE_TIMES`'s body and is not made here.** §20.7
 * found that *"Green rings are new, faded ones you dropped"* names a colour as the mechanism,
 * which Part 13 forbids, and §20.12 books the rewrite to §12 rather than inventing it in an
 * accessible name. Until that lands the sentence is the one the deck holds, and the diff
 * grid's own cell names carry *newly added* and *dropped* in words regardless.
 */
export function promptCopy(raised: RaisedPrompt): PromptCopy {
  return {
    ...question(raised),
    closer: PROMPT_CLOSER,
    ...(promptSuppression(raised.prompt) === undefined
      ? {}
      : { suppression: promptSuppression(raised.prompt) }),
  };
}

function question(raised: RaisedPrompt): { readonly title: string; readonly body: string } {
  switch (raised.prompt) {
    case 'KEEP_THESE_TIMES':
      return {
        title: 'Keep these times?',
        body:
          `${counted(raised.slotsNow, 'slot', 'slots')} now · ${raised.slotsWas} on your profile. ` +
          'Green rings are new, faded ones you dropped.',
      };
    case 'KEEP_THIS_RADIUS':
      return {
        title: `Keep ${raised.radiusKm} km?`,
        body: "You've widened to this three searches running. Make it your usual, or keep it to this one.",
      };
    case 'UPDATE_PLAY_INTENT':
      return {
        title: 'Your searches say something else',
        body:
          `Your last five ${raised.sportName} searches were ${modeWord(raised.mode)}. ` +
          'Your profile still says otherwise — want to change it?',
      };
    case 'REFRESH_YOUR_TIMES':
      return { title: 'Is this week still right?', body: REFRESH_YOUR_TIMES_BODY };
  }
}
