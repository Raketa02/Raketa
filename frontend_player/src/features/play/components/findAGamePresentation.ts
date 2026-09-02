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

import { builderTitle, isDoubles } from './builderPresentation';

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
 * *A plus is a time this search added* — the sentence that explains the mark on a cell the
 * player never ticked ([#283](https://github.com/Raketa02/Raketa/issues/283)).
 *
 * **The cell is not named**, which is `takenRungLine`'s rule read here: the offer that made it
 * says *look outside your week* rather than naming a Saturday morning, and the grid is already
 * showing which square it is. Naming it in prose as well would be the one place the feature
 * prints a slot the player did not choose.
 */
export const WEEK_ADDED_FOR_THIS_SEARCH =
  'A plus is a time this search added, not one you asked for. Nothing is saved.';

/** Both at once, in one sentence, because the slot under the grid holds two lines and no more. */
export const WEEK_CHANGED_AND_ADDED =
  'Changed from your profile, and a plus is a time this search added. Nothing is saved.';

/**
 * What the grid says about itself — **at most one sentence, and sometimes none.**
 *
 * Two facts can be true under one grid: the player edited their week, and a rung added a cell
 * to the search that ran. The slot beneath is two lines by 6.8's own rule, so they are one
 * sentence rather than two stacked — and the pair is decided **here** rather than by a screen
 * concatenating whichever happen to hold.
 *
 * @param week.improvised whether the working copy differs from the profile's grid.
 * @param week.addedForThisSearch whether a times rung widened the search on screen.
 */
export function weekFootnote(week: {
  readonly improvised: boolean;
  readonly addedForThisSearch: boolean;
}): string | undefined {
  if (week.improvised && week.addedForThisSearch) return WEEK_CHANGED_AND_ADDED;
  if (week.addedForThisSearch) return WEEK_ADDED_FOR_THIS_SEARCH;
  return week.improvised ? WEEK_CHANGED_FROM_PROFILE : undefined;
}

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
 * **The way onto the court** — the card this screen ends on, and the whole of what it says.
 *
 * The search control is not a word on a button. It is a picture of the court the search is
 * about to open, because *Search* names the machinery and this screen's own act is *build a
 * line-up*: a player pressing it lands on an empty court seating nobody but themselves, and a
 * control that said only *Search* would leave the court a surprise. It is the one way through
 * for a competitive game — the deck is the other half of `PlaySegment`, and never a second
 * copy of this one.
 *
 * Every sentence below branches on the **seat count** and none of them counts for itself:
 * `isDoubles` is `builderPresentation`'s, for the reason recorded there — *four* is a word
 * about a Sport, and a squash court must never be told to build one. The title is
 * `builderTitle`'s outright, at the one filling the card draws: **you, and nobody else.**
 */
const COURT_ENTRY_SEATED = 1;

export function courtEntryTitle(seats: number): string {
  return builderTitle({ seats, filled: COURT_ENTRY_SEATED });
}

/**
 * The pill beside the title, and the two different jobs it does.
 *
 * On a doubles court it names the **fact a player did not choose** — *padel is doubles* — so
 * four seats where two were expected are explained before they are counted. On a singles court
 * there is nothing to explain, so it says what the screen is handing over instead: the sides
 * are yours to pick. The sport is lower-cased because it is read inside a sentence rather than
 * on a control (§2's split, the same one `modeWord` is on).
 */
export function courtEntryTag(court: {
  readonly seats: number;
  readonly sportName: string;
}): string {
  return isDoubles(court.seats)
    ? `${court.sportName.toLowerCase()} is doubles`
    : 'you pick the sides';
}

/** What the court is for, in the order the builder offers it: the engine first, then the pool. */
export function courtEntryBody(seats: number): string {
  return (
    `Start from an empty court. Let the engine find the evenest ${isDoubles(seats) ? 'four' : 'opponent'}, ` +
    'or read the ranked cards and pick yourself — then swap anybody and watch the forecast move.'
  );
}

/**
 * The line beside the picture: **what the court is, and what pressing it does not do.**
 *
 * The second half is the whole reason a court can be drawn here at all. Nothing about this
 * screen reaches another player — `NOBODY_IS_CONTACTED_BY_SEARCHING` says it of the search and
 * this says it of the court — and a picture of four seats with no such sentence beside it
 * would read as four people about to be messaged.
 */
export function courtEntrySeatLine(seats: number): string {
  const shape = isDoubles(seats) ? 'Four seats · two a side' : 'Two seats · one a side';
  return `${shape} · nobody is contacted until you send it`;
}

/**
 * The card's **spoken name**, and one element for one action (`the-words.md` §20.1).
 *
 * The interpuncts and the picture are the sighted half; a listener gets the same three facts
 * as sentences. The sport is not in it — the chip row above has already said which sport this
 * screen is on, and the court inside the card is hidden from the tree for exactly that reason.
 */
export function courtEntryLabel(seats: number): string {
  const shape = isDoubles(seats) ? 'Four seats, two a side.' : 'Two seats, one a side.';
  return `${courtEntryTitle(seats)}. ${shape} Nobody is contacted until you send it.`;
}

/** Under the card, and true of both halves of Play. The last word the screen says. */
export const NOBODY_IS_CONTACTED_BY_SEARCHING =
  'Nobody is contacted by searching. You choose whom to challenge.';

/** What stands in front of the card while the sport has no declaration. */
export const SAY_WHAT_KIND_FIRST = 'Say what kind of game first';

/**
 * The search control: the act, or what is standing in front of it.
 *
 * `no-rated-sport` has no label because it has no control — a screen with nothing to search
 * for draws the sentence above instead, which is 6.1's rule that this app never draws a
 * pressable-looking control that refuses.
 *
 * The searchable case is the **card's** name rather than a verb, because the card *is* the
 * control: there is no *Search* button on this screen and there is nothing else the press
 * could be. The seat count comes in rather than being looked up, so this file keeps saying
 * nothing about a Sport it cannot see.
 */
export function searchControlLabel(
  standing: FindAGameStanding,
  court: { readonly seats: number },
): string | undefined {
  switch (standing.kind) {
    case 'searchable':
      return courtEntryLabel(court.seats);
    case 'undeclared':
      return SAY_WHAT_KIND_FIRST;
    case 'no-rated-sport':
      return undefined;
  }
}

/**
 * **There is no busy label**, and its absence is the decision rather than an omission.
 *
 * A busy control keeps a label of its own — which is why every other act in this app has one.
 * This one has no busy state to label: `SearchingLatch` covers the screen for as long as the
 * search is in flight, so nothing a *searching…* would be written on is on screen to read it.
 * The one moment the card is pressed and no latch goes up is a **paused** write, and that is
 * not a search running: the amber sentence beside it says the request resumes, and a card
 * reading *searching…* over it would contradict the only true thing on screen.
 */

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
