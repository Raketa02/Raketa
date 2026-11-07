/**
 * **Every sentence the friends card and *Find a court* compose from a value** — the words
 * [§29.6](../../../../../docs/specs/matchmaking/the-words.md#296-the-friends-tab)
 * ([#757](https://github.com/Raketa02/Raketa/issues/757)). The fixed words are
 * `friendsCardCopy.ts`; the court line, the share and the *vs* line are the deck's
 * (`deckPresentation`), cited, because the card is the deck's card without its tiles.
 *
 * **A nickname is said whole** (ADR-0199 §1) and a list of them joined as a sentence joins one —
 * *ania.k*, *magda.p and ania.k* (§29's placeholders, `sentenceList`). **No refusal names
 * anybody** (Q6): the card never says which pair blocked each other, nor who has no level.
 */

import { sportInLine } from '@/features/onboarding/types';
import { dayDate } from '@/shared/date/calendarDay';
import { platformClock } from '@/shared/date/platformZone';
import { sentenceList } from '@/shared/formatting/sentenceList';
import { dayLabel } from '@/shared/vocabulary/availabilityPresentation';
import type { Sport } from '@/shared/vocabulary/sport';

import type { DeckCard } from '../domain/deck';
import type { CardPerson, FriendsCardRefusal, FriendsCourt } from '../domain/friendsCard';
import type { GameDay } from '../domain/when';

import { LINE_JOIN, clubName, gameDayWords } from './deckPresentation';
import { FRIENDS_CARD_COPY } from './friendsCardCopy';
import { eachWords } from './postingPresentation';

const COPY = FRIENDS_CARD_COPY;

/**
 * **Who is busy at a row's hour** — *Everybody free*, *ania.k busy*, *magda.p and ania.k busy*;
 * the reader first and as *you*: *You're busy*, *You and ania.k busy* (§29.6). A friend the
 * composer did not hand in is *Somebody*.
 */
export function busyLine(
  busy: readonly string[],
  readerId: string | undefined,
  people: readonly CardPerson[],
): string {
  if (busy.length === 0) return COPY.findACourt.everybodyFree;
  const you = readerId !== undefined && busy.includes(readerId);
  const names = busy
    .filter((id) => id !== readerId)
    .map((id) => people.find((one) => one.playerId === id)?.name ?? 'Somebody');
  if (names.length === 0) return COPY.findACourt.youAreBusy;
  return `${sentenceList(you ? ['You', ...names] : names)} busy`;
}

/**
 * **A day's heading** — the court block's own words, *Today*, *Tomorrow*, *Saturday*, and then
 * *Sat 26 Sep* from a week ahead, short as mocks 10–11 head it; drawn upper case by its style.
 */
export function courtDayHeading(when: GameDay): string {
  return when.kind === 'dated'
    ? `${dayLabel(when.weekday)} ${dayDate(when.day)}`
    : gameDayWords(when);
}

/**
 * ***Ogrody 33 is full at 10:00*** — another club's court, offered because the group's home club
 * has none free then (§29.6, ADR-0202 §7). Nothing for the home club's own.
 */
export function fullAtLine(
  court: Pick<FriendsCourt, 'startsAt' | 'homeClubFull'>,
  homeClub: DeckCard['club'],
): string | undefined {
  if (!court.homeClubFull) return undefined;
  return `${clubName({ club: homeClub })} is full at ${platformClock(court.startsAt) ?? ''}`;
}

/** *19:00* — a row's hour, mono. */
export function courtRowHour(court: Pick<FriendsCourt, 'startsAt'>): string {
  return platformClock(court.startsAt) ?? '';
}

/** *Bonarka Arena · Court 2* — a row's court. */
export function courtRowName(court: Pick<FriendsCourt, 'club' | 'courtName'>): string {
  return `${clubName(court)}${LINE_JOIN}${court.courtName}`;
}

/** *25 zł each* — a row's share, and the card's. */
export function courtShare(court: Pick<FriendsCourt, 'shareGrosze'>): string {
  return eachWords(court.shareGrosze);
}

/** **A row, spoken** — the hour, the court, who is free, the share, the marker, and *picked*. */
export function courtRowSpoken(
  court: FriendsCourt,
  busy: string,
  fullAt: string | undefined,
  picked: boolean,
): string {
  return [
    courtRowHour(court),
    courtRowName(court),
    busy,
    courtShare(court),
    ...(fullAt === undefined ? [] : [fullAt]),
    ...(picked ? [COPY.findACourt.picked] : []),
  ].join(', ');
}

/**
 * **What the card says in its place** — each refusal of the line-up (the mechanics §7.5), naming
 * nobody. `seats` is the court's: four in doubles, two in singles.
 */
const REFUSAL_LINES: Readonly<Record<FriendsCardRefusal, (sport: Sport, seats: number) => string>> =
  {
    cannot_play_together: (_sport, seats) =>
      seats > 2 ? COPY.refused.blockedDoubles : COPY.refused.blockedSingles,
    no_level: (sport) => `Somebody here has no ${sportInLine(sport)} level yet. Swap someone.`,
    not_a_friend: () => COPY.refused.notAFriend,
  };

export function refusalLine(refusal: FriendsCardRefusal, sport: Sport, seats: number): string {
  return REFUSAL_LINES[refusal](sport, seats);
}
