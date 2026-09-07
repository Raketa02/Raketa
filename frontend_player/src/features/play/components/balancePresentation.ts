/**
 * How even a game is, in a word — §B9's word, and the tone it does not quite share.
 *
 * [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §18 cites this
 * vocabulary rather than writing it, because §B9 already fixed the four words and their
 * breaks. What §20 adds is **why the word is not optional**: the bar is a colour, and
 * [Part 13](../../../../docs/design-system.md#part-13--accessibility) forbids colour as the
 * only signal. So the word is drawn beside every figure and it is the whole of the bar's
 * accessible name (§20.4).
 *
 * ## It lives in `components/`, and that line is drawn once
 *
 * [`the-play-components.md`](../../../../../docs/specs/matchmaking/the-play-components.md) §7:
 * *"a rule somebody could be wrong about goes to `domain/`; a table mapping a value to the
 * words this app chose for it goes to `components/`."* Nobody can be wrong about *Fairly
 * even* — it is this app's word for a number — so it sits beside the other copy tables, on
 * `radiusPresentation.ts`'s precedent.
 *
 * ## The word breaks in four where the tone breaks in three
 *
 * §B9's word steps at 85 / 70 / 55 and its colour steps at 70 / 55, so *Very even* and
 * *Fairly even* share one green. [7.11](../../../../docs/design-system.md#711-the-balance-bar)
 * records that as **correct rather than untidy**: Part 13 is satisfied by the word, and a
 * fourth tone would need a fourth *meaning*, which
 * [15.2](../../../../docs/design-system.md#152-adding-a-colour) forbids inventing. Left
 * unwritten, somebody eventually tidies it into four colours.
 *
 * **The percentage is the server's and is never derived here.** `the-play-screens.md` §11.3
 * is *no forecast arithmetic on the client*; the bar maps an advantage to a fold and this
 * file maps a served evenness to a word, and neither computes the other.
 */

import { formatPercent } from '@/shared/formatting/ratingFormat';
import type { BalanceBarTone } from '@/shared/ui/BalanceBar';

/**
 * The word's three breaks, in the order they are tested — §B9's 85 / 70 / 55.
 *
 * A list of pairs rather than a `Record`, because this vocabulary is an **ordered** one: the
 * value that decides a word is a threshold, and a table keyed by the word would put the
 * ordering somewhere a reader has to reconstruct.
 */
const WORD_BREAKS: readonly (readonly [number, string])[] = [
  [85, 'Very even'],
  [70, 'Fairly even'],
  [55, 'One side favoured'],
];

/** Below every break. Named rather than inlined, so the fourth word is as findable as three. */
const LOPSIDED = 'Lopsided';

/** The tone's two breaks — one step coarser, deliberately. */
const TONE_BREAKS: readonly (readonly [number, BalanceBarTone])[] = [
  [70, 'ok'],
  [55, 'warn'],
];

const LOPSIDED_TONE: BalanceBarTone = 'bad';

/**
 * *Very even* · *Fairly even* · *One side favoured* · *Lopsided*.
 *
 * `pct` is the served evenness, whole or not — the rounding is the figure's, not the word's,
 * so a 84,6 that prints as *85%* still reads *Fairly even*. That is the honest pairing: the
 * word describes the number the engine sent, and only the drawn figure is rounded.
 */
export function balanceWord(pct: number): string {
  return stepped(WORD_BREAKS, LOPSIDED, pct);
}

/** The bar's colour. Three, because a fourth would be a fourth meaning. */
export function balanceTone(pct: number): BalanceBarTone {
  return stepped(TONE_BREAKS, LOPSIDED_TONE, pct);
}

/**
 * The first step a value clears, or the floor.
 *
 * One function for both, because the word and the tone read the **same ladder at different
 * rungs** — that is the whole of what §B9 recorded rather than tidied, and two copies of the
 * lookup is where somebody eventually makes one of them `>` and the other `>=`.
 */
function stepped<T>(breaks: readonly (readonly [number, T])[], floor: T, pct: number): T {
  return breaks.find(([step]) => pct >= step)?.[1] ?? floor;
}

/**
 * The bar's accessible name — **the word first, then the figure** (§20.4).
 *
 * The word leads because it is the point: a listener who hears *74%* has heard the number the
 * sighted player reads in the tint, and nothing of what the tint meant. The figure takes
 * §B16's one percentage shape through `formatPercent`.
 */
export function balanceLabel(pct: number): string {
  return `${balanceWord(pct)}, ${formatPercent(pct)}`;
}

/**
 * The same two facts **drawn**, and the reason a bar is never alone on a surface.
 *
 * [Part 13](../../../../docs/design-system.md#part-13--accessibility)'s *never colour alone*
 * bites on the sighted half as hard as on the spoken one: a bar is a tint, its three tones
 * step at 70 and 55, and a reader who has not been told what the tint means has read a
 * colour. So every surface that draws the bar draws this beside it — which is also what makes
 * `PREDICTED_BALANCE` a term the card **renders a value for** rather than one it tints.
 *
 * It is a separate function from `balanceLabel` and the difference is one separator, which is
 * the difference between the two registers: a middot is a visual join that a screen reader
 * reads as a word or not at all, and a comma is the pause a spoken clause needs.
 */
export function balanceReading(pct: number): string {
  return `${balanceWord(pct)} · ${formatPercent(pct)}`;
}
