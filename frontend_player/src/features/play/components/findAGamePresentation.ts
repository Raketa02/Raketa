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

import {
  declarationOptionLabel,
  intentGloss,
  intentLabel,
} from '@/shared/vocabulary/playIntentPresentation';

import type { FindAGameStanding } from '../domain/findAGame';
import {
  declarationAgreesWithMode,
  declarationNamesAKind,
  intentForMode,
} from '../domain/playMode';
import type { PlayIntent, SearchMode } from '../domain/vocabulary';

import { isDoubles } from '../domain/lineup';

import { builderTitle } from './builderPresentation';

/** The screen's own title, and the one ⚡ opens on. */
export const FIND_A_GAME_TITLE = 'Find a game';

export const SPORT_HEADING = 'Sport';

/**
 * The mode section's heading — **one line, and it is the question the segment answers.**
 *
 * It was two: an eyebrow reading *This search only* over *What kind of game tonight*, written
 * when the segment and the declaration card still stood in one column and the pair had to be
 * told apart by their words ([#293](https://github.com/Raketa02/Raketa/issues/293)). **The
 * render order is what keeps them apart now** — the declaration is a precondition for this
 * form, so the two controls never co-occur — and the lifetime is still said in the two places
 * a player can act on it: `modeControlLabel` announces *Competitive, this search*, and the
 * standing line under the segment prints the durable answer the moment the two differ.
 *
 * *Tonight* went with the eyebrow. It was the shortest metaphor for a lifetime this section no
 * longer states, and the week grid below is where a search says which evenings it is about.
 */
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
 * The three declarations, their glosses and one answer's spoken name — **`shared/vocabulary`'s
 * now, and re-exported here because this is still where Play reads its words.**
 *
 * They moved the day `player_profile` became the second feature to draw a declaration: the You
 * tab lists what a player has declared per sport and offers the identical three answers about
 * the identical fact ([#296](https://github.com/Raketa02/Raketa/issues/296)), and it cannot
 * reach this file — `PlayerProfileSurface` is where that arrow is argued away. The promotion
 * test is `shared/README.md`'s, *"whether a second feature would have written the identical
 * table"*, and it would have written all three exactly.
 *
 * **Everything this screen says about the control stayed here**, which is the other half of the
 * same rule: the card's title, its eyebrow and the sentence naming who reads the answer are
 * about the question that gates a search, and no other screen asks it.
 */
export { declarationOptionLabel, intentGloss, intentLabel };

/**
 * **The standing line** — the declaration, said out loud on a screen the player is already on,
 * in each of the states the pair of values can be in
 * ([#294](https://github.com/Raketa02/Raketa/issues/294),
 * [#295](https://github.com/Raketa02/Raketa/issues/295)).
 *
 * Answered once, the durable value used to have no representation anywhere after that moment:
 * there was no *your usual at padel* on any screen, and no way to change it except by tripping
 * a prompt five searches later. That is what taught players the question had been a hurdle
 * rather than a setting they own, and it is the half of the reported confusion the render
 * order could not reach.
 *
 * ## Two states, one slot, and the disagreement is one of them
 *
 * Moving the segment **never writes the declaration** — the two values must be able to
 * disagree, which is `domain/playMode`'s whole argument and what ADR-0094's drift backstop
 * exists to catch — so the line changes in place instead and says what the disagreement costs.
 * The player watches the durable fact hold still while the switch moves, which is the clearest
 * demonstration available that they are two different things, and it costs no dismissal.
 *
 * Agreement is `declarationAgreesWithMode`'s and not an equality: *either suits me* is
 * contradicted by no search, which is the backend's own rule read on the client rather than a
 * second one invented here.
 *
 * ## And the third state is a surface with nothing to disagree with
 *
 * The deck has no mode — `SearchEnvelope.mode` is null exactly there — so it deals on the
 * declaration itself, and the line says so rather than offering to reconcile a pair that has
 * only one member ([#295](https://github.com/Raketa02/Raketa/issues/295)). `dealtParts` is
 * where the sentence and its one exception are written.
 *
 * ## Why the sentence arrives in pieces
 *
 * The value is drawn in `ink` inside a line that is otherwise `tiny` in `muted`, because the
 * declaration is the fact and the rest is the frame around it. A component splitting the
 * sentence itself would be a template inlined in a screen (`the-words.md` §20), so the split is
 * made here — and `spoken` is the same sentence whole, because a listener gets one element with
 * one name rather than three fragments read a beat apart.
 *
 * **Both names carry the lifetime**, which is this screen's recurring problem said once more:
 * *Competitive* is on it twice, and only *your usual* against *just this search* tells the two
 * apart. The action's name says what pressing it does rather than repeating the word on it —
 * *Update* alone is a verb with no object, and the object is the whole of what is at stake.
 */
export interface DeclarationLine {
  /**
   * What this surface and the profile are saying to each other.
   *
   * `agrees` and `differs` are the pair a **mode** makes available; `deals` is the state of a
   * surface that has none, and it is a third value rather than `agrees` because the sentence is
   * a different sentence and the absence is the reason for it.
   */
  readonly kind: 'agrees' | 'differs' | 'deals';
  /** The words before the declaration. */
  readonly lead: string;
  /** The declaration itself — drawn in `ink`, and the one word that does not move. */
  readonly value: string;
  /** The words after it, or `''` where the sentence ends on the value. */
  readonly tail: string;
  /** The whole of it, for a listener: one element, one name. */
  readonly spoken: string;
  /** The word on the control. */
  readonly action: string;
  /** What pressing it does, said in full. */
  readonly actionLabel: string;
  /**
   * **What pressing the control writes, or `undefined` where it writes nothing.**
   *
   * The one state that writes is `differs`, and the value is the mode's own declaration —
   * `intentForMode`, which is why this is decided here rather than re-derived by the row. A
   * component branching on the kind and reaching for the mode again would be the same rule in
   * two places, and the second one is the one that gets missed; it also has to carry a guard
   * for a mode that cannot be absent in that state. This is the fact `actionLabel` already
   * states in words — *make for fun your usual at padel* — in the shape the write takes.
   */
  readonly updatesTo: PlayIntent | undefined;
}

/**
 * *Change* — **the control that is not a write**, on both of the states that do not have one.
 *
 * The word and the name it is announced by move together, which is why they are one function
 * rather than a constant and a template repeated beside it: what the name has to carry is the
 * lifetime, and a second copy is where the two would stop saying the same thing.
 */
function changeTheProfile(sportName: string) {
  return { action: 'Change', actionLabel: `Change your usual at ${sportName}` };
}

export function declarationLine(facts: {
  readonly intent: PlayIntent;
  /**
   * What the segment above is sitting on, or **`undefined` where the surface has no mode**.
   *
   * The key is required and the value is nullable, so a caller states which of the two it is
   * rather than omitting a fact by accident. `undefined` is the deck: `SearchEnvelope.mode` is
   * null exactly there, and it is what makes the third state reachable.
   */
  readonly mode: SearchMode | undefined;
  readonly sportName: string;
}): DeclarationLine {
  const { intent, mode, sportName } = facts;
  const value = intentLabel(intent);
  const parts =
    mode === undefined ? dealtParts(intent, sportName) : searchParts(intent, mode, sportName);

  return { ...parts, value, spoken: `${parts.lead}${value}${parts.tail}` };
}

/** The two states a screen with a segment on it can be in. */
function searchParts(intent: PlayIntent, mode: SearchMode, sportName: string) {
  return declarationAgreesWithMode(intent, mode)
    ? {
        kind: 'agrees' as const,
        lead: `Your usual at ${sportName} is `,
        tail: '',
        updatesTo: undefined,
        ...changeTheProfile(sportName),
      }
    : {
        kind: 'differs' as const,
        lead: 'Just this search. Players still find you as ',
        tail: ` at ${sportName}.`,
        updatesTo: intentForMode(mode),
        action: 'Update',
        actionLabel: `Make ${modeLabel(mode)} your usual at ${sportName}`,
      };
}

/**
 * **The deck's one state** — and the sentence the whole line was worth writing for.
 *
 * A deal carries no mode, so there is nothing here for the declaration to disagree with and no
 * drift variant at all ([#295](https://github.com/Raketa02/Raketa/issues/295)). What that
 * absence buys is the plainest statement in the product of what the two values are: on this
 * screen the durable answer genuinely **is** what the deal runs on, and the sentence says it
 * rather than leaving the player to infer it from a control that is missing.
 *
 * *Either suits me* gets a different frame rather than a different word inside the same one.
 * `declarationNamesAKind` is where that is argued: the deal inherits a for-fun vector from an
 * answer that named no kind, and *dealing for fun games at padel — your usual* would report the
 * inheritance back as the player's own answer. So the frame states what the deal is **read
 * from** and claims no kind, which is all that answer ever claimed.
 */
function dealtParts(intent: PlayIntent, sportName: string) {
  return {
    kind: 'deals' as const,
    ...(declarationNamesAKind(intent)
      ? { lead: 'Dealing ', tail: ` games at ${sportName} — your usual` }
      : { lead: `Dealing on your usual at ${sportName} — `, tail: '' }),
    updatesTo: undefined,
    ...changeTheProfile(sportName),
  };
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
 * for a competitive game — the deck is the Players tab's, and never a second copy of this one.
 *
 * Every sentence below branches on the **seat count** and none of them counts for itself:
 * `isDoubles` is `domain/lineup`'s, for the reason recorded there — *four* is a word
 * about a Sport, and a squash court must never be told to build one.
 *
 * **The control names the game rather than the furniture.** It was the builder's title
 * outright — *Build the four* against *Set up the match* — and those two are one sentence in
 * two registers: one counts seats and the other names an occasion, so the pair only reads as a
 * pair to somebody who has seen both. *Doubles* and *singles* are the sport's own words, and
 * they differ by one word rather than by all of them.
 *
 * **And the builder now carries these same two words as its own title**, which is why this
 * reads `builderTitle` rather than repeating the pair. **The control names the screen it
 * opens** — `whyFitControlWord`'s rule and its reason — so a button promising *Build a
 * doubles* cannot land somebody on a heading that says something else. What is decided here is
 * still this control's own question, *what does pressing this do*; what it no longer does is
 * hold a second copy of the answer.
 */
export function courtEntryTitle(seats: number): string {
  return builderTitle(seats);
}

/**
 * The control's **spoken name**, and one element for one action (`the-words.md` §20.1).
 *
 * It says the shape in full — *Four seats, two a side* — where the button's own label says it
 * in one word. That was the split when a picture of the court stood above the control and was
 * hidden from the tree; the picture has since gone, and the sentence survives the change
 * rather than being made redundant by it. **A listener has no picture and no chip row to
 * count**, so *doubles* is a word they have to already know the arity of, and this is the one
 * place the platform spells it out. The sport is still not in it: the chips above have already
 * named which sport this screen is on.
 */
export function courtEntryLabel(seats: number): string {
  const shape = isDoubles(seats) ? 'Four seats, two a side.' : 'Two seats, one a side.';
  return `${courtEntryTitle(seats)}. ${shape}`;
}

/**
 * The search control: the act, or the absence of a control to name.
 *
 * **Two of the three standings have no label, because neither of them has a control.** That is
 * 6.1's rule — this app never draws a pressable-looking control that refuses — and it now
 * covers `undeclared` as well: the declaration is a precondition for the form existing, so a
 * screen without one draws the question and nothing under it
 * ([#293](https://github.com/Raketa02/Raketa/issues/293)). It used to draw the card greyed
 * with *Say what kind of game first* written on it, which was the availability step's settled
 * shape for a dead control — and a dead control is what stopped being drawn.
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
