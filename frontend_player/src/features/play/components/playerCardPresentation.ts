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

import { counted } from '@/shared/formatting/counted';
import { formatLevel, formatPercent, formatRange } from '@/shared/formatting/ratingFormat';
import { slotName } from '@/shared/vocabulary/availabilityPresentation';
import type { WeekCell } from '@/shared/vocabulary/week';

import type { CandidateAction } from './accessibilityPresentation';

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

/**
 * The two facts a card draws as a **labelled row** rather than as a sentence.
 *
 * A row and a reason line are the same fact in two registers, and the register is what
 * decides which of them a surface gets: a reason line answers *why this person* and is
 * **selected**, where a row is a fact the card states unconditionally. That is also the whole
 * mechanism behind the de-duplication filter — a card that draws one of these rows declares
 * the term in its own drawn set, and the sentence for it never appears twice
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §5, §10).
 *
 * The labels are the spec's own names for the rows.
 */
export const BALANCE_ROW_LABEL = 'Predicted balance';
export const OVERLAP_ROW_LABEL = 'You overlap';

/**
 * `74% even · 66% sure` — the forecast, and the platform's own caveat beside it.
 *
 * The **row's** half of `predictedBalanceReason`, which is written as this plus the word
 * *Forecast*: the sentence has to name what the figure is about because it stands alone in a
 * reason list, and the row does not because its label already did. One spelling and two
 * registers, rather than two spellings of one fact — and `reasonPresentation` composes this
 * one rather than repeating it, so the pair cannot drift.
 *
 * **Both figures are the server's**, through §B16's one percentage shape. There is no
 * forecast arithmetic on the client ([`the-play-screens.md`](../../../../../docs/specs/matchmaking/the-play-screens.md) §11.3).
 */
export function balanceRowValue(evidence: {
  readonly pct: number;
  readonly confidence: number;
}): string {
  return `${formatPercent(evidence.pct)} even · ${formatPercent(evidence.confidence)} sure`;
}

/**
 * The measured zero — §6.2's own sentence, and **the one string both registers share**.
 *
 * It lives here rather than in `reasonPresentation` because the *row* is the surface that can
 * reach it: every card that draws an overlap row has `AVAILABILITY_OVERLAP` in its drawn set,
 * so the reason line for that term is filtered off exactly the cards the row appears on. A
 * zero spelled `0 slots` on the row and *No shared slots* in the sentence would make the
 * copy the row could reach the copy nobody ever reads.
 *
 * It is **a fact about arranging a game and not a refusal**: the availability term zeroes,
 * nobody is removed, and the times rung of the ladder exists for exactly this pairing.
 */
export const NO_SHARED_SLOTS = 'No shared slots — one of you would have to bend';

/**
 * `3 slots · next Tue evening` — how much of your week is theirs, and the soonest of it.
 *
 * The count routes through the one pluralisation helper, so no string here hardcodes an `s`
 * (§4, §19), and the slot name is the **promoted** `DayPart` and weekday tables rather than a
 * third list. The zero takes {@link NO_SHARED_SLOTS} rather than `0 slots`, for the reason
 * written there.
 */
export function overlapRowValue(evidence: {
  readonly sharedCount: number;
  readonly nextSlot: WeekCell | null;
}): string {
  if (evidence.sharedCount === 0) return NO_SHARED_SLOTS;

  const slots = counted(evidence.sharedCount, 'slot', 'slots');
  return evidence.nextSlot === null ? slots : `${slots} · next ${slotName(evidence.nextSlot)}`;
}

/**
 * What a card's primary button **says**, against what it announces.
 *
 * The visible word is short because it sits on a card in a list of them; the spoken name is
 * `candidateActionLabel`'s and names the subject, on
 * [6.9](../../../../docs/design-system.md#69-the-photo-tile-and-picker)'s rule that a control
 * acting on one of twenty identical rows says which one. A `Record` over the closed set, so a
 * third action arrives with its word or does not build.
 */
export const CANDIDATE_ACTION_WORD: Readonly<Record<CandidateAction, string>> = {
  ADD_TO_COURT: 'Add',
  CHALLENGE: 'Challenge',
};

/**
 * The deck's two, and the 🎾 that is drawn and never spoken.
 *
 * The glyph is in the visible word alone — `deckAnswerLabels` composes the spoken pair
 * without it, per §E6: *"otherwise it announces as 'tennis ball let's play'"*. It is the same
 * split the fit pill's ✦ takes, and it is a split rather than a rule about glyphs.
 */
export const DECK_ANSWER_WORDS = { pass: 'Not today', accept: "🎾 Let's play" } as const;

/**
 * What the generated poster says it is, on a card.
 *
 * [6.9](../../../../docs/design-system.md#69-the-photo-tile-and-picker) requires the sentence
 * of every poster it draws — *"nobody should have to see a poster to know they are not
 * looking at the player"* — and the profile step's own wording is second-person and about a
 * photo the reader could go and add, which is not this. Third-person, and it names no one:
 * the card body's label already says whose face this is standing in for.
 *
 * It is **unspoken on every surface that draws it today**, because §20.1 merges an actionless
 * element into the nearest action above it and the card body is that action. The sentence is
 * carried anyway rather than left blank, so a poster drawn somewhere with no such ancestor
 * cannot arrive silently claiming to be a photograph.
 */
export const CANDIDATE_POSTER_LABEL = 'A generated court poster, not a photograph';
