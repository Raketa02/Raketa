/**
 * The result conversation, for one viewer, at one instant.
 *
 * `ADR-0074`'s screen in this app's vocabulary, and `ADR-0060`'s before it. Four
 * things about it are decisions rather than transcription:
 *
 * - **It is not a card**, so it is not a `MatchCard`. The wire sends no fit badge,
 *   no emphasis flag and no card stamp, because all three are judgements the
 *   *composition* made about a card's place on Now and none of them means anything
 *   on a screen with one thing on it. What it shares with a card is the **spine**
 *   and the **situation half**, and those are Now's types, imported rather than
 *   restated — the same choice the departure screen made, for the same reason.
 * - **Nothing here is derived.** `ADR-0053` leaves the phone one derivation —
 *   subtracting a moment it was handed from the current time — and this feature
 *   reaches it through Now's `countdown`, so there is still exactly one. Every
 *   field below arrived on the wire, and the ones that read as words arrived as
 *   codes and were resolved in `mappers/`.
 * - **There is no rendering identifier.** `ADR-0060` is explicit that the route
 *   *"renders by situation, not by a screen identifier"*, so the five renderings
 *   are the ladder's four post-play names resolved for this viewer, plus the three
 *   booleans saying what she may do about them. A `phase` here would be a second
 *   vocabulary answering a question `ADR-0040` already answers once.
 * - **No version, and no level movement.** `ADR-0074` refused a client-held
 *   version outright — it would make the phone hold a rule about its own staleness
 *   — and `ADR-0049` refuses the other: no engine produces a level movement, and
 *   there is nowhere in this type for a number nothing computed.
 */

import type { Moment, NowUpdate, Place, ScoreLine, SituationCopy } from '@/features/now/types';
import type { Money } from '@/shared/lib/formatting';

import type { EndingCopy } from './presentation';

/**
 * What is on the table, and who has spoken. Four facts and no history.
 *
 * **Empty rather than absent when nothing has been entered** — an empty score and
 * a zero count on `needsResult`, so *not there* and *there and empty* cannot be
 * handled in one place and not the other.
 *
 * **No history.** A counter *replaces* what was on the table, and printing the
 * score it beat invites arguing with a number that is no longer live.
 */
export interface ResultBlock {
  /** Whether this score has settled — by an opponent's tap, or by silence. */
  readonly agreed: boolean;
  /**
   * How many **sides** have spoken, capped at two.
   *
   * Never how many taps there were: replacing her own side's live score is a
   * correction, and `ADR-0048` says in as many words that it is not one of the
   * attempts. It is the one number on this screen the words read, because what
   * silence does depends on it — one proposal stands, two count for nothing.
   */
  readonly proposals: number;
  /** The score, or absent when nothing is on the table. */
  readonly score: ScoreLine | undefined;
  /**
   * Which side put it there, as an index into `score.sides`.
   *
   * `0` is always *your side*, because the server has already put hers first — so
   * the phone subtracts nothing to know whose score it is reading. A **side and
   * never a player**: proposals are capped per side, and naming the teammate who
   * typed it would put a person into an argument the model holds between two
   * halves of a net.
   */
  readonly proposedBy: number | undefined;
}

/**
 * How full the match is, counted by money, and how many turned up.
 *
 * `turnedUp` is present once the match has been **played**, which is every
 * rendering of this screen but one — and it is sent rather than derived, because
 * *one less than the seats* stops being minus one the moment a doubles match loses
 * two people.
 */
export interface SeatCounts {
  readonly seats: number;
  readonly paid: number;
  readonly held: number;
  readonly turnedUp: number | undefined;
}

/** The screen: the spine, the situation, what is on the table, and two clocks. */
export interface Result {
  readonly matchId: string;
  readonly where: Place;
  /** Her seat's amount — her own share inside this match, not the court's total. */
  readonly price: Money;
  /** The situation's name as it arrived. Kept as a string and never branched on. */
  readonly situation: string;
  /** What the match is doing, or absent for a name this build has never heard of. */
  readonly status: SituationCopy | undefined;
  /**
   * How the conversation ended, on the two situations that end it, and absent on
   * the four that do not.
   *
   * `ADR-0060`'s *"the route renders by situation"*, and the only block on this
   * screen that is: everything else is composed from a boolean, a score or a clock.
   * A settled result and an unscored evening say opposite things, so neither can be
   * read off the other's absence.
   */
  readonly ending: EndingCopy | undefined;
  readonly result: ResultBlock;
  readonly counts: SeatCounts;
  /**
   * Whether she may put **her own side's** score up: the first entry, and
   * replacing her side's live proposal, which are one act at two moments.
   *
   * Which of the two a given tap would be is the rule the phone does not hold
   * (`ADR-0053`): there is one address, and the server decides what a score was.
   */
  readonly mayEnter: boolean;
  /** Whether she may agree with what is on the table. Opposing side only. */
  readonly mayAccept: boolean;
  /**
   * Whether she may put a **different** score up against it.
   *
   * False once her side has spoken, because from two proposals only an explicit
   * acceptance settles it. There is no bare rejection anywhere near it: a counter
   * carries a score, and the way that is made true is by there being nowhere to
   * say *no* (`ADR-0048`).
   */
  readonly mayCounter: boolean;
  /**
   * **The hero clock** — when this conversation ends by itself.
   *
   * The live proposal's own deadline once there is one, and the entry deadline
   * before that; absent once the answer is in, because a settled result and an
   * unscored evening count to nothing rather than to zero. `ADR-0060` makes it the
   * largest figure on the screen, *"next to the sentence that says nobody has to
   * do anything"*.
   */
  readonly settlementDeadline: Moment | undefined;
  /**
   * The second, quieter clock, present **only while it runs**.
   *
   * Inside it a counter beats a pending acceptance, so a screen that hid it would
   * say *settled* half an hour early — which is the outcome `ADR-0048` built the
   * grace to prevent, inverted.
   */
  readonly acceptanceGrace: Moment | undefined;
}

/**
 * What a tap on one of this screen's controls did.
 *
 * **A refusal is not a second shape** (`ADR-0070`). A side that has already
 * spoken, a result that settled while her screen was open, a deadline that ran
 * out, a leaver tapping through a stale screen — every one of them comes back as
 * what a success returns, so there is one code path and the player *sees* the
 * correction rather than being told it.
 *
 * There is no `applied` here and that is the difference from a departure. Leaving
 * is one irreversible act whose refusal is invisible without a flag; here the
 * screen she gets back **is** the answer — a score she can see on the table, or an
 * acceptance that has settled it — so a second field saying so would be a fact the
 * screen already states.
 */
export interface ResultAnswer {
  readonly screen: Result;
  /**
   * The one card on Now that changed, so the screen behind this one corrects
   * itself off the player's own tap rather than off a second request.
   *
   * It rides in the write's answer (`ADR-0074`) and is handed to Now unread: where
   * a card sits is Now's knowledge, and a result that decided it would be a second
   * opinion about the composition.
   */
  readonly update: NowUpdate;
}
