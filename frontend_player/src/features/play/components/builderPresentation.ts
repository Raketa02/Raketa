/**
 * Everything the builder says, and the two facts that decide most of it: **how many seats the
 * sport has, and how many of them are still open.**
 *
 * §1's mechanism, as everywhere else in this feature: a code or a count in, a sentence out,
 * and never a template inlined in a component. What is *not* here is the court's own
 * vocabulary — the four `UnfilledReason` codes, the five `GroupReason` codes, the withheld
 * mark and `OptimisedFor` are `courtPresentation.ts`'s, because they are things the **engine**
 * named and this file writes only what the screen is entitled to say for itself.
 *
 * ## *The four* is a word about a sport, not about a number the copy invents
 *
 * Padel and badminton seat four, tennis and squash two, and *"the seat count is the Sport"* —
 * read off `Court`'s own coordinates. So every sentence here that could say *four* takes the
 * count and asks for it, which is what stops a squash court being told to build one.
 *
 * ## The forecast's heading is not the mode's, and it names what the card draws
 *
 * The prototype split it four ways on doubles × competitive-or-fun — *Pairing forecast*,
 * *Balance forecast*, *How the four sits*, *How it would go*. **One heading per court shape**
 * still: the remaining split is one word of tone for a doubling of the table, and the mode is
 * already said in the eyebrow.
 *
 * **Which pair survives is a reversal, and the argument that replaced it is this.** This note
 * refused the first two — *"two of those name the engine"*, on `the-words.md` §20.3's rule that
 * *Match Fit* is the engine's name and a screen must not borrow it — and kept *How the four
 * sits* / *How it would go*. That was right for the card those headings were chosen for, which
 * said one number and nothing about where it came from: a heading over a bare percentage that
 * reached for *pairing* or *balance* would have been borrowing a word for the thing that
 * computed it. The card now prints **two side strengths, the gap between them and a bar**
 * ([#290](https://github.com/Raketa02/Raketa/issues/290)), so the heading stands over a
 * **split** rather than over a figure — a *pairing* is who is beside you and a *balance* is
 * which way the two halves lean, and both are what is drawn on the card. §20.3 is untouched:
 * its rule is about *Match Fit* and *Match score*, and neither word is here.
 */

import { modeWord } from './searchPresentation';
import { isDoubles, type CourtHalf } from '../domain/lineup';
import type { SearchMode } from '../domain/vocabulary';

/**
 * The screen's title.
 *
 * *Complete* rather than *Build* the moment somebody is already seated, because that is what
 * the screen is then for: `locked_seats` are people the fill will seat **around**, and a title
 * still saying *build* would describe an empty court the player can see is not empty.
 */
export function builderTitle(court: { readonly seats: number; readonly filled: number }): string {
  const noun = isDoubles(court.seats) ? 'four' : 'match';
  return court.filled > 1
    ? `Complete the ${noun}`
    : isDoubles(court.seats)
      ? 'Build the four'
      : 'Set up the match';
}

/** `Padel · doubles · for fun` — the three facts the search was run under. */
export function builderEyebrow(court: {
  readonly sportName: string;
  readonly seats: number;
  readonly mode: SearchMode;
}): string {
  const shape = isDoubles(court.seats) ? 'doubles' : 'singles';
  return `${court.sportName} · ${shape} · ${modeWord(court.mode)}`;
}

/**
 * ⚡'s label, and it names **what is left** rather than the whole court.
 *
 * *The seats* on an untouched court and *the rest* the moment anybody is seated: the engine
 * fills around `locked_seats` and never over them, so a control offering to fill *the seats*
 * beside three faces would be offering to do something the request cannot ask for.
 */
export function fillSeatsLabel(court: { readonly seats: number; readonly filled: number }): string {
  return court.filled > 1 ? 'Let the engine fill the rest' : 'Let the engine fill the seats';
}

/** The other branch, and the screen that owns widening. */
export const PICK_PLAYERS_LABEL = 'Pick players myself';

/**
 * The two ways to the same line-up, said once and beneath both controls.
 *
 * It exists because ⚡ and the pool are **not** a fast path and a slow one: the engine looks
 * for the combination that plays out evenest rather than the four best individual fits, which
 * is a different answer and not a quicker one.
 */
/**
 * **What a seat does, said above the court** — the one sentence that replaced the toggle.
 *
 * Swapping was a mode: a `switch` in a card over the court, two descriptions under it, and a
 * tap on a seat that meant *replace* or *trade* depending on which way it was thrown. The
 * mode is gone and a seat trades, always (`domain/lineup`'s truth table), so what was a
 * control's description becomes a **capability line** — the screen's own statement of what
 * the graphic beneath it will do.
 *
 * It is one string and not two because there is no longer a state for a second one to
 * describe. It is drawn only where a trade is possible at all — one other person on the court
 * — for the reason the toggle was: a sentence advertising an act nobody can perform yet is a
 * sentence that teaches the wrong thing.
 *
 * **It is announced.** The court's summary element names the Sport and the seats filled and
 * every seat names its own place; none of them says what pressing one does, and this is the
 * only place that fact is written. It was the toggle's job, and the toggle announced itself.
 */
export const SWAP_HINT = 'Tap a seat to swap players and propose your game layout';

/**
 * The two halves of the court, as the forecast card's own rows label them.
 *
 * They are **your** side and **their** side rather than A and B, because a side follows you:
 * swap mode is *change sides, never seats*, so the half you are standing in is yours whichever
 * half of the picture it is. The same two words a seat's spoken name opens with, in the one
 * place they are read rather than heard.
 *
 * Keyed by `CourtHalf` rather than by its own inline shape, on §1's mechanism: a table over a
 * closed vocabulary is what makes *a half with no words* fail to compile instead of rendering
 * blank. The union itself is spelled once, in `domain/lineup.ts`, which is where the rule that
 * folds three seat places onto two halves lives
 * ([#300](https://github.com/Raketa02/Raketa/issues/300)).
 *
 * `as const` stays: the key check is what `Record` buys, and the literal values are what the
 * tests and every caller read.
 */
export const SIDE_HEADINGS = {
  yours: 'Your side',
  theirs: 'Their side',
} as const satisfies Record<CourtHalf, string>;

/** The forecast card's region label. One per court shape — see the module note. */
export function forecastHeading(seats: number): string {
  return isDoubles(seats) ? 'Pairing forecast' : 'Balance forecast';
}

/**
 * `You + Piotr` — **one half of the court, named by who is standing on it**.
 *
 * §15's `sideNames` was deleted for a rule that still holds — *"a formatter that returns one
 * string has decided the layout, and this one must not"* — and the row it was deleted for is
 * still a **list**: the names beneath the split are one control per person, because each opens
 * `SH.whyfit` for the player it names. This is the other row, and it is not a list of people:
 * it is the **label of a strength**, one box over one number, and the bar's own segment label
 * beneath it takes exactly one string per side. So the join is the layout here rather than a
 * formatter deciding one, and it truncates in its own box per side — which is what stops
 * two 64-character handles reflowing a three-column row.
 *
 * The handles themselves are `playerName()`'s, whole (ADR-0107); this only joins them.
 *
 * **A side with nobody on it is named by which side it is.** An empty half is a real state on
 * a provisional court, and an empty label over a strength the engine did serve would read as a
 * missing number rather than as a missing player.
 */
export function sideName(names: readonly string[], whenEmpty: string): string {
  return names.length === 0 ? whenEmpty : names.join(SIDE_JOIN);
}

const SIDE_JOIN = ' + ';

/**
 * The word between the two **sides**, and the whole of what the column between them says.
 *
 * Lower case for `GAP_WORD`'s reason — it is a joint rather than a heading — and it is drawn
 * and hidden, because the two panels either side of it are already named *Your side* and
 * *Their side*: a listener hearing *your side, vs, their side* is being read the punctuation.
 */
export const VS_WORD = 'vs';

/**
 * The word between the two strengths, and the whole of what the middle column says.
 *
 * Lower case, because it is a unit rather than a heading: the two figures either side of it
 * are the sentence, and the row's spoken form reads *… gap 0,00* for the same reason.
 */
export const GAP_WORD = 'gap';

/**
 * **The one word beneath the tinted number**, and the whole of the mark.
 *
 * `Forecast.provisional` is the fact; the sentence under it is `forecastAssumption`'s, and it
 * is the engine's. This word is what makes the figure readable at a glance without it —
 * ADR-0108's rule that the figure and its caveat are one thing, held at the size the eye
 * actually reaches first.
 */
export const PROVISIONAL_WORD = 'Provisional';

/** *Even it out* — a **selection** out of a response already held, and never a calculation. */
export const EVEN_IT_OUT_LABEL = 'Even it out';

/** What the control says when it would select what is already drawn. */
export const ALREADY_EVENEST = 'This is the evenest these four can be arranged.';

/**
 * The other half of that sentence — **what the arrangement on screen costs against the
 * evenest one**, quoted rather than computed.
 *
 * The card said `ALREADY_EVENEST` or nothing, which left the one state a player can actually
 * act on unexplained: a court arranged by hand, with *Even it out* beside it and no account of
 * what pressing it would buy. The figure is the **evenest arrangement's own `pct`**, read out
 * of a response the screen is already holding — every arrangement crosses, so this is a
 * selection like the button beneath it and not a second forecast (`domain/forecast`).
 *
 * It is a percentage read through `formatPercent` at the call site, for §B16's reason: how a
 * figure is spelled is one table, and this file writes sentences rather than numbers.
 */
export function arrangedYourWayLine(evenest: string): string {
  return `Arranged your way. The evenest split of these four would read ${evenest}.`;
}

/**
 * Empty the court and start again. It writes nothing outbound; nobody has been asked.
 *
 * **It sits inside the forecast card, beside *Even it out***, because the two are the same
 * kind of act on the same object: one re-arranges the four and the other discards them, and a
 * *Start over* stranded under the card read as a way off the screen rather than a way to empty
 * the court. Neither is the screen's pinned slot, which belongs to the send.
 */
export const START_OVER_LABEL = 'Start over';

/**
 * The forecast's own wait, and the **one retry in this tab that gains a control of its own**.
 *
 * `retryTarget`'s placement rule: three of the four waits reuse a control the screen already
 * has, *"and only the forecast gains one, because a player who has stopped changing seats
 * would otherwise sit with no number and no way to ask again."*
 */
export const FORECASTING_LABEL = 'Working out how even this would be…';

export const RETRY_FORECAST_LABEL = 'Try the forecast again';

/** ⚡'s own wait, on the control that failed — the fill mints a record, so the retry is ⚡. */
export const FILLING_LABEL = 'Filling the seats…';

/**
 * What the builder says when it is holding a line-up and cannot read the search it came off.
 *
 * `lineupStanding`'s `unreadable`, which is *"the honest answer while the origin search has not
 * been read back yet, or when the cache no longer holds it"*. A screen that cannot say whether
 * a line-up is current must not act as though it is — so it says so, and offers the act that
 * is defined either way.
 */
export const NO_RECORD_TITLE = 'This line-up has lost its search';

export const NO_RECORD_BODY =
  'The search it was built from is no longer here, so nobody can be added or replaced. Running ' +
  'a new one starts a fresh court.';
