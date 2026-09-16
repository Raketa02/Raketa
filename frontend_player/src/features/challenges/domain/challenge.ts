/**
 * A challenge as this build reads one — and the two questions asked of it.
 *
 * `GET /challenges` is *"every challenge you hold a seat in, newest first"*, and until the
 * Chats tab it had exactly one reader: a send refused with `open_challenge_stands` names
 * nobody, so the client re-reads the list that was always its own to find out who
 * ([`the-play-screens.md`](../../../../../docs/specs/matchmaking/the-play-screens.md) §5.1).
 * The second reader is the inbox — `domain/challengeInbox.ts`, which is where every rule about
 * *whose turn it is* lives. This file holds what a challenge **is** and the pair rule read
 * from this side.
 *
 * ## The pair rule, read from this side
 *
 * *"Sharing a line-up makes a pair"*: every occupied seat but your own is somebody you have an
 * open game with, organiser and co-invitees alike, and a seat that declined or lapsed is empty
 * again — so that person is a stranger to you once more the moment they leave.
 *
 * **The clock is not read here, and that is deliberate.** A standing is *"derived from the
 * seats and the clock, never stored"*, and it was derived **at the moment this list was
 * answered**. Folding it again on this side would be a second implementation of a rule whose
 * whole consumer is a name in one sentence, and the two would disagree first about the seat
 * that lapsed between the read and the render. So an ended challenge is one the server called
 * ended, and a seat is out of it when it says it declined or lapsed.
 *
 * **And who ended it is not read here either** ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
 * §3): every ending carries `ended_by`, read on the server from the same per-seat instants the
 * ending is dated from, so the row's name and the row's date cannot come from two clocks. This
 * side used to walk the seats for *the first decline in court order*, which was wrong the moment
 * a departure ended a court and undefined when nobody declined; now it looks one id up.
 *
 * **This names nobody the server refused about.** The gate ran server-side and refused whole;
 * all this decides is which of the organiser's **own** open games to point at, which #222 puts
 * on the *embarrassment* side rather than the safety side.
 *
 * ## A standing this build cannot read
 *
 * `standing` is optional, and the absence is *the server sent a code this app is too old for*.
 * `the-words.md` §3 puts a challenge's standing among the five placements that owe a **named
 * gap** rather than a drop — the code *is* the whole line, so the row prints `OUT_OF_DATE_GAP`
 * and stays. The pair rule reads the absence the safe way round: an unreadable standing has
 * not been called ended, so the people on that court stay paired.
 */

import type { NamedPlayer } from '@/shared/formatting/playerName';
import type { Sport } from '@/shared/vocabulary/sport';

import {
  GIVES_UP_THE_SEAT,
  type ChallengeSide,
  type EndedFacts,
  type EndedStanding,
  type EndingFacts,
  type SeatAnswer,
  type Standing,
  type StandingFacts,
} from './standing';

/** One seat of a challenge: who is in it, what they did about being asked, and by when. */
export interface ChallengeSeat {
  /** Absent on a seat nobody was put in — *an empty seat is a seat*, and it keeps its place. */
  readonly playerId?: string;
  /** Absent while they have not answered, and on a seat nobody was put in. */
  readonly answer?: SeatAnswer;
  /**
   * The whole name, and never a familiar form derived from it (ADR-0107, read through
   * ADR-0171) — and never the nickname, which is a handle drawn on a record and said nowhere.
   *
   * Absent on an empty seat and absent where `users` no longer has the account — never for an
   * unnamed player, whom the entry gate holds at the naming step. The seat stays either way —
   * a seat with no name is still a position on the court, and every sentence that would have
   * named them says `?` instead.
   */
  readonly name?: string;
  /**
   * When this seat's answer stops being wanted — **this seat's own**, dated when it was
   * invited.
   *
   * Absent exactly where nobody was asked: an empty seat, the organiser's, and both seats of a
   * challenge born from a mutual yes. A nullable deadline is how a later reader invents one
   * that never existed, so the absence is the fact rather than a gap to fill in.
   */
  readonly answerBy?: string;
}

/**
 * A challenge, as much of it as this build has a reader for.
 *
 * `organiserId` is here rather than a side, because *"**Challenge sent** and **Challenge for
 * you** are one standing read from two sides"* and which one a reader gets is decided by
 * whether the seat is theirs — a `side` field would be that decision taken by a mapper on
 * somebody else's behalf.
 *
 * `readAt` is the instant every standing and deadline on the list was folded against, copied
 * onto each row the way `gameMappers` copies `GameListResponse`'s. It is carried per challenge
 * because the screens hold one at a time, and carrying it is what makes it impossible for a row
 * to print a countdown against a clock the standing beside it never saw.
 */
export interface Challenge {
  readonly challengeId: string;
  readonly organiserId: string;
  /** Absent when the contract sent a code this build has no words for. See the module note. */
  readonly standing?: Standing;
  readonly sport: Sport;
  readonly openedAt: string;
  /**
   * When it ended — **absent because it has not, or because this standing is not one the
   * contract calls an ending** ([#388](https://github.com/Raketa02/Raketa/issues/388)).
   *
   * Served on `DECLINED`, `LAPSED` and `WITHDRAWN`: exact for the last two, and an upper bound
   * for a decline, because nothing records the instant somebody said no. It is **not** on `ON`,
   * which the contract holds is not an ending at all — a completed line-up produced a game,
   * which is the opposite of nothing being left.
   *
   * Its one reader is the inbox's shelf life, and `domain/challengeInbox.ts` is where all of
   * that is argued rather than here: what the row needs is *when did this row's news happen*,
   * which is this field for three standings and the court's own deadlines for the fourth.
   */
  readonly endedAt?: string;
  /**
   * **The player whose act ended it** — on every ending, and absent on the three standings that
   * are not one ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
   * §3). Always the occupant of one of the court's seats, never a second copy of a name: the
   * face and the name a row draws are that seat's, which is what makes *the face is who the
   * sentence names* one lookup. On `CALLED_OFF` it is the last leaver or whoever pressed *Call
   * it off*, told apart by their seat; on `DECLINED` the seat whose no or departure completed the
   * desertion; on `LAPSED` the seat whose window was the last to run out; on `WITHDRAWN` the
   * organiser.
   *
   * **On the list and on every act's reply, and not on the detail read** — `GET /challenges/{id}`
   * carries neither this nor `gameId` today, so the screen that draws an ended court reads them
   * off the row the list already holds (`useChallengeRow`).
   */
  readonly endedBy?: string;
  /**
   * **The game this court became**, and absent until its line-up first completed — the same id
   * ever after, through a re-seat and through the ending (ADR-0172 §4). What lets the leaver's
   * sheet tell *calls the game off* from *closes this court* without a join on the games cache.
   * On the list and on every act's reply, as `endedBy` is.
   */
  readonly gameId?: string;
  /** The instant the whole list was folded against. Every duration on the row is read from it. */
  readonly readAt: string;
  /** The court in its fixed order, empty seats included. */
  readonly seats: readonly ChallengeSeat[];
}

/**
 * The four standings that mean **this challenge has ended**.
 *
 * A `Record` keyed by the union rather than a list, for §1's reason: an eighth standing added
 * to the contract fails `pnpm typecheck` here rather than quietly counting as open — which is
 * exactly how `CALLED_OFF` arrived (ADR-0172 §2).
 */
const ENDED: Readonly<Record<Standing, boolean>> = {
  AWAITING_ANSWERS: false,
  ON: false,
  LINE_UP_INCOMPLETE: false,
  DECLINED: true,
  LAPSED: true,
  WITHDRAWN: true,
  CALLED_OFF: true,
};

/** Whether this standing is one of the four endings — `ENDED`, read as a type guard. */
export function isAnEnding(standing: Standing): standing is EndedStanding {
  return ENDED[standing];
}

/** The same guard over the fold: whether these facts are an ending's, with who and how on them. */
export function hasEnded(facts: StandingFacts): facts is EndedFacts {
  return isAnEnding(facts.standing);
}

/**
 * Whether a game still stands between the people in it.
 *
 * A standing this build cannot read answers **yes**, and that is the safe direction: the pair
 * rule is what stops somebody being invited into a refusal, so a code nobody here understands
 * keeps the pair rather than releasing it on a guess.
 */
export function challengeStands(challenge: Challenge): boolean {
  return challenge.standing === undefined ? true : !ENDED[challenge.standing];
}

/**
 * Everybody still in this game: an occupied seat that has neither declined, lapsed nor left.
 *
 * Empty on an ended challenge, which is the whole of *the pair releases when the challenge
 * does* — stated here rather than left to each caller to remember. Which answers give a seat up
 * is the vocabulary's own table, `GIVES_UP_THE_SEAT`, for the reason it gives: the pair rule is
 * what stops somebody being invited into a refusal, and a fourth answer missing from an `||`
 * chain here would silently have kept somebody in a game they had walked out of.
 */
export function playersStillIn(challenge: Challenge): readonly string[] {
  if (!challengeStands(challenge)) return [];

  return challenge.seats.flatMap((seat) =>
    seat.playerId === undefined || (seat.answer !== undefined && GIVES_UP_THE_SEAT[seat.answer])
      ? []
      : [seat.playerId],
  );
}

/**
 * **Whether this reader holds the exit** — *Call it off*'s own rule, read on the client so the
 * control is drawn only where the act would be accepted
 * ([ADR-0165](../../../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
 * §5, [#428](https://github.com/Raketa02/Raketa/issues/428)): **the reader is on the court** — an
 * accepted seat — and nothing about who organised it. ADR-0163 §1's organiser-first rule and its
 * fallback are gone: a group that has given up on a game ends it in one act, whoever presses.
 *
 * Read off the cheap list rather than the detail, because the tab bar already holds that list for
 * its badge and the fact is on every row of it. Nothing here reads the standing — that the caller
 * is not on the court is true regardless of what the fold says, exactly as the server checks it —
 * and whether the court has a seat open is the composer's to say. Somebody who left, the organiser
 * who left, and a newcomer still deciding on a fill are all *no*, as the route tells them.
 */
export function holdsTheExit(challenge: Pick<Challenge, 'seats'>, playerId: string): boolean {
  return challenge.seats.some((seat) => seat.playerId === playerId && seat.answer === 'ACCEPTED');
}

/**
 * **Whether this reader may remove the challenge** — the withdraw while nobody has joined
 * ([ADR-0165](../../../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
 * §4, [#428](https://github.com/Raketa02/Raketa/issues/428)): the reader is the organiser, the
 * challenge is still being arranged, and **nobody besides them holds an accepted seat** —
 * whatever seats are still deciding, before any answer included, and again once everybody who
 * joined has left. The moment somebody is in it is nobody's to end for the others, and from then
 * on the organiser leaves like anybody else.
 *
 * It is the row's reveal decision on the Chats list and the arranging arm's on the challenge
 * screen, so it is one function read twice rather than a swipe and a button remembering the same
 * rule. Read off the cheap list, as {@link holdsTheExit} is, because the row is drawn from it. A
 * standing this build cannot read answers **no**: an app that cannot say what a challenge is
 * cannot offer to end it — the opposite direction from the pair rule, and the right one for an
 * act.
 */
export function mayRemove(
  challenge: Pick<Challenge, 'organiserId' | 'standing' | 'seats'>,
  playerId: string,
): boolean {
  if (playerId !== challenge.organiserId) return false;
  if (challenge.standing === undefined || ENDED[challenge.standing]) return false;
  return nobodyHasJoined(challenge);
}

/**
 * **Whether this reader may clear a called-off court from their lists** — the row on Chats and
 * the card on Now, which are one court and go together
 * ([ADR-0173](../../../../../docs/adr/0173-a-called-off-court-is-cleared-from-both-lists-by-one-act.md)):
 * the challenge is `CALLED_OFF`, it has a game (every called-off court does — the standing is
 * reached only once a line-up completed), and the reader is **still on it**, holding an accepted
 * seat. A leaver's seat reads `LEFT` and their own row left the inbox at once; the server answers
 * them as a stranger, so the row never offers what it would refuse.
 *
 * The act behind it is the game card's dismissal, unchanged in what it sends — one act, one fact,
 * and the challenge list subtracts its reader off the same set the rail does. It is the one row
 * on the ended shelf that moves, because it is the one ending whose row carries nothing the
 * reader is owed for a day: the news is theirs alone, and they have read it.
 */
export function mayDismiss(
  challenge: Pick<Challenge, 'standing' | 'seats' | 'gameId'>,
  playerId: string,
): boolean {
  if (challenge.standing !== 'CALLED_OFF' || challenge.gameId === undefined) return false;
  return challenge.seats.some((seat) => seat.playerId === playerId && seat.answer === 'ACCEPTED');
}

/**
 * **Nobody besides the organiser holds an accepted seat** — the court is the organiser's alone,
 * whatever seats are still deciding and whoever has already given theirs up.
 *
 * The half of {@link mayRemove} that survives the ending: the inbox reads it on a `WITHDRAWN` row
 * to tell a removal — the organiser's own act, by construction — from a game called off with
 * others on the court (`challengeInbox.ts`).
 */
export function nobodyHasJoined(challenge: Pick<Challenge, 'organiserId' | 'seats'>): boolean {
  return !challenge.seats.some(
    (seat) =>
      seat.playerId !== undefined &&
      seat.playerId !== challenge.organiserId &&
      seat.answer === 'ACCEPTED',
  );
}

/**
 * **Who on this court you already have a game with** — the name the refusal would not carry.
 *
 * @param invitees the people being invited, in seat order and **without the organiser**: they
 *   hold a seat in every challenge of their own, so including them would match all of them.
 *
 * `undefined` covers two states and does not tell them apart, because the screen says the same
 * thing either way: nothing of yours is in the way, and the pair the send refused about is
 * between two of your invitees — a game that is theirs and not yours to read.
 *
 * The **first** in seat order, because §21's sentence names one person. Counting them would be
 * a figure the refusal deliberately did not send, arrived at by the client doing the
 * arithmetic instead — the ceiling the withheld mark is already held to.
 */
export function pairAlreadyPlaying(
  challenges: readonly Challenge[],
  invitees: readonly string[],
): string | undefined {
  const inAGame = new Set(challenges.flatMap(playersStillIn));
  return invitees.find((player) => inAGame.has(player));
}

/** The reader's own seat, or nothing where they hold none — an id the list should not answer. */
export function ownSeat(challenge: Challenge, playerId: string): ChallengeSeat | undefined {
  return challenge.seats.find((seat) => seat.playerId === playerId);
}

/**
 * What this challenge's standing says **to this reader** — the fold every sentence is keyed on.
 *
 * `undefined` where the standing is one this build has no words for: the row draws
 * `OUT_OF_DATE_GAP` in its place, which is `the-words.md` §3's named gap rather than a shorter
 * list.
 *
 * Three of the readings are worth stating, because each was wrong somewhere before it was
 * written down:
 *
 * - **`open` counts seats nobody has accepted**, never seats still to answer. At the rung that
 *   yields `LINE_UP_INCOMPLETE` nothing is awaiting, so an `awaiting` count there is
 *   structurally zero — a field that could only ever be zero is what let the shipped sentence
 *   read *"2 in, 0 still to answer"*.
 * - **The invitee's sentence reads their own seat**, not only their side (§13.1). A padel four
 *   where one declines and two accept is `LINE_UP_INCOMPLETE` for the player who declined too,
 *   and *"You're in"* is false for them in both clauses.
 * - **And it reads it on `AWAITING_ANSWERS` too** (§13.2,
 *   [#389](https://github.com/Raketa02/Raketa/issues/389)). That standing holds while *any* seat
 *   is awaiting, so the reader's own answer may already be given, and *"They're waiting on you"*
 *   was drawn for somebody who had already spoken.
 *
 * **Who an ending's sentence names is `ended_by`'s seat**, and it is always the whole name or
 * nobody: a seat `users` can no longer answer for is `unknown`, which draws `?` rather than a
 * name this app invented — and so is an ending the wire named nobody for.
 */
export function standingFactsFor(
  challenge: Challenge,
  playerId: string,
): StandingFacts | undefined {
  if (challenge.standing === undefined) return undefined;

  const side: ChallengeSide = challenge.organiserId === playerId ? 'organiser' : 'invitee';
  // What the reader's own seat says. Both **live** standings key an invitee's sentence on it
  // (§13.1, §13.2) and the two folded endings read it before naming anybody else, so it is read
  // once here. Absence means opposite things on the two live ones — see `StandingFacts`.
  const ownAnswer = ownSeat(challenge, playerId)?.answer;

  switch (challenge.standing) {
    case 'AWAITING_ANSWERS':
      // This standing holds while *anybody* is awaiting, so the reader's own answer may already
      // be given — which is the whole of #389.
      return {
        side,
        standing: 'AWAITING_ANSWERS',
        awaiting: countAwaiting(challenge),
        ...(ownAnswer === undefined ? {} : { ownAnswer }),
      };
    case 'ON':
      return { side, standing: 'ON' };
    case 'LINE_UP_INCOMPLETE':
      return {
        side,
        standing: 'LINE_UP_INCOMPLETE',
        accepted: challenge.seats.filter((seat) => seat.answer === 'ACCEPTED').length,
        // A seat is open unless somebody has accepted it — an empty one, and one whose
        // occupant has left. ADR-0142: *a decline reopens that one seat*.
        open: challenge.seats.filter((seat) => seat.answer !== 'ACCEPTED').length,
        ...(ownAnswer === undefined ? {} : { ownAnswer }),
      };
    case 'DECLINED':
    case 'LAPSED':
    case 'WITHDRAWN':
    case 'CALLED_OFF':
      return { side, standing: challenge.standing, ...endingFacts(challenge, playerId) };
  }
}

/** Occupied seats nobody has answered for. The organiser's is accepted from birth. */
function countAwaiting(challenge: Challenge): number {
  return challenge.seats.filter((seat) => seat.playerId !== undefined && seat.answer === undefined)
    .length;
}

/**
 * **Whose act ended it, and how** — `ended_by` looked up on the court, once, for the four
 * endings' one payload (ADR-0172 §3, §7).
 *
 * `you` where the id is the reader's; the seat's whole name where it is somebody else's; and
 * `unknown` where the wire named nobody, or named a seat `users` no longer answers for. A
 * departure is read off that seat's own answer — `LEFT` — and off nothing else, so the sentence
 * is always true of the person it names whichever of two the server's bound picked.
 */
function endingFacts(challenge: Challenge, playerId: string): EndingFacts {
  const seat = whoEndedIt(challenge);
  const ownAnswer = ownSeat(challenge, playerId)?.answer;

  return {
    endedBy: seat?.playerId === playerId ? { kind: 'you' } : seatName(seat),
    byADeparture: seat?.answer === 'LEFT',
    ...(ownAnswer === undefined ? {} : { ownAnswer }),
  };
}

/**
 * **The seat `ended_by` holds**, or nothing — where the wire named nobody, or named somebody who
 * holds no seat on this court, which the contract says cannot happen and this side does not
 * assume.
 */
export function whoEndedIt(challenge: Challenge): ChallengeSeat | undefined {
  if (challenge.endedBy === undefined) return undefined;
  return challenge.seats.find((seat) => seat.playerId === challenge.endedBy);
}

/**
 * **Whether an ending's sentence is about the reader's own act** — and therefore whose face the
 * row draws ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
 * §7's *the face is who the sentence names*, read from the other side).
 *
 * Two ways: `ended_by` is the reader — their own removal, their own press, the departure that
 * called it off — or, on the two **folded** endings, the reader's own seat gave up: §13's
 * invitee column says *You said no* and *Your day ran out* of a seat that did, whoever's act
 * closed the court after it. The two announced endings never read the reader's seat that way:
 * a *Called off* row names the act that called it off, and a withdrawal names the organiser to
 * everybody asked, answered or not (§13 — *separating them would say who else was on the court*).
 *
 * It is one predicate here rather than one in the deck and one in the faces rule, because the
 * two must agree: a row drawing `ended_by`'s face under a sentence about the reader would be a
 * face the words do not name.
 */
export function endingIsTheReadersOwn(facts: EndedFacts): boolean {
  if (facts.endedBy.kind === 'you') return true;
  if (facts.standing !== 'DECLINED' && facts.standing !== 'LAPSED') return false;
  return facts.ownAnswer !== undefined && GIVES_UP_THE_SEAT[facts.ownAnswer];
}

/**
 * **What the reader's leaving would do to this court** — the sheet's rule
 * ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
 * §9), read off the row the list already holds and never off a second read.
 *
 * The ending rule is *at most one player on the court and no seat awaiting an answer*
 * (ADR-0165 §3), so the reader's leaving ends it exactly when they hold an accepted seat, **one**
 * other seat is accepted, and nobody is still deciding. Which sentence that earns is
 * `gameId`'s: on a court that has been a game the departure calls the game off — for the one
 * left, too — and on one that has not it closes the court. `undefined` is every other court,
 * where today's line stands: the seat opens for somebody else.
 *
 * A court already over answers nothing, because there is nothing to leave. The row can be a
 * beat behind the server — a second departure landing while the sheet is up — and the server's
 * answer is what happens; a refusal is said on the sheet as every refusal there is.
 */
export function leavingWouldEnd(challenge: Challenge, playerId: string): LeavingEnds | undefined {
  if (!challengeStands(challenge)) return undefined;
  if (ownSeat(challenge, playerId)?.answer !== 'ACCEPTED') return undefined;
  if (countAwaiting(challenge) > 0) return undefined;

  const others = challenge.seats.filter(
    (seat) => seat.playerId !== playerId && seat.answer === 'ACCEPTED',
  );
  const [theOneLeft] = others;
  if (theOneLeft === undefined || others.length !== 1) return undefined;

  return {
    court: challenge.gameId === undefined ? 'never-a-game' : 'a-game',
    theOneLeft: seatName(theOneLeft),
  };
}

/** What a departure ends, and for whom — {@link leavingWouldEnd}'s answer where it has one. */
export interface LeavingEnds {
  /** Whether the court has been a game: the departure calls it off, or closes a court that never was one. */
  readonly court: 'a-game' | 'never-a-game';
  /** The one person the reader would leave alone on it. */
  readonly theOneLeft: NamedPlayer;
}

/**
 * A seat as a sentence may name it — **the whole handle, or the question mark.**
 *
 * `unknown` covers an empty seat and a seat whose account `users` can no longer answer for, and
 * the two stay one case on purpose: there is no word to draw in either, and inventing one is
 * exactly what ADR-0107 forbids.
 */
export function seatName(seat: ChallengeSeat | undefined): NamedPlayer {
  return seat?.name === undefined ? { kind: 'unknown' } : { kind: 'player', name: seat.name };
}
