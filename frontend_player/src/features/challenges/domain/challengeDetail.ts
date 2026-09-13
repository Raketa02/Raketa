/**
 * One challenge **richly** — the arrangement, the people on it, and the fold the screen over it
 * is keyed on.
 *
 * `GET /challenges/{id}` is *the screen you answer on*: the list tells you what you have been
 * asked, and this tells you who is asking and what the platform makes of playing them
 * ([ADR-0143](../../../../../docs/adr/0143-the-challenge-is-the-gate-and-the-card-is-recomputed-for-the-reader.md)).
 * `domain/challenge.ts` beside it holds what a challenge **is** on the cheap list; what is here
 * is the richer read and the one question the screen could get wrong.
 *
 * ## The card block's lifetime is the arrangement's lifetime
 *
 * **The person block and the pairing block are drawn in `AWAITING_ANSWERS` and
 * `LINE_UP_INCOMPLETE`, and in no other standing** (ADR-0143 §8). That is **one rule stated on
 * the two that draw a card** rather than a list of exceptions, so a seventh standing added to
 * the contract is silent by default rather than inheriting a card block nobody decided it
 * should have.
 *
 * The wire already omits the cards outside those two, so this is the same rule read twice on
 * purpose: the fold decides what the screen draws, and a client that drew whatever arrived
 * would be trusting a response to enforce a rule this app is the one stating.
 *
 * **One level down, the same rule per seat.** Somebody who declined or lapsed inside a court
 * that is still open gets no card — *that person is a stranger to you once more the moment they
 * leave* — and neither does your own seat, because a pairing with yourself is not a question.
 * That half is the wire's alone: it omits `card`, and this file counts nobody.
 *
 * **And one level down again, per reader — this file's own** (#392,
 * [ADR-0143](../../../../../docs/adr/0143-the-challenge-is-the-gate-and-the-card-is-recomputed-for-the-reader.md)'s
 * 2026-09-10 amendment). A reader whose **own** seat has left is drawn no card block in either
 * live standing: the card is what a reader answers against, and the pair has released those
 * people. `hasLeft` is that question, and it is the one level the wire does **not** enforce —
 * the server still builds their court, which is [#394](https://github.com/Raketa02/Raketa/issues/394).
 *
 * ## The two answers are gated on the **seat**, never on the standing alone
 *
 * §2.1's table offers `I'm in · Not this time` to the `AWAITING_ANSWERS` invitee **who has not
 * answered**, and the side alone is not enough to key that on — the table is split per reading
 * for exactly this reason ([#389](https://github.com/Raketa02/Raketa/issues/389)). A padel four
 * where one invitee has already accepted is **still** `AWAITING_ANSWERS` — `standing_of` yields it
 * while *any* seat is awaiting — so that reader is an invitee in the standing that offers the
 * buttons, with an act that is already spent:
 * `POST /accept` answers `seat_already_answered`, which
 * [`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §2.4 files
 * under *the two-devices case*. **Neither button may name a state the act cannot produce**, so
 * the predicate is *the reader holds a seat and nobody has answered for it*.
 *
 * A reader who holds **no** seat falls out of the same predicate. The route 404s rather than
 * serving a stranger's challenge, so this is a state the wire does not produce; it is written
 * as a consequence of one rule rather than as a fourth arm, because an arm for it would be a
 * screen nobody can reach with a sentence nobody has read.
 *
 * **The sentence is `standingLine`'s and is not re-keyed here.** §13's seventeen sentences are
 * settled and [#331](https://github.com/Raketa02/Raketa/issues/331) ruled rewriting them out of
 * scope; what this fold adds is which *controls* exist, which is the question §13 never
 * answered.
 */

import type { NamedPlayer } from '@/shared/formatting/playerName';
import type { Sport } from '@/shared/vocabulary/sport';
import type { AtStake, Forecast, LikelyRange, ScoredTerm, Term } from '@/features/play/types';

import {
  ownSeat,
  seatName,
  standingFactsFor,
  type Challenge,
  type ChallengeSeat,
} from './challenge';
import { GIVES_UP_THE_SEAT, type SeatAnswer, type Standing, type StandingFacts } from './standing';

/**
 * Who one person on this court is — **a closed list with two permanent gaps.**
 *
 * No bio and no free text of any kind, and no activity recency at any granularity. The refusal
 * is **stronger here than where it was written**: a searcher chose to look, and an invitee was
 * put in front of somebody without asking (ADR-0143 §5).
 *
 * It is `challenges`' own spelling and deliberately narrower than a `PlayerCard` — no social
 * tags, no run of form, no counted games, no photo verdict — because `challenges` may not
 * import `matchmaking` and the alternative to two spellings is the matcher owning the
 * vocabulary of the context built to take it off him.
 */
export interface CourtPerson {
  /** The whole handle. Nothing derives a familiar form from it — ADR-0107. */
  readonly nickname: string;
  /**
   * The short-lived signed link that draws their photograph, **omitted with the id** when they
   * have none — and the client draws the generated poster instead.
   *
   * The id is not kept: it expires within minutes and is not a stored value, so the URL is the
   * only address this photograph has.
   */
  readonly photoUrl?: string;
  /** Their coarse area, as a machine code. **Never printed** — it is one half of a comparison. */
  readonly areaCode: string;
  readonly level: number;
  /** The band's **published name**. Its numeric edges are not here. */
  readonly band: string;
  readonly range: LikelyRange;
  /**
   * Their **published** Player Score, and never a re-derivation of one (ADR-0140).
   *
   * **Omitted where the platform has watched nothing**, which is most people today. The segment
   * disappears rather than reading `Score 0`, because a nought printed for somebody nothing was
   * watched of is a claim where there is a gap.
   */
  readonly playerScore?: number;
}

/**
 * What this platform makes of you **against** this person — recomputed when the screen is
 * opened, in your own direction.
 *
 * Nothing is copied at send and nothing is replayed from the organiser's search, which is the
 * only shape under which *for you* is true (ADR-0143 §3).
 */
export interface CourtPairing {
  /** Out of a hundred, and drawn as served. Nothing on this side rounds or rescales it. */
  readonly fit: number;
  /** Whole kilometres, **omitted rather than zero** when the distance term stood down. */
  readonly distanceKm?: number;
  /** Every term that fired, **ranked by contribution**. Nothing on this side sorts. */
  readonly terms: readonly ScoredTerm[];
  /**
   * Every term that stood down, and whose gap each one was — **the Fit's renormalisation
   * basis**, without which the number above cannot be read.
   *
   * It ships even though no *Why?* sheet is drawn over it, because printing a Fit without its
   * basis is the exact failure the field exists to prevent (ADR-0143 §5).
   */
  readonly degradedTerms: readonly DegradedTerm[];
  /** The terms the engine is not comfortable about on this pairing, ranked. */
  readonly concerns: readonly Term[];
  /**
   * What the court **as it stands** would leave on court, read in your direction.
   *
   * **Omitted where no game can be arranged out of what is left** — a side with nobody on it is
   * not a side, and an invented number would be worse than the absence.
   */
  readonly forecast?: Forecast;
  /**
   * What a **counted** game against this person would do to your Level.
   *
   * **Omitted in for fun** and omitted where either of you holds no rating in this sport. Present
   * is not the same as drawn: `stakeOnACard` refuses a doubles court, because a win against one
   * named person is not a thing that exists until the other three seats are known.
   */
  readonly atStake?: AtStake;
}

/**
 * A term the engine **did not count**, and whose gap that was — `challenges`' own spelling of
 * the pair, for `CourtPerson`'s reason.
 *
 * The two halves are one sentence, so neither travels alone.
 */
export interface DegradedTerm {
  /** `null` where the served term is a code this build has no name for — §3's gap in place. */
  readonly term: Term | null;
  /** `null` where the served reason is one this build has never seen. */
  readonly reason: DegradedReason | null;
}

/** Whose gap a stood-down term was. Spelled here for {@link DegradedTerm}'s reason. */
export type DegradedReason = 'NOT_YET_ON_THIS_PLATFORM' | 'NOTHING_FROM_YOU' | 'NOTHING_FROM_THEM';

/** The card for one seat: who they are, and what you make of them. */
export interface SeatCard {
  readonly person: CourtPerson;
  readonly pairing: CourtPairing;
}

/**
 * One seat on the detail read — the list's seat, and a card where one is drawn.
 *
 * `card` is absent on your own seat, on an empty one, on a seat that declined or lapsed, and on
 * every seat when the pairing could not be computed at all.
 */
export interface DetailSeat extends ChallengeSeat {
  readonly card?: SeatCard;
}

/**
 * Why no seat carries a card — **two codes, and a third answer that is their absence.**
 *
 * `NOTHING_TO_COMPUTE` is *you hold no rating, no declared intent or no committed profile in the
 * sport you were challenged in*, which is **how this feature works rather than a corner of it**:
 * being asked to play a sport you never declared for draws the arrangement and the handle, and
 * the screen does not apologise for it. `COULD_NOT_BE_READ` is somebody else's outage.
 *
 * **Three answers and not two**, because an outage drawing the identical absence as an unrated
 * sport is indistinguishable from four erased accounts (ADR-0143 §6). **Answering is never gated
 * on any of it** — the arrangement always answers, and the buttons are drawn from the standing.
 */
export const PAIRING_ABSENCES = ['NOTHING_TO_COMPUTE', 'COULD_NOT_BE_READ'] as const;

export type PairingAbsence = (typeof PAIRING_ABSENCES)[number];

/**
 * One challenge as the screen that answers it reads one.
 *
 * `readAt` is **its own**, because this response is its own fold against its own instant: the
 * standing, every seat's deadline and which seats are still in were all read against this one
 * moment. Every duration the screen states is measured from it and never from this phone's
 * clock — *draw the clock, never obey it.*
 */
export interface ChallengeDetail {
  readonly challengeId: string;
  readonly organiserId: string;
  /** Absent when the contract sent a code this build has no words for. */
  readonly standing?: Standing;
  readonly sport: Sport;
  readonly openedAt: string;
  /** The instant this whole answer was folded against. */
  readonly readAt: string;
  /** The court in its fixed order — every **A** seat, then every **B**. Empty seats included. */
  readonly seats: readonly DetailSeat[];
  /** Absent when there is no absence to report — see {@link PAIRING_ABSENCES}. */
  readonly pairingAbsence?: PairingAbsence;
}

/**
 * What this screen is, for this reader — **the state it is keyed on.**
 *
 * Five arms over six standings and two sides, because what the screen branches on is not the
 * standing: it is *is there a sentence*, *is there a card block*, and *is there anything to
 * press*. The sentence rides on the arm as `StandingFacts` so that the one fold answers all
 * three and a component cannot arrive at a different reading of the same challenge.
 *
 * That is also how §2.4's *"an affordance is never removed without the space saying what took
 * it"* is discharged **by construction**: the controls and the sentence come out of one fold, so
 * there is no state in which the buttons are gone and the standing has not changed.
 */
export type ChallengeArm =
  /**
   * A standing this build has no word for. It draws §3's named gap and offers nothing: acting
   * on a challenge whose standing we cannot name is how an answer lands on a state nobody drew.
   */
  | { readonly kind: 'unreadable' }
  /**
   * **Yours to answer** — the card block, and the two answers.
   *
   * `answerBy` is the reader's own seat's deadline, **stated and never counted down**: absent on
   * a challenge born of a mutual yes, which carries no window at all.
   */
  | { readonly kind: 'answer'; readonly facts: StandingFacts; readonly answerBy?: string }
  /**
   * **Still being arranged, and there is one thing here you might press** — the card block, the
   * standing sentence over it, and the way out.
   *
   * The organiser waiting on answers, and an invitee who has **accepted** and is still in it —
   * an invitee who has *left* is drawn the sentence alone instead (#392). A court
   * that is still **filling** left this arm with [#362](https://github.com/Raketa02/Raketa/issues/362):
   * it draws the same card block and the same sentence and three controls besides, which is a
   * different reading of the fold and therefore a different arm.
   *
   * `mayLeave` is [ADR-0165](../../../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
   * §1's — see {@link onACourtWithSomebody}.
   */
  | { readonly kind: 'arranging'; readonly facts: StandingFacts; readonly mayLeave: boolean }
  /**
   * **A half-built court, and the three things a live member does about one** — grow · talk ·
   * end, in that order ([ADR-0150](../../../../../docs/adr/0150-the-fill-names-the-challenge-it-completes-and-the-gate-steps-aside.md)).
   *
   * *"`LINE_UP_INCOMPLETE` is not a waiting room"*: the people who are in are in, and a
   * conversation between them is already open. **Any live member may complete the line-up and
   * only the organiser may end it**, because growing a court and ending one are different acts —
   * and a mutual-born pair decides that on its own, since making an arbitrary tiebreak the only
   * person who can finish a padel four would leave the other looking at a court they can neither
   * complete nor leave.
   *
   * The reader who has **left** such a court is not here: they are `stated`, on §13.1's own
   * sentences. The row that explains it must stay because a departed seat is still a seat — **not
   * because the pair rule still binds them**, which it does not
   * ([#393](https://github.com/Raketa02/Raketa/issues/393)).
   */
  | {
      readonly kind: 'filling';
      readonly facts: StandingFacts;
      /** Whether the withdraw is drawn. The organiser's, and nobody else's (ADR-0142). */
      readonly mayEnd: boolean;
      /** Whether *Leave the game* is drawn — {@link onACourtWithSomebody}. */
      readonly mayLeave: boolean;
    }
  /**
   * **The sentence alone** — every ending, `ON`, and the reader who has left a court that has
   * not, **in either live standing** (#392).
   *
   * `ON` is here because #324 gave the **card** to the game's own standing the moment a game
   * exists — not because nothing reaches it. A completed line-up keeps its row while it is news
   * ([`challengeInbox.ts`](./challengeInbox.ts)), and every row is a door, so this is the arm that
   * row opens. The row draws §13's `ON` sentence as well; what draws it nowhere is a system line,
   * which §3.4 refused, so the row is what makes this arm reachable (§2.1, #390).
   */
  | { readonly kind: 'stated'; readonly facts: StandingFacts };

/**
 * **Has this reader left a challenge that has not?** — asked of the reader's own seat, and the
 * one question both live standings ask before drawing a card block (#392).
 *
 * An **accepted** seat has not left: they are still on the court and the pair still holds them,
 * which is why they keep their cards in both standings. `undefined` is the reader holding **no
 * seat** — not an empty seat, which *is* a seat and keeps its place — and the route 404s that
 * rather than serving a stranger's challenge.
 *
 * It reads the answer **the wire sent**, so a seat past its window whose lapse has not been
 * swept is not *left* here yet and keeps the answering arm. That is deliberate: deriving the
 * lapse would mean this side reading the clock, which `challenge.ts` refuses in writing, and
 * §2.4 already rules the expired offer acceptable — *the offer may expire under the finger and
 * is let to*.
 *
 * **The vocabulary's own table, `GIVES_UP_THE_SEAT`, read under this file's name for it** —
 * one `Record` keyed by the union for the two readers that ask, so a fifth `SeatAnswer` fails
 * `pnpm typecheck` once rather than quietly counting as *not left* here and *in* one file over,
 * which is the exact class of miss this rule was written to close.
 */
const LEFT: Readonly<Record<SeatAnswer, boolean>> = GIVES_UP_THE_SEAT;

function hasLeft(seat: ChallengeSeat | undefined): boolean {
  return seat?.answer === undefined ? false : LEFT[seat.answer];
}

export function challengeArm(detail: ChallengeDetail, playerId: string): ChallengeArm {
  // `ChallengeDetail` is a `Challenge` with cards on its seats, so every rule already written
  // over the cheap list — the side, the counts, who a sentence names — reads it unchanged.
  // Spelling those a second time over the richer shape is how a row and the screen behind it
  // start disagreeing about one challenge.
  const facts = standingFactsFor(detail, playerId);
  if (facts === undefined) return { kind: 'unreadable' };

  const seat = ownSeat(detail, playerId);

  // The seat and not the side: an invitee who has already accepted is still in this standing,
  // and their act is spent. See the module note.
  if (facts.standing === 'AWAITING_ANSWERS' && seat !== undefined && seat.answer === undefined) {
    return {
      kind: 'answer',
      facts,
      ...(seat.answerBy === undefined ? {} : { answerBy: seat.answerBy }),
    };
  }

  // #392: a reader with no answer left to give is drawn no card, and this standing holds while
  // *anybody* is awaiting — so it reaches the same question `LINE_UP_INCOMPLETE` asks below.
  if (facts.standing === 'AWAITING_ANSWERS') {
    if (hasLeft(seat)) return { kind: 'stated', facts };
    return { kind: 'arranging', facts, mayLeave: onACourtWithSomebody(detail, playerId) };
  }

  // The one reading §2.5 had to close: a court still filling draws a card block, three controls
  // and the sentence for the people still in it, and the sentence alone for the reader who left.
  if (facts.standing === 'LINE_UP_INCOMPLETE') {
    if (hasLeft(seat)) {
      return { kind: 'stated', facts };
    }
    return {
      kind: 'filling',
      facts,
      mayEnd: facts.side === 'organiser',
      mayLeave: onACourtWithSomebody(detail, playerId),
    };
  }

  return { kind: 'stated', facts };
}

/**
 * **Whether *Leave the game* is drawn** — the reader is on a court that is not whole, and so is
 * somebody else ([ADR-0165](../../../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
 * §1, [#427](https://github.com/Raketa02/Raketa/issues/427)).
 *
 * Asked only on the two live arms, whose reader holds an accepted seat by construction — the
 * organiser's from birth, an invitee's by their yes — so what is left to ask is the second half:
 * **is anybody on this court with them?** A yes taken back opens a seat the others can fill, and
 * that is the whole of what the act means; a court of one has nobody to keep the seat open for. The
 * organiser alone, with every invitee still deciding or already out, is on no court with anybody,
 * and their way out there is *Remove the challenge* (ADR-0165 §4, #428) — drawing *Leave the game*
 * beside it would be two doors out of an empty room.
 *
 * The organiser is a **player** in this rule and not a role: once somebody has joined, they leave
 * like anybody else, and `mayEnd` one arm over stays the withdraw's own question.
 *
 * It says nothing about whether the court has been a game. On a court that has, the same act is
 * the game screen's *Leave this game* and this control posts the same route; the moment guard the
 * server keeps there is answered by the words on the sheet rather than by hiding a control this
 * read cannot see the moment for.
 */
function onACourtWithSomebody(detail: ChallengeDetail, playerId: string): boolean {
  return detail.seats.some(
    (seat) =>
      seat.playerId !== undefined && seat.playerId !== playerId && seat.answer === 'ACCEPTED',
  );
}

/**
 * **Who on this court has already said yes** — the seats a fill may never take out, and the ones
 * that are not controls on the builder it pushes (ADR-0150 §8).
 *
 * Read here rather than off the fill's own answer, because the answer cannot say it: the people
 * who accepted *"come back as ordinary candidate rows"*, and an ordinary row says nothing about
 * a challenge. It is a fact about the court, and this is the read that holds the court.
 *
 * **In seat order and without the reader**, which is the order and the membership the request
 * wants: your own seat is the thing the court is composed around rather than something anybody
 * is completing, and it is `courtWithYou`'s to put back at the send.
 */
/**
 * **Whether the reader is somebody the room this challenge opened would hold** — read off the
 * arm, so the door and the sentence are two readings of one fold.
 *
 * The room's membership is the challenge's accepted seats until the line-up completes and the
 * game's frozen line-up after (ADR-0146 §7), and a room opens on the first acceptance. So the
 * reader is in it on the two arms reached only by somebody being in — an accepted seat or the
 * organiser waiting on answers, a live member of a half-built court — and on a court that is
 * **on**; and not on the `answer` arm, where they have not said yes, nor on any other `stated`
 * arm, every one of which is a reader who left or an episode that ended.
 *
 * It is asked beside the join and not instead of it. The join is what says a room *exists*
 * (ADR-0149 §3), and a list can be a beat behind the reply that took the reader out of one —
 * a decline or a withdraw invalidates the list rather than patching it — so for that beat the
 * list still holds a room the reader may no longer read. This is the reading that closes it:
 * a door is drawn only where both say so.
 */
export function readerIsInTheRoom(arm: ChallengeArm): boolean {
  switch (arm.kind) {
    case 'arranging':
    case 'filling':
      return true;
    case 'stated':
      return arm.facts.standing === 'ON';
    case 'answer':
    case 'unreadable':
      return false;
  }
}

export function acceptedPlayers(detail: ChallengeDetail, playerId: string): readonly string[] {
  return detail.seats.flatMap((seat) =>
    seat.playerId === undefined || seat.playerId === playerId || seat.answer !== 'ACCEPTED'
      ? []
      : [seat.playerId],
  );
}

/**
 * The seats the organiser is waiting on, each with the deadline that is **its own**.
 *
 * §14's second sentence names a person and a duration and is drawn once per seat, because the
 * window is per seat and nothing about it is a property of the challenge: a seat invited later
 * starts its own day and cannot inherit a deadline from a send it was not part of.
 *
 * An empty seat is not in the list because nobody was asked, and neither is a seat that has
 * answered — including the organiser's own, which is accepted from birth.
 */
export function seatsAwaiting(
  detail: ChallengeDetail,
): readonly { readonly player: NamedPlayer; readonly answerBy: string }[] {
  return detail.seats.flatMap((seat) =>
    seat.playerId === undefined || seat.answer !== undefined || seat.answerBy === undefined
      ? []
      : [{ player: seatName(seat), answerBy: seat.answerBy }],
  );
}

/**
 * **The reply is the redraw** — the answer routes' `ChallengeSchema` folded onto the detail the
 * screen is already holding.
 *
 * Both answer routes return the challenge as it now stands, which *is* the server's derived
 * standing, so writing it in is not guessing: it is the same fold the next read would perform,
 * arriving one round trip earlier. **Pending, never optimistic** is about what happens *before*
 * the reply; this is what happens after one.
 *
 * ## The cards are kept, and the rule drops them
 *
 * ADR-0143 §8 in as many words: *"a doubles accept that leaves the challenge in
 * `LINE_UP_INCOMPLETE` keeps the card block the client already holds — nothing about accepting
 * changes who those people are — and an accept or decline that ends the arrangement drops it by
 * this rule, not by a refetch."* So the cards ride across, and {@link challengeArm} stops drawing
 * them the moment the standing leaves the two that draw a block. A refetch to discover that would
 * be a request asking a question this client can already answer.
 *
 * **A seat that has left loses its card here**, which is the same rule one level down: the pair
 * releases the moment somebody leaves, and holding their card because the response we merged had
 * no cards in it either way would keep a stranger on screen.
 *
 * ## Seats are matched by position, and the card is kept only for the same person
 *
 * The court is *"in its fixed order — every A seat, then every B"* and neither answer route
 * reseats anybody, so position is the join. The occupant is checked anyway: a card is a
 * statement about a **person**, and one carried onto a seat somebody else now holds would be the
 * one mistake this merge could make that nothing downstream could detect.
 *
 * ## `readAt` is the detail's own and is not moved forward
 *
 * The reply carries none — `ChallengeSchema` has no `read_at`, deliberately, because it is one
 * challenge rather than a fold of a list against an instant. Nothing the redrawn screen states is
 * measured from it: the seat deadlines belong to the arms this answer has just left, and an
 * invented instant would be this phone's clock arriving exactly where §14 refuses it.
 */
export function redrawnFrom(detail: ChallengeDetail, answered: AnsweredChallenge): ChallengeDetail {
  return {
    ...detail,
    // Assigned rather than spread-when-present: the reply's standing **replaces** the one the
    // screen holds, and a code this build cannot read has to clear it rather than leave the
    // previous sentence standing over a challenge that has moved.
    standing: answered.standing,
    seats: answered.seats.map((seat, at) => {
      const held = detail.seats[at];
      // The card block leaves with the person: a seat given up in any of the three ways draws its
      // arrangement and the handle alone, and that person is a stranger again (ADR-0143 §8).
      const keeps = held?.card !== undefined && held.playerId === seat.playerId && !hasLeft(seat);

      return keeps && held.card !== undefined ? { ...seat, card: held.card } : seat;
    }),
  };
}

/**
 * **The reply is the redraw, for the row** — the same fold onto the cheap `Challenge` the inbox
 * holds, for the one act whose reply is what takes the row away
 * ([#427](https://github.com/Raketa02/Raketa/issues/427)).
 *
 * The departure's reply says the reader's own seat is `LEFT`, and the inbox drops an own *left*
 * at once ([`challengeInbox.ts`](./challengeInbox.ts)) — so writing the reply into the list is
 * what makes the row go on the reply rather than on the re-read that follows it. No cards here to
 * keep or drop; what rides across is the standing and the seats, and **`readAt` stays the
 * list's**: it is the instant the rows beside this one were folded against, the reply carries
 * none, and a row measuring from a different instant than its neighbours is exactly the mistake
 * `challengeKeys.detail`'s note refuses.
 */
export function rowRedrawnFrom(row: Challenge, answered: AnsweredChallenge): Challenge {
  return { ...row, standing: answered.standing, seats: answered.seats };
}

/**
 * What an answer route says back — the standing, and the court under it.
 *
 * Spelled as the two fields the merge reads rather than as a whole `Challenge`: the reply carries
 * a sport and an `opened_at` this screen already holds and no `read_at` at all, and a shape with
 * fields the merge must remember to ignore is how one of them eventually gets written in.
 */
export interface AnsweredChallenge {
  /** Absent when the reply named a standing this build has no words for. */
  readonly standing?: Standing;
  readonly seats: readonly ChallengeSeat[];
}
