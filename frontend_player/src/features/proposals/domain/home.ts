/**
 * **Home's booked games, and a booked game in detail** — the rules a card and the details are
 * drawn by ([#556](https://github.com/Raketa02/Raketa/issues/556); the screens A4.1, A8; the
 * mechanics §11, §14).
 *
 * Pure, and the server's folds are never re-derived: the status, *needs you*, the sides, the share,
 * whether it was paid and the cut-off are the read's (`GET /home`, `GET /bookings/{id}`, #542). What
 * is decided here is how a booked game is **drawn** — which money line a status takes, how long an
 * ended card stays on Home, which games are *new*, when the Chat door is open, and which result act
 * the details offer.
 *
 * **One clock, the read's.** Every fold here takes `now`, an instant on the server's clock — the
 * read's `read_at` moved on by however long the phone has held it — so the line that says *30 zł ·
 * free to leave until Sat 17:00* becomes *Paid · 30 zł* at that instant by itself, as the wire asks,
 * and never by this phone's idea of the time.
 */

import type { ReliabilityBand } from '@/features/player_record/types';
import type { Sport } from '@/shared/vocabulary/sport';

import type { DeckCard } from './deck';
import type { PaymentToConfirm } from './fill';
import {
  courtPrice,
  seatsCanRunOut,
  type FriendsGame,
  type FriendsGameInvitation,
} from './friendsGame';
import type {
  CalledOffReason,
  ClubCancelReason,
  GameKind,
  HomeStatus,
  LeavingKind,
  PlayedWithRelation,
  ShareState,
  TimeTo,
  UncountedReason,
} from './vocabulary';
import { GAME_LENGTH_MS, gameDayOf } from './when';

/**
 * *30 zł · free to leave until Sat 17:00*, *Paid · 30 zł* — **the money a booked game carries**.
 * Since Q113 the shares are held on the cards when the game fills and taken at the club's cut-off.
 */
export interface BookedMoney {
  /** Every seat's share, in grosze. */
  readonly shareGrosze: number;
  /** Every seat's share was **taken** — at the cut-off, or at once for a game booked after it. */
  readonly paid: boolean;
  /**
   * **Where the shares stand** (#637, #639): held until the cut-off, the reader's only checked
   * because a hold would not last that long, or taken. Absent while nobody's money is on the game.
   */
  readonly shareState?: ShareState;
  /** When a checked share is held — its Holding time, four days before the cut-off — while ahead. */
  readonly heldFrom?: string;
  /** When the shares are taken — the club's cut-off — or were. Present exactly with `shareState`. */
  readonly takenAt?: string;
  /**
   * The club's cut-off while it was still ahead at the read: leaving before it takes nothing — the
   * hold on the card is let go — so the line says *free to leave until* it (Q113, amending Q99).
   */
  readonly freeToLeaveUntil?: string;
  /** What everybody still in was given back — a game its club cancelled after the cut-off (#637). */
  readonly refundedGrosze?: number;
}

/**
 * **One card on Home** — a game the reader booked, from the moment it filled. The sides are the
 * deck's people, the reader's side first and the reader first on it, each with their *paid*.
 */
export interface HomeGame {
  /** The booking — the same id the game had while it filled. */
  readonly bookingId: string;
  /**
   * The ordinary Game it opened: the result and the forecast are reached by it, and the room by the
   * booking (#577). **Absent while a full game waits for one payment** (#625) — there is no Game
   * until it books — and on one that never booked.
   */
  readonly gameId?: string;
  /** The pool it filled in — a group's id. */
  readonly groupId: string;
  readonly sport: Sport;
  readonly kind: GameKind;
  readonly status: HomeStatus;
  /** Why it is `CALLED_OFF` — absent on every other status. */
  readonly calledOffReason?: CalledOffReason;
  /** Why the club cancelled it — present with `CANCELLED_BY_THE_CLUB` alone (#547). */
  readonly clubCancelReason?: ClubCancelReason;
  /** Why it is `UNCOUNTED` with nobody disagreeing about a score — absent otherwise. */
  readonly uncountedReason?: UncountedReason;
  /** Seats somebody left and nobody has taken yet — *1 seat open* (#544). */
  readonly openSeats: number;
  /**
   * A result to enter, a score waiting on the reader's agreement, a seat open in their game — or,
   * at the court (#658), their own *I'm here* while they are awaited, their *I was there* while they
   * didn't come, or somebody else's *I was there* to confirm.
   */
  readonly needsYou: boolean;
  /** The court hour's start; games are an hour. */
  readonly startsAt: string;
  readonly club: DeckCard['club'];
  /** What the club calls the court — *Court 2*. Absent on a game that never booked. */
  readonly courtName?: string;
  /** The booked court's kind — *Court 2 · indoor* (#677). Absent with no court, or none the read holds. */
  readonly indoor?: boolean;
  readonly sides: DeckCard['sides'];
  readonly money: BookedMoney;
  /**
   * **A full game gone back to filling before it was booked** (#625, Q106) — a player left while one
   * payment was awaited, or a yes was taken back. *Seat open* while it fills, nobody paid; *Called
   * off* once its last moment to book passes first. It books again the moment it is full. Absent on
   * every booked game, and from an older server.
   */
  readonly fillingAgain?: boolean;
  /**
   * **When the payment the game waits for is due** (#625, #626; Q111) — one player's share was
   * refused, and their seat is theirs alone until then: *Waiting for one payment · until 14:40*.
   * Never whose. Present on `WAITING_FOR_A_PAYMENT` alone, and absent from an older server.
   */
  readonly paymentDueBy?: string;
  /**
   * **The reader's own refused share, and their time to pay** (#625, #626; Q111) — *Confirm your
   * payment by 14:40*, beside their *To confirm* row — on a game waiting for it, or one gone back to
   * filling meanwhile. Absent for everybody else, from the moment it runs out, and from an older
   * server.
   */
  readonly yourPaymentDueBy?: string;
  /**
   * **What that time is for** (#638; Q113) — to fix the card, refused before the club's cut-off
   * where nothing is taken (*Fix your card by 14:40*), or to pay, after it. Only the payer's words
   * change by it. Absent while no time runs, and from an older server.
   */
  readonly timeTo?: TimeTo;
  /**
   * **A friends game's own facts** (#751, #759) — the sender, the pay mode, each seat's state: the
   * sender's game in Your games (*2 of 3 friends in · waiting for Ania*), and a friend's once they
   * accepted. Absent on a game a fill booked.
   */
  readonly friendsGame?: FriendsGame;
}

/** **Home** — the reader's booked games, soonest first, and how many need them. */
export interface Home {
  /** The instant every status and money line was folded against, on the server's clock. */
  readonly readAt: string;
  /** Home's badge: the cards that need the reader, and every payment they have to confirm. */
  readonly needingYou: number;
  readonly games: readonly HomeGame[];
  /**
   * **FRIEND REQUESTS** — the requests waiting on the reader, newest first (#753). Not counted in
   * `needingYou`. This feature reads them because they ride on Home's read; `friends` draws them and
   * answers them.
   */
  readonly friendRequests: readonly HomeFriendRequest[];
  /**
   * **FRIENDS GAME · n** — the friends games whose invitation waits on the reader, the soonest to
   * end first (#759; friends 12). Not counted in `needingYou`. A card leaves once answered.
   */
  readonly friendsGames: readonly FriendsGameInvitation[];
  /**
   * **ASKED FOR A LEVEL · n** — one card per sport a friend asked the reader to get a level in, the
   * sport with the newest ask first (#765; the friends mechanics §5.1). Not counted in `needingYou`.
   * This feature reads them because they ride on Home's read; `friends` draws them and answers them.
   */
  readonly levelAsks: readonly HomeLevelAsk[];
  /**
   * **The trophy left of the bell** (#775; the rankings screens §1) — absent while the reader has no
   * result in any sport, when the trophy draws no number and still opens Rankings. This feature reads
   * it because it rides on Home's read; `rankings` draws it.
   */
  readonly ranking?: HomeRanking;
  /**
   * **TO CONFIRM · n** — every payment the reader has to confirm, soonest game first (#815, #819):
   * the same rows as their own read (`GET /players/me/payments-to-confirm`), at this read's instant.
   * Needs your answer draws them from here, so the sheet shows exactly what `needsYourAnswer`'s
   * watermark covers; You › Payments keeps their own read.
   */
  readonly paymentsToConfirm: readonly PaymentToConfirm[];
  /** **The envelope's badge**, and the watermark the visit sends back (#819, ADR-0205 §3). */
  readonly needsYourAnswer: NeedsYourAnswerNews;
}

/**
 * **What is new in Needs your answer** (#815, #819; ADR-0205 §3) — kept on the server, so every
 * phone agrees.
 */
export interface NeedsYourAnswerNews {
  /**
   * How many waiting items arrived since the sheet was last closed, on any phone: each payment to
   * confirm, invitation and request by its own arrival, and each friend on an ask for a level by
   * their own ask. A change of state is never new.
   */
  readonly newCount: number;
  /**
   * **This read's watermark**, the newest arrival among everything waiting, exactly as served —
   * an instant the visit hands back untouched, never re-formatted and never the phone's clock.
   * Absent while nothing waits.
   */
  readonly watermark?: string;
}

/**
 * **The watermark a closing sheet names** (#819, ADR-0205 §3) — `held`, what was kept so far, moved
 * on to `read`'s watermark whenever the sheet is `shown` on it: open, never covered by a record or a
 * fill's sheet, under which a read lands unseen. Every item of a read the sheet is shown on is on
 * screen, so everything up to its watermark is seen. A read with nothing waiting has no watermark
 * and moves nothing, so the close after the last answer names the read that held it.
 */
export function watermarkShown(
  held: string | undefined,
  shown: boolean,
  read: string | undefined,
): string | undefined {
  return shown && read !== undefined ? read : held;
}

/**
 * **The envelope's badge, after this phone's visits** (#819) — `visits` are the watermarks of the
 * visits this phone sent that are on their way or recorded. **A read whose watermark is no later
 * than one of them holds nothing new**: everything in it arrived by then, and was seen. A read newer
 * than all of them has something that arrived after, so the server's count stands — it is exact
 * once a visit is recorded, and the re-read after the visit makes it so. Nothing is written into the
 * read, so a read already on its way, or one that lands before the visit does, keeps the badge gone
 * and drops nothing it carried. Instants are compared, never their spelling.
 */
export function newCountAfter(news: NeedsYourAnswerNews, visits: readonly string[]): number {
  const newest = news.watermark === undefined ? Number.NaN : Date.parse(news.watermark);
  if (Number.isNaN(newest)) return news.newCount;
  return visits.some((visit) => Date.parse(visit) >= newest) ? 0 : news.newCount;
}

/**
 * **The trophy's ranking** (the rankings mechanics §8) — the sport of the reader's latest result in
 * any sport, and their place in it on each view: absent where they have none there, which draws the
 * trophy with no number.
 */
export interface HomeRanking {
  readonly sport: Sport;
  readonly generalPlace?: number;
  readonly friendsPlace?: number;
}

/**
 * **One card in ASKED FOR A LEVEL** (the friends screens §6.4; the words §29.5) — *tomek.k wants to
 * play padel with you*: the sport, and every friend whose ask in it waits on the reader, newest
 * first and never none. It names no group.
 */
export interface HomeLevelAsk {
  readonly sport: Sport;
  readonly askers: readonly HomeLevelAsker[];
}

/** One friend on a level ask's card — a face that opens their record. */
export interface HomeLevelAsker {
  readonly playerId: string;
  /** Whole, never with an @ (ADR-0199 §1). */
  readonly nickname: string;
  /** Omitted when they have no photograph: the face draws their poster. */
  readonly photoUrl?: string;
}

/**
 * **Home without the level asks in these sports** — what a level just got changes before Home is
 * read again (#765): the server ends a sport's card the moment the reader holds any level in it (the
 * friends mechanics §5.1), so the cache drops it on the way back to Home rather than drawing it until
 * the re-read lands.
 */
export function withoutLevelAsksIn(home: Home, sports: readonly Sport[]): Home {
  const left = home.levelAsks.filter((ask) => !sports.includes(ask.sport));
  return left.length === home.levelAsks.length ? home : { ...home, levelAsks: left };
}

/**
 * **Where they found the reader, said in place of the group line** (the words §29.2, §30.8, §31.10) —
 * one at most, which is why it is one field and not a flag each:
 *
 * | `kind` | Line |
 * | --- | --- |
 * | `link` | *Invited you to Raketa* — made by their Friend link |
 * | `ranking` | *Found you in the padel ranking* — the reader's record on the Rankings page, `sport`'s (#779) |
 * | `newInRakieta` | *Found you among new players* — Home's New in Rakieta, or a record it opened (#801) |
 * | `sameLevel` | *Your level in padel · 91% even* — Home's Same competitive level, or a record it opened, in `sport` (#802): **today's** %, absent once either holds no level there — *Found you at your padel level* |
 * | `sameVibe` | *6 things in common* — Home's Same vibe, or a record or vibe sheet it opened (#803): **today's** count, `0` once they share none — *Found you through your tags* |
 *
 * Absent for a request asked from a group's Members, a record or a result: the group line.
 */
export type RequestFoundBy =
  | { readonly kind: 'link' }
  | { readonly kind: 'ranking' }
  | { readonly kind: 'newInRakieta' }
  | { readonly kind: 'sameLevel'; readonly percentEven?: number }
  | { readonly kind: 'sameVibe'; readonly inCommon: number };

/**
 * **One friend request on Home** (friends 5; the words §29.2): *Inés wants to be your friend · With
 * you in Kazimierz crew · Padel 3,40 · ✦ 98*. Every part but the requester and their reliability is
 * absent where the wire says nothing: a request found by a link, the ranking or a Home row says where
 * in place of the group (`foundBy`); a request asked from a screen with no group names none, and
 * neither does one either of them has since left.
 *
 * Since #818 the tile in Needs your answer draws none of the where: it reads `levels` instead —
 * *● Padel 3,40 · ● Tennis 2,90* (ADR-0205 §1). The where is still read, as the wire still serves it.
 */
export interface HomeFriendRequest {
  readonly playerId: string;
  /** Whole, never with an @ (ADR-0199 §1). */
  readonly nickname: string;
  /** Omitted when they have no photograph: the face draws their poster. */
  readonly photoUrl?: string;
  /** Where they found the reader, where the card says so in place of the group line. */
  readonly foundBy?: RequestFoundBy;
  /** The group they asked from, while both are in it. */
  readonly group?: { readonly id: string; readonly name: string };
  /** The sport of the screen they asked from — absent for one this build cannot name. */
  readonly sport?: Sport;
  /** Their Level in it, where they hold one. */
  readonly level?: number;
  /** Player reliability in points — the chip's *✦ 98*. */
  readonly playerScore: number;
  /** The band the server put it in — absent where this build cannot name the code. */
  readonly reliabilityBand?: ReliabilityBand;
  /**
   * **Every sport they hold a published Level in, with that Level** (#818; ADR-0205 §1, §10) — the
   * tile's sport-levels line, in the order served, which is the app's sport order. Empty when they
   * hold none, and the line is left out.
   */
  readonly levels: readonly HomeFriendRequestLevel[];
}

/** One sport on a request's sport-levels line — *● Padel 3,40*. */
export interface HomeFriendRequestLevel {
  readonly sport: Sport;
  readonly level: number;
}

/**
 * **What *Leave the game* would cost now** (the mechanics §13; #544) — the line under the button and
 * the sheet in front of it. Absent where there is no button: once the hour has come, on a game that
 * is over, and for a reader not on the game.
 *
 * Before the cut-off nothing is taken (Q113). After it the read quotes what comes back if somebody
 * takes the seat, to the grosz, or nothing while the fee kept is not known (#641).
 */
export interface Leaving {
  readonly kind: LeavingKind;
  /**
   * **Before the cut-off, whether leaving lets a hold on the card go** (Q113) — while the reader's
   * share is held; not while it is only checked, which holds nothing yet. Folded on the read's
   * clock (`leavingAt`); the read's own `leaving` carries none.
   */
  readonly letsAHoldGo?: boolean;
  /**
   * **After the cut-off, the read's exact quote** (#641, #644) — absent while the fee kept on the
   * payment is not yet known, where the words give no figure and no clause, never an estimate.
   */
  readonly lateRefund?: LateRefund;
}

/**
 * *If someone takes your seat, you get 38,24 zł back (40 zł less the 1,76 zł kept on your payment)*
 * — **what a leaver after the cut-off gets back if somebody takes the seat** (Q113): the share less
 * exactly what was kept on the reader's own payment, both the server's to the grosz. The two
 * together are the payment.
 */
export interface LateRefund {
  readonly backGrosze: number;
  readonly keptGrosze: number;
}

/** **The payment a late refund is less of** — *40 zł*: what comes back and what was kept, together. */
export function paymentOf(refund: LateRefund): number {
  return refund.backGrosze + refund.keptGrosze;
}

/**
 * **The open seat, offered to a reader not on the game** (#545) — a *Seat open* card or a *Seats to
 * fill* row opened: they stand in the seat that opened first, unpaid (*You?*), and *I'm in* takes it.
 */
export interface RescueOffer {
  /** When the seat leaves the board — the club's cut-off while it is ahead, then the start. */
  readonly deadline: string;
  /** *fills by Fri 16:00* — the game is off unless its seats are taken by then. */
  readonly fillsByTheCutOff: boolean;
}

/** What leaving costs while a full game waits for one payment — nobody has paid anything (#625). */
export const LEAVING_WHILE_WAITING: Leaving = { kind: 'WHILE_WAITING_FOR_A_PAYMENT' };

/** **A booked game in detail** (the screens A4.1) — the card's facts, and what only the details draw. */
export interface BookedGame extends Omit<HomeGame, 'club'> {
  /** The instant the status and the money were folded against. */
  readonly readAt: string;
  /** An hour after the start: TIME's *until*. */
  readonly endsAt: string;
  /** WHERE: the club, and how far it is from the reader — omitted with no Location area. */
  readonly where: DeckCard['club'] & { readonly distanceKm?: number };
  /** Draw the balance forecast — the Game's own pairing read — while the full game awaits its entry. */
  readonly showsForecast: boolean;
  /** *Leave the game*'s cost now — absent where there is no button. */
  readonly leaving?: Leaving;
  /** The reader is not on the game, and its open seat is offered to them: a rescue seen from outside. */
  readonly rescue?: RescueOffer;
  /**
   * **PLAYED WITH** (#754; ADR-0202 §1): everybody else on the game, with **the reader's own**
   * relation to each — empty for a reader not on the game.
   */
  readonly playedWith: readonly PlayedWith[];
}

/** **Somebody else on a booked game, and where the reader stands with them** (#754). */
export interface PlayedWith {
  readonly playerId: string;
  readonly relation: PlayedWithRelation;
}

/**
 * **One of PLAYED WITH's people, as the card draws them** (#754) — named off their seat. The shape
 * `friends`' card takes, stated by this feature for its own demand (`PlayedWithRelation`'s note).
 */
export interface PlayedWithPerson {
  readonly playerId: string;
  /** Absent for a seat that can no longer be named — the card leaves them off. */
  readonly nickname?: string;
  readonly photoUrl?: string;
  readonly level?: number;
  readonly relation: PlayedWithRelation;
}

/**
 * **PLAYED WITH's people** (#754; the friends screens §3) — each of the others named off their
 * seat: the face, the whole nickname and the Level the card draws, beside where the reader stands
 * with them. In the relations' order, which is the game's; anybody with no seat (a read caught
 * mid-move) is left off, and a seat that can no longer be named is passed on unnamed, for the card
 * to leave off. Whether the card is drawn at all is `friends`' rule.
 */
export function playedWithOf(
  game: Pick<BookedGame, 'sides' | 'playedWith'>,
): readonly PlayedWithPerson[] {
  const seats = [...game.sides.yours, ...game.sides.theirs];
  return game.playedWith.flatMap(({ playerId, relation }): PlayedWithPerson[] => {
    const seat = seats.find((one) => one.playerId === playerId);
    if (seat === undefined) return [];
    return [
      {
        playerId,
        relation,
        ...(seat.name === undefined ? {} : { nickname: seat.name }),
        ...(seat.level === undefined ? {} : { level: seat.level }),
        ...(seat.photoUrl === undefined ? {} : { photoUrl: seat.photoUrl }),
      },
    ];
  });
}

// ---------------------------------------------------------------------------
// The money line
// ---------------------------------------------------------------------------

/**
 * **The line under a Home card** (the mechanics §14.1's table) — or nothing, which is every result
 * state's: *unchanged from today*, and today's cards carry no money.
 *
 * - `booked` — *30 zł · free to leave until Sat 17:00* while the cut-off is ahead, the share held
 *   or only checked; *Paid · 30 zł* once it is taken (Q113).
 * - `seatOpen` — *1 seat open*, and *fills by Sat 17:00 or the game is off* before the cut-off;
 *   *offered to others · the game goes ahead* after it.
 * - `fillingAgain` — a full game gone back to filling (Q106): *1 seat open*, *books when it's full*,
 *   and *nobody paid*.
 * - `paymentAwaited` — one player's payment awaited (Q111): *Waiting for one payment · until 14:40
 *   · Nobody pays until it's in*, the time while it is ahead. Never whose.
 * - `yourPayment` — the same game, or one gone back to filling meanwhile, read by the payer while
 *   their time runs: *Confirm your payment by 14:40*, or before the cut-off *Fix your card by 14:40*
 *   (`window`, Q113). So is a booked game whose holding was refused (#639): it stays booked, and
 *   only its player's card says so.
 * - `calledOff` — why, and *refunded 30 zł* when the shares came back; when none did, *nothing was
 *   taken* or *nobody paid*, by the reason. The club is carried for the reasons that are the club's.
 * - `seatEmpty` — *Uncounted* because its hour came with a seat still open: no Level moved.
 * - `didntCome` — *Uncounted* because somebody didn't come (#658): while a late *I was there* waits
 *   on the reader — theirs to say, or somebody else's to confirm (`needsYou`) — that they should say
 *   who was there; to everybody else, that no Level moved.
 * - `senderPaid` — a friends game whose sender pays the whole court, read by a friend on it (#759;
 *   §29.8): *tomek.k paid the court*, in place of a share that is not theirs to pay, and *free to
 *   leave until Fri 10:00* while the cut-off is ahead (the friends mechanics §11.1). **The sender's
 *   own** reads the court's price, held until the cut-off, and never *free to leave*: leaving, they
 *   still pay the court (§11.2).
 */
export type MoneyLine =
  | {
      readonly kind: 'booked';
      readonly shareGrosze: number;
      /** Taken, at `now`. */
      readonly paid: boolean;
      /** The club's cut-off while the share is not yet taken and it is still ahead of `now`. */
      readonly freeToLeaveUntil?: string;
    }
  | { readonly kind: 'seatOpen'; readonly seats: number; readonly fillsBy?: string }
  | { readonly kind: 'fillingAgain'; readonly seats: number }
  | { readonly kind: 'paymentAwaited'; readonly until?: Deadline }
  | ({ readonly kind: 'yourPayment' } & YourTime)
  | {
      readonly kind: 'calledOff';
      readonly reason?: CalledOffReason;
      /** The club's own reason, with `CANCELLED_BY_THE_CLUB` (#547). */
      readonly clubCancelReason?: ClubCancelReason;
      readonly club?: string;
      /** A friends game's sender, named for `BY_THE_SENDER` (#759): *tomek.k called it off*. */
      readonly sender?: string;
      readonly refundedGrosze?: number;
    }
  | {
      readonly kind: 'senderPaid';
      readonly sender?: string;
      /** The club's cut-off while it is ahead: a friend may leave free until then (§11.1). */
      readonly freeToLeaveUntil?: string;
    }
  | { readonly kind: 'seatEmpty' }
  | { readonly kind: 'didntCome'; readonly needsYou: boolean };

/**
 * **What the reader's money on a booked game comes to** — every seat's share, but the court's price
 * for a friends game's sender who pays the whole court (#759; the friends mechanics §8.1): the
 * sport's seats are the friends it seats and the sender.
 */
export function yourMoneyGrosze(game: Pick<HomeGame, 'money' | 'friendsGame'>): number {
  const friends = game.friendsGame;
  return friends?.payMode === 'WHOLE_COURT' && friends.youAreTheSender
    ? courtPrice(game.money.shareGrosze, friends.friendsSeated + 1)
    : game.money.shareGrosze;
}

/**
 * **The cut-off, while it is still ahead of `now`** — the instant *free to leave until …* leaves the
 * card's line, and *fills by …* a seat open's.
 */
export function cutOffAhead(money: BookedMoney, now: number): string | undefined {
  const until = money.freeToLeaveUntil;
  return until !== undefined && Date.parse(until) > now ? until : undefined;
}

/**
 * **Where the reader's share stands at `now`** (Q113; the mechanics §12.2) — the details' money row
 * says it: *held on your card · taken Wed 19:00*, *held from Sat 19:00 · taken Wed 19:00*, or paid.
 */
export type ShareAt =
  | { readonly kind: 'held'; readonly takenAt: string }
  | { readonly kind: 'checked'; readonly heldFrom: string; readonly takenAt: string }
  | { readonly kind: 'taken' };

/**
 * **The read's share, folded on the read's clock** — the wire's state switches by itself at the two
 * instants it names, and so does this: a checked share is held from `heldFrom`, and every share is
 * taken at `takenAt`, the cut-off, where the server's own `paid` turns too. Nothing for a share the
 * read gives no state, which is no money on the game.
 */
export function shareAt(money: BookedMoney, now: number): ShareAt | undefined {
  const { shareState, takenAt, heldFrom } = money;
  if (money.paid || shareState === 'TAKEN') return { kind: 'taken' };
  if (shareState === undefined || takenAt === undefined) return undefined;
  if (!(Date.parse(takenAt) > now)) return { kind: 'taken' };
  if (shareState === 'CHECKED' && heldFrom !== undefined && Date.parse(heldFrom) > now) {
    return { kind: 'checked', heldFrom, takenAt };
  }
  return { kind: 'held', takenAt };
}

/**
 * **A deadline Home names** — a time to pay (*until 14:40*, *Confirm your payment by 14:40*, Q111) —
 * and whether it falls on `now`'s day on the club's calendar: the hour alone then, the weekday with
 * it on any other day (the screens A8).
 */
export interface Deadline {
  readonly at: string;
  readonly today: boolean;
}

/**
 * **The window a refused card's words are in** (#638; Q113) — the one the read names while the time
 * runs: `FIX_THE_CARD` before the club's cut-off, where nothing is taken and nobody is asked to pay,
 * `PAY` after it. `UNNAMED` once the time has gone — the read names none then, and a seat taken back
 * is held before the cut-off and paid after it — where no time was given, and from an older server:
 * the words then say *confirm*, never *pay* nor *fix*.
 */
export type PaymentWindow = TimeTo | 'UNNAMED';

/**
 * **The payer's own time, and its window** — *Fix your card by 14:40* or *Confirm your payment by
 * 14:40*: what Home's line, the details' row, a *TO CONFIRM* row and the sheet name.
 */
export interface YourTime {
  readonly by: Deadline;
  readonly window: PaymentWindow;
}

/** The window at `now`: the read's, while `by` is ahead of it. */
export function paymentWindowAt(
  by: string | undefined,
  timeTo: TimeTo | undefined,
  now: number,
): PaymentWindow {
  return timeTo === undefined || deadlineAhead(by, now) === undefined ? 'UNNAMED' : timeTo;
}

/**
 * **Whose seat a refused card's time keeps** — the player's own, on a game that filled or was booked
 * (*to keep your seat*), or a rescue's, kept for them alone to take and not yet theirs (*to take the
 * seat*, #640): the notice's and the email's two endings.
 */
export type SeatAtStake = 'yours' | 'aRescue';

/**
 * **The seat the details' money row says is at stake**, beside the payer's own time — where the
 * status tag does not say it: a rescue's, seen from outside (#640), and the player's own on a game
 * booked already, whose holding was refused and whose tag still says *Booked* (#639; the screens
 * A4.1). Nothing on a game not booked yet: its tag says it waits.
 */
export function stakeOnTheDetails(
  game: Pick<BookedGame, 'rescue' | 'status' | 'fillingAgain'>,
): SeatAtStake | undefined {
  if (game.rescue !== undefined) return 'aRescue';
  return courtIsGiven(game) ? 'yours' : undefined;
}

/** **A deadline as Home writes it, from `now`** — whether it is still ahead or not. */
export function deadlineOf(at: string, now: number): Deadline {
  return { at, today: gameDayOf(at, now)?.kind === 'today' };
}

/**
 * **A deadline, while it is still ahead of `now`** — the instant a clause naming it leaves a card's
 * line and either details' money row, as *free to leave until* leaves at the cut-off. Nothing for
 * no deadline, or a value that is not an instant.
 */
export function deadlineAhead(at: string | undefined, now: number): Deadline | undefined {
  return at === undefined || !(Date.parse(at) > now) ? undefined : deadlineOf(at, now);
}

/**
 * **Whether the game's line carries a clause that runs out by itself** — *free to leave until* and
 * *fills by* at the cut-off, *held from* at a checked share's holding time, *until* and *Confirm your
 * payment by* at a time to pay, and a friends game's seat still *waiting*. While one is there the read's clock ticks (`useReadClock`), so the
 * clause leaves the screen at that instant rather than at the next read.
 */
export function lineCanRunOut(
  game: Pick<HomeGame, 'money' | 'paymentDueBy' | 'yourPaymentDueBy' | 'friendsGame'>,
): boolean {
  return (
    game.money.freeToLeaveUntil !== undefined ||
    game.money.heldFrom !== undefined ||
    game.paymentDueBy !== undefined ||
    game.yourPaymentDueBy !== undefined ||
    // A friends game's seat *waiting · 3 h left* turns *didn't answer* at its end (#759).
    (game.friendsGame !== undefined && seatsCanRunOut(game.friendsGame))
  );
}

/**
 * The line a card takes at `now`. **Nothing here is counted**: how many seats are open, why a game
 * is off and what came back are the read's (#544), and only the clauses that run out — at the
 * cut-off and at a time to pay — are folded on the clock.
 *
 * **The payer reads their own time first** (Q111): on a game waiting for their payment, or gone back
 * to filling meanwhile, *Confirm your payment by 14:40* while it runs — the status tag still says
 * which of the two it is — and on a booked game whose holding was refused, *Fix your card by 14:40*
 * (#639, Q113), the tag still *Booked*. The read names the time to its payer alone, so whichever the
 * status, it is theirs. From the deadline on, the line is everybody's.
 */
export function moneyLineOf(
  game: Pick<
    HomeGame,
    | 'status'
    | 'money'
    | 'club'
    | 'openSeats'
    | 'calledOffReason'
    | 'clubCancelReason'
    | 'uncountedReason'
    | 'needsYou'
    | 'fillingAgain'
    | 'paymentDueBy'
    | 'yourPaymentDueBy'
    | 'timeTo'
    | 'friendsGame'
  >,
  now: number,
): MoneyLine | undefined {
  const { money, friendsGame } = game;
  const club = game.club.name === undefined ? {} : { club: game.club.name };
  const sender =
    friendsGame?.senderNickname === undefined ? {} : { sender: friendsGame.senderNickname };
  const yours = deadlineAhead(game.yourPaymentDueBy, now);
  if (yours !== undefined) {
    return {
      kind: 'yourPayment',
      by: yours,
      window: paymentWindowAt(game.yourPaymentDueBy, game.timeTo, now),
    };
  }
  // Whole court (§29.8): a friend pays nothing and the line says who did; the sender pays the court.
  const live = game.status === 'BOOKED' || game.status === 'SEAT_OPEN';
  if (live && friendsGame?.payMode === 'WHOLE_COURT') {
    const until = cutOffAhead(money, now);
    if (!friendsGame.youAreTheSender) {
      return {
        kind: 'senderPaid',
        ...sender,
        ...(until === undefined ? {} : { freeToLeaveUntil: until }),
      };
    }
    return {
      kind: 'booked',
      shareGrosze: yourMoneyGrosze({ money, friendsGame }),
      paid: shareAt(money, now)?.kind === 'taken',
    };
  }
  switch (game.status) {
    case 'BOOKED': {
      if (shareAt(money, now)?.kind === 'taken') {
        return { kind: 'booked', shareGrosze: money.shareGrosze, paid: true };
      }
      const until = cutOffAhead(money, now);
      return {
        kind: 'booked',
        shareGrosze: money.shareGrosze,
        paid: false,
        ...(until === undefined ? {} : { freeToLeaveUntil: until }),
      };
    }
    case 'WAITING_FOR_A_PAYMENT': {
      const until = deadlineAhead(game.paymentDueBy, now);
      return { kind: 'paymentAwaited', ...(until === undefined ? {} : { until }) };
    }
    case 'SEAT_OPEN': {
      // Gone back to filling (Q106): nobody paid, so there is no cut-off to fill by.
      if (game.fillingAgain === true) return { kind: 'fillingAgain', seats: game.openSeats };
      const until = cutOffAhead(money, now);
      return {
        kind: 'seatOpen',
        seats: game.openSeats,
        ...(until === undefined ? {} : { fillsBy: until }),
      };
    }
    case 'CALLED_OFF':
      return {
        kind: 'calledOff',
        ...(game.calledOffReason === undefined ? {} : { reason: game.calledOffReason }),
        ...(game.clubCancelReason === undefined ? {} : { clubCancelReason: game.clubCancelReason }),
        ...club,
        ...sender,
        ...(money.refundedGrosze === undefined ? {} : { refundedGrosze: money.refundedGrosze }),
      };
    case 'UNCOUNTED':
      switch (game.uncountedReason) {
        case 'SEAT_EMPTY':
          return { kind: 'seatEmpty' };
        case 'DIDNT_COME':
          return { kind: 'didntCome', needsYou: attendanceNeedsYou(game) };
        case undefined:
          return undefined;
      }
    case 'NEEDS_RESULT':
    case 'CONFIRM_THE_RESULT':
    case 'COUNTED':
    case 'PLAYED_NO_SCORE':
      return undefined;
  }
}

// ---------------------------------------------------------------------------
// Which cards Home draws
// ---------------------------------------------------------------------------

/** How long an ended game keeps its card — **a day, the Classic rail's number** (`plans`). */
export const ENDED_HOME_SHELF_LIFE_MS = 24 * 60 * 60 * 1000;

/**
 * **A status as Home draws it** — the wire's, with one more: a full game **gone back to filling**
 * (#624, Q106) reads *Seat open* as a booked game a player left does, and is another thing under
 * it — nobody paid, no Game, no room and no court.
 */
type Stage = HomeStatus | 'FILLING_AGAIN';

function stageOf(game: Pick<HomeGame, 'status' | 'fillingAgain'>): Stage {
  return game.status === 'SEAT_OPEN' && game.fillingAgain === true ? 'FILLING_AGAIN' : game.status;
}

/**
 * **What each stage says about a booked game** — one table, so a tenth status is one row and every
 * rule below answers for it at once:
 *
 * - `ended` — one of the four ends: a game that will not be played, or whose result is settled.
 * - `fresh` — filled and not yet past its hour, which is when a game can be *new*.
 * - `room` — the game can have a room. **Its own life decides past that** (the mechanics §14.3): a
 *   booked game's room opens with the booking and closes as today — 48 hours after *we played*,
 *   when the result window closes, or when the game is called off — so the door is drawn while the
 *   join finds the room, and a counted game's room outlives the result by a day or two. A
 *   called-off one has none any more.
 * - `court` — the court is given, which it is when the game books (A4.2: *no court number* before).
 *
 * **A game waiting for one payment** (Q111) filled, so it is *new* until opened — the four are
 * matched — but nobody paid and nothing is booked: no room and no court until the payment is in
 * (the wire gives none while it waits).
 *
 * **A game gone back to filling is none of the four**: still live, not *new* — the tag marks a game
 * that filled, and this one is not full any more — and, like a game waiting for one payment, no
 * room and no court until it is booked.
 */
const STATUS: Readonly<
  Record<
    Stage,
    {
      readonly ended: boolean;
      readonly fresh: boolean;
      readonly room: boolean;
      readonly court: boolean;
    }
  >
> = {
  WAITING_FOR_A_PAYMENT: { ended: false, fresh: true, room: false, court: false },
  BOOKED: { ended: false, fresh: true, room: true, court: true },
  SEAT_OPEN: { ended: false, fresh: true, room: true, court: true },
  NEEDS_RESULT: { ended: false, fresh: false, room: true, court: true },
  CONFIRM_THE_RESULT: { ended: false, fresh: false, room: true, court: true },
  COUNTED: { ended: true, fresh: false, room: true, court: true },
  UNCOUNTED: { ended: true, fresh: false, room: true, court: true },
  PLAYED_NO_SCORE: { ended: true, fresh: false, room: true, court: true },
  CALLED_OFF: { ended: true, fresh: false, room: false, court: true },
  FILLING_AGAIN: { ended: false, fresh: false, room: false, court: false },
};

/**
 * **What a booked game's tag says** — its status as Home, the details and the room name it.
 *
 * The wire's, with one more: **a For fun game after its hour reads *Played*** (#656; the mechanics
 * §15.2). It asks nobody for a result — no *Needs result* — and a score put up on it stands at once
 * and counts nothing, so *Counted* would be the wrong word for it too. Its ending with no score is
 * everybody's *Played · no score*.
 */
export type ShownStatus = HomeStatus | 'PLAYED';

export function shownStatus(game: Pick<HomeGame, 'status' | 'kind'>): ShownStatus {
  const played = game.status === 'NEEDS_RESULT' || game.status === 'COUNTED';
  return game.kind === 'forFun' && played ? 'PLAYED' : game.status;
}

/**
 * **Whether a game is on Home at `now`** — every live game, and an ended one until a day after its
 * hour. **The server sends only what Home draws** (#613): live games, games that ended less than a
 * day after their hour, and any game that needs the reader. So this rule is not the shelf: it
 * catches a card that crosses the line while Home is on screen, at that instant rather than at the
 * next read. **No card that needs the reader is dropped by it** (#658): a late *I was there* may be
 * said and confirmed until a day after the first half hour, which is half an hour before this
 * rule's day after the hour ends.
 *
 * **Measured from the hour's end, the one instant every ending has**: the wire dates no ending of a
 * booking, so a game called off days ahead stays until a day after the hour it was for — the player
 * who looks at Home that evening finds why there is no game — and a result settled later than a day
 * after the hour is not drawn, which is the Classic rail's own cost for a score counted by silence.
 */
export function onHome(
  game: Pick<HomeGame, 'status' | 'fillingAgain' | 'startsAt'>,
  now: number,
): boolean {
  if (!STATUS[stageOf(game)].ended) return true;
  const hourEnds = Date.parse(game.startsAt) + GAME_LENGTH_MS;
  return Number.isNaN(hourEnds) || now - hourEnds < ENDED_HOME_SHELF_LIFE_MS;
}

/**
 * **Marked *new* until opened** (the mechanics §11.4; the screens A8) — a game that filled since you
 * last looked, while its details have never been opened on this phone and its hour is still ahead.
 * A game past its hour is asking for a result or is over, and *new* is not what it is any more.
 *
 * `opened` is `undefined` while the phone is being read, and **nothing is new until it has said**:
 * a *new* tag flashing on every card for the frame before the list arrives is the noise the tag is
 * meant to cut through.
 */
export function isNew(
  game: Pick<HomeGame, 'bookingId' | 'status' | 'fillingAgain'>,
  opened: ReadonlySet<string> | undefined,
): boolean {
  return opened !== undefined && STATUS[stageOf(game)].fresh && !opened.has(game.bookingId);
}

/**
 * **The opened games, as the phone kept them** — a JSON list of booking ids, and nothing for a value
 * that is not one: a store this build cannot read is a store that kept nothing (ADR-0188 §4).
 */
export function openedFrom(saved: string | undefined): readonly string[] {
  if (saved === undefined) return [];
  try {
    const parsed: unknown = JSON.parse(saved);
    return Array.isArray(parsed) ? parsed.filter((id): id is string => typeof id === 'string') : [];
  } catch {
    return [];
  }
}

/**
 * **What the phone keeps once a game is opened** — that game, and every earlier one Home still
 * holds. The list is pruned to Home's own read, so it is never longer than the games a player has;
 * with no read of Home to prune by, nothing is dropped.
 */
export function openedToKeep(
  kept: readonly string[],
  opened: string,
  onHomeNow: readonly string[] | undefined,
): readonly string[] {
  const still = onHomeNow === undefined ? kept : kept.filter((id) => onHomeNow.includes(id));
  return still.includes(opened) ? still : [...still, opened];
}

// ---------------------------------------------------------------------------
// The details
// ---------------------------------------------------------------------------

/**
 * **Whether the game can have a room** — the Chat door's status half (the mechanics §14.2, §14.3);
 * the other half is the join finding the room, whose own life closes it as today (`STATUS`).
 */
export function chatIsOpen(game: Pick<HomeGame, 'status' | 'fillingAgain'>): boolean {
  return STATUS[stageOf(game)].room;
}

/**
 * **What *Leave the game* costs at `now`** (Q113, the mechanics §13) — the read's, folded on the
 * read's clock as the money row is: before the cut-off whether it lets a hold on the card go (while
 * the reader's share is held, and not while it is only checked, which holds nothing until its holding
 * time), and **after the cut-off from the instant the share is taken**, as the server will say once
 * read again. Nothing where there is no button.
 */
export function leavingAt(
  game: Pick<BookedGame, 'leaving' | 'money'>,
  now: number,
): Leaving | undefined {
  const { leaving } = game;
  if (leaving?.kind !== 'BEFORE_THE_CUT_OFF') return leaving;
  const share = shareAt(game.money, now)?.kind;
  return share === 'taken'
    ? { kind: 'AFTER_THE_CUT_OFF' }
    : { ...leaving, letsAHoldGo: share === 'held' };
}

/**
 * ***You complete it* on a rescue seen from outside** — the reader's yes takes the last open seat,
 * the card's own rule (A2.3); *You?* while more are open.
 */
export function completesTheRescue(game: Pick<BookedGame, 'rescue' | 'openSeats'>): boolean {
  return game.rescue !== undefined && game.openSeats === 1;
}

/**
 * **A full game gone back to filling, while it fills** (Q106) — whose way out is a game still
 * filling's, *Withdraw*. Not once it is called off: the read keeps the mark on that game, and
 * there is nothing left to withdraw from.
 */
export function isFillingAgain(game: Pick<HomeGame, 'status' | 'fillingAgain'>): boolean {
  return stageOf(game) === 'FILLING_AGAIN';
}

/** **Whether the court is given** — WHERE names it once the game is booked (A4.2). */
export function courtIsGiven(game: Pick<HomeGame, 'status' | 'fillingAgain'>): boolean {
  return STATUS[stageOf(game)].court;
}

/**
 * The result act the details lead to — today's game screen, which tells and agrees a result, and
 * says who turned up (#658).
 */
export type ResultAct = 'whos-here' | 'we-played' | 'add-score' | 'confirm' | 'who-was-there';

/**
 * **What the details offer once the hour has come** — in its **first half hour**, *Who's here*
 * (#658): the door a player at the court takes to say somebody isn't here yet, and an awaited
 * player to say they are. After it, *We played* while nobody has said, *Confirm the result* once a
 * score is on the table, and — while a late *I was there* waits on the reader, theirs to say or
 * somebody else's to confirm — *Say who was there*; or nothing. **A For fun game asks nothing**
 * (#656): its door is *Add the score*, which a player may take or leave. The acts are today's
 * screen's; the details are only the door to it.
 *
 * `atTheCourt` is whether the first half hour runs at the read's clock — `games`' rule
 * (`tapsAreOpen`), asked by the screen that holds the clock.
 */
export function resultActOf(
  game: Pick<HomeGame, 'status' | 'kind' | 'uncountedReason' | 'needsYou'>,
  { atTheCourt = false }: { readonly atTheCourt?: boolean } = {},
): ResultAct | undefined {
  if (game.status === 'NEEDS_RESULT') {
    if (atTheCourt) return 'whos-here';
    return game.kind === 'forFun' ? 'add-score' : 'we-played';
  }
  if (game.status === 'CONFIRM_THE_RESULT') return 'confirm';
  return attendanceNeedsYou(game) ? 'who-was-there' : undefined;
}

/**
 * **A late *I was there* waits on the reader** (#658) — the read's *needs you* on a game uncounted
 * because somebody didn't come: on an uncounted game nobody disagreed about, the late claim is the
 * only thing that needs anybody — the absent player's to say, or a courtmate's to confirm. Home's
 * line says it and the details' door opens on it; which of the two it is, the screen says.
 */
function attendanceNeedsYou(
  game: Pick<HomeGame, 'status' | 'uncountedReason' | 'needsYou'>,
): boolean {
  return game.status === 'UNCOUNTED' && game.uncountedReason === 'DIDNT_COME' && game.needsYou;
}
