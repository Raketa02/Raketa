/**
 * **The game being built on a group's Friends tab** — who sits where beside the reader, and the
 * court picked for them ([#757](https://github.com/Rakieta02/Rakieta/issues/757); the friends
 * mechanics §7.1–§7.4, the screens §7.1).
 *
 * Pure: the seats as the player arranged them, and the four things they do to them — **Done**
 * seats the picks, a **swap** trades two faces, the **×** empties a seat, and *Find a court* picks
 * a court. Nothing here decides the sides: the card's read does (`evenest`), and the court draws
 * what it answered (`shownSeats`).
 *
 * ## The seats beside the reader
 *
 * The court's seat order with the reader's own left off — the reader always stands in the first,
 * on *your side* (the card's `sides.yours` starts with them). So in doubles the first seat here is
 * **the partner**, and the two after it are **their side**; in singles the one seat is theirs.
 * `null` is a seat a friend could fill.
 *
 * ## Done asks the card for the evenest sides
 *
 * Right after Done the line-up is `evenest`: the picks sit in the order picked, and the card is
 * read **without a partner**, so the server stands them in the evenest sides — and the court
 * redraws to the sides it answered, so **the court and the card always name the same sides**
 * (the friends README, note 3). The moment the player acts on the court — a swap, a ×, a court or
 * a kind picked — what the court shows becomes the player's own arrangement (`pinned`), so a
 * re-read never moves a face the player is looking at. That is the one place a read's answer
 * becomes a choice, and it is the player's act that makes it one.
 */

import type { FriendsCardAsk, FriendsCourtPick } from '@/features/proposals/types';

/** A seat beside the reader — a friend's id, or nobody. */
export type FriendSeat = string | null;

export interface FriendsLineUp {
  /** Beside the reader, in seat order: doubles the partner, then their side; singles theirs. */
  readonly seats: readonly FriendSeat[];
  /** Done just seated them: the card stands them in the evenest sides, and the court follows. */
  readonly evenest: boolean;
  /** Picked in *Find a court* — absent, the card proposes its own. */
  readonly court?: FriendsCourtPick;
}

/** The sides a card was read for — ids, the reader first on theirs. */
export interface CardSides {
  readonly yours: readonly string[];
  readonly theirs: readonly string[];
}

/** What the card is read with, but its kind: everybody seated, the partner, the court picked. */
export type LineUpAsk = Omit<FriendsCardAsk, 'kind'>;

/** Nobody seated yet: `seats` is how many stand beside the reader — three, or one. */
export function emptyLineUp(seats: number): FriendsLineUp {
  return { seats: Array.from({ length: seats }, () => null), evenest: false };
}

/** Every face on the court, in seat order. */
export function seatedOf(seats: readonly FriendSeat[]): readonly string[] {
  return seats.filter((seat): seat is string => seat !== null);
}

/** How many seats a friend could still fill — *Seat 1 more friend*. */
export function openSeatsOf(seats: readonly FriendSeat[]): number {
  return seats.filter((seat) => seat === null).length;
}

function sameFriends(a: readonly FriendSeat[], b: readonly string[]): boolean {
  const seated = seatedOf(a);
  return seated.length === b.length && seated.every((id) => b.includes(id));
}

/** The court picked, kept — or left off when `keep` is false. */
function courtIf(lineUp: FriendsLineUp, keep: boolean): Pick<FriendsLineUp, 'court'> {
  return keep && lineUp.court !== undefined ? { court: lineUp.court } : {};
}

/**
 * **Done** — the picks, seated. A friend still picked keeps their seat; the others fill the empty
 * seats in the order picked, and whoever was unpicked leaves theirs. The card is then asked for the
 * evenest sides. A court picked for these same friends stays picked; for others it is dropped.
 */
export function seatPicks(lineUp: FriendsLineUp, picks: readonly string[]): FriendsLineUp {
  const kept = lineUp.seats.map((seat) => (seat !== null && picks.includes(seat) ? seat : null));
  const newcomers = picks.filter((pick) => !kept.includes(pick));
  const seats = kept.map((seat) => seat ?? newcomers.shift() ?? null);
  return { seats, evenest: true, ...courtIf(lineUp, sameFriends(lineUp.seats, seatedOf(seats))) };
}

/**
 * **The seats as the court draws them** — the card's evenest sides once it has answered for these
 * friends, the partner first and then theirs; otherwise as they stand. A singles court has one
 * way to stand.
 */
export function shownSeats(
  lineUp: FriendsLineUp,
  sides: CardSides | undefined,
): readonly FriendSeat[] {
  if (!lineUp.evenest || sides === undefined || lineUp.seats.length < 2) return lineUp.seats;
  const answered = [...sides.yours.slice(1), ...sides.theirs];
  const forThem = answered.length === lineUp.seats.length && sameFriends(lineUp.seats, answered);
  return forThem ? answered : lineUp.seats;
}

/**
 * **A tick in the picker** — a friend picked, or unpicked if they were; nobody more once the seats
 * beside the reader are full (three in doubles, one in singles).
 */
export function togglePick(
  picks: readonly string[],
  playerId: string,
  seats: number,
): readonly string[] {
  if (picks.includes(playerId)) return picks.filter((one) => one !== playerId);
  return picks.length >= seats ? picks : [...picks, playerId];
}

/** **What the court shows, made the player's own** — the sides stay as drawn from here on. */
export function pinned(lineUp: FriendsLineUp, shown: readonly FriendSeat[]): FriendsLineUp {
  return { seats: [...shown], evenest: false, ...courtIf(lineUp, true) };
}

/**
 * **Another kind chosen** keeps the sides the court shows: the card is asked again, and a face the
 * player is looking at does not move. Nothing changes while a seat is open, or once the sides are
 * the player's already.
 */
export function keptAsShown(lineUp: FriendsLineUp, shown: readonly FriendSeat[]): FriendsLineUp {
  return lineUp.evenest && openSeatsOf(shown) === 0 ? pinned(lineUp, shown) : lineUp;
}

/** **A court picked in *Find a court*** — on the line-up, the sides kept as the court shows them. */
export function withCourt(
  lineUp: FriendsLineUp,
  shown: readonly FriendSeat[],
  court: FriendsCourtPick,
): FriendsLineUp {
  return { ...pinned(lineUp, shown), court };
}

/** **A court picked that is no longer for sale** — let go, so the card proposes one. */
export function withoutCourt(lineUp: FriendsLineUp): FriendsLineUp {
  return { seats: lineUp.seats, evenest: lineUp.evenest };
}

/**
 * **A swap** — the first face tapped and the second trade seats. The same friends, standing
 * differently, so a court picked for them stays picked.
 */
export function swapSeats(
  lineUp: FriendsLineUp,
  shown: readonly FriendSeat[],
  first: string,
  second: string,
): FriendsLineUp {
  const seats = shown.map((seat) => {
    if (!shown.includes(first) || !shown.includes(second)) return seat;
    if (seat === first) return second;
    return seat === second ? first : seat;
  });
  return pinned(lineUp, seats);
}

/** **The ×** — that face's seat emptied. Different friends now: the court picked goes too. */
export function takeOff(
  lineUp: FriendsLineUp,
  shown: readonly FriendSeat[],
  playerId: string,
): FriendsLineUp {
  return { seats: shown.map((seat) => (seat === playerId ? null : seat)), evenest: false };
}

/**
 * **A friend who is no longer one leaves an empty seat** (the mechanics §7.5, `not_a_friend`) —
 * read off the friends list, once it is read. Unchanged, the same line-up comes back.
 */
export function withoutStrangers(
  lineUp: FriendsLineUp,
  friends: ReadonlySet<string> | undefined,
): FriendsLineUp {
  if (friends === undefined || seatedOf(lineUp.seats).every((id) => friends.has(id))) {
    return lineUp;
  }
  return {
    seats: lineUp.seats.map((seat) => (seat !== null && friends.has(seat) ? seat : null)),
    evenest: lineUp.evenest,
  };
}

/**
 * **What the card is read with** — nothing until every seat is filled (no card, Q16). The friends
 * go in the order they are held, which a read never moves, so the card is not asked again because
 * it answered. A partner is named once the player stood the sides, and never in singles.
 */
export function cardAskOf(lineUp: FriendsLineUp): LineUpAsk | undefined {
  if (openSeatsOf(lineUp.seats) > 0) return undefined;
  const friendIds = seatedOf(lineUp.seats);
  const [partner] = friendIds;
  return {
    friendIds,
    ...(lineUp.evenest || friendIds.length < 2 || partner === undefined
      ? {}
      : { partnerId: partner }),
    ...courtIf(lineUp, true),
  };
}
