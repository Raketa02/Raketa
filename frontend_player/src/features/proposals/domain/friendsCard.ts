/**
 * **The friends card, and *Find a court*** — a fixed line-up's card on a group's Friends tab, and
 * every court it could take ([#757](https://github.com/Raketa02/Raketa/issues/757), over #750's
 * reads; the friends mechanics §7.4–§7.6, the screens §7.2–§7.3).
 *
 * Pure, and as little as the deck's: **the sides, the forecast or the Social vibe, the overlap, the
 * court proposed and who is busy are the read's** (`ReadFriendsLineUp`, #750; the vibe #834), and
 * nothing here re-derives one. Which of the two numbers is drawn is the deck's `headlineOf`. What
 * is decided here is only how they are drawn: which step of the tint a row wears, which day it is
 * listed under, which row is the card's own, and the people the deck's own drawing is handed.
 *
 * **The card names its people by id**: every face on it is a friend the picker already drew, so the
 * composer hands them in (`CardPerson`) — `proposals` imports nothing of `friends`.
 */

import { platformDay } from '@/shared/date/platformZone';

import type { DeckCard, DeckPerson, Overlap } from './deck';
import type { GameKind } from './vocabulary';
import { calendarDayOf, type GameDay } from './when';

/** A court picked in *Find a court* — sent back as `court_id` and `starts_at`. */
export interface FriendsCourtPick {
  readonly courtId: string;
  readonly startsAt: string;
}

/** **What the card is read for** — the composer's line-up, in the order it holds it. */
export interface FriendsCardAsk {
  readonly kind: GameKind;
  /** Beside the reader: three in doubles, one in singles. */
  readonly friendIds: readonly string[];
  /** After a swap, the friend beside the reader; absent, the evenest sides. */
  readonly partnerId?: string;
  /** Picked in *Find a court*; absent, the one the card proposes. */
  readonly court?: FriendsCourtPick;
}

/** **One court the line-up could take** — a row of *Find a court*, and the card's court panel. */
export interface FriendsCourt {
  readonly startsAt: string;
  readonly club: DeckCard['club'];
  readonly courtId: string;
  /** What the club calls it — *Court 3*. */
  readonly courtName: string;
  readonly indoor: boolean;
  /** *25 zł each*. */
  readonly shareGrosze: number;
  /** Another club's, offered because the group's home club is full then: *Ogrody 33 is full at 10:00*. */
  readonly homeClubFull: boolean;
  /** Who of the line-up is not free for the whole hour — outside their weekly hours — in its order. */
  readonly busy: readonly string[];
}

/** **The friends card** — the deck's card without its tiles. */
export interface FriendsCard {
  /** The kind it was read for — which number it leads with (the deck's `headlineOf`). */
  readonly kind: GameKind;
  /** The group's home club — the name in *… is full at 10:00*. */
  readonly homeClub: DeckCard['club'];
  /** The evenest sides, or the ones sent: ids, the reader first on `yours`. */
  readonly sides: { readonly yours: readonly string[]; readonly theirs: readonly string[] };
  /**
   * *87% · Very even* — absent where it could not be read. The server sends none on For fun, where
   * the sides are still the evenest but the card says its Social vibe instead (ADR-0207 §5).
   */
  readonly forecast?: { readonly pct: number; readonly provisional: boolean };
  /**
   * **The line-up's Social vibe, on For fun** (#834): everybody seated, however they stand, so a
   * swap never moves it. Absent on a competitive card, and where nobody seated holds a tag.
   */
  readonly vibe?: { readonly pct: number };
  /** Absent: no court is free in the next 14 days — and then no overlap either. */
  readonly court?: FriendsCourt;
  readonly overlap?: Overlap;
  /**
   * **The club's cut-off for the court's hour** (#759) — *We hold 100 zł on your card until Fri
   * 10:00*, on the send sheet. Absent with no court.
   */
  readonly cutOff?: string;
}

/** *Find a court* for a line-up: every court it could take, soonest first. */
export interface FriendsCourts {
  readonly homeClub: DeckCard['club'];
  readonly courts: readonly FriendsCourt[];
}

/**
 * **The card's three refusals of a line-up** (the mechanics §7.5), each naming nobody: two of them
 * blocked each other, somebody has no Level in the sport, somebody is no longer a friend.
 */
export const FRIENDS_CARD_REFUSALS = ['cannot_play_together', 'no_level', 'not_a_friend'] as const;

export type FriendsCardRefusal = (typeof FRIENDS_CARD_REFUSALS)[number];

/** The refusal a read's code is, or nothing for any other answer. */
export function refusalOf(code: string | undefined): FriendsCardRefusal | undefined {
  return FRIENDS_CARD_REFUSALS.find((refusal) => refusal === code);
}

/**
 * **A court picked that the read no longer lists** (`court_hour_not_for_sale`): taken, past its
 * book-by, or an hour one of them now has a game at. It is let go and the card proposes one.
 */
export function isCourtGone(code: string | undefined): boolean {
  return code === 'court_hour_not_for_sale';
}

/** A friend on the card, as the composer read them: their whole nickname and Level in the sport. */
export interface CardPerson {
  readonly playerId: string;
  readonly name: string;
  readonly level?: number;
}

/**
 * **A row's tint, as a step** — `0`, brightest, with everybody free; one step dimmer for each one
 * busy, down to `3` (the friends README note 5: brightest for all four, then three, two, one). A
 * row where nobody is free stays at the dimmest: the words under it say who.
 */
export type FreeStep = 0 | 1 | 2 | 3;

export function freeStepOf(court: Pick<FriendsCourt, 'busy'>): FreeStep {
  const busy = court.busy.length;
  if (busy <= 0) return 0;
  if (busy === 1) return 1;
  return busy === 2 ? 2 : 3;
}

/** One day of *Find a court*: how it is headed, and its rows. */
export interface CourtDay {
  /** The calendar day, on the platform's clock. */
  readonly day: string;
  readonly when: GameDay;
  readonly courts: readonly FriendsCourt[];
}

/**
 * **The rows by day**, in the order served — soonest first, the home club first within an hour —
 * headed *Tomorrow*, *Saturday*, *Sat 26 Sep* against the instant the list was read. A row whose
 * day cannot be read is left off: it could be headed under no day.
 */
export function courtsByDay(courts: readonly FriendsCourt[], readAt: number): readonly CourtDay[] {
  const days: { day: string; when: GameDay; courts: FriendsCourt[] }[] = [];
  for (const court of courts) {
    const day = platformDay(court.startsAt);
    const when = day === undefined ? undefined : calendarDayOf(day, readAt);
    if (day === undefined || when === undefined) continue;
    const last = days.at(-1);
    if (last !== undefined && last.day === day) last.courts.push(court);
    else days.push({ day, when, courts: [court] });
  }
  return days;
}

/** **The row the card shows** — its court at its hour. */
export function isShownCourt(
  court: Pick<FriendsCourt, 'courtId' | 'startsAt'>,
  shown: Pick<FriendsCourt, 'courtId' | 'startsAt'> | undefined,
): boolean {
  return (
    shown !== undefined && court.courtId === shown.courtId && court.startsAt === shown.startsAt
  );
}

/**
 * **The card's sides as the deck's drawing takes them** — the reader, who stands first on their own
 * side (the read's rule), marked *You* with their Level; each friend named with theirs; nobody In,
 * since nothing has been sent. Somebody the composer did not hand in is drawn unnamed, as the deck
 * draws an account it can no longer name.
 */
export function sidesOn(
  card: Pick<FriendsCard, 'sides'>,
  people: readonly CardPerson[],
  yourLevel: number | undefined,
): DeckCard['sides'] {
  const friend = (playerId: string): DeckPerson => {
    const known = people.find((one) => one.playerId === playerId);
    return {
      playerId,
      isYou: false,
      isIn: false,
      ...(known === undefined ? {} : { name: known.name }),
      ...(known?.level === undefined ? {} : { level: known.level }),
    };
  };
  const [you, ...partner] = card.sides.yours;
  const reader: readonly DeckPerson[] =
    you === undefined
      ? []
      : [
          {
            playerId: you,
            isYou: true,
            isIn: false,
            ...(yourLevel === undefined ? {} : { level: yourLevel }),
          },
        ];
  return { yours: [...reader, ...partner.map(friend)], theirs: card.sides.theirs.map(friend) };
}
