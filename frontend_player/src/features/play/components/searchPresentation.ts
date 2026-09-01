/**
 * The search's own vocabulary: the windows, the ladder's offers, the sorts, and the caveat a
 * provisional forecast carries
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §17).
 */

import { counted } from '@/shared/formatting/counted';

import type { ForecastAssumption, SearchMode, SortOption, Window } from '../domain/vocabulary';

/**
 * How soon a search is asking about — *"a code, never a sentence: **tonight** is the client's
 * word."*
 *
 * §B16's title case is kept: these are window names, which §F1 rule 1 exempts.
 *
 * **`ANY` is the only rung that claims nothing.** An empty grid reads `ANY`, so *Whenever
 * suits* must not read as an enthusiastic answer to a question nobody answered — which is why
 * it is not *Any time!* and not *I'm flexible*.
 */
const WINDOW: Readonly<Record<Window, string>> = {
  TODAY: 'Tonight',
  TOMORROW: 'Tomorrow',
  WEEKEND: 'This weekend',
  THIS_WEEK: 'This week',
  ANY: 'Whenever suits',
};

export function windowLabel(window: Window): string {
  return WINDOW[window];
}

/**
 * The pool an answer came out of, as one sentence — ADR-0099's own shape, in words.
 *
 * The kernel *"emits values and stable machine codes, never display text"*, so the wire sends
 * `{sport, radius_km_used, players_in_range, window, post_gate}` and **the client writes the
 * sentence**. This is that sentence, and it is the honest empty state's whole body: a thin
 * pool and a broken floor are indistinguishable without it, which is why the description is
 * sent on every answer rather than only on the empty ones.
 *
 * **The count is post-gate, always**, and it is drawn as served: no pre-gate figure crosses,
 * because the delta between them is the number of people a mutual preference hid from this
 * searcher ([ADR-0096](../../../../../docs/adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)).
 *
 * **The sport's name is the caller's**, exactly as it is on `poolRankingStatus`: the screen
 * asking about a pool already holds this app's word for the sport it asked about, and
 * narrowing the served code a second time would be a second place it could be narrowed
 * differently.
 *
 * **The window clause is dropped where the code is one this build cannot read** — §3's drop
 * rather than a gap, because the sentence around it still states the count and the radius,
 * which are the two facts a player acts on.
 */
export function poolDescription(pool: {
  readonly playersInRange: number;
  readonly radiusKmUsed: number;
  readonly window: Window | null;
  readonly sportName: string;
}): string {
  const players = counted(pool.playersInRange, 'player', 'players');
  const range = `${players} in range for ${pool.sportName}, within ${pool.radiusKmUsed} km`;
  return pool.window === null ? `${range}.` : `${range} · ${windowLabel(pool.window)}`;
}

/**
 * A rung of the relaxation ladder, as the offer a player is given.
 *
 * The ladder ships on the pool alone ([#223](https://github.com/Raketa02/Raketa/issues/223)),
 * and every *widen* sentence is gated by `radius_clamp` before it is drawn — each is addressed
 * to a player who may already be at 50 km, and asking somebody for something they cannot give
 * is the one thing the ladder must not do.
 *
 * **The rung's letter is never printed.** `Rung` values are letters rather than numbers
 * precisely so nobody lines them up against a struck rung, and printing either spelling would
 * publish an engine-internal ordering — so it is not a parameter of this function at all.
 */
export function relaxationOffer(
  offer: { readonly ask: 'TIMES' } | { readonly ask: 'RADIUS'; readonly radiusKm: number },
): string {
  return offer.ask === 'TIMES' ? 'Look outside your week' : `Look out to ${offer.radiusKm} km`;
}

/**
 * The sorts a row may offer.
 *
 * The row draws `sorts_available` and vanishes when it is empty (#231), so two of these have
 * words and no reachable surface: `MOST_RELIABLE` is in the vocabulary and never offered
 * today, and `EVENEST` reads `would_be_forecast`, which nothing has ever written. **Both keep
 * words so the table is exhaustive by type** — that is what makes the day one becomes
 * offerable a change to nothing at all.
 */
const SORT: Readonly<Record<SortOption, string>> = {
  BEST_FIT: 'Best fit',
  CLOSEST: 'Closest',
  MOST_RELIABLE: 'Most reliable',
  EVENEST: 'Evenest',
};

export function sortLabel(sort: SortOption): string {
  return SORT[sort];
}

/**
 * What a provisional figure assumed — ADR-0108's rule that the figure and its caveat are one
 * thing.
 *
 * §F2 #6, **verbatim**. The wire carries this as an open string rather than a union, so a code
 * this build has no words for gets nothing back and the caller draws §3's gap: the figure it
 * heads is a total, and a total with an unexplained assumption is the reading ADR-0108 exists
 * to prevent.
 */
const ASSUMPTION: Readonly<Record<ForecastAssumption, string>> = {
  EMPTY_SEAT_MATCHES_ITS_PARTNER:
    'Runs on what is seated so far, reading each half-empty side as if the missing player ' +
    'matched the one already there. It settles as you add.',
};

export function forecastAssumption(assumption: ForecastAssumption): string {
  return ASSUMPTION[assumption];
}

/**
 * The mode as a **word inside a sentence** — *"your last five padel searches were for fun"*.
 *
 * Lower case, because it is prose rather than a control. The mode toggle's own labels arrive
 * with the screen that draws the toggle; what is here is the one reading a sentence needs.
 */
const MODE_WORD: Readonly<Record<SearchMode, string>> = {
  COMPETITIVE: 'competitive',
  FOR_FUN: 'for fun',
};

export function modeWord(mode: SearchMode): string {
  return MODE_WORD[mode];
}
