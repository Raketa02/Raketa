/**
 * Answering a question a search raised — **and the answer splits across two modules.**
 *
 * *Yes* is a write through the route that owns the value; *not now* is a row in
 * `matchmaking`. That is surprising enough to state rather than let a session discover:
 * *"accepting a prompt is a profile write, declining it is a matchmaking write, because the
 * record is about **the question** and not about the value"*
 * ([#237](https://github.com/Raketa02/Raketa/issues/237) §2). Nothing in the prompt's own
 * module writes a profile, on either side of the wire.
 *
 * ## The three writes arrive as ports
 *
 * They are `player_profile`'s routes, `player_profile`'s bounds and `player_profile`'s cache
 * effects — each answers with the value **as the profile now holds it**, and something has to
 * write that back. Reaching around those hooks to call the routes directly would leave the
 * profile read holding a number the server has already corrected, which is `findAGame`'s own
 * argument for taking the radius write as a port rather than as an endpoint.
 *
 * ## Two prompts, two absences, and neither is an oversight
 *
 * **`REFRESH_YOUR_TIMES` accepts into no write**, because it carries no value to write. It is
 * only ever the prompt on screen when the week the search ran on is the profile's own — an
 * edited week raises `KEEP_THESE_TIMES`, which sorts first — and re-sending an unchanged week
 * lands the same state, records nothing and leaves the grid exactly as stale as it was. So its
 * *yes* is the sheet handing the player back to the grid, and the button says so.
 *
 * **`KEEP_THESE_TIMES` declines into no row**, because it is the one prompt with no
 * suppression: a grid legitimately differs per search where a radius, a declaration and a
 * described week do not ([#164](https://github.com/Raketa02/Raketa/issues/164) §6). The route
 * refuses it with `prompt_does_not_suppress`, and this is where that refusal is honoured
 * rather than caught — a request sent to be told *no* is a round trip spent learning something
 * the copy deck already knows.
 */

import { toWireSport } from '@/features/onboarding/types';
import type { PlayIntentDeclaration } from '@/features/player_profile/types';
import type { Sport } from '@/shared/vocabulary/sport';
import type { WeekCell } from '@/shared/vocabulary/week';

import { recordPromptDecline } from '../api/promptApi';
import { intentForMode } from '../domain/playMode';
import { promptSuppresses, type RaisedPrompt } from '../domain/raisedPrompt';

/**
 * Which prompt, and which sport's screen raised it.
 *
 * The sport is **not the key** — a radius and a week are one fact each for the whole player,
 * and only a play intent is declared per sport — but the route takes it on every decline, so
 * the answer carries it on every prompt rather than on the one that keys by it.
 */
export interface PromptAnswer {
  readonly raised: RaisedPrompt;
  readonly sport: Sport;
}

/** The three routes that own the values these questions are about. */
export interface PromptWrites {
  /** `PUT /players/me/availability` — the whole week, and a blank one is a legal value. */
  readonly saveWeek: (week: readonly WeekCell[]) => Promise<unknown>;
  /** `PUT /players/me/search-radius`, with its clamp and its cache effect attached. */
  readonly saveRadius: (radiusKm: number) => Promise<unknown>;
  /** `PUT /play-intents/{sport}` — ADR-0094's route, and the third of the three. */
  readonly declareIntent: (declaration: PlayIntentDeclaration) => Promise<unknown>;
}

/**
 * Where a declaration made from this sheet says it came from.
 *
 * The **one** of `PlayIntentSurface`'s closed five that names this exact act — a drift the
 * platform noticed, offered, and had accepted. It is the sheet's alone: the interstitial two
 * files over now takes its surface from its caller, and the type it accepts is narrowed to the
 * two Play screens, so this value cannot be reported from anywhere but here.
 */
const DECLARED_ON = 'DRIFT_PROMPT' as const;

/**
 * *Yes.* One write, through the route that owns the value — never through the prompt.
 *
 * Exhaustive over the union, so a fifth prompt cannot ship without somebody stating what
 * accepting it writes.
 */
export async function acceptPrompt(
  { raised, sport }: PromptAnswer,
  writes: PromptWrites,
): Promise<void> {
  switch (raised.prompt) {
    case 'KEEP_THESE_TIMES':
      // The week the **search** ran on, off the prompt's own payload: the engine compares the
      // post-rung grid, so the working copy on the screen behind the sheet is not always it.
      await writes.saveWeek(raised.week);
      return;
    case 'KEEP_THIS_RADIUS':
      await writes.saveRadius(raised.radiusKm);
      return;
    case 'UPDATE_PLAY_INTENT':
      await writes.declareIntent({
        sport,
        intent: intentForMode(raised.mode),
        surface: DECLARED_ON,
      });
      return;
    case 'REFRESH_YOUR_TIMES':
      // Nothing to write — `acceptWritesTheValue` is where that is decided and why. The grid
      // is the screen's, and the sheet closing onto it is the whole of this answer.
      return;
  }
}

/**
 * *Not now.* A durable row, keyed by the question and never by the value it quoted.
 *
 * **Dismissal reaches here too.** Closing the sheet is an answer rather than an escape —
 * walking away from a sheet whose footer promises *"Either way the search runs now"* is
 * indistinguishable in intent from pressing the button — so both call this.
 *
 * The prompt with no suppression writes nothing, and `domain/raisedPrompt` is what decides
 * that: `promptSuppresses` is the same fact as the route's refusal and as the sheet's missing
 * sentence, read once instead of stated in three places that can disagree.
 */
export async function declinePrompt({ raised, sport }: PromptAnswer): Promise<void> {
  if (!promptSuppresses(raised.prompt)) return;

  await recordPromptDecline({ prompt: raised.prompt, sport: toWireSport(sport) });
}
