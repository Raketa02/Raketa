/**
 * **A friends game, sent and answered** — the send sheet's two ways to pay, an invitation on Home,
 * the sender's game in Your games and every seat's state on the details
 * ([#759](https://github.com/Rakieta02/Rakieta/issues/759), over #751's routes; ADR-0202 §5–§6; the
 * friends mechanics §8–§9, §11.2; the screens §6.1, §6.3, §8, §9) — and an empty seat's two
 * actions and the sender's two ways to leave
 * ([#760](https://github.com/Rakieta02/Rakieta/issues/760), over #752's; the mechanics §10–§11).
 *
 * Pure, and the server's folds are never re-derived: who is In, whose invitation waits and until
 * when, who may call it off, whether the game is whole — all the read's (`friends_game`, #751).
 * What is decided here is only how they are drawn, on the read's clock: **a seat still *waiting*
 * once its time has run out reads *didn't answer***, as the wire says it would at that instant
 * (`DIDNT_ANSWER`, *read off the clock whether or not the job has recorded it*), so a card or a line
 * never says *waiting* for a friend who can no longer answer.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import { peopleOn, type DeckCard, type DeckPerson } from './deck';
import type { YourPayment } from './fill';
import type { FriendsCardAsk, FriendsCourtPick } from './friendsCard';
import type { GameKind, LeavingKind, PayMode, SeatState } from './vocabulary';

/**
 * **A friend invited into an empty seat, still to answer** (#752, #760) — *piotr.s invited · 20 h
 * left*. The first to accept, or the first rescue, takes the seat.
 */
export interface SeatInvitation {
  readonly playerId: string;
  /** Absent for an account that can no longer be named. */
  readonly nickname?: string;
  /** When their 24 hours end — never past the cut-off, or the start for one made after it. */
  readonly until: string;
}

/**
 * **One seat of a friends game** — whose face it draws, where it stands, and while it waits, until
 * when; and on an **empty seat** (#752, #760), its name and what the reader may do with it. A field
 * the read leaves out reads as none: no name, nobody invited, neither action.
 */
export interface FriendsSeat {
  /**
   * Whose face it draws — the player In, the friend it is held for, or on an empty seat whose it
   * was; the reader's own, on a seat they are invited into.
   */
  readonly playerId: string;
  readonly state: SeatState;
  /** With `WAITING`: when the friend's 24 hours end — never past the cut-off. */
  readonly waitingUntil?: string;
  /** On an empty seat: the name *Invite a friend* and *Open to {group}* are sent under. */
  readonly seatOf?: string;
  /** Every friend invited into this empty seat and still to answer, as read. */
  readonly invitations?: readonly SeatInvitation[];
  /** *Invite a friend* is the reader's on this seat — the server's word (#752). */
  readonly canInvite?: boolean;
  /** *Open to {group}* is the reader's on this seat — the sender's, before the cut-off. */
  readonly canOpen?: boolean;
}

/**
 * **The empty seats** (the words §29.8): a no, a silence, a friend who left, and a seat open to the
 * group — every state but *In* and *waiting*.
 */
export function isEmptySeat(state: SeatState): boolean {
  return state !== 'IN' && state !== 'WAITING';
}

/**
 * **A friends game's own facts** (#751) — on every Home card and booked game's details of one, and
 * on each invitation in *FRIENDS GAME · n*.
 */
export interface FriendsGame {
  readonly senderId: string;
  /** *Tomek's game*, *Tomek paid the court* — absent for an account that can no longer be named. */
  readonly senderNickname?: string;
  readonly youAreTheSender: boolean;
  readonly payMode: PayMode;
  /** Every seat: the sender's first, then each friend's in the card's order. */
  readonly seats: readonly FriendsSeat[];
  /** The friends In beside the sender — *2 of 3 friends in*. */
  readonly friendsIn: number;
  /** The friends the sport seats beside the sender: 3 in doubles, 1 in singles. */
  readonly friendsSeated: number;
  /** The reader's own invitation, while it waits on them: when it ends. */
  readonly yourInvitationUntil?: string;
  /** *Call it off* is the reader's — the sender, before the club's cut-off and the hour. */
  readonly canCallOff: boolean;
}

/**
 * **One card in *FRIENDS GAME · n*** (friends 12): a friends game whose invitation waits on the
 * reader — *Tomek's game*, the clock, the four faces, *Saturday 10:00 · Ogrody 33 · Court 3 · Padel
 * · Competitive*, and the two answers.
 */
export interface FriendsGameInvitation {
  readonly bookingId: string;
  readonly groupId: string;
  readonly sport: Sport;
  readonly kind: GameKind;
  readonly startsAt: string;
  readonly club: DeckCard['club'];
  readonly courtName: string;
  readonly indoor: boolean;
  /** Each seat's share — *Accept and pay 25 zł* with *Split*. */
  readonly shareGrosze: number;
  /** Every seat the card drew, the reader's side first and the reader first on it. */
  readonly sides: DeckCard['sides'];
  readonly friendsGame: FriendsGame;
}

/**
 * **A friends game as a court draws it** — its facts, and the sides its faces stand on: a Home
 * card, a booked game's details, an invitation. The seats are named off the sides.
 */
export interface FriendsGameOnCourt {
  readonly friendsGame?: FriendsGame;
  readonly sides: DeckCard['sides'];
}

// ---------------------------------------------------------------------------
// The writes
// ---------------------------------------------------------------------------

/**
 * **What a send asks** — the card as it was read (the line-up, the sides sent, the court it names)
 * and how to pay; with `bookingId`, the send again after its payments were confirmed.
 */
export interface FriendsGameSend {
  readonly sport: Sport;
  readonly ask: FriendsCardAsk;
  /** The court the card names — its own, or the one picked in *Find a court*. */
  readonly court: FriendsCourtPick;
  readonly payMode: PayMode;
  readonly bookingId?: string;
}

/** **What a send did** — the court booked, or nothing booked and the payments to confirm. */
export interface FriendsGameSent {
  readonly bookingId: string;
  readonly booked: boolean;
  readonly yourPayments: readonly YourPayment[];
}

/** **What an *Accept* did** — the reader In (and the game whole), or their share refused. */
export interface FriendsGameAccepted {
  readonly bookingId: string;
  readonly accepted: boolean;
  /** Every seat is taken now — *It's a game!*. */
  readonly whole: boolean;
  readonly yourPayment?: YourPayment;
}

// ---------------------------------------------------------------------------
// The seats, on the read's clock
// ---------------------------------------------------------------------------

/**
 * **A seat's state at `now`** — the read's, but a seat still waiting once its time is over reads
 * *didn't answer*, as the server says it at that instant.
 */
export function seatStateAt(seat: FriendsSeat, now: number): SeatState {
  if (seat.state !== 'WAITING' || seat.waitingUntil === undefined) return seat.state;
  return Date.parse(seat.waitingUntil) > now ? 'WAITING' : 'DIDNT_ANSWER';
}

/** **Whether the reader's own invitation still waits on them at `now`.** */
export function invitationWaits(game: Pick<FriendsGame, 'yourInvitationUntil'>, now: number) {
  const until = game.yourInvitationUntil;
  return until !== undefined && Date.parse(until) > now;
}

/** **Whether any seat's clause runs out by itself** — a *waiting* that turns *didn't answer*. */
export function seatsCanRunOut(game: Pick<FriendsGame, 'seats' | 'yourInvitationUntil'>) {
  return (
    game.yourInvitationUntil !== undefined ||
    game.seats.some((seat) => seat.state === 'WAITING' && seat.waitingUntil !== undefined)
  );
}

/**
 * ***2 of 3 friends in · waiting for Ania*** (the words §29.8; the screens §6.3) — the sender's game
 * in Your games, while a seat is not In: how many friends are In of how many the sport seats, who
 * the game still waits for (named off their seat on the court), and how many seats are empty — a
 * no, a silence, a friend who left. **Nothing once every seat is In**: the ordinary row, *Booked*.
 * Nothing either for a friend's own card — the line is the sender's (§29.8: *the sender's game*).
 */
export interface SeatsLine {
  readonly friendsIn: number;
  readonly friendsSeated: number;
  /** The friends still to answer, off the court, in the seats' order. */
  readonly waitingFor: readonly DeckPerson[];
  readonly empty: number;
}

export function seatsLineOf(game: FriendsGameOnCourt, now: number): SeatsLine | undefined {
  const friends = game.friendsGame;
  if (friends === undefined || !friends.youAreTheSender) return undefined;
  const shown = seatsShown(game, now);
  if (shown.every(({ state }) => state === 'IN')) return undefined;
  return {
    // The read's own count: who is In moves only on the server, never on the clock.
    friendsIn: friends.friendsIn,
    friendsSeated: friends.friendsSeated,
    waitingFor: shown.filter(({ state }) => state === 'WAITING').map(({ person }) => person),
    empty: shown.filter(({ state }) => isEmptySeat(state)).length,
  };
}

/**
 * **One seat on the details** (the screens §9): the person, from the court, and their state at
 * `now` — the sender's first, then each friend's in the card's order — and on an empty seat its
 * name, the invitations still waiting at `now`, and the two the server lets the reader press.
 */
export interface SeatShown {
  readonly person: DeckPerson;
  readonly state: SeatState;
  readonly waitingUntil?: string;
  readonly seatOf?: string;
  /** Still to answer at `now` — one whose 24 hours ended on the read's clock is gone. */
  readonly invitations: readonly SeatInvitation[];
  readonly canInvite: boolean;
  readonly canOpen: boolean;
}

export function seatsShown(game: FriendsGameOnCourt, now: number): readonly SeatShown[] {
  const friends = game.friendsGame;
  if (friends === undefined) return [];
  const people = peopleOn(game);
  return friends.seats.map((seat) => {
    const state = seatStateAt(seat, now);
    const person = people.find((one) => one.playerId === seat.playerId) ?? {
      playerId: seat.playerId,
      isYou: false,
      isIn: false,
    };
    return {
      person,
      state,
      ...(state === 'WAITING' && seat.waitingUntil !== undefined
        ? { waitingUntil: seat.waitingUntil }
        : {}),
      ...(seat.seatOf === undefined ? {} : { seatOf: seat.seatOf }),
      invitations: (seat.invitations ?? []).filter(({ until }) => Date.parse(until) > now),
      canInvite: seat.canInvite === true,
      canOpen: seat.canOpen === true,
    };
  });
}

// ---------------------------------------------------------------------------
// An empty seat, and the sender leaving
// ---------------------------------------------------------------------------

/**
 * **What the reader may do with a seat at `now`** (the screens §9; the mechanics §10.1, §10.3, §11.3):
 *
 * - `invite` — ***Invite a friend***, anyone In, on an empty seat, before the cut-off or after it,
 *   **until the hour** — read off the clock, as the server would refuse it then;
 * - `open` — ***Open to {group}***, the sender's, on an empty seat not yet open, **before the
 *   cut-off**: at that instant every seat still empty opens on its own.
 *
 * Whose each is stays the server's (`canInvite`, `canOpen`); this only takes them away at the
 * instants the read's clock passes. A seat the read does not name (`seatOf`) offers neither — one
 * whose *waiting* ran out on the clock, until the next read names it.
 */
export interface SeatActions {
  readonly invite: boolean;
  readonly open: boolean;
}

export function seatActionsAt(
  seat: Pick<SeatShown, 'state' | 'seatOf' | 'canInvite' | 'canOpen'>,
  at: { readonly now: number; readonly cutOff: string | undefined; readonly startsAt: string },
): SeatActions {
  if (!isEmptySeat(seat.state) || seat.seatOf === undefined) {
    return { invite: false, open: false };
  }
  const beforeTheCutOff = at.cutOff !== undefined && Date.parse(at.cutOff) > at.now;
  return {
    invite: seat.canInvite && Date.parse(at.startsAt) > at.now,
    open: seat.canOpen && seat.state !== 'SEAT_OPEN' && beforeTheCutOff,
  };
}

/**
 * **Whether the reader may open some seat of the game to its group** — the server's word on any
 * seat. Only then is the group's name read, for *Open to {group}*.
 */
export function anySeatToOpen(game: Pick<FriendsGameOnCourt, 'friendsGame'>): boolean {
  return game.friendsGame?.seats.some((seat) => seat.canOpen === true) ?? false;
}

/**
 * **What the picker with one seat needs** (#760): the game's group and sport, whose friends it
 * lists; the hour, which a refusal may name; and **everybody already on the game**, whom it leaves
 * out — the faces the court draws, whoever each seat was held for (a no, a silence, a friend who
 * left), and every friend invited into a seat. The server refuses each of them
 * `already_on_the_game`; leaving them out spares the refusal.
 */
export interface SeatToInvite {
  readonly bookingId: string;
  readonly seatOf: string;
  readonly groupId: string;
  readonly sport: Sport;
  readonly startsAt: string;
  readonly onTheGame: readonly string[];
}

export function seatToInviteOf(
  game: FriendsGameOnCourt & {
    readonly bookingId: string;
    readonly groupId: string;
    readonly sport: Sport;
    readonly startsAt: string;
  },
  seatOf: string,
): SeatToInvite {
  const seats = game.friendsGame?.seats ?? [];
  const everybody = [
    ...peopleOn(game).map((person) => person.playerId),
    ...seats.map((seat) => seat.playerId),
    ...seats.flatMap((seat) => (seat.invitations ?? []).map((one) => one.playerId)),
  ];
  return {
    bookingId: game.bookingId,
    seatOf,
    groupId: game.groupId,
    sport: game.sport,
    startsAt: game.startsAt,
    onTheGame: [...new Set(everybody)],
  };
}

/**
 * **The pay mode the sender's two-way leave is worded in** — before the cut-off (the mechanics
 * §11.2; the screens §9) their sheet offers two ways, *Call it off for everyone* and *Leave · the
 * others play on*, the second's line by the pay mode. Nothing after the cut-off, where the sender is any late leaver (§11.3), for a
 * friend (the ordinary sheet, §11.1), and while *Call it off* is not the reader's — the server's
 * word for both.
 */
export function twoWayLeaveIn(
  game: Pick<FriendsGameOnCourt, 'friendsGame'>,
  leaving: LeavingKind | undefined,
): PayMode | undefined {
  const friends = game.friendsGame;
  if (friends === undefined || !friends.youAreTheSender || !friends.canCallOff) return undefined;
  return leaving === 'BEFORE_THE_CUT_OFF' ? friends.payMode : undefined;
}

// ---------------------------------------------------------------------------
// The invitation's faces
// ---------------------------------------------------------------------------

/**
 * **One face on an invitation** (friends 12) — ✓ on those In, faded on those still to answer, the
 * reader drawn as *You* and never faded: the card is theirs to answer.
 */
export interface InvitationFace {
  readonly person: DeckPerson;
  readonly isIn: boolean;
  readonly faded: boolean;
}

/**
 * **The four faces, as friends 12 orders them** — the sender first, then each friend in the card's
 * order, and the reader last: *Karol ✓ · Zofia ✓ · Ania · You*. A seat the court does not draw is
 * left off (a read caught mid-move).
 */
export function invitationFaces(
  invitation: FriendsGameOnCourt,
  now: number,
): readonly InvitationFace[] {
  const shown = seatsShown(invitation, now).map(({ person, state }) => ({
    person,
    isIn: state === 'IN',
    faded: !person.isYou && state !== 'IN',
  }));
  return [...shown.filter((face) => !face.person.isYou), ...shown.filter((f) => f.person.isYou)];
}

// ---------------------------------------------------------------------------
// The money
// ---------------------------------------------------------------------------

/**
 * **The court's price** — every seat's share, the sport's seats: *100 zł* in padel at 25 zł a seat,
 * *50 zł* in singles. What *Split* holds on the sender's card until the cut-off, and what *Whole
 * court* pays.
 */
export function courtPrice(shareGrosze: number, seats: number): number {
  return shareGrosze * seats;
}

/** **What the sender's button charges** — their share with *Split*, the court with *Whole court*. */
export function sendCharge(payMode: PayMode, shareGrosze: number, seats: number): number {
  return payMode === 'SPLIT_THE_COST' ? shareGrosze : courtPrice(shareGrosze, seats);
}

/**
 * **What a send refused for its money needs next** (#751: *a refused card books nothing*) — read
 * off the payments it names, in the order they must be met:
 *
 * - `setUp` — no method at the hold: save one, and send again;
 * - `termsAgain` — the card's brand changed: its terms are accepted again on You › Payments;
 * - `confirm` — each payment the bank refused or wants confirmed, **one after another**, then the
 *   send again under the same booking, which takes the holds confirmed;
 * - `sendAgain` — nothing named (an older server): nothing to confirm, so the send goes again,
 *   under the same booking, at the player's next press.
 */
export type SendPayments =
  | { readonly kind: 'setUp' }
  | { readonly kind: 'termsAgain' }
  | { readonly kind: 'confirm'; readonly payments: readonly YourPayment[] }
  | { readonly kind: 'sendAgain' };

export function sendPaymentsOf(payments: readonly YourPayment[]): SendPayments {
  if (payments.some((one) => one.refusal === 'NO_METHOD')) return { kind: 'setUp' };
  if (payments.some((one) => one.refusal === 'TERMS_NEEDED')) return { kind: 'termsAgain' };
  const toConfirm = payments.filter(
    (one) => one.refusal === 'AUTHENTICATION_REQUIRED' || one.refusal === 'DECLINED',
  );
  return toConfirm.length === 0 ? { kind: 'sendAgain' } : { kind: 'confirm', payments: toConfirm };
}

/**
 * **What an *Accept* refused for its money needs** (#751) — the bank wants the reader present, or
 * declined the card: the confirmation in the app, which is the accept again; no method: the setup,
 * then *Accept* again; the card's brand changed: its terms again, on You › Payments.
 */
export type AcceptPayment = 'confirm' | 'setUp' | 'termsAgain';

export function acceptPaymentOf(payment: Pick<YourPayment, 'refusal'>): AcceptPayment {
  switch (payment.refusal) {
    case 'AUTHENTICATION_REQUIRED':
    case 'DECLINED':
      return 'confirm';
    case 'NO_METHOD':
      return 'setUp';
    case 'TERMS_NEEDED':
      return 'termsAgain';
  }
}

// ---------------------------------------------------------------------------
// The refusals
// ---------------------------------------------------------------------------

/**
 * **What a refused send does with the sheet** (the screens §8; the mechanics §7.5):
 *
 * - `setUp` — no saved method: the setup, then the send again;
 * - `reread` — the court went (`court_just_taken`), or somebody seated no longer may be
 *   (`not_a_friend`, `no_level`, `cannot_play_together`): the sheet closes and the card is read
 *   again — with the court's sentence, or with its own refusal in the card's place;
 * - `courtGone` — the club no longer sells the hour picked: the sheet closes and the card proposes
 *   another, as a gone court does on the card itself;
 * - `say` — the sentence in the sheet, the order still there: two games waiting, the sender's
 *   hour or week, anything else.
 */
export type SendRefusal = 'setUp' | 'reread' | 'courtGone' | 'say';

export function sendRefusalOf(code: string | undefined): SendRefusal {
  switch (code) {
    case 'payment_method_required':
      return 'setUp';
    case 'court_just_taken':
    case 'not_a_friend':
    case 'no_level':
    case 'cannot_play_together':
      return 'reread';
    case 'court_hour_not_for_sale':
      return 'courtGone';
    default:
      return 'say';
  }
}

/**
 * **What a refused answer does with the invitation** (the screens §6.1):
 *
 * - `setUp` — *Split* with no saved method: the setup, then *Accept* again;
 * - `gone` — the invitation no longer waits, the game is off or under way, or it was never theirs:
 *   Home is read again and the card leaves, with the sentence;
 * - `say` — on the card, which stays: a full week, a game at that hour, anything else.
 */
export type AnswerRefusal = 'setUp' | 'gone' | 'say';

export function answerRefusalOf(code: string | undefined): AnswerRefusal {
  switch (code) {
    case 'payment_method_required':
      return 'setUp';
    case 'invitation_not_waiting':
    case 'booking_is_called_off':
    case 'game_has_started':
    case 'booking_not_found':
      return 'gone';
    default:
      return 'say';
  }
}

/**
 * **What a refused *Invite a friend* or *Open to {group}* does** (#752's 409s):
 *
 * - `gone` — the seat is no longer there to fill: taken, the game off or under way, no longer the
 *   reader's, or — opening — the cut-off came and opened it already. The game is read again, and
 *   the sentence said;
 * - `say` — the sentence where the act was pressed, the act still there: the friend picked is on the
 *   game already, no friend any more, has no Level, can't play with somebody on it, plays then, or
 *   has a full week.
 */
export type SeatWriteRefusal = 'gone' | 'say';

export function seatWriteRefusalOf(code: string | undefined): SeatWriteRefusal {
  switch (code) {
    case 'seat_just_taken':
    case 'booking_is_called_off':
    case 'game_has_started':
    case 'booking_not_found':
    case 'cut_off_has_passed':
      return 'gone';
    default:
      return 'say';
  }
}

/** *Your week is full: 3 games* — the number the refusal names, when it names one. */
export function gamesPerWeekOf(details: Readonly<Record<string, unknown>> | undefined) {
  const games = details?.games_per_week;
  return typeof games === 'number' && Number.isInteger(games) && games > 0 ? games : undefined;
}

/** *2 friends games waiting* — the cap the refusal names, or the mechanics' 2. */
export function waitingCapOf(details: Readonly<Record<string, unknown>> | undefined): number {
  const cap = details?.cap;
  return typeof cap === 'number' && Number.isInteger(cap) && cap > 0 ? cap : FRIENDS_GAMES_WAITING;
}

/** **At most 2 friends games waiting for answers** per sender (Q34; the mechanics §8.4). */
export const FRIENDS_GAMES_WAITING = 2;
