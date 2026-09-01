/**
 * A question a search raised, **as facts rather than as a sentence.**
 *
 * Each of the four prompts quotes a value — *"the value already in play, never a value the
 * engine picked"* — so the payload and the code travel together and a prompt cannot be drawn
 * without the facts its sentence names. That union is what `components/promptPresentation`
 * writes words over and what `mappers/searchMappers` lifts off the response.
 *
 * **It is here rather than beside the copy** because the dependency arrow points inward: a
 * mapper and a use-case both hold one, and `_template/README.md` lets `mappers/` and
 * `use-cases/` reach `domain/` and never `components/`. The shape is not copy — it is a code
 * and its payload, which is exactly what `domain/vocabulary.ts` beside it is for. What
 * `components/` owns is the sentence over it.
 */

import type { Sport } from '@/shared/vocabulary/sport';
import type { WeekCell } from '@/shared/vocabulary/week';

import type { Prompt, SearchMode } from './vocabulary';

export type RaisedPrompt =
  /**
   * `week` is the grid the search actually **ran** on and `profileWeek` is the one the profile
   * holds — two weeks from two sides, because the engine compares the post-rung grid and only
   * the client holds the profile's.
   *
   * **The cells, and not two counts.** The sheet that answers this one draws the difference as
   * a grid — [6.8](../../../../docs/design-system.md#68-the-availability-grid)'s diff variant,
   * a plus on what the search added and a dash on what it dropped — and the two numbers its
   * sentence quotes are these two weeks' own lengths. Carrying the counts beside the cells
   * would be one fact spelled twice, and *yes* to this prompt is a write of `week` itself.
   */
  | {
      readonly prompt: 'KEEP_THESE_TIMES';
      readonly week: readonly WeekCell[];
      readonly profileWeek: readonly WeekCell[];
    }
  | { readonly prompt: 'KEEP_THIS_RADIUS'; readonly radiusKm: number }
  /**
   * `sportName` is passed in rather than resolved anywhere here: what a sport is called is
   * `sportPresentation`'s, and a payload quoting a name is not a second table of names.
   */
  | { readonly prompt: 'UPDATE_PLAY_INTENT'; readonly sportName: string; readonly mode: SearchMode }
  | { readonly prompt: 'REFRESH_YOUR_TIMES' };

/**
 * Whether saying *not now* to this question buys any silence — **three of the four, and the
 * odd one out is stated rather than omitted.**
 *
 * The line is **whether the condition outlives the act**, and not per-search versus loop: an
 * improvised grid is gone when the search ends, where a widening habit, a drift and a week
 * described months ago are all still true tomorrow
 * ([#237](https://github.com/Raketa02/Raketa/issues/237) §4). So `KEEP_THESE_TIMES` is asked
 * again on the next search — a genuinely different grid next Tuesday — and the route refuses
 * a decline of it with `prompt_does_not_suppress`.
 *
 * **It is here rather than beside the sentence it produces**, because two things read it and
 * only one of them is words: the sheet draws *"Not now means not for a month"* where this is
 * true, and the use-case sends a request where this is true, and a copy table the request path
 * had to import would be the dependency arrow pointing the wrong way. Exhaustive over the
 * union, so a fifth prompt states its own answer or does not compile.
 */
const SUPPRESSES: Readonly<Record<Prompt, boolean>> = {
  KEEP_THESE_TIMES: false,
  KEEP_THIS_RADIUS: true,
  UPDATE_PLAY_INTENT: true,
  REFRESH_YOUR_TIMES: true,
};

export function promptSuppresses(prompt: Prompt): boolean {
  return SUPPRESSES[prompt];
}

/**
 * Whether saying *yes* to this question **writes a value** — three of the four, and the odd
 * one out is stated rather than left to a component.
 *
 * Every prompt quotes the value already in play, and `REFRESH_YOUR_TIMES` quotes none: it is
 * only ever the one raised on a week the profile already holds — an edited week raises
 * `KEEP_THESE_TIMES`, which sorts first — and re-sending an unchanged week lands the same
 * state and records nothing. So its *yes* is a request for the grid rather than a write, and
 * the sheet stays on the screen that has one.
 *
 * **Here rather than in the sheet**, for `promptSuppresses`'s reason one paragraph up: two
 * things read it — the use-case that picks the route, and the sheet that decides where the
 * player goes next — and the same fact stated at both is two places to disagree.
 */
const ACCEPT_WRITES: Readonly<Record<Prompt, boolean>> = {
  KEEP_THESE_TIMES: true,
  KEEP_THIS_RADIUS: true,
  UPDATE_PLAY_INTENT: true,
  REFRESH_YOUR_TIMES: false,
};

export function acceptWritesTheValue(prompt: Prompt): boolean {
  return ACCEPT_WRITES[prompt];
}

/**
 * Whether answering this question **needs the week grid** — one of the four, and the other
 * three say so rather than being inferred from anything.
 *
 * Three routes raise prompts and only one of them is a screen the week is edited on. ⚡ lands
 * on the court the player is already looking at and a deal replaces the card in place, so
 * neither the builder nor the deck has a grid for `REFRESH_YOUR_TIMES`'s *yes* to hand anybody
 * back to ([#287](https://github.com/Raketa02/Raketa/issues/287)). Drawing it there would
 * either promise a control that is not on the screen or — because dismissal is *not now*, and
 * *not now* suppresses it for thirty days — spend the offer on the one surface that cannot
 * honour it. So it is **dropped**, which is `the-words.md` §3's own answer for a prompt a
 * surface cannot draw: an offer is not a row in a count, and nothing on screen is left
 * unaccounted for by its absence.
 *
 * **Its own table rather than `ACCEPT_WRITES` read backwards.** Today the prompt whose *yes*
 * writes nothing is the same one whose *yes* is the grid, and those are two facts that happen
 * to agree on four values. A fifth prompt that wrote nothing and needed no grid — an offer to
 * re-read something, say — would be dropped from two surfaces by a coincidence nobody stated,
 * which is exactly what the tables either side of this one exist to prevent: a fifth prompt
 * states its own answer or does not compile.
 */
const NEEDS_THE_WEEK_GRID: Readonly<Record<Prompt, boolean>> = {
  KEEP_THESE_TIMES: false,
  KEEP_THIS_RADIUS: false,
  UPDATE_PLAY_INTENT: false,
  REFRESH_YOUR_TIMES: true,
};

/**
 * The questions a surface with no week grid may ask — **written once, because two use-cases
 * ask it.**
 *
 * A list rather than a predicate each caller filters with: dropping a prompt is one decision
 * about one screen, and two `filter` calls spelled out is two places for one of them to invert
 * the test.
 */
export function answerableWithoutAWeekGrid(
  raised: readonly RaisedPrompt[],
): readonly RaisedPrompt[] {
  return raised.filter((one) => !NEEDS_THE_WEEK_GRID[one.prompt]);
}

/**
 * The questions a screen has **already put to this player**, where asking is not a press.
 *
 * Find a game and ⚡ need none of this: both are pressed, and a second press is a second
 * question worth asking, so each keys its sheet by the search it minted. A **deal** is neither
 * — the entry deal is an effect and a spent hand deals again on its own — so a question keyed
 * by the deal would be put in front of the player again every ten cards, which on
 * `KEEP_THESE_TIMES` is every deal of the visit
 * ([#287](https://github.com/Raketa02/Raketa/issues/287)).
 *
 * **The sport is half the identity**, because `UPDATE_PLAY_INTENT` is the one prompt declared
 * per sport: a drift answered on padel is not the same question on tennis, and a key that was
 * the code alone would swallow the second one for the rest of the visit.
 */
export type AskedQuestions = readonly string[];

export const NOTHING_ASKED: AskedQuestions = [];

const identity = (sport: Sport, prompt: Prompt) => `${sport}:${prompt}`;

/** The same list with this question on it. Answering the same one twice adds nothing. */
export function alsoAsked(asked: AskedQuestions, sport: Sport, prompt: Prompt): AskedQuestions {
  const one = identity(sport, prompt);
  return asked.includes(one) ? asked : [...asked, one];
}

/**
 * The question to put next — **the first one not yet asked, rather than the first one.**
 *
 * The response orders prompts in the vocabulary's own order so *"a client rendering the first
 * one it understands gets the same one twice for the same search"*, and a surface that took
 * `prompts[0]` and *then* checked whether it had been answered would go silent for the whole
 * visit the moment the leading question was: every later list starts with the same code, and
 * the question behind it would never be reached. Skipping the answered ones keeps both — one
 * question at a time, and none of them lost.
 */
export function firstUnasked(
  raised: readonly RaisedPrompt[],
  sport: Sport,
  asked: AskedQuestions,
): RaisedPrompt | undefined {
  return raised.find((one) => !asked.includes(identity(sport, one.prompt)));
}
