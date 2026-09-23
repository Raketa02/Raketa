/**
 * What the You tab says about the **per-sport declaration** — the fact a stranger's search
 * reads, given a home that is not the search form
 * ([#296](https://github.com/Raketa02/Raketa/issues/296)).
 *
 * As long as the only place a declaration was ever seen was Find a game, it read as a search
 * setting; ADR-0094 makes it a fact about the player, kept per sport and read by other people.
 * So the words here are about **who reads it and what it does not do**, which are the two
 * things a player cannot guess from the value alone: it is what other searches see, and it does
 * not narrow what this player may search for.
 *
 * The three answers themselves are **not here**. They are the platform's words for a closed
 * vocabulary and live in `shared/vocabulary/playIntentPresentation` — Find a game prints the
 * identical value, and the same word spelled twice is two facts the day one of them is
 * reworded. What is this screen's is the frame around them.
 *
 * **`PROFILE_SCREEN` is the write surface and this is the only screen that may report it.**
 * The backend has held that value in `PlayIntentSurface`'s closed five with no client behind
 * it; nothing about it changes a contract.
 */

import { intentLabel } from '@/shared/vocabulary/playIntentPresentation';
import type { PlayIntent } from '@/shared/vocabulary/playIntent';

/**
 * **The section's heading and body are gone**, and on purpose (ADR-0179 §2, §9). They read
 * *What other players see* and *The kind of game you want. Searches read this per sport when
 * deciding whether you would suit them. It does not change what you can search for.* — and
 * the You tab's *What kind of game* screen says the one thing they said in one line under its
 * title, `KIND_OF_GAME_LINE`, so the section is the list and the footnote.
 */

/**
 * A rated sport nobody has answered for.
 *
 * **Not an em dash and not a blank.** This is the first place in the app a player can find out
 * that a search in that sport will be refused *before* trying to run one — every matchmaking
 * route answers `play_intent_not_declared` — and a row that simply said nothing would have told
 * them the same as an empty screen.
 */
export const NOT_DECLARED = 'Not set';

export function declaredValue(intent: PlayIntent | undefined): string {
  return intent === undefined ? NOT_DECLARED : intentLabel(intent);
}

/**
 * What *Not set* costs, drawn only while at least one row says it.
 *
 * The value is the discovery; this is the consequence, and a player who reads *Not set* and is
 * not told what it stops has been shown a gap rather than a problem. It is not drawn when every
 * sport is answered, because a sentence about a state nobody is in is chrome.
 */
export const NOT_DECLARED_LINE = 'A sport with no answer cannot be searched in until you give one.';

/**
 * One row's spoken name: **the sport and its answer, together.**
 *
 * A row is one element or it is a sport read a screen apart from the value it names
 * (`Row`'s own rule). The hint below carries what pressing it does, because the name says what
 * the row *is* and a name ending in *change it* would announce an action twice on a control
 * whose role already does.
 */
export function playIntentRowLabel(sportName: string, intent: PlayIntent | undefined): string {
  return `${sportName}, ${declaredValue(intent)}`;
}

export const PLAY_INTENTS_ROW_HINT = 'Opens the three answers';
