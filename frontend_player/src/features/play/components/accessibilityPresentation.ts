/**
 * What each Play control announces —
 * [`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §20.
 *
 * [Part 13](../../../../docs/design-system.md#part-13--accessibility) is the **requirement**
 * — names on everything tappable, `accessibilityState` on selected chips, modal semantics on
 * the sheet, an announcement on every toast, *"never colour as the only signal."* §E6 is the
 * **inventory**, and it opens by recording what the prototype has: *"seven `aria-label`s in
 * the whole file, two of them in this feature."*
 *
 * Neither is the **sentences**. An accessible name is copy — it is localisable, it quotes
 * numbers that need §B16's formats, and it composes codes whose sentences already have a home
 * in this folder. So it lives here, through §1's mechanism and no other: **code → message,
 * never message → message**, and never a template inlined in a component.
 *
 * ## §20.1 — the rule that decides an element
 *
 * Part 13's two worked examples disagree on their face: the question navigator is *"one
 * element, one label — never one per segment"*, where the availability grid is twenty-one
 * elements with the column heads hidden.
 *
 * > **One accessibility element per action. Everything with no action of its own merges into
 * > the nearest action above it.**
 *
 * Actions are what a listener navigates *by*. The navigator has none, so it is one element; a
 * grid cell is an answer, so there are twenty-one. That is one rule rather than two
 * precedents, and it is why the fit pill is not its own element, why the balance bar is one,
 * and why the why-fit meter is nothing at all.
 *
 * **This file is the accessibility tree; `the-play-components.md` is the component tree**, and
 * they are independent — a card may be one element built from six components, or six elements
 * built from one.
 *
 * ## §20.2 — the role vocabulary is React Native's, not ARIA's
 *
 * `accessibilityState` offers only `{disabled, selected, checked, busy, expanded}` — **no
 * `pressed`**, which §E6 asks for three times. *Prefer the role that carries the state; where
 * no role carries it, the label carries it; never style alone.* A seat selected for a swap is
 * therefore `selected`, and no name here restates a state a role already announces: the swap
 * toggle is *Swap players* and not *Swap players, on*, and a grid cell names its slot and lets
 * `checked` say the rest.
 *
 * ## What is *not* here
 *
 * The tab bar (#227, shipped), the availability grid in edit mode
 * ([6.8](../../../../docs/design-system.md#68-the-availability-grid)), focus order, touch
 * targets, contrast and Dynamic Type — all cited by §20.13 and written elsewhere. The toast
 * region's own sentences belong to the screens that raise them; what this file names is
 * **which regions exist**.
 *
 * Three of §20's rulings are **not sentences and so are not here**, and each has its home:
 *
 * - *"Every screen title takes `accessibilityRole="header"`"* (§20.11) — `ScreenHeader`
 *   already carries it. §C records the page header as **not** a shell region, *"the title
 *   scrolls away"*, so the role is what makes it reachable again by heading navigation.
 * - **The collapse** (§20.11) — `useCollapsedPresentation()` in `@/shared/ui/overlay`. What
 *   collapses is named where it is drawn: the fill animation, the deck's stagger, and #228
 *   §9's minimum-display latch, which goes to zero.
 * - *"The searching region announces the **result** once and never a stage"* (§20.11) — a
 *   rule about **when** `poolRankingStatus` and `engineFillStatus` are handed to a live
 *   region, which is the screen's to obey. It is §3's *no fake stages* reaching a second
 *   surface, and the sentences it governs are `searchingPresentation.ts`'s.
 */

import { counted } from '@/shared/formatting/counted';
import { formatLevel } from '@/shared/formatting/ratingFormat';
import type { AvailabilityDiffState } from '@/shared/ui/AvailabilityGrid';
import type { Announcement } from '@/shared/ui/overlay';
import { cellLabel } from '@/shared/vocabulary/availabilityPresentation';
import { orOutOfDate } from '@/shared/vocabulary/outOfDate';
import type { WeekCell } from '@/shared/vocabulary/week';

import type { ForecastAssumption, UnfilledReason } from '../domain/vocabulary';

import { balanceLabel } from './balancePresentation';
import { unfilledSeatLine } from './courtPresentation';
import {
  levelRow,
  metaLine,
  type LevelRowFacts,
  type MetaLineFacts,
} from './playerCardPresentation';
import { forecastAssumption } from './searchPresentation';

/** The scale Fit is against, spelled out rather than assumed. See {@link fitSentence}. */
const FIT_DENOMINATOR = 100;

/**
 * `Fit 78 out of 100`, and **not** §E6's *"Match score 78 out of 99"*.
 *
 * Fit is `CONTEXT.md`'s term — *"how good the game would be, printed on the card as one
 * number out of a hundred"* — which is where the denominator comes from. *Match Fit* is the
 * **engine's** name, and a card must not borrow it. **§E6 rewritten, first of five.**
 *
 * The denominator is stated rather than left implicit for
 * [7.10](../../../../docs/design-system.md#710-the-fit-pill)'s reason: Part 17 records that
 * the deleted fit badge's threshold *"named a scale the deleted engine defined"*, so a number
 * on this platform says what it is out of.
 */
export function fitSentence(fit: number): string {
  return `Fit ${fit} out of ${FIT_DENOMINATOR}`;
}

/** Everything the card draws about its subject, as the card already holds it. */
export interface CandidateCardFacts {
  /** §15's `playerName()` — **the handle, whole.** A seat label may truncate; a name never. */
  readonly name: string;
  readonly fit: number;
  readonly level: LevelRowFacts;
  readonly meta: MetaLineFacts;
  /** The lines `selectReasons` returned, in the order the card draws them. */
  readonly reasons: readonly string[];
  /** What the card draws of `concerns[]` — one on a card, all of them in *Why 78?*. */
  readonly concerns: readonly string[];
}

/**
 * The card body's name — **spoken in a different order than it is drawn** (§20.3).
 *
 * Identifying facts lead, the argument follows. This is the one recorded divergence from
 * visual order in the feature, and it exists because §10 is titled *Why this person is on the
 * list*: dropping the reason lines to satisfy a word count would delete what the card is for.
 * §20.1's cap is on **what precedes an action**, not on the label — a listener who has heard
 * enough interrupts and acts.
 *
 * The card is **two elements**, and this is the first: the body, whose action is *Why 78?*
 * ([#231](https://github.com/Raketa02/Raketa/issues/231) repointed the long-press there when
 * K-7 ruled the record sheets out), and its primary button. **The fit pill is not a third**
 * — it merges, which is also how its ✦ comes to be unspoken: by the merge, rather than by a
 * rule of its own.
 *
 * **A concern needs no marker, seven times out of nine.** §7's sentences carry their own
 * polarity. The two tag terms do not, and §20.12 books that gap rather than inventing a word
 * for it here.
 */
export function candidateCardLabel(facts: CandidateCardFacts): string {
  return sentences([
    facts.name,
    fitSentence(facts.fit),
    levelRow(facts.level),
    metaLine(facts.meta),
    ...facts.reasons,
    ...facts.concerns,
  ]);
}

/**
 * What the card's primary button does — the two the feature has.
 *
 * A code and not a boolean, so the day a third surface grows a third action it gains a word
 * here or it does not compile.
 */
export const CANDIDATE_ACTIONS = ['ADD_TO_COURT', 'CHALLENGE'] as const;

export type CandidateAction = (typeof CANDIDATE_ACTIONS)[number];

/**
 * `Add Marek to the court` · `Challenge Marek`.
 *
 * The visible label is *Add* / *Let's play*, which announces **identically on twenty cards**.
 * Naming the subject is [6.9](../../../../docs/design-system.md#69-the-photo-tile-and-picker)'s
 * remove control, whose label *"names which photo it removes"*.
 */
export function candidateActionLabel(action: CandidateAction, name: string): string {
  return action === 'ADD_TO_COURT' ? `Add ${name} to the court` : `Challenge ${name}`;
}

/** The deck card's two buttons. It is §20.3's card with two actions instead of one. */
export interface DeckAnswerLabels {
  readonly pass: string;
  readonly accept: string;
}

/**
 * `Not today, Marek` · `Let's play, Marek`.
 *
 * The 🎾 is hidden, per §E6 — *"otherwise it announces as 'tennis ball let's play'"* — and,
 * like the ✦, it is hidden by never entering the sentence rather than by a rule about glyphs.
 *
 * **There is no gesture to announce.** [#231](https://github.com/Raketa02/Raketa/issues/231)
 * §3 decided UI Open decision #9 against a swipe, so the deck's contract is two named buttons
 * and a card that leaves: no drag threshold to describe, and no alternative to provide for a
 * reader who could not perform one.
 */
export function deckAnswerLabels(name: string): DeckAnswerLabels {
  return { pass: `Not today, ${name}`, accept: `Let's play, ${name}` };
}

/**
 * Where a seat is, in the only two terms a listener can use: **a side, and a role.**
 *
 * §E6 proposes *"Seat 3, Marek Z., level 2,92."* **An index is not a place.** A listener has
 * no picture of the court, and H-25 makes the number mean different things in different sports
 * — squash puts both players on the same half, so seat 3 is not where seat 3 was. **§E6
 * rewritten, second, third and fourth of five**: the seat, the clear badge and the empty seat
 * all lose their numbers.
 *
 * Three values and not four, because *their partner* is a role nobody on this screen is
 * seated relative to: a listener places the far half by its side alone.
 */
export const SEAT_PLACES = ['YOUR_SIDE', 'YOUR_PARTNER', 'THEIR_SIDE'] as const;

export type SeatPlace = (typeof SEAT_PLACES)[number];

/** The place as a seat label **opens** with it — capitalised, because it starts a sentence. */
const PLACE: Readonly<Record<SeatPlace, string>> = {
  YOUR_SIDE: 'Your side',
  YOUR_PARTNER: 'Your side, your partner',
  THEIR_SIDE: 'Their side',
};

/**
 * The **side** as a sentence names it mid-way — *"Remove Marek from your side"*.
 *
 * Two tables and not one lower-cased at the call site: the clear badge wants the side and
 * never the role, because *"from your side, your partner"* is a phrase nobody says. The name
 * is what disambiguates two seats on one side, exactly as 6.9's remove control names its
 * photo.
 */
const SIDE: Readonly<Record<SeatPlace, string>> = {
  YOUR_SIDE: 'your side',
  YOUR_PARTNER: 'your side',
  THEIR_SIDE: 'their side',
};

/**
 * Who is in a seat, as the court knows it.
 *
 * `empty` carries §11's per-seat obstacle where the engine gave one, and `null` where the seat
 * was simply never filled — the two spellings of absence, kept apart because a court that
 * *stated* a shortfall and one that has not been asked to fill a seat are different things.
 */
export type SeatOccupant =
  | { readonly kind: 'you' }
  | { readonly kind: 'player'; readonly name: string; readonly level: number }
  | { readonly kind: 'empty'; readonly unfilled: UnfilledReason | null };

/**
 * `Your side, you` · `Your side, your partner, Marek, level 2,92` · `Their side, Ana, level
 * 3,10` · `Their side, empty. Nobody left in range — everybody who fits is already seated`.
 *
 * A seat is a `button` in all four cases. Selected for a swap it takes
 * `accessibilityState={{ selected: true }}`, which §20.2 substitutes for the `pressed` React
 * Native does not ship — the state is never written into the name.
 *
 * **The 9,5pt seat label does not earn `allowFontScaling={false}`.** Part 13 permits that
 * escape only *"inside the level bar's drawn geometry"*, and §15 already ruled the court's
 * case the other way: *"a seat label may truncate visually; a sentence may not, and a spoken
 * name never does."* The visible label scales and truncates; this one is whole.
 *
 * The **holding ring** — the 430 ms press feedback — announces nothing. It exists to confirm
 * a finger is down, on a channel this listener is not using.
 */
export function seatLabel(place: SeatPlace, occupant: SeatOccupant): string {
  const where = PLACE[place];
  switch (occupant.kind) {
    case 'you':
      return `${where}, you`;
    case 'player':
      return `${where}, ${occupant.name}, level ${formatLevel(occupant.level)}`;
    case 'empty':
      return occupant.unfilled === null
        ? `${where}, empty`
        : `${where}, empty. ${unfilledSeatLine(occupant.unfilled)}`;
  }
}

/** `Remove Marek from your side` — the side, never the index, and never the role. */
export function clearSeatLabel(seat: { readonly name: string; readonly place: SeatPlace }): string {
  return `Remove ${seat.name} from ${SIDE[seat.place]}`;
}

/**
 * The court's summary element, which **precedes** the seats: `Padel, 3 of 4 seats filled.`
 *
 * Four seats announced against nothing are four seats a listener cannot place. The sport is
 * the served name, as `poolRankingStatus` takes it; the count routes through `counted()` for
 * §19's reason, which is that no string in this app hardcodes an `s`.
 */
export function courtSummaryLabel(court: {
  readonly sportName: string;
  readonly filled: number;
  readonly seats: number;
}): string {
  return `${court.sportName}, ${court.filled} of ${counted(court.seats, 'seat filled', 'seats filled')}.`;
}

/**
 * The swap toggle — a `switch`, named by what it does.
 *
 * `checked` carries the state, so the name does not: §20.2's *prefer the role that carries the
 * state*, which is 6.8's own argument about its column heads read on a control instead of a
 * grid.
 */
export const SWAP_TOGGLE_LABEL = 'Swap players';

/**
 * `SH.whyfit`'s accessible name — **not** its visible title (§20.6).
 *
 * The title draws `Why ✦ {score}`, and the ✦ must not be spoken. It is the one place in the
 * feature where the visible name and the spoken one differ, and it differs because a glyph is
 * doing work in the visible one.
 *
 * The sheet's other Part 13 obligations are already the overlay's:
 * `accessibilityViewIsModal`, hidden siblings, focus returned to the trigger. What §20.6 adds
 * is where focus lands on the way *in* — **the title, not the first action**, one rule for all
 * of them, because `SH.propose`'s first action is *send* and landing focus there by default
 * would make the worst outcome the cheapest to trigger.
 */
export function whyFitSheetLabel(fit: number): string {
  return `Why fit ${fit}`;
}

/**
 * One why-fit row: `{term label}. {figure}. {reason}` (§20.8).
 *
 * **The meter is decoration and the row's words carry it.** The row draws a label, a mono
 * `×{weight} → {value}`, *then* a meter — so the number is already text two words earlier, and
 * a bar visualising a printed number is 6.8's double announcement. **§E6 rewritten, fifth of
 * five**: its *"expose it as a progress indicator with its current, minimum and maximum
 * values"* would publish a precision the row already states in a shape the row already chose.
 * `SH.player`'s three meters are K-7's, so **`progressbar` appears nowhere in this contract.**
 *
 * `figure` is **the string the row draws**, not a second rendering of it. That is the whole
 * point: the meter is hidden precisely because this text is the number, and composing a
 * different wording here would put two spellings of one figure on one row.
 */
export function whyFitRowLabel(row: {
  readonly term: string;
  readonly figure: string;
  /** Absent where the term stood down — the clause is dropped, never announced empty. */
  readonly reason?: string;
}): string {
  return sentences([row.term, row.figure, ...(row.reason === undefined ? [] : [row.reason])], '');
}

/**
 * A cell of `SH.saveav`'s diff grid — `Monday evening` · `, newly added` · `, dropped`.
 *
 * **This is the first of §20's two colour-only findings.** Newly-on drew a volt ring and
 * newly-off dropped to 45% opacity, and the sheet's own body text said *"Green rings are new,
 * faded ones you dropped"* — Part 13's prohibition in the one place the copy **names the
 * colour as the mechanism**. 6.8's diff variant answered the drawing with three shapes; this
 * answers the announcement with three sentences.
 *
 * **`undefined` is hidden, never an empty name.** A slot that was off and stayed off has
 * nothing to tell a listener, and twenty-one of those between the ones that do is the double
 * announcement 6.8 hides its column heads to avoid. The cell is not interactive either way:
 * §20.7 records the diff grid as *"a different control with a third fact"*, and a role that
 * carried `checked` would offer a state a reader could try to change.
 *
 * `KEEP_THESE_TIMES`'s body — the copy that names the colour — is a rewrite booked on §12 by
 * §20.12, and is deliberately not invented here.
 */
export function availabilityDiffCellLabel(
  cell: WeekCell,
  state: AvailabilityDiffState,
): string | undefined {
  const suffix = DIFF_SUFFIX[state];
  return suffix === null ? undefined : `${cellLabel(cell)}${suffix}`;
}

/**
 * What each of the diff grid's four states adds to the slot's name.
 *
 * Keyed by the component's own union, so a fifth state cannot ship without words — and `null`
 * rather than an empty string, because *hidden* and *named with nothing after it* are the two
 * outcomes this table decides between.
 */
const DIFF_SUFFIX: Readonly<Record<AvailabilityDiffState, string | null>> = {
  on: '',
  added: ', newly added',
  dropped: ', dropped',
  off: null,
};

/**
 * The three live regions this feature has, and their politeness. **There is no fourth.**
 *
 * A `Record` keyed by the union rather than a list, so a region added here states what it is
 * worth in the same edit — and all three are polite, because
 * `announceForAccessibilityWithOptions` with `queue` is what Part 13's requirement means once
 * nineteen toasts fire from one tab (§20.10). The single interrupting message in the feature
 * is not a region: it is the send confirmation, and `shared/store/toast.store.ts` owns it.
 */
export const PLAY_LIVE_REGIONS: Readonly<Record<PlayLiveRegion, Announcement>> = {
  /** Part 13's requirement, with §20.10's amendment. Mounted once, at the overlay host. */
  toast: 'queued',
  /** §16's two sentences, with `players_in_range` from the response. */
  searching: 'queued',
  /** The only figure in the tab that changes while focus is elsewhere. */
  provisionalForecast: 'queued',
};

export type PlayLiveRegion = 'toast' | 'searching' | 'provisionalForecast';

/**
 * The third region's sentence — the one nobody had claimed.
 *
 * Moving a player across the net changes the forecast **while focus stays on the seat that
 * moved**, so the figure announces itself. It carries §17's caveat rather than a bare number,
 * which is ADR-0108's rule that the figure and its caveat are one thing — and §B9's word
 * rather than a bare percentage, which is the same Part 13 rule the pool header's figure is
 * fixed under.
 *
 * An assumption code this build has no words for takes §3's gap: the figure it heads is a
 * **total**, and a total with an unexplained assumption is exactly the reading ADR-0108 exists
 * to prevent.
 */
export function provisionalForecastAnnouncement(forecast: {
  readonly pct: number;
  /** `null` where the wire's open string is a code this build cannot read (§3). */
  readonly assumption: ForecastAssumption | null;
}): string {
  const caveat = forecast.assumption === null ? undefined : forecastAssumption(forecast.assumption);
  return `${balanceLabel(forecast.pct)}. ${orOutOfDate(caveat)}`;
}

/**
 * Join clauses into one spoken name, dropping the ones that have nothing in them.
 *
 * A merged label is a **list of sentences**, and the two failure modes it has are a doubled
 * separator where a clause was empty and a trailing one where the last clause was dropped.
 * Both are silent on screen and audible to the one person the label exists for, which is why
 * the join is a function rather than a template.
 */
function sentences(clauses: readonly string[], terminator = '.'): string {
  const spoken = clauses.filter((clause) => clause !== '');
  return spoken.length === 0 ? '' : `${spoken.join('. ')}${terminator}`;
}
