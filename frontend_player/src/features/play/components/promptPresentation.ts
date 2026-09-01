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

import type { RaisedPrompt } from '../domain/raisedPrompt';
import type { Prompt } from '../domain/vocabulary';

import { modeWord } from './searchPresentation';

/**
 * A prompt as it was raised, with the value it is asking about — **`domain/raisedPrompt`'s**.
 *
 * The shape is a code and its payload rather than copy, and a mapper and a use-case both hold
 * one, so it sits inward of this file and is re-exported here for the callers that reach the
 * sentence and its facts together.
 */
export type { RaisedPrompt };

/** §F2's closer, on all four. It is what makes a prompt an offer rather than a gate. */
export const PROMPT_CLOSER = 'Either way the search runs now.';

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
 * **`KEEP_THESE_TIMES` writes two bodies from one arm**, keyed on whether the week the search
 * ran on is empty ([#277](https://github.com/Raketa02/Raketa/issues/277)).
 *
 * A week with cells names the two marks
 * [6.8](../../../../docs/design-system.md#68-the-availability-grid)'s diff variant draws — a
 * **plus** and a **dash**. The sentence they replace named *"Green rings … faded ones"*, which
 * was a colour as the mechanism when it was written and, once the diff variant replaced the
 * volt ring and the 45% opacity with shapes, a description of marks that are not on the screen
 * at all.
 *
 * A **cleared week has no *new* half**, so it takes a body of its own rather than the same
 * sentence stretched over a twenty-second value. *"0 slots now"* would assert a **measured
 * zero**, which is the one reading
 * [ADR-0102](../../../../../docs/adr/0102-silence-is-never-scored.md) says the matcher never
 * takes: a blank grid is *absent*, never *never*. So the empty body states what happens
 * instead — the only prompt body that names a scoring rule, and it earns it, because the count
 * it replaces was already naming one and naming it wrongly. It takes the matcher as its
 * subject, which is §F1 rule 6's shape and `REFRESH_YOUR_TIMES`'s own.
 *
 * Both keep §F2's closer, and the suppression stays the typed absence it was.
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
          raised.slotsNow === 0
            ? `Nothing ticked · ${raised.slotsWas} on your profile. ` +
              'The matcher skips a blank week rather than scoring it nought.'
            : `${counted(raised.slotsNow, 'slot', 'slots')} now · ${raised.slotsWas} on your profile. ` +
              'A plus is new, a dash is one you dropped.',
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
