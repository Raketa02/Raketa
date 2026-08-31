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

import type { SearchMode } from './vocabulary';

export type RaisedPrompt =
  /**
   * `slotsNow` is the week the search actually **ran** on and `slotsWas` is the count on the
   * profile — two numbers from two sides, because the engine compares the post-rung grid and
   * only the client holds the profile's.
   */
  | { readonly prompt: 'KEEP_THESE_TIMES'; readonly slotsNow: number; readonly slotsWas: number }
  | { readonly prompt: 'KEEP_THIS_RADIUS'; readonly radiusKm: number }
  /**
   * `sportName` is passed in rather than resolved anywhere here: what a sport is called is
   * `sportPresentation`'s, and a payload quoting a name is not a second table of names.
   */
  | { readonly prompt: 'UPDATE_PLAY_INTENT'; readonly sportName: string; readonly mode: SearchMode }
  | { readonly prompt: 'REFRESH_YOUR_TIMES' };
