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
 * ## The forecast's heading is not the mode's
 *
 * The prototype split it four ways on doubles × competitive-or-fun — *Pairing forecast*,
 * *Balance forecast*, *How the four sits*, *How it would go*. Two of those name the engine
 * (`the-words.md` §20.3 already refused *Match score* on the card for the same reason: *Match
 * Fit* is the engine's name and a screen must not borrow it), and the remaining split is one
 * word of tone for a doubling of the table. **One heading per court shape**, and the mode is
 * already said in the eyebrow.
 */

import { counted } from '@/shared/formatting/counted';

import { modeWord } from './searchPresentation';
import type { SearchMode } from '../domain/vocabulary';

/** Whether the sport puts four people on the court, or two. The one branch in this file. */
const isDoubles = (seats: number) => seats > 2;

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
 * `2 seats open · tap one to pick somebody, or let the engine do it`.
 *
 * It states the two ways out in the order the controls under it are drawn, and it is the one
 * place *tap a seat* is said — the court itself cannot say it, because a seat's own accessible
 * name is a place and a state rather than an instruction.
 */
export function seatsOpenLine(open: number): string {
  return `${counted(open, 'seat open', 'seats open')} · tap one to pick somebody, or let the engine do it`;
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
export const TWO_WAYS_TITLE = 'Two ways to the same line-up';

export const TWO_WAYS_BODY =
  'The engine looks for the combination that plays out evenest — not simply the best fits one ' +
  'at a time. Picking yourself gives you the same ranked list, with everything on it.';

/**
 * What the swap toggle's row says under its own label, in both states.
 *
 * The label is `SWAP_TOGGLE_LABEL` and the state is the `switch` role's, so neither is
 * repeated here — §20.2's *prefer the role that carries the state*. What the line adds is what
 * a **tap** will now do, which is the thing the truth table changes and the control cannot
 * announce.
 */
export const SWAP_TOGGLE_DESCRIPTION: Readonly<Record<'on' | 'off', string>> = {
  on: 'Tap two seats to trade places. Nobody leaves the court.',
  off: 'Tap a seat to swap that player for somebody else.',
};

/**
 * The two halves of the court, as the forecast card's own rows label them.
 *
 * They are **your** side and **their** side rather than A and B, because a side follows you:
 * swap mode is *change sides, never seats*, so the half you are standing in is yours whichever
 * half of the picture it is. The same two words a seat's spoken name opens with, in the one
 * place they are read rather than heard.
 */
export const SIDE_HEADINGS = { yours: 'Your side', theirs: 'Their side' } as const;

/** The forecast card's region label. One per court shape — see the module note. */
export function forecastHeading(seats: number): string {
  return isDoubles(seats) ? 'How the four sits' : 'How it would go';
}

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

/** Empty the court and start again. It writes nothing outbound; nobody has been asked. */
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
