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
 * element, one label — never one per segment"*, where the availability grid is one element
 * per hour with the column heads hidden.
 *
 * > **One accessibility element per action. Everything with no action of its own merges into
 * > the nearest action above it.**
 *
 * Actions are what a listener navigates *by*. The navigator has none, so it is one element; a
 * grid cell is an answer, so there is one per hour. That is one rule rather than two
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
 * therefore `selected` and its name says nothing about being held, and a grid cell names its
 * slot and lets `checked` say the rest.
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
 *   collapses is named where it is drawn: the fill animation, the deck's stagger, and the
 *   stagger drawn over #228 §9's minimum-display floor. **The floor is not one of them** — a
 *   hold is not an animation, and `motion.hold` says so about itself (`searchingWait.ts`).
 * - *"The searching region announces the **result** once and never a stage"* (§20.11) — a
 *   rule about **when** `poolRankingStatus` and `engineFillStatus` are handed to a live
 *   region, which is the screen's to obey. It is §3's *no fake stages* reaching a second
 *   surface, and the sentences it governs are `searchingPresentation.ts`'s.
 */

import { levelRow, type LevelRowFacts } from '@/features/games/types';
import type { DeckAnswerLabels } from '@/features/proposals/types';
import { formatLevel } from '@/shared/formatting/ratingFormat';
import type { AvailabilityDiffState } from '@/shared/ui/AvailabilityGrid';
import type { Announcement } from '@/shared/ui/overlay';
import { cellLabel } from '@/shared/vocabulary/availabilityPresentation';
import { balanceLabel } from '@/shared/vocabulary/balancePresentation';
import { orOutOfDate } from '@/shared/vocabulary/outOfDate';
import type { SeatPlace } from '@/shared/vocabulary/seatPlace';
import {
  PLACE_CLAUSE,
  courtSummaryLabel,
  seatLabel as courtSeatLabel,
  type CourtSummary,
  type SeatOccupant as CourtSeatOccupant,
} from '@/shared/vocabulary/seatPlacePresentation';
import type { WeeklyHour } from '@/shared/vocabulary/week';

import type { Split } from '../domain/forecast';
import { courtHalfOf, type CourtHalf } from '../domain/lineup';
import type { ForecastAssumption, UnfilledReason } from '../domain/vocabulary';

import { GAP_WORD } from './builderPresentation';
import { WITHHELD_SEAT_LINE, unfilledSeatLine } from './courtPresentation';
import { DECK_ANSWER_WORDS, metaLine, type MetaLineFacts } from './playerCardPresentation';
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
 *
 * **Rounded, because the pill is.** Fit arrives with its decimals on and `FitPill` makes it a
 * whole number to draw it; a listener hearing *Fit 78,42131 out of 100* beside a reader seeing
 * `✦ 78` would be the two registers on two numbers, which is the one thing §20.3's *spoken in
 * a different order than it is drawn* does not license. `whyFitControlWord` rounds for the
 * same reason and always has.
 */
export function fitSentence(fit: number): string {
  return `Fit ${Math.round(fit)} out of ${FIT_DENOMINATOR}`;
}

/** Everything the card draws about its subject, as the card already holds it. */
export interface CandidateCardFacts {
  /** §15's `playerName()` — **the handle, whole.** A seat label may truncate; a name never. */
  readonly name: string;
  readonly fit: number;
  readonly level: LevelRowFacts;
  /**
   * `ON_COURT_CLAUSE`, on a card whose photograph passed the on-court check — and **nothing
   * at all** on the two answers that did not ([#313](https://github.com/Raketa02/Raketa/issues/313)).
   *
   * The panel announces nothing of its own — §20.1 merges an actionless element into the
   * nearest action above it, and the photograph inside it is hidden outright — so this is the
   * mark's one route to a listener, and it has to have one. **A mark is a fact**, and the rule
   * §20.1 is applying is *decoration merges*: a fact drawn on one card and not the next is
   * exactly what cannot be left to the pixels. `CANDIDATE_POSTER_LABEL` makes the same
   * argument one register up and stops short of this one — a poster's sentence is carried so
   * that it is never silently a photograph, and it goes unspoken inside a card because every
   * card already says whose face it stands in for. Nothing else says this.
   *
   * **Its absence carries no clause**, which is what keeps *flagged* and *never checked*
   * indistinguishable in the register where a difference would be easiest to leak: two
   * absences, one silence, and `wearsOnCourtMark` is the single place either is decided.
   */
  readonly onCourt?: string;
  /**
   * The forecast, **where the card draws it rather than saying it as a reason line**.
   *
   * §20.3's row is written against §B10's card and reaches every surface, so it does not name
   * this clause — but the rule above it does. §20.1 merges an actionless element into the
   * nearest action above it, and the balance bar has no action, so the bar's own name is not
   * an element on a card the way it is on a court. Its reading has to arrive somewhere or the
   * competitive card draws a figure a listener never hears while the term is filtered out of
   * the reasons for being drawn.
   *
   * Omitted on the two cards that say it as a sentence instead — one spelling per card,
   * which is the whole of §10.
   */
  readonly balance?: string;
  /**
   * **Omitted where the card does not draw a meta line**, which is two different absences.
   *
   * `distance_km` is omitted rather than sent as zero when the distance term stood down — the
   * two spellings of absence (ADR-0106 §4) — and the competitive card draws no distance row
   * at all, which is why `DISTANCE` is not in its drawn set and its reason line survives. A
   * label that stated the kilometres anyway would say them twice, once as a clause and once
   * as the reason: §10's rule broken in the one register nobody can see it in.
   */
  readonly meta?: MetaLineFacts;
  /**
   * What the **Social tag row** contributes, or nothing where the card draws no row.
   *
   * §20.3's row is written against §B10's card and names no tag clause, because no card drew
   * tags when it was written and `CandidateCardSocial` said so in writing. The competitive card
   * draws them now ([#311](https://github.com/Raketa02/Raketa/issues/311)), and the objection
   * that kept them off — *"content on the card that the label cannot announce"* — is answered
   * by this field rather than argued with: the content **can** be announced, so it is, and a
   * tag the label does not speak is a tag the card does not draw.
   *
   * `socialTagClauses`' nought, one or two sentences, given rather than composed here: the row
   * is the same value the chips are drawn from, which is what keeps §20.3's claim — that the
   * card is spoken in a different order than it is drawn — a statement about **one** card.
   */
  readonly socialTags?: readonly string[];
  /**
   * What the **three record blocks** contribute — nought to three clauses, or nothing at all
   * where the card draws no record ([#312](https://github.com/Raketa02/Raketa/issues/312)).
   *
   * They sit with the identifying facts, after the level and before the argument, because
   * that is the register they are in: what the platform has watched somebody do is a fact
   * about that person, where *why this person* is the reasons'. The same slot the Social tag
   * row took, and for the same reason — the tags follow because what somebody published about
   * themselves comes after what the platform recorded of them.
   *
   * **The run of form is one clause and not five.** `Last 5` is five squares distinguished by
   * fill, which a listener gets nothing of, and announcing them one by one would read the row
   * as a table. `lastFiveReading` counts them instead.
   */
  readonly record?: readonly string[];
  /**
   * What's at stake — **two clauses or none**, and never one.
   *
   * After the record and before the tags: it is the last fact about *this pairing* the card
   * states, and everything after it is either what the candidate published or the engine's
   * argument. Absent on a doubles seat and in for fun, both of which are decided before the
   * label is composed (`domain/atStake`), so there is no seat count in this file.
   */
  readonly stake?: readonly string[];
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
    // Straight after the level, because the two are the **panel's** pair: it prints a Level
    // hugely and a mark above it, and a listener meets that object before the argument over
    // it. It is also as early as the clause can go without displacing the two figures the
    // card is actually for.
    facts.onCourt ?? '',
    facts.balance ?? '',
    facts.meta === undefined ? '' : metaLine(facts.meta),
    // The record, then the stake, then the tags — the three blocks the card draws between the
    // band and the buttons, in the order it draws them. They are all identifying facts, so
    // §20.3's one divergence from visual order does not reach them: what it moves is the
    // argument, and none of these three is one.
    ...(facts.record ?? []),
    ...(facts.stake ?? []),
    // After the identifying facts and before the argument, which is where the row itself sits
    // in meaning rather than where it sits on the card: what somebody published about
    // themselves is the same register as their level, and *why this person* is the reasons'.
    // The amber sentence rides in the same slot — it is the row's own content and not a
    // concern, which is the engine's word for a graded claim it made.
    ...(facts.socialTags ?? []),
    ...facts.reasons,
    ...facts.concerns,
  ]);
}

/**
 * `Why Marek fits 78` — the card's **second** control, and the one whose visible word is the
 * same eight characters on twenty rows.
 *
 * The primary button's rule read on the button beside it:
 * [6.9](../../../../docs/design-system.md#69-the-photo-tile-and-picker) says a control acting
 * on one of twenty identical rows names which one, and *Why 78?* is more identical than *Add*
 * — two cards on one screen can carry the same Fit.
 *
 * **Not `whyFitSheetLabel` with a name pushed into it.** That string is the sheet's own name,
 * and a control and the surface it opens announcing identically is what §20.6 keeps apart on
 * the one sheet where the visible and spoken names already differ. This one is a **question
 * about somebody**; that one is the **answer's** name.
 *
 * The figure is rounded for `whyFitControlWord`'s reason — the button names the sheet it
 * opens, and the sheet's number is the column's.
 */
export function whyFitControlLabel(name: string, fit: number): string {
  return `Why ${name} fits ${Math.round(fit)}`;
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

/**
 * `Look out to 22 km, 9 to choose from` — a rung, with its price **in its own name**.
 *
 * ADR-0099 §5 puts the count on the button, and §20.1 reaches the same two elements from the
 * other side: the price has no action of its own, so it merges into the control it prices
 * rather than standing beside it as a second stop with no verb. The visible layout keeps them
 * apart — the count is a `.tiny` under the control — and the line beneath is hidden, exactly
 * as the court's own shortfall statements are.
 *
 * Both halves are given rather than composed here from a code, because they already have
 * homes: the label is `relaxationOffer`'s and the price is `rungCount`'s, and re-deriving
 * either would be a second spelling of a sentence this feature writes once.
 */
export function rungOfferLabel(offer: string, price: string): string {
  return `${offer}, ${price}`;
}

/**
 * The deck card's **spoken name** — the same rule as `candidateCardLabel`, read on a card that
 * makes no case.
 *
 * Identifying facts, in the order the card draws them, because there is no argument to move
 * behind them: the deck card draws no reason line and no concern (ADR-0169 §7 — the tiles, the
 * tags and the intro are the card), so §20.3's one divergence from visual order does not reach
 * it. The intro is spoken inside its quotation marks, so a listener hears it as the person's
 * own words rather than the card's; the tiles are spoken as clauses and a tile with no figure
 * says nothing (`deckTileClauses`).
 *
 * The card is **one element**, the body, whose action is the long press that opens the record;
 * the three buttons below the stage are three more, each named for the person
 * (`deckAnswerLabels`). The fit pill, the mark and the stamps are not elements: the first two
 * merge, and the stamps are hidden because they are feedback for a thumb.
 */
export interface DeckCardSpokenFacts {
  readonly name: string;
  readonly fit: number;
  readonly level: LevelRowFacts;
  /** `ON_COURT_CLAUSE`, or nothing — the drawing surface's one answer, spoken. */
  readonly onCourt?: string;
  /** The deck's meta line, already composed — with its third clause where the deal said so. */
  readonly meta?: string;
  /** The intro, already quoted, or nothing where they wrote none. */
  readonly intro?: string;
  readonly socialTags: readonly string[];
  readonly tiles: readonly string[];
}

export function deckCardLabel(facts: DeckCardSpokenFacts): string {
  return sentences([
    facts.name,
    fitSentence(facts.fit),
    levelRow(facts.level),
    facts.onCourt ?? '',
    facts.meta ?? '',
    facts.intro ?? '',
    ...facts.socialTags,
    ...facts.tiles,
  ]);
}

/**
 * A face or a card on the radar, spoken: `Filip N., 1,9 km, Padel 2,60` — the whole name, the
 * one-decimal distance, the reading's sport and their level in it
 * ([`the-words.md`](../../../../../docs/specs/matchmaking/the-words.md) §26).
 *
 * **One sentence for the three states.** A face at 24 pt, a face with its level under it and
 * the card are one person drawn at three widths, and a listener navigates by people rather
 * than by zoom: the name is what tells the elements apart, and the distance and the level are
 * what the card prints in full and the face abbreviates. Every face and card is a button — a
 * face flies to them, a card opens the record — and the sheet is the accessible path to acting
 * (§7.8): nothing on the field itself answers anybody.
 *
 * The level is `formatLevel`'s comma spelling, so the spoken figure is the drawn one; the
 * sport is the pane's own word for it (`sportLabel`), handed in rather than looked up, because
 * a label composed here from a code would be a second place the sport is named.
 */
export function radarTileLabel(facts: {
  readonly name: string;
  readonly distance: string;
  readonly sportName: string;
  readonly level: number;
}): string {
  return `${facts.name}, ${facts.distance}, ${facts.sportName} ${formatLevel(facts.level)}`;
}

/**
 * `Not today, Marek` · `Let's play, Marek`.
 *
 * The ball is hidden, per §E6 — *"otherwise it announces as 'tennis ball let's play'"* — and,
 * like the ✦, it is hidden by never entering the sentence rather than by a rule about glyphs:
 * it is a drawing with no words in it (`DeckBall`).
 *
 * **There is no gesture to announce.** [#231](https://github.com/Raketa02/Raketa/issues/231)
 * §3 decided UI Open decision #9 against a swipe, so the deck's contract is two named buttons
 * and a card that leaves: no drag threshold to describe, and no alternative to provide for a
 * reader who could not perform one.
 */
export function deckAnswerLabels(name: string): DeckAnswerLabels {
  return {
    pass: `${DECK_ANSWER_WORDS.pass}, ${name}`,
    accept: `${DECK_ANSWER_WORDS.accept}, ${name}`,
    record: `${name}’s record`,
  };
}

/**
 * The **side** as a sentence names it mid-way — *"Remove Marek from your side"*.
 *
 * Two tables and not one lower-cased at the call site: the clear badge wants the side and
 * never the role, because *"from your side, your partner"* is a phrase nobody says. The name
 * is what disambiguates two seats on one side, exactly as 6.9's remove control names its
 * photo.
 *
 * **Keyed by `CourtHalf`, and the fold is `courtHalfOf`'s.** This was a `Record<SeatPlace, …>`
 * writing *your side* twice, which is the three-onto-two collapse `domain/lineup.ts` owns,
 * spelled as a table instead of as a comparison — the same defect
 * [#300](https://github.com/Raketa02/Raketa/issues/300) took out of `handlesOn`, and one a
 * grep for the literal does not find. Two tables disagreeing about which half `YOUR_PARTNER`
 * is on is a sentence naming the wrong side of a court.
 *
 * **Exported, because a drawn sentence needs it too.** `awaitingBalanceLine` says *add somebody
 * to their side* on the pool header; that is the same half in the same register — mid-sentence
 * and lower case — and a literal there would be the second spelling this table exists to
 * prevent ([#297](https://github.com/Raketa02/Raketa/issues/297)).
 */
export const SIDE: Readonly<Record<CourtHalf, string>> = {
  yours: 'your side',
  theirs: 'their side',
};

/**
 * Who is in a seat, as the court knows it — the shared seat's three kinds, and the two only a
 * line-up being built can hold.
 *
 * `empty` carries §11's per-seat obstacle where the engine gave one, and `null` where the seat
 * was simply never filled — the two spellings of absence, kept apart because a court that
 * *stated* a shortfall and one that has not been asked to fill a seat are different things.
 */
export type SeatOccupant =
  | Exclude<CourtSeatOccupant, { readonly kind: 'empty' }>
  /**
   * A seat that still holds somebody the **record no longer describes** — the withheld mark
   * ([#271](https://github.com/Raketa02/Raketa/issues/271)).
   *
   * It is a fourth kind rather than a `player` with optional facts, because there is nothing
   * to read out: a withheld row carries **one field** and no card, so the name and the level
   * that a seat's spoken form is made of are both gone. What is left is the same shape the
   * empty seat already uses — a place, and a sentence — and it says the fact and never the
   * cause, exactly as `WITHHELD_SEAT_LINE` does everywhere else.
   */
  | { readonly kind: 'withheld' }
  | { readonly kind: 'empty'; readonly unfilled: UnfilledReason | null };

/**
 * `Your side, you` · `Your side, your partner, Marek, level 2,92` · `Their side, Ana, level
 * 3,10` · `Their side, empty. Nobody left in range — everybody who fits is already seated`.
 *
 * The seat's own sentence is `shared/vocabulary/seatPlacePresentation.ts`' — the group page's
 * court says it too (#574) — and this adds the two clauses only a line-up being built says: the
 * withheld mark, and the engine's obstacle after an empty seat.
 *
 * **The holding ring is struck rather than announced** (§20.4,
 * [#278](https://github.com/Raketa02/Raketa/issues/278)). The prototype's 430 ms ring fed two
 * sheets K-7 removed, and what replaces it is 6.6's *one channel per state*: the seat already
 * dims to `.7` on press-in, so a finger being down is confirmed and there is no second signal
 * for a name to carry. What a seat **does** hold now is a hold, and it announces nothing
 * either — a hold duplicates a route and never carries one, so what is announced is the
 * route: {@link seatedNameLabel} on the forecast card's own names row.
 */
export function seatLabel(place: SeatPlace, occupant: SeatOccupant): string {
  switch (occupant.kind) {
    case 'withheld':
      return `${PLACE_CLAUSE[place]}. ${WITHHELD_SEAT_LINE}`;
    case 'empty': {
      const empty = courtSeatLabel(place, { kind: 'empty' });
      return occupant.unfilled === null
        ? empty
        : `${empty}. ${unfilledSeatLine(occupant.unfilled)}`;
    }
    default:
      return courtSeatLabel(place, occupant);
  }
}

/**
 * `Remove Marek from your side` — the side, never the index, and never the role.
 *
 * **`name` is absent on a withheld seat**, where the record no longer holds the row the name
 * came off. The badge is still drawn, because the seat is still clearable and a control a
 * player needs most is not one to withdraw — so it names the place and the act, which is the
 * whole of what 6.9's rule asks for: a remove control says *which* thing it removes, and on a
 * court the place is what disambiguates two seats on one side.
 */
export function clearSeatLabel(seat: {
  readonly name?: string;
  readonly place: SeatPlace;
}): string {
  return `Remove ${seat.name ?? 'this player'} from ${SIDE[courtHalfOf(seat.place)]}`;
}

/**
 * A seated handle on the forecast card — `Your side, Marek, player record` (§20.4).
 *
 * **It names the record it opens, not the Fit.** A face is a picture of a *person*, and
 * somebody tapping one is asking who they are; the pairing's arithmetic moves behind a row
 * inside the record that says what it is
 * ([#384](https://github.com/Raketa02/Raketa/issues/384)). A button that promised *why fit 78*
 * and opened a photograph, a Level and a run of form would be the one kind of label that is
 * worse than none.
 *
 * It opens with the **same place clause a seat's own spoken name opens with** — *your side*,
 * *your side, your partner*, *their side* — and takes `PLACE_CLAUSE` rather than the heading the
 * row draws, for §1's reason: a formatter composes from a code, never from another surface's
 * message. The heading says *Your side* where the partner's own name says *Your side, your
 * partner*, which is §20.4's rule that the role disambiguates two seats on one half. That is
 * also what hides the two side headings — each name now names its own side, exactly as 7.12
 * hides the court's caption and side labels because each seat does.
 *
 * **Your own face carries the sheet's other title**, because it opens the other view: *how
 * others see you* is what that sheet is, and a listener who heard *player record* on their own
 * seat would reasonably expect a settings screen.
 *
 * Both clauses are spelled here rather than lower-cased from the sheet's own titles, on
 * `PLACE_CLAUSE` and `SIDE`'s precedent: **two tables and not one lower-cased at the call site**
 * — a transformation over a composed sentence is a rule that breaks on the first proper noun.
 */
const RECORD_CLAUSE = 'player record';
const OWN_RECORD_CLAUSE = 'how others see you';

export function seatedNameLabel(
  place: SeatPlace,
  seated: { readonly name: string; readonly self: boolean },
): string {
  return `${PLACE_CLAUSE[place]}, ${seated.name}, ${seated.self ? OWN_RECORD_CLAUSE : RECORD_CLAUSE}`;
}

/**
 * The forecast card's split row — `You + Piotr 2,82, Bartek + Inés 2,82, gap 0,00`.
 *
 * **One element and not six**, which is §20.1 applied to a row with no action in it: the three
 * numbers and the two side names are one claim — *what the percentage above is a percentage
 * of* — and six stops is a listener navigating a table that is drawn as a row.
 *
 * The two names are the same strings the row prints (`sideName`), because the row's whole job
 * is to say **whose** strength each figure is; and the figures take §B16's one level shape,
 * `gap` included, since all three are on the Skill scale. The gap is spoken **signed, as it was
 * served** — a reader sees which side is bigger from the two figures either side of it, and a
 * listener hearing them in sequence has the same evidence.
 *
 * The bar beneath this row announces nothing at all, and this is why: it would be the fourth
 * reading of one fact (§20.1's merge rule, 6.8's double announcement).
 *
 * It takes the **`Split` itself** rather than three loose numbers, so the three figures a
 * listener hears cannot be assembled in a different order from the three a reader sees. The
 * two names are the screen's, because who is standing where is a seating rather than a fact
 * about a split.
 */
export function splitRowLabel(sides: Readonly<Record<CourtHalf, string>>, split: Split): string {
  const yours = `${sides.yours} ${formatLevel(split.yourSide)}`;
  const theirs = `${sides.theirs} ${formatLevel(split.theirSide)}`;
  return `${yours}, ${theirs}, ${GAP_WORD} ${formatLevel(split.gap)}`;
}

/**
 * The pool header — **one element over a court, a count and a list of names**
 * ([#297](https://github.com/Raketa02/Raketa/issues/297)).
 *
 * §20.1's merge rule, applied to a block with no action anywhere in it: a listener navigating a
 * drawn court, then a seat count, then four names stops three times to assemble a single claim
 * — *this is the court you are filling, and this is who is on it*. So the `Court` inside is
 * hidden and its own summary is carried here instead, which is why this opens with
 * `courtSummaryLabel`'s sentence rather than a second wording of it.
 *
 * **This is the only place the handles are said at all.** The card draws them once, on the
 * balance bar's two segment labels, and that bar is hidden — so a listener who did not hear
 * them here would not hear them. They were also printed as a middot-joined line under the seat
 * count until the same four names appeared twice in one card; the commas are what a spoken
 * clause needs, which is the split `balanceReading` and `balanceLabel` already keep one file
 * over.
 *
 * **It takes the percentage rather than a composed reading**, on §20's *code → message, never
 * message → message*: handed a string, a caller could pass the drawn form and put a middot into
 * a spoken name. The word leads the figure inside `balanceLabel`, because a listener who hears
 * *84%* has heard the number the sighted player reads in the tint and nothing of what the tint
 * meant.
 *
 * @param court.pct absent until there is a reading to state — which is
 *   `theirSideSeated`'s answer, not a missing value.
 */
export function poolHeaderLabel(
  court: CourtSummary & {
    readonly names: readonly string[];
    readonly pct?: number;
  },
): string {
  const summary = courtSummaryLabel(court);
  const who = `${court.names.join(', ')}.`;
  return court.pct === undefined
    ? `${summary} ${who}`
    : `${summary} ${who} ${balanceLabel(court.pct)}.`;
}

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
 *
 * Rounded, with `whyFitTitle` and for its reason: the sheet is opened by a control that has
 * always named a whole number, and it must not announce a different one.
 */
export function whyFitSheetLabel(fit: number): string {
  return `Why fit ${Math.round(fit)}`;
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
 * A cell of the week Play searches on — `Thursday 19:00` · `Thursday 19:00, added for this
 * search`.
 *
 * 6.8's editor cell, whose name is `cellLabel`'s and stays it: **the suffix is a third fact and
 * not a state**, so `checked` still says what the *week* holds and this says what the *search*
 * did ([#283](https://github.com/Raketa02/Raketa/issues/283)). It is the one thing a listener
 * has instead of the plus, and without it a cell the player never ticked is announced exactly
 * like every hour around it.
 *
 * The suffix is the diff grid's *", newly added"* said the other way round, because it is a
 * different claim: that one is *your* week against your profile, this one is a cell the engine
 * added to one search.
 */
export function searchWeekCellLabel(cell: WeeklyHour, addedForThisSearch: boolean): string {
  return addedForThisSearch ? `${cellLabel(cell)}, added for this search` : cellLabel(cell);
}

/**
 * A cell of `SH.saveav`'s diff grid — `Monday 19:00` · `, newly added` · `, dropped`.
 *
 * **This is the first of §20's two colour-only findings.** Newly-on drew a volt ring and
 * newly-off dropped to 45% opacity, and the sheet's own body text said *"Green rings are new,
 * faded ones you dropped"* — Part 13's prohibition in the one place the copy **names the
 * colour as the mechanism**. 6.8's diff variant answered the drawing with three shapes; this
 * answers the announcement with three sentences.
 *
 * **`undefined` is hidden, never an empty name.** An hour that was off and stayed off has
 * nothing to tell a listener, and a hundred of those between the ones that do is the double
 * announcement 6.8 hides its column heads to avoid. The cell is not interactive either way:
 * §20.7 records the diff grid as *"a different control with a third fact"*, and a role that
 * carried `checked` would offer a state a reader could try to change.
 *
 * **`KEEP_THESE_TIMES`'s body is the third answer, and it is written** — §12, through
 * `promptPresentation` ([#277](https://github.com/Raketa02/Raketa/issues/277)). It names 6.8's
 * plus and dash, so the sentence a reader is given and the suffixes a listener is given
 * describe the same two marks rather than the scheme the drawing retired.
 */
export function availabilityDiffCellLabel(
  cell: WeeklyHour,
  state: AvailabilityDiffState,
): string | undefined {
  const suffix = DIFF_SUFFIX[state];
  return suffix === null ? undefined : `${cellLabel(cell)}${suffix}`;
}

/**
 * What each of the diff grid's four states adds to the hour's name.
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
  /**
   * The only figure in the tab that changes while focus is elsewhere — and **claimed once**,
   * by the builder, although two screens now draw it.
   *
   * The pool draws the same running figure and moves it by adding somebody, but the court is
   * still mounted underneath that route and `announce` is imperative: it fires from behind a
   * screen the platform has marked hidden, so the change is already spoken. A second claimant
   * would say one change twice ([#272](https://github.com/Raketa02/Raketa/issues/272)).
   */
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
  /**
   * Whether the figure assumes anybody — **the engine's boolean, never re-derived here.**
   *
   * It decides whether there is a caveat at all, which is what keeps `assumption: null`
   * unambiguous: on a provisional figure it is *a code this build cannot read* and takes §3's
   * gap, and on a settled one it is *nothing was assumed* and takes nothing. Collapsing the
   * two would announce **too old to read this one** over every complete court.
   */
  readonly provisional: boolean;
  /** `null` where the wire's open string is a code this build cannot read (§3). */
  readonly assumption: ForecastAssumption | null;
}): string {
  const reading = balanceLabel(forecast.pct);
  if (!forecast.provisional) return `${reading}.`;

  const caveat = forecast.assumption === null ? undefined : forecastAssumption(forecast.assumption);
  return `${reading}. ${orOutOfDate(caveat)}`;
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
