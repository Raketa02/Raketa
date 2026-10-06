/**
 * The rating's numbers, as they are written — and, because the decimal comma has one home,
 * the app's other decimals too: a star average and a distance.
 *
 * **Comma decimals, two places** (design-system Appendix B). Every figure here is drawn in
 * a mono, tabular role, which is the mechanism that stops a row reflowing when a level goes
 * from 2,71 to 2,80 — the formatting is only the other half of it.
 *
 * `toFixed` and a substitution rather than `toLocaleString`: Hermes ships without the full
 * ICU data unless it is explicitly built in, so a locale-aware formatter would produce a
 * comma on one device and a point on another for the same rating. This is a **house
 * convention**, not a localisation — when the app is genuinely localised it becomes one,
 * in one place, which is here.
 *
 * **It is in `shared/` because a level is printed wherever a player is.** It was
 * `onboarding/components/` while the result screen was the only thing that drew one; Play
 * prints a level on every card, in every reason line about a level gap, and on every seat of
 * a court, and ESLint blocks a deep import between features outright — so the two options
 * were promotion or a second copy of *two fixed decimals, decimal comma*. A second copy of
 * that is the drift the design system's *every number is mono and tabular* rule exists to
 * prevent ([`the-play-components.md`](../../../../docs/specs/matchmaking/the-play-components.md)
 * §7).
 */

const DECIMALS = 2;

/** What the platform publishes a star average to — see {@link formatStars}. */
const STAR_DECIMALS = 1;

/** What the platform serves a distance to — see {@link formatDistanceKm}. */
const DISTANCE_DECIMALS = 1;

/**
 * **U+2212, never the hyphen** — `the-words.md` §6.2's *"two decimals, decimal comma, U+2212
 * minus"*, which is §B16 read at the one place a figure on this scale can be negative.
 *
 * Nothing printed a negative level until the forecast card's **gap**, which is `your_side −
 * their_side` and signed by construction
 * ([#290](https://github.com/Raketa02/Raketa/issues/290)) — so this is inert on every other
 * caller by construction: a Level is 1,00–5,00 and a range is two of them.
 */
const MINUS = '\u2212';

/** The en dash is the range dash, and it is spaced so two 4-character numbers stay apart. */
const RANGE_DASH = ' – ';

/** The comma substitution itself — spelled once, which is the whole of this module's claim. */
function comma(value: number, places: number): string {
  return value.toFixed(places).replace('.', ',');
}

function decimal(value: number): string {
  return comma(value, DECIMALS).replace('-', MINUS);
}

/** A Level, an Uncertainty, a band edge — anything on the 1,00–5,00 scale. */
export function formatLevel(value: number): string {
  return decimal(value);
}

/**
 * A **movement** on that scale — `+0,08`, `−0,05`.
 *
 * The plus is the whole of what this adds, and it is not decoration: the competitive card's
 * stake boxes print two figures whose signs are the fact
 * ([#312](https://github.com/Raketa02/Raketa/issues/312)), and a bare `0,08` beside a
 * `−0,05` reads as a magnitude somebody forgot to sign rather than as a gain. The minus is
 * `decimal`'s own U+2212, so the pair lines up in a tabular column.
 *
 * A zero takes neither sign, which is inert on the one caller today — the server's invariant is
 * `win_delta > 0 > loss_delta` — and is the honest reading anywhere else: nothing moved.
 */
export function formatSignedLevel(value: number): string {
  return value > 0 ? `+${decimal(value)}` : decimal(value);
}

/**
 * A **star average** — `4,7`, `3,0`. One decimal, and the trailing nought is never trimmed.
 *
 * Not `formatLevel`, though both are on a one-to-five scale: the platform publishes this mean to
 * **one** decimal, and printing `4,70` would claim a second place nobody serves, on the one
 * figure whose whole design is being coarse enough to be honest. It is here rather than beside
 * the block that draws it because the decimal comma is a house convention with one home — a
 * second `replace('.', ',')` in a feature is exactly the drift this module's note names.
 *
 * The word *rating* on this platform is Skill rating's, which is why this is spelled **stars**
 * ([`CONTEXT.md`](../../../../CONTEXT.md) · Sportsmanship).
 */
export function formatStars(value: number): string {
  return comma(value, STAR_DECIMALS);
}

/**
 * A **distance** — `1,9 km`, `12,0 km`, `0,1 km`. One decimal, the comma, the unit; the trailing
 * nought is never trimmed.
 *
 * **One function, every caller** ([ADR-0174](../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
 * §2): the deck card's meta line, the record's identity line and the why-fit sentence print the
 * same number for the same person, and that is only true while they print it through the same
 * function. `distance_km` is served to one place already — measured between two **drawn spots**,
 * and never below `0.1` — so this rounds nothing the server did not, and the floor is printed
 * as served rather than enforced here. Nothing prints a whole kilometre any more.
 *
 * Here rather than in a `distanceFormat` of its own for `formatStars`' reason: the decimal
 * comma is a house convention with one home, and a second `replace('.', ',')` is the drift this
 * module's note names.
 */
export function formatDistanceKm(value: number): string {
  return `${comma(value, DISTANCE_DECIMALS)} km`;
}

export function formatRange(range: { readonly low: number; readonly high: number }): string {
  return `${decimal(range.low)}${RANGE_DASH}${decimal(range.high)}`;
}

/**
 * A percentage — **whole, always**.
 *
 * A confidence, a forecast's evenness, a term's value read as a share: none of them survives
 * being read as "28,4% sure", the engine's own precision is not a fact about the pairing, and
 * nothing on any screen compares two of them closely enough for a decimal to answer a
 * question. One shape for every percentage in the app is §B16's rule; this is where it is.
 */
export function formatPercent(value: number): string {
  return `${Math.round(value)}%`;
}

/** Grosze in a złoty — the wire's unit is the grosz (`docs/value-formatting.md`). */
const GROSZE = 100;

/**
 * **Money, from the wire's grosze** — `32 zł`, `27,50 zł`: the decimal comma, a space before the
 * unit, and the grosze only when there are some.
 *
 * The first price the app draws is a share on a group's game card (#553), and
 * `docs/value-formatting.md` left the rendering to that first client. A share is exact to the
 * grosz — a price that does not split among the seats is refused — so a whole złoty is the usual
 * case, and printing `32,00 zł` on every card would be two characters of nothing. Here for the
 * comma's one home.
 */
export function formatZloty(grosze: number): string {
  const whole = grosze % GROSZE === 0;
  return `${whole ? String(grosze / GROSZE) : comma(grosze / GROSZE, DECIMALS)} zł`;
}
