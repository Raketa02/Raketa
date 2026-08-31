/**
 * The two lines a card prints **about the player it draws** — the level row and the meta line.
 *
 * Both come off `player_card` and nowhere else, which is ADR-0107's rule that *a card says
 * only what its subject published, and every field on it is a fact about that person alone*.
 * The client computes nothing here: not the likely range from a σ, not a band from a table of
 * four edges. Either would be a domain rule encoded in TypeScript, which is the objection that
 * promoted `distance_km` out of the distance evidence in the first place.
 *
 * ## The level row — three facts, and the word the prototype spent on the wrong one
 *
 * §B11 and §B12 draw the row as `"{level} · band {low}–{high}"`, and **that is not a band**.
 * The four bands are New · Developing · Established · Advanced; `2,55–2,87` is the **likely
 * range**, μ ± σ. The prototype spent the domain's word on a different concept, and a reader
 * who has seen the band names anywhere else in the app reads the pair as the band's own edges
 * — which is exactly what `Band`'s docstring forbids: *"a card can never name a band that
 * disagrees with the number beside it"*
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §6.4).
 *
 * So the range carries a word of its own and the band keeps its name. *Fact · mechanism*,
 * §F1 rule 4's shape — the level and its plain-language meaning, then the caveat.
 *
 * ## The meta line — **`{km} km`, or `In your area · {km} km`**, and nothing else.
 *
 * §B11 draws it as `"{area} · {km} · active {x}"`, and **two of those three slots have
 * nothing behind them**
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §6.3):
 *
 * - `active {x}` was refused in writing by [#218](https://github.com/Raketa02/Raketa/issues/218) —
 *   a datable activity figure is exactly what ADR-0106 §5 withholds.
 * - `{area}` is refused by `areas.py`, in writing: an `area_code` is a **coordinate string**
 *   (`A+050612+0019938`), *"the human-readable area a player card prints has no producer in
 *   this repository yet, and deriving one there would be inventing a naming scheme nobody has
 *   calibrated. That refusal stands."*
 *
 * What the module licenses is **one** client sentence from that code, and it is honest: *"a
 * card saying they are in your area is a comparison the client makes between two codes, which
 * is exactly the shape [ADR-0021](../../../../../docs/adr/0021-kernel-in-backend-clients-derive-by-comparison.md)
 * licenses a client to compute."*
 *
 * So the comparison is drawn and the code never is. The day a gazetteer exists, this line
 * gains a name and no other consumer moves.
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

/** Whole kilometres, as the contract sends them — the client rounds nothing. */
export interface MetaLineFacts {
  readonly km: number;
  /** Their coarse area, as a machine code. **Never printed.** */
  readonly theirAreaCode: string;
  /** Yours, for the one comparison this line is allowed to make. */
  readonly myAreaCode: string;
}

export function metaLine(facts: MetaLineFacts): string {
  const distance = `${facts.km} km`;
  return facts.theirAreaCode === facts.myAreaCode ? `In your area · ${distance}` : distance;
}
