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
import {
  formatLevel,
  formatPercent,
  formatRange,
  formatSignedLevel,
} from '@/shared/formatting/ratingFormat';
import { slotName } from '@/shared/vocabulary/availabilityPresentation';
import { socialTagLabel, socialTagName } from '@/shared/vocabulary/socialTagPresentation';
import type { SocialTagId } from '@/shared/vocabulary/socialTags';
import type { WeekCell } from '@/shared/vocabulary/week';

import type { AtStake } from '../domain/candidate';
import type { SharedTag, SocialTagOverlap } from '../domain/socialTagOverlap';
import type { GameResult, InclusionReason } from '../domain/vocabulary';

import type { CandidateAction } from './accessibilityPresentation';
import { livenessLine } from './livenessPresentation';

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
  /**
   * Yours, for the one comparison this line is allowed to make — **absent on a search that
   * did not record one**.
   *
   * The envelope carries it as the search ran on it (`domain/candidate`), and the two
   * absences must not be conflated: an absent code is *the comparison cannot be made*, where
   * a code that differs is *they are not in your area*. Both draw the same line, and only one
   * of them is a claim.
   */
  readonly myAreaCode?: string;
}

export function metaLine(facts: MetaLineFacts): string {
  const distance = `${facts.km} km`;
  // `undefined === undefined` would be true, so the absence is tested rather than compared:
  // a card with no area of its own must not tell twenty strangers they are in it.
  if (facts.myAreaCode === undefined) return distance;
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
 * The spoken name is `candidateActionLabel`'s and names the subject, on
 * [6.9](../../../../docs/design-system.md#69-the-photo-tile-and-picker)'s rule that a control
 * acting on one of twenty identical rows says which one. A `Record` over the closed set, so a
 * third action arrives with its word or does not build.
 *
 * **The add names its destination, and the choice between three wordings is made here.** The
 * designs offer *Add to the court*, *Add to the four* and *Add — this is the match*, which
 * are three wordings of one action ([#309](https://github.com/Raketa02/Raketa/issues/309)).
 * *Add to the four* is **wrong on a squash court**, where `Court`'s own coordinates give two
 * seats — the same trap `courtEntryCard`'s copy already branches on — and *Add — this is the
 * match* is a **claim** the card is not making: what the card states is a Fit out of a
 * hundred and the sheet behind it explains that number, and a button asserting the answer
 * would be the one sentence on the surface with no evidence under it. The destination is true
 * at every seat count, in both modes, and it is the clause the spoken name already carries —
 * so the visible word and `Add {name} to the court` differ by the name alone, which is the
 * whole of what naming the subject was for.
 *
 * The word was `Add` while the button stood alone at the foot of the card. It stopped standing
 * alone when *Why 78?* joined it, and a bare verb beside a second control is the one place the
 * missing object is felt.
 */
export const CANDIDATE_ACTION_WORD: Readonly<Record<CandidateAction, string>> = {
  ADD_TO_COURT: 'Add to the court',
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

/**
 * **The Social tag row's words** — the chip, its *you too* marker, and the amber sentence.
 *
 * The row is `domain/socialTagOverlap`'s four answers; these are the four things they say
 * ([#311](https://github.com/Raketa02/Raketa/issues/311)). Nothing here decides which tags are
 * shared, and nothing here re-words a tag: `socialTagLabel` and `socialTagName` are the
 * promoted table's, and a second spelling of nineteen labels is what the promotion existed to
 * prevent ([`the-words.md`](../../../../docs/specs/matchmaking/the-words.md) §1).
 *
 * ## The chip is drawn with a glyph and a marker, and spoken as neither
 *
 * `socialTagLabel` carries the emoji because a wall of same-length chips is found by shape;
 * `socialTagName` is what a listener gets, because *"beer mug, stays for a drink"* is the app
 * reading its own layout aloud. The **marker** goes the other way and is the more interesting
 * half: `· you too` is drawn on the chip because the tint alone would be colour as the only
 * cue ([Part 13](../../../../docs/design-system.md#part-13--accessibility)), and it is *not*
 * repeated per tag in the spoken name — the label groups the shared ones under one clause
 * instead, because a listener hearing *you too* six times is being read a table.
 *
 * **A shared chip can truncate its marker at the largest text sizes.** `Tag` is
 * `numberOfLines={1}` by design ([6.4](../../../../docs/design-system.md#64-tag--the-status-pill)
 * — *a long state tag truncates rather than breaking the row*), and the longest label plus the
 * marker exceeds the card at roughly double the system size. The tint survives it and the
 * spoken name always carries the whole clause, so the fact is never lost; what is lost is the
 * second cue, for the reader who has asked for the largest type. Recorded rather than papered
 * over — fixing it means a wrapping tag, which is a change to the primitive and to 6.4.
 *
 * What a chip in the row is **drawn** with: the tag, and the marker where it is shared.
 */
export function socialTagChip(tag: SharedTag): string {
  const label = socialTagLabel(tag.id);
  return tag.shared ? `${label} · ${YOU_TOO_MARKER}` : label;
}

/** The two words, once. Re-worded here and nowhere else — the clause has its own phrasing. */
const YOU_TOO_MARKER = 'you too';

/**
 * The amber sentence, which **stands in the row's place** rather than beside it.
 *
 * The one claim this row makes, and the only state in which the candidate's own tags are not
 * drawn: six untinted chips under a line saying none of them matched would be the card
 * answering a question nobody asked twice over, and the ticket puts the sentence *in the row's
 * place* in as many words. The tags are still a fact about them alone — they are read in full
 * on the surface that draws tags as tags, and the card's job here is the comparison.
 */
export const NO_TAGS_IN_COMMON = 'No tags in common';

/**
 * What the row contributes to the card's **spoken** name — nought, one or two clauses.
 *
 * Grouped rather than marked per tag, for the reason above, and worded so each clause says
 * whose fact it is: *tags you share* is about the pair, *their other tags* and *their tags* are
 * about the candidate alone. That distinction is the whole of the row, so it is the one thing
 * the wording must not blur.
 *
 * The `shared` case can still produce **no** shared clause: this build may have matched a tag
 * the mapper narrowed out of `social_tags` while keeping another in `matched`. The clause is
 * omitted rather than emptied, and the amber sentence is never reached — which is
 * `socialTagOverlap`'s third spelling arriving here intact.
 */
export function socialTagClauses(row: SocialTagOverlap): readonly string[] {
  switch (row.kind) {
    case 'shared': {
      const shared = row.tags.filter((tag) => tag.shared);
      const rest = row.tags.filter((tag) => !tag.shared);
      return [
        ...(shared.length === 0 ? [] : [`Tags you share: ${tagNames(shared.map((t) => t.id))}`]),
        ...(rest.length === 0 ? [] : [`Their other tags: ${tagNames(rest.map((t) => t.id))}`]),
      ];
    }
    case 'unknown':
      return [`Their tags: ${tagNames(row.tags)}`];
    case 'none-in-common':
      return [NO_TAGS_IN_COMMON];
    case 'hidden':
      return [];
  }
}

/** The words alone. Prose does not carry glyphs — `socialTagPresentation`'s own split. */
function tagNames(tagIds: readonly SocialTagId[]): string {
  return tagIds.map(socialTagName).join(', ');
}

/**
 * **The three record blocks' words** — what the platform has watched this person do
 * ([#312](https://github.com/Raketa02/Raketa/issues/312)).
 *
 * Three names and two readings. The names are the product's own and are not re-worded here;
 * what this file writes is the pair of sentences a listener gets, because the run of form is
 * **five squares** and the count is a figure with no unit on it.
 *
 * ## *Player Score* is not a second rating, and the block must not read as one
 *
 * It is reliability — turning up, answering challenges, confirming results
 * ([ADR-0140](../../../../../docs/adr/0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md))
 * — and the card already prints a Level twice. So the figure keeps the block's own name in
 * front of it and states the scale behind it, exactly as `fitSentence` does and for
 * [7.10](../../../../docs/design-system.md#710-the-fit-pill)'s reason: *a number on this
 * platform says what it is out of*. Two out-of-a-hundred figures on one card is why the
 * denominator is spoken rather than assumed.
 *
 * ## The run of form is read as a count, never as a picture
 *
 * The squares are distinguished by **fill**, which is exactly the half of
 * [Part 13](../../../../docs/design-system.md#part-13--accessibility) a listener gets nothing
 * of. Announcing five elements would read the row as a table — *won, won, lost, won, won* — so
 * the whole row is one clause and it is a count: *3 of the last 5 won*.
 *
 * **And the denominator is the real one.** A run of three says *of the last 3*, because fewer
 * than five is a real answer and *the gap is the honest statement*: a clause that said *of the
 * last 5* over three squares would pad in words what the drawing refuses to pad in squares.
 */
export const PLAYER_SCORE_BLOCK = 'Player Score';
export const LAST_FIVE_BLOCK = 'Last 5';
export const COUNTED_BLOCK = 'Counted';

/** What a Player Score is out of, spelled rather than assumed. See the note above. */
const PLAYER_SCORE_DENOMINATOR = 100;

/** The three facts the record block states, each **omitted** where the platform watched none. */
export interface RecordBlockFacts {
  readonly playerScore?: number;
  readonly lastFive?: readonly GameResult[];
  readonly countedGames?: number;
}

/**
 * What the record block contributes to the card's **spoken** name — nought to three clauses.
 *
 * One clause per block that is drawn, in the order the blocks are drawn, because there is no
 * argument for a different one: the three are the same register and the row reads left to
 * right. A block that is hidden says nothing, which is the whole of *hidden, never blank* read
 * in the register a reader cannot see.
 */
export function recordClauses(record: RecordBlockFacts): readonly string[] {
  const { playerScore, lastFive, countedGames } = record;
  return [
    ...(playerScore === undefined
      ? []
      : [`${PLAYER_SCORE_BLOCK} ${playerScore} out of ${PLAYER_SCORE_DENOMINATOR}`]),
    ...(lastFive === undefined ? [] : [lastFiveReading(lastFive)]),
    ...(countedGames === undefined ? [] : [countedGamesReading(countedGames)]),
  ];
}

/** `3 of the last 5 won` — the squares as a count, against the run's own length. */
export function lastFiveReading(results: readonly GameResult[]): string {
  const won = results.filter((result) => result === 'WIN').length;
  return `${won} of the last ${results.length} won`;
}

/**
 * `29 counted games` — the figure with the noun it is a count of.
 *
 * Through the one pluralisation helper, so no sentence here hardcodes an `s`
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §4, §19), and *counted*
 * is in the noun rather than left to the block's name: a listener hears the clause on its own.
 */
export function countedGamesReading(count: number): string {
  return counted(count, 'counted game', 'counted games');
}

/**
 * **The stake boxes' words** — what a counted game would move, either way.
 *
 * `Win, counted` and `Lose, counted`, which are the designs' own two labels and are worth
 * keeping as written: the comma is doing the work. *Win* alone would read as a claim about
 * this game, and *If you win* is a sentence where the row has two boxes; what the label says
 * is **which of the two counted outcomes** the figure under it belongs to.
 *
 * **The figures are drawn as served and signed by `formatSignedLevel`.** Nothing here rounds,
 * rescales, negates or derives one from the other — `win_delta > 0 > loss_delta` is the
 * server's invariant and the minus on the loss is the number's own.
 *
 * **No tone.** The palette is not spent here: `mint` is *settled, safe, covered* and `red` is
 * *ended badly*, and neither is true of an outcome that has not happened
 * ([1.3](../../../../docs/design-system.md#13-semantic-colour-is-never-decorative) — semantic
 * colour is never decorative). The sign carries the direction and the label carries the word,
 * which is also [Part 13](../../../../docs/design-system.md#part-13--accessibility) satisfied
 * without a colour being asked to mean anything.
 */
export const WIN_STAKE_BLOCK = 'Win, counted';
export const LOSS_STAKE_BLOCK = 'Lose, counted';

/**
 * What the stake boxes contribute to the spoken name — **two clauses or none**.
 *
 * Never one. The pair is the fact: a listener told what a win is worth and not what a loss
 * costs has been read half of a symmetrical thing, and the contract sends the two together or
 * neither.
 */
export function stakeClauses(stake: AtStake): readonly string[] {
  return [
    `${WIN_STAKE_BLOCK} ${formatSignedLevel(stake.winDelta)}`,
    `${LOSS_STAKE_BLOCK} ${formatSignedLevel(stake.lossDelta)}`,
  ];
}

/**
 * The tag beside the handle — **at most one, and the strong fact wins**.
 *
 * The competitive card's identity row is a name with a tag beside it, which **reverses
 * [#231](https://github.com/Raketa02/Raketa/issues/231)'s open decision #14**
 * ([#309](https://github.com/Raketa02/Raketa/issues/309)). That decision turned the volt tag
 * into a sentence under the name because *"a full sentence does not go where a two-word tag
 * went"* — which was the right reading of the sentence it had been given, and the wrong
 * conclusion: the two-word form was always available, and it is `INTEREST_RECEIVED`'s.
 *
 * ## Two facts, two colours, and only one of them is drawn
 *
 * - **Best match** — coral, the app's one accent, on the row with the highest Fit. It is a
 *   statement about **where somebody sits in the list this player is reading**.
 * - **Wants to play you** — volt, on somebody the engine admitted because they had already
 *   said yes. It is a statement about **a decision somebody else made**, and that is why it
 *   **replaces** the coral one where both would fall on the same card rather than sitting
 *   beside it: the designs' *"because it's the stronger fact"*, and two tags on one handle is
 *   a row whose width depends on how lucky the reader got.
 *
 * **Neither is a new field.** The volt one is `inclusionReason === 'INTEREST_LIFT'` — the
 * admitting code, per [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md)
 * §10's *"the tag is bound to the admitting code"* — and its **words are its liveness twin's**,
 * reached through `livenessLine` rather than re-typed, because §10's claim is that the two
 * codes are *two facts with one tag*. The coral one is `bestMatch`, which this file does not
 * decide: **which row wears it is the ordering rule's**
 * ([#310](https://github.com/Raketa02/Raketa/issues/310)), and a card that worked it out for
 * itself would be a component reading a list it cannot see.
 *
 * **There is no third tag and no default.** Most people on a list are neither, and a tag
 * drawn for them would be a word meaning *nothing in particular* — which is
 * [1.2](../../../../docs/design-system.md#12-one-accent-used-sparingly) read on the one row
 * that repeats twenty times.
 */
export interface CandidateTag {
  readonly label: string;
  /** `hot` is the coral tag and `volt` is the fill — 6.4's own variant names. */
  readonly variant: 'hot' | 'volt';
}

export function candidateTag(facts: {
  /** A union of one, and it **admits**. Omitted where nothing lifted them. */
  readonly inclusionReason?: InclusionReason;
  /** The ordering rule's answer, never this card's. */
  readonly bestMatch: boolean;
}): CandidateTag | undefined {
  const admitted = facts.inclusionReason;
  if (admitted !== undefined) return { label: INCLUSION_TAG_WORD[admitted], variant: 'volt' };
  return facts.bestMatch ? { label: BEST_MATCH_WORD, variant: 'hot' } : undefined;
}

/**
 * The volt tag's words, **per admitting code**.
 *
 * A `Record` and not `if (inclusionReason !== undefined)`, for `CANDIDATE_ACTION_WORD`'s reason
 * one register over: `WireInclusionReason` is a union of one *today*, and a presence check
 * would silently label a second admitting code *Wants to play you* — a sentence about interest
 * put on a code that might admit somebody for something else entirely. Keyed by the union, a
 * second code arrives with its own two words or does not compile, which is the discipline every
 * other table in this folder already has.
 *
 * The value is `INTEREST_RECEIVED`'s line rather than a second copy of those four words: §10's
 * claim is that the two codes are **two facts with one tag**, and reaching the twin through
 * `livenessLine` is what keeps that one string when either is re-worded.
 */
const INCLUSION_TAG_WORD: Readonly<Record<InclusionReason, string>> = {
  INTEREST_LIFT: livenessLine('INTEREST_RECEIVED'),
};

/**
 * The coral tag's two words.
 *
 * *Best match* and not *Best fit*: [#310](https://github.com/Raketa02/Raketa/issues/310) makes
 * *Best fit* a **sort**, and a tag and a sort chip reading the same two words on one screen
 * would have a reader looking for the connection between them. `CONTEXT.md`'s Fit is the
 * number in the pill; this is the row that has the most of it.
 */
const BEST_MATCH_WORD = 'Best match';
