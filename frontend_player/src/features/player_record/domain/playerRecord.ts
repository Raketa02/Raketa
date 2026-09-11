/**
 * **Everything the platform will say about one person, to this reader** — the record sheet's
 * own shape, mapped once at the wire boundary and read by nothing else
 * ([#384](https://github.com/Raketa02/Raketa/issues/384)).
 *
 * ## A record is live, and a card is recorded
 *
 * A player card is a *recorded* answer frozen into an immutable search record, bounded to
 * twenty rows and closed by decision to facts about the searched sport. This is the other
 * thing: current at the moment of opening, every sport, and able to answer about **you** —
 * which no card route can, because no search ever returned the searcher. That is why the
 * shapes are separate types over separate routes rather than one widened card.
 *
 * ## Absence has one spelling, and it is the field's own
 *
 * Every optional here is *the platform has nothing to say*, and **never a nought**. A player
 * with no rating in any sport has no `skill` and an empty `sports`; one nothing has ever
 * fallen due for has no `reliability`; one nobody has rated has no `opinion`. **Each absence
 * asks a different question and they do not move together** — somebody rated in four sports may
 * never have had a game counted, and somebody with a full record of counted games may have been
 * rated by nobody, since rating is a favour and nothing anywhere records that a card was
 * ignored — so each is read where it is drawn and nothing is inferred from another.
 *
 * ## What is deliberately not here
 *
 * **No moment, at any granularity.** Not a timestamp, not *active today*, not a green dot.
 * `lastFive` carries outcomes in order and no dates, and a `lastPlayedAt` beside it would be
 * the same refusal one field further in.
 */

import type { GameResult } from '@/shared/vocabulary/gameResult';
import type { SocialTagId } from '@/shared/vocabulary/socialTags';
import type { Sport } from '@/shared/vocabulary/sport';

/**
 * **Whose record is being opened, and through which door.**
 *
 * Two routes and not one comparison: your own face reads `GET /players/me/record`, which is
 * ungated deliberately — *this is the one screen a held player has for finding out how they
 * appear* — and every other face reads the parameterised route, where admission is decided
 * against a prior disclosure the client cannot see.
 *
 * **The `kind` is the caller's own knowledge and never a derived one.** The court already
 * knows which seat is the searcher's; what it must not do is compare identifiers to find out.
 * Whether the sheet retitles is `PlayerRecord.isSelf` — **the server's answer** — and the two
 * are separate on purpose: this one picks a route, that one picks the words.
 *
 * `playerId` is carried on both arms because the header draws a **generated poster** for a
 * player with no photograph, and a poster is a fact about an id. The `/me` route never sends
 * one back.
 */
export type RecordSubject =
  | { readonly kind: 'me'; readonly playerId: string }
  | { readonly kind: 'player'; readonly playerId: string };

/**
 * **The six strands a reliability reading is built from**, read separately.
 *
 * Written down here rather than read off the contract because a copy table is keyed by it and
 * transport does not reach `components/` — the two are held equal by the compiler in
 * `mappers/wireVocabulary.ts`, which is where a code added, removed or renamed fails the build.
 *
 * **Three of them have no provider on this platform today** and never cross on this response.
 * They are in the union because the vocabulary is closed and shared with the Fit breakdown,
 * not because they are coming.
 */
export const RELIABILITY_STRANDS = [
  'SHOWS_UP',
  'ANSWERS_CHALLENGES',
  'ANSWERS_RESULTS',
  'KEEPS_PLANS',
  'SETTLES_UP',
  'SPORTSMANSHIP',
] as const;

export type ReliabilityStrand = (typeof RELIABILITY_STRANDS)[number];

/**
 * **One metered row: what fell due, what came of it, and the figure the platform acts on.**
 *
 * All three are carried and the third is not a convenience. `good` and `opportunities` are the
 * raw pair, because a perfect record over nine and one over forty are different claims and a
 * bar alone hides which; `pct` is the platform's own rounding of them, so that a client
 * dividing for itself is not the fourth place one record gets rounded.
 */
export interface StrandRow {
  readonly strand: ReliabilityStrand;
  /**
   * How many of those opportunities went the way the strand is named for.
   *
   * **A no is a good outcome on two of the three.** Turning somebody down inside your day *is*
   * answering them, and so is countering a score you believe is wrong: what both price is
   * silence, which is the whole of
   * [ADR-0160](../../../../../docs/adr/0160-a-results-strand-counts-answers-and-never-agreements.md).
   */
  readonly good: number;
  /**
   * How many times it fell due. **An opportunity and never a total** — a game still awaiting
   * its entry and a score still inside its window are in neither half, because publishing them
   * either way would state a conclusion the clock has not reached. Never nought: a row with
   * nothing behind it is not served at all.
   */
  readonly opportunities: number;
  /** The figure out of a hundred. **Served, never derived** — see the interface note. */
  readonly pct: number;
}

/**
 * **What the platform watched somebody do** — the pill, and the rows it is the mean of.
 *
 * One optional and not two, because it is **one absence**: nothing has ever fallen due for
 * them. A `playerScore` beside a separate list of rows would let a build draw a figure over an
 * empty card, which is the shape this response is served whole precisely to prevent. There is
 * always at least one row.
 */
export interface Reliability {
  /** Out of a hundred — the figure the matcher acts on, at the player's own published weights. */
  readonly playerScore: number;
  /** In the strand vocabulary's own order, and never re-sorted. Only the strands they have. */
  readonly strands: readonly StrandRow[];
}

/**
 * **How widely they spread their games — the raw pair, over their whole record.**
 *
 * Two counts and no percentage, deliberately: the card argues three rows above that a perfect
 * record over nine games and one over forty are different claims, so a bare share here would
 * break the rule the card had just made about itself. The share is one division and it is this
 * client's ([`recordCard`](./recordCard.ts)).
 *
 * **It is about every sport**, unlike the skill panel's run of five — a person who plays padel
 * with the same four faces and squash with twenty has one habit — and it is a **career
 * statistic rather than a window**, which is what makes the number mean *how widely do they
 * spread their games* rather than *how widely this season*.
 */
export interface OpponentVariety {
  /**
   * How many **different people** those games were against.
   *
   * A doubles partner is one of them: *a pair is anybody you were on a court with* is the rule
   * this platform already counts familiarity by.
   */
  readonly distinctOpponents: number;
  /**
   * How many **times they were on a court with somebody**, across their counted games.
   *
   * **A count of seats opposite and never of games**, which is the correction rather than a
   * preference: a doubles evening puts three people on the court, so a game-denominated pair
   * published `3 of 1` — a fraction whose numerator exceeds its denominator, drawable only by
   * clamping a share that had gone over a hundred. Counting encounters makes both halves the
   * same kind of thing, and `distinctOpponents` can never exceed it.
   *
   * **Not the skill panel's `countedGames`.** That one is what a Level rests on — confirmed
   * results, in one sport, that the rating folded. This counts people met, across every sport.
   */
  readonly timesOnCourt: number;
}

/**
 * **The three steps a subject may be told**, and there is no fourth for *nobody has said
 * anything* — that is the field's absence, on the rule every zone on this sheet takes.
 *
 * Written down here rather than read off the contract for the reason `RELIABILITY_STRANDS` is:
 * a copy table is keyed by it and transport does not reach `components/`. The two are held
 * equal by the compiler in `mappers/wireVocabulary.ts`.
 */
export const OPINION_BANDS = ['GOOD', 'MIXED', 'POOR'] as const;

export type OpinionBand = (typeof OPINION_BANDS)[number];

/**
 * **What other players said** — one arm or the other, and never both.
 *
 * A reader is answered with the average and the number of different people it rests on; the
 * **subject** is answered with a band and no count. The contract sends those as two fields and
 * says they never cross together; this is one value with two arms, so a build cannot draw the
 * figure over somebody's own record even if a response carried both.
 *
 * That is not tidiness. A published average beside a published count is a **subtraction**: an
 * average moving from 4,80 over ten to 4,73 over eleven names the new rating as a 4, and the
 * subject knows who they played — so every answer would be identifiable by the one person who
 * must never see it, and people stop answering honestly once that is true. Which arm a record
 * carries is decided at the wire boundary, from `is_self`.
 *
 * **Neither arm is a strand and neither enters the pill.** A star average is not a ratio out of
 * a hundred, the matcher never reads it, and it is drawn one block down under a heading naming
 * its own author — because the card above promises *counted by the system, not written by
 * people* and this is the one thing on the sheet people wrote.
 */
export type Opinion =
  | ({ readonly kind: 'figure' } & OpinionFigure)
  | {
      readonly kind: 'band';
      /** Deliberately too coarse to read anything into. Never a number, a bar or a trend. */
      readonly band: OpinionBand;
    };

/**
 * **The two numbers a reader is answered with, named** — because three layers pass them around.
 *
 * The mapper builds them, the block draws them and the spoken name reads them, and a shape
 * restated at each of those is the shape that eventually differs at one of them.
 */
export interface OpinionFigure {
  /** The mean of what they said, out of five, to one decimal. **Served, never derived.** */
  readonly average: number;
  /**
   * How many **different people** it rests on — always drawn beside the figure.
   *
   * People and not ratings: only somebody's most recent stars count, so a weekly partner is one
   * rater however many evenings they play. At most fifty, which is the window.
   */
  readonly raters: number;
}

/** One sport somebody holds a rating in, as the header's pill draws it. */
export interface RatedSport {
  readonly sport: Sport;
  readonly level: number;
}

/**
 * The skill card, **for the one sport the sheet is about** — which the server resolved and
 * states back.
 *
 * The sport asked for wins where they are rated in it; otherwise it is the one they have
 * played most. So `sport` is read here rather than assumed to be what was sent, and the panel
 * prints it.
 */
export interface SkillPanel {
  readonly sport: Sport;
  readonly level: number;
  /**
   * The band's published **name**, exactly as the wire spelled it.
   *
   * A key and never derived from the Level: a client mapping a number to a band would be a
   * second set of drawing constants, and the day the boundaries move the two disagree. It is
   * resolved to the bar's own `BandKey` where the bar is drawn, and a band this build cannot
   * name draws no highlighted segment rather than a guessed one.
   */
  readonly band: string;
  /** How sure the platform is, as a whole percentage. Meaningless without `countedGames`. */
  readonly confidence: number;
  /** What that certainty rests on. **`0` is a real answer** — a rating no game has tested. */
  readonly countedGames: number;
  readonly likelyRange: { readonly low: number; readonly high: number };
  /**
   * Their last counted results **in this sport**, oldest to newest.
   *
   * Fewer than five is a real answer and is never padded; an empty list is none. Absent
   * entirely where an outcome this build cannot read was in the run — its length is a claim,
   * so a run half read is a run that cannot be drawn.
   */
  readonly lastFive?: readonly GameResult[];
}

export interface PlayerRecord {
  /**
   * **The server's answer, never a comparison this client made.** It retitles the sheet and
   * drops the distance, and getting it wrong is most visible on the one screen it matters on.
   */
  readonly isSelf: boolean;
  /** The whole handle. Nothing may derive a familiar form from it. */
  readonly nickname: string;
  /** Absent where they have no photograph, and on a link that has expired — both draw the poster. */
  readonly photoUrl?: string;
  /**
   * Whether the photograph wears the **ON COURT** mark — folded here and nowhere else.
   *
   * A boolean rather than the verdict, because *checked and flagged* and *nobody looked* draw
   * **identically** (ADR-0138): a sheet holding the code could branch on it a second way, and
   * the second way is the one that tells a reader a stranger's photograph was doubted. Folding
   * it at the wire boundary makes that unrepresentable rather than merely undone.
   */
  readonly onCourt: boolean;
  /** Their coarse area, as a machine code. **An identifier and never a name.** */
  readonly areaCode: string;
  /** The tags they publish, in the vocabulary's own order. The overlap is not here. */
  readonly socialTags: readonly SocialTagId[];
  /** One per rated sport, **in the registry's own order** — never re-sorted. */
  readonly sports: readonly RatedSport[];
  /** Omitted where they hold no rating at all; the pills then speak alone. */
  readonly skill?: SkillPanel;
  /**
   * The pill and the metered rows under it.
   *
   * Omitted where nothing has ever fallen due for them, which is most people today, and is
   * never a nought: nobody has failed to turn up who was never due to.
   */
  readonly reliability?: Reliability;
  /**
   * The variety row, which is a **different absence** and does not move with the one above.
   *
   * Omitted where no counted game has ever been recorded for them — a habit nobody has been
   * observed having is not a narrow one — and a plan that dissolved is an opportunity above
   * without being a game anybody played.
   */
  readonly variety?: OpponentVariety;
  /**
   * What other players said, in whichever of the two registers the subject is owed.
   *
   * A **fourth absence**, asking a fourth question: omitted where nobody has rated them, which
   * is most people. Rating is a favour, ignoring the card costs nothing, and nothing anywhere
   * records that somebody did not answer — so a plan that dissolved and a seat that ran out are
   * opportunities above, and neither is an opinion anybody offered.
   */
  readonly opinion?: Opinion;
}
