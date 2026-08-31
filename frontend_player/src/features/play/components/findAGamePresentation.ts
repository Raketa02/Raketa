/**
 * The words on *Find a game* — the screen behind ⚡.
 *
 * Four of them are section headings and the rest are the two sentences this screen owns
 * outright: **what a changed week means**, and **what the one-tap declaration buys**. Neither
 * is in the copy deck, and both are recorded here rather than invented in a component
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §1 — a sentence has one
 * home, and a template inlined in a screen is not one).
 *
 * ## The mode's control labels are here and its prose is not
 *
 * §2 fixes that mode reaches exactly three places, and a toggle is none of them:
 * `searchPresentation`'s `modeWord` is the **lower-case reading inside a sentence** — *"your
 * last five padel searches were for fun"* — and a control is not prose. So the two spellings
 * are deliberately two tables, and the one that is not a sentence lives with the screen that
 * draws the control.
 *
 * ## Why the declaration has three labels and the toggle has two
 *
 * The arity gap is ADR-0094's central move and it is visible in the copy: a search is
 * `COMPETITIVE` or `FOR_FUN`, and a *player* may also say that either kind of evening suits
 * them. `NO_PREFERENCE` is **an explicit answer** — *"the matcher must be able to tell*
 * either suits me *from* I never opened that screen" — so its label says something rather than
 * declining to, and it is never drawn as a way of skipping the question.
 *
 * ## A closed control says what is missing
 *
 * The search control is shut while the sport is undeclared, and its **label carries the
 * reason** rather than leaving the button merely grey — the shape the availability step
 * settled, *"a player facing a dead control deserves the sentence that explains it."*
 */

import type { FindAGameStanding } from '../domain/findAGame';
import type { PlayIntent, SearchMode } from '../domain/vocabulary';

/** The screen's own title, and the one ⚡ opens on. */
export const FIND_A_GAME_TITLE = 'Find a game';

export const SPORT_HEADING = 'Sport';
export const MODE_HEADING = 'What kind of game';
export const WEEK_HEADING = 'When you could play';

/**
 * The mode as a **control label** — Title case, because it is a thing to press.
 *
 * A `Record` over the union, so a third mode would not compile without words. There will not
 * be one: `SearchMode` has two values by construction, and that is the point of the table.
 */
const MODE_LABEL: Readonly<Record<SearchMode, string>> = {
  COMPETITIVE: 'Competitive',
  FOR_FUN: 'For fun',
};

export function modeLabel(mode: SearchMode): string {
  return MODE_LABEL[mode];
}

/**
 * The three declarations, as a player would say them.
 *
 * *Either suits me* is the whole of `NO_PREFERENCE` and states a preference rather than the
 * absence of one — *"indifference about the kind of evening is not a third kind of evening"*,
 * but it is still an answer somebody gave.
 */
const INTENT_LABEL: Readonly<Record<PlayIntent, string>> = {
  COMPETITIVE: 'Competitive',
  FOR_FUN: 'For fun',
  NO_PREFERENCE: 'Either suits me',
};

export function intentLabel(intent: PlayIntent): string {
  return INTENT_LABEL[intent];
}

/**
 * *Changed from your profile* — drawn under the grid, and only while it is true.
 *
 * The comparison is `workingWeek`'s and is made **on every tap**: a slot ticked on and off
 * again is not a changed week, so this cannot be a flag a toggle sets. What the sentence adds
 * to the marker is the consequence — the week travels with this one search and is not written
 * anywhere — because a player who sees that something differs and is not told what that costs
 * has been warned about nothing.
 *
 * It is deliberately **not** the `KEEP_THESE_TIMES` prompt. That one compares the grid a
 * search actually ran on, after any rung it took, and only the backend knows what that was.
 */
export const WEEK_CHANGED_FROM_PROFILE =
  'Changed from your profile — this search only, and nothing is saved.';

/**
 * What the slider does, said out loud — because it is the one control here that **writes**.
 *
 * A sport, a mode and a week edited on this screen reach the server as an ask on one search
 * and never as a change to the player. The radius cannot: `RunSearchRequest` carries none, so
 * the searcher's ask *is* their profile radius and moving the slider is moving the profile.
 * That asymmetry is the wire's rather than a choice, and a control that quietly changed a
 * durable value while three beside it changed nothing would be the surprise this line exists
 * to remove.
 */
export const RADIUS_IS_YOUR_PROFILE = 'Kept on your profile — a search has no distance of its own.';

/** The one-tap declaration, on the screen ADR-0094 makes the edit surface. */
export function declarationTitle(sportName: string): string {
  return `What kind of game at ${sportName}?`;
}

/**
 * What answering buys, and what it does not touch.
 *
 * Both halves are load-bearing. The first is why the question is being put at all — it is
 * asked once per sport and a search will not run before it. The second keeps the answer from
 * reading as the switch above it, which is the collapse ADR-0094 spent a type on preventing.
 */
export const DECLARATION_BODY =
  'Asked once for this sport, and kept on your profile. The switch above still moves for a ' +
  'single search.';

/** Unreachable from the flow — the Play tab is behind a rating — and said rather than drawn. */
export const NO_RATED_SPORT_LINE =
  'A search runs in a sport you have been rated in, and there is not one yet.';

/**
 * The search control: the act, or what is standing in front of it.
 *
 * `no-rated-sport` has no label because it has no control — a screen with nothing to search
 * for draws the sentence above instead, which is 6.1's rule that this app never draws a
 * pressable-looking control that refuses.
 */
export function searchControlLabel(standing: FindAGameStanding): string | undefined {
  switch (standing.kind) {
    case 'searchable':
      return 'Search';
    case 'undeclared':
      return 'Say what kind of game first';
    case 'no-rated-sport':
      return undefined;
  }
}

/** A busy control is not a disabled one, so it keeps a label of its own. */
export const SEARCHING_LABEL = 'Searching…';

/**
 * The chrome's two words, here rather than in the component.
 *
 * `the-words.md` §20 is unqualified about it — *a label is never a template inlined in a
 * component* — and a spinner's name and a retry are labels like any other. They are the
 * screen's own rather than a code's, which is why they are constants and not a table.
 */
export const LOADING_PROFILE_LABEL = 'Loading your profile';

/** The read's retry. Distinct from *Search*, which is the **search's** own retry. */
export const RETRY_READ_LABEL = 'Try again';

/**
 * The two rows of answers that share their words, told apart by what each one commits to.
 *
 * *Competitive* is on this screen **twice** — once as the mode of one search, once as the
 * declaration kept on the profile — and to a listener moving between them the two are the same
 * word. The visible layout is what separates them for anybody who can see it; these names are
 * that separation for anybody who cannot, and each says the **lifetime** rather than the
 * heading above it, because the lifetime is the whole of the difference.
 */
export function modeControlLabel(mode: SearchMode): string {
  return `${modeLabel(mode)}, this search`;
}

export function declarationOptionLabel(intent: PlayIntent, sportName: string): string {
  return `${intentLabel(intent)}, your usual at ${sportName}`;
}
