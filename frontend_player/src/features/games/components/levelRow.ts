/**
 * **The level row** — a Skill rating as one line of text: `2,71 · Established · likely 2,55 – 2,87`
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §6.4).
 *
 * It began in Play's player card presentation, where every candidate card drew it. A booked
 * game's players card draws the same three clauses under each handle, with the confidence after
 * them (`seatLevelLine`), and may not import `features/play/` — the loop
 * [#569](https://github.com/Raketa02/Raketa/issues/569) removes — so the row came here
 * ([#574](https://github.com/Raketa02/Raketa/issues/574)): the players card is the reader that
 * stays, and Play's cards and the challenge screen read it through this feature's surface until
 * they go. Cited rather than re-spelled, so the band's name, the range's dash and the two-decimal
 * comma cannot drift between them.
 */

import { formatLevel, formatRange } from '@/shared/formatting/ratingFormat';

/** Everything the level row states, exactly as `player_card` published it. */
export interface LevelRowFacts {
  readonly level: number;
  /** The band's **published name**. Its numeric edges are not on the card, and not here. */
  readonly band: string;
  /** μ ± σ, clamped to the scale, as `rating` published it. */
  readonly range: { readonly low: number; readonly high: number };
}

/**
 * `2,71 · Established · likely 2,55–2,87`.
 *
 * The one word this app writes into the row is *likely*: the band's name is the server's, and
 * all three numbers take §B16's format through the one formatter.
 */
export function levelRow(facts: LevelRowFacts): string {
  return `${formatLevel(facts.level)} · ${facts.band} · likely ${formatRange(facts.range)}`;
}
