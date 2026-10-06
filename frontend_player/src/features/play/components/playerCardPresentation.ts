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
 * ## The meta line — **`{km} km`, or `In your area · {km} km`**, and nothing else — the
 * kilometres to one decimal, through the one formatter.
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
  formatDistanceKm,
  formatPercent,
  formatSignedLevel,
} from '@/shared/formatting/ratingFormat';
import { slotName } from '@/shared/vocabulary/availabilityPresentation';
import { NO_TAGS_IN_COMMON, socialTagName } from '@/shared/vocabulary/socialTagPresentation';
import type { SocialTagId } from '@/shared/vocabulary/socialTags';
import type { WeeklyHour } from '@/shared/vocabulary/week';

import type { AtStake } from '../domain/candidate';
import type { SocialTagOverlap } from '../domain/socialTagOverlap';
import type { GameResult, InclusionReason } from '../domain/vocabulary';

import type { CandidateAction } from './accessibilityPresentation';
import { livenessLine } from './livenessPresentation';

/** What the meta line states — a distance, and the one comparison it may draw beside it. */
export interface MetaLineFacts {
  /**
   * Kilometres **to one decimal**, as the contract sends them — the client rounds nothing.
   *
   * Measured between two **drawn spots**, one fixed point inside each player's coarse area,
   * and the same number the record's identity line and the why-fit sentence print for the
   * same person ([ADR-0174](../../../../../docs/adr/0174-the-radar-plots-the-reach-and-a-look-is-not-a-deal.md)
   * §2). Nothing prints a whole kilometre any more.
   */
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
  const distance = formatDistanceKm(facts.km);
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
 * zero spelled `0 hours` on the row and *No shared hours* in the sentence would make the
 * copy the row could reach the copy nobody ever reads.
 *
 * It is **a fact about arranging a game and not a refusal**: the availability term zeroes,
 * nobody is removed, and the times rung of the ladder exists for exactly this pairing.
 */
export const NO_SHARED_HOURS = 'No shared hours — one of you would have to bend';

/**
 * `3 hours · next Tue 19:00` — how much of your week is theirs, and the soonest of it.
 *
 * The count routes through the one pluralisation helper, so no string here hardcodes an `s`
 * (§4, §19), and the hour's name is the **promoted** weekday and hour tables rather than a
 * third list. The zero takes {@link NO_SHARED_HOURS} rather than `0 hours`, for the reason
 * written there.
 */
export function overlapRowValue(evidence: {
  readonly sharedCount: number;
  readonly nextSlot: WeeklyHour | null;
}): string {
  if (evidence.sharedCount === 0) return NO_SHARED_HOURS;

  const hours = counted(evidence.sharedCount, 'hour', 'hours');
  return evidence.nextSlot === null ? hours : `${hours} · next ${slotName(evidence.nextSlot)}`;
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
 * The deck's two answers, as words.
 *
 * They are the **stamps'** words now rather than two buttons' labels: the deck's buttons draw
 * marks — Feather's ✕, the drawn tennis ball (`DeckBall`, never spoken) — and the words appear
 * on the card under the thumb as the drag reveals them (ADR-0169 §3). `deckAnswerLabels`
 * composes the spoken names from the same two, so a stamp and the name a listener hears cannot
 * drift apart.
 */
export const DECK_ANSWER_WORDS = { pass: 'Not today', accept: "Let's play" } as const;

/**
 * What the row contributes to the card's **spoken** name — nought, one or two clauses.
 *
 * Grouped rather than marked per tag — `shared/vocabulary/socialTagPresentation`'s
 * `socialTagChip` is where that is argued — and
 * worded so each clause says
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
 * conclusion: the two-word form was always available, and it is `INTEREST_RECEIVED`'s. The
 * social card drew that sentence under its own head until
 * [ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §8 put the same two-word tag in its place — **both tags on both card styles**.
 *
 * ## Three facts, three colours, and only one of them is drawn
 *
 * - **Wants to play you** — volt, on somebody the engine admitted because they had already
 *   said yes. It is a statement about **a decision somebody else made**.
 * - **You said yes** — `base`, the plain status pill, on somebody in the reader's own outgoing
 *   list for the sport on screen. It is a statement about **a decision the reader made**, and
 *   it is deliberately not volt: volt is *they want you*
 *   ([6.4](../../../../docs/design-system.md#64-tag)), the green border travels with that word
 *   alone, and two facts in one colour would be a reader looking for the difference.
 * - **Best match** — coral, the app's one accent, on the row with the highest Fit. It is a
 *   statement about **where somebody sits in the list this player is reading**.
 *
 * **A fact about a person outranks a fact about a list**, which is why either interest tag
 * **replaces** the coral one where both would fall on the same card rather than sitting beside
 * it: the designs' *"because it's the stronger fact"*, and two tags on one handle is a row
 * whose width depends on how lucky the reader got. **Both interest facts true is a mutual**,
 * and a mutual is not on the list; should one ever be, *Wants to play you* wins — the other
 * person's decision is the one the reader did not already know.
 *
 * **None of the three is a new field.** The volt one is `inclusionReason === 'INTEREST_LIFT'`
 * — the admitting code, per [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md)
 * §10's *"the tag is bound to the admitting code"* — and its **words are its liveness twin's**,
 * reached through `livenessLine` rather than re-typed, because §10's claim is that the two
 * codes are *two facts with one tag*. The plain one is `saidYesTo` over the reader's own
 * `GET /interest` outgoing list (`domain/outgoingInterest`), no code and no nudge. The coral
 * one is `bestMatch`, which this file does not decide: **which row wears it is the ordering
 * rule's** ([#310](https://github.com/Raketa02/Raketa/issues/310)), and a card that worked it
 * out for itself would be a component reading a list it cannot see.
 *
 * **There is no fourth tag and no default.** Most people on a list are none of the three, and
 * a tag drawn for them would be a word meaning *nothing in particular* — which is
 * [1.2](../../../../docs/design-system.md#12-one-accent-used-sparingly) read on the one row
 * that repeats twenty times.
 */
/**
 * Which fact a tag is — so a caller binds a consequence to the **fact** and never to the colour.
 * The green border is `wants-to-play-you`'s, and a card reading `variant === 'volt'` would draw
 * it on whatever else was ever made volt.
 */
export type CandidateTagKind = 'wants-to-play-you' | 'you-said-yes' | 'best-match';

export interface CandidateTag {
  readonly kind: CandidateTagKind;
  readonly label: string;
  /** `hot` is the coral tag, `volt` the fill, `base` the plain pill — 6.4's own variant names. */
  readonly variant: 'hot' | 'volt' | 'base';
}

export function candidateTag(facts: {
  /** A union of one, and it **admits**. Omitted where nothing lifted them. */
  readonly inclusionReason?: InclusionReason;
  /** The reader's own list's answer — `saidYesTo` — never this card's. */
  readonly saidYes: boolean;
  /** The ordering rule's answer, never this card's. */
  readonly bestMatch: boolean;
}): CandidateTag | undefined {
  const kind = tagKind(facts);
  return kind === undefined ? undefined : { kind, ...CANDIDATE_TAG[kind] };
}

/** The precedence, and nothing else: the strong fact wins — see the note above. */
function tagKind(facts: {
  readonly inclusionReason?: InclusionReason;
  readonly saidYes: boolean;
  readonly bestMatch: boolean;
}): CandidateTagKind | undefined {
  if (facts.inclusionReason !== undefined) return 'wants-to-play-you';
  if (facts.saidYes) return 'you-said-yes';
  return facts.bestMatch ? 'best-match' : undefined;
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
 * The plain tag's three words — **the reader's own act, on the other person's card.**
 *
 * *You said yes* and not *You want to play them*: the deck's answer is *Let's play*, a yes, and
 * the tag names the act the reader remembers making. Exported for the suites that assert what
 * a row says, so a reworded tag is one red build rather than a string hunted through five
 * files.
 */
export const YOU_SAID_YES_WORD = 'You said yes';

/**
 * The coral tag's two words.
 *
 * *Best match* and not *Best fit*: [#310](https://github.com/Raketa02/Raketa/issues/310) makes
 * *Best fit* a **sort**, and a tag and a sort chip reading the same two words on one screen
 * would have a reader looking for the connection between them. `CONTEXT.md`'s Fit is the
 * number in the pill; this is the row that has the most of it.
 */
const BEST_MATCH_WORD = 'Best match';

/**
 * Each tag's words and colour, **keyed by the kind** — so a fourth kind does not compile
 * without both, and the colour is a function of the fact rather than a literal at a call site.
 */
const CANDIDATE_TAG: Readonly<Record<CandidateTagKind, Omit<CandidateTag, 'kind'>>> = {
  'wants-to-play-you': { label: INCLUSION_TAG_WORD.INTEREST_LIFT, variant: 'volt' },
  'you-said-yes': { label: YOU_SAID_YES_WORD, variant: 'base' },
  'best-match': { label: BEST_MATCH_WORD, variant: 'hot' },
};
