/**
 * **The proposals feature's query keys** — one factory, so every read and every write names the
 * same entries.
 *
 * Under one group, the deck for a sport and a kind: an answer, a withdraw and a declared intent
 * re-read the group's root, which is every sport and both kinds — a yes moves the badge, which
 * spans the segments, and a declaration decides which segments there are. **Every group's decks
 * sit under one root too**, because Games & money bounds them all: a changed limit re-reads it.
 *
 * Beside the decks, the player's own two reads (#554): their live yeses, which every answer and
 * withdraw changes, and Games & money. And Home's two (#556): the booked games, which a fill
 * changes, and one booked game in detail.
 */

import type { Sport } from '@/shared/vocabulary/sport';

import type { FriendsCardAsk } from '../domain/friendsCard';
import type { PostingAsk, PostingWeek } from '../domain/posting';
import type { DayRange, GameKind } from '../domain/vocabulary';

export const proposalKeys = {
  all: ['proposals'] as const,
  /** Every deck read, of every group — the root a changed limit re-reads. */
  decks: () => [...proposalKeys.all, 'deck'] as const,
  /** Every deck read for one group — the root an answer re-reads. */
  group: (groupId: string) => [...proposalKeys.decks(), groupId] as const,
  /** One group's deck, for one sport and one kind. */
  deck: (groupId: string, sport: Sport, kind: GameKind) =>
    [...proposalKeys.group(groupId), sport, kind] as const,
  /**
   * **A mutation key**: an answer to a card — the deck's, the details' and the fill's booked yes —
   * so the deck can tell which cards have an answer on its way (`useAnswersOnTheirWay`).
   */
  answers: () => [...proposalKeys.all, 'answer'] as const,
  /**
   * **A mutation key**: Needs your answer's visit (#819), so the envelope's badge can tell which
   * watermarks this phone has sent (`useAnswersWaiting`).
   */
  needsYourAnswerVisit: () => [...proposalKeys.all, 'needs-your-answer-visit'] as const,
  /** `GET /players/me/live-yeses` — every yes on a game still filling, across groups. */
  liveYeses: () => [...proposalKeys.all, 'live-yeses'] as const,
  /** `GET /players/me/payments-to-confirm` — the reader's refused shares, waiting for them (#555). */
  paymentsToConfirm: () => [...proposalKeys.all, 'payments-to-confirm'] as const,
  /** `GET /players/me/games-and-money` — the two limits. */
  gamesAndMoney: () => [...proposalKeys.all, 'games-and-money'] as const,
  /** `GET /home` — the reader's booked games and Home's badge, held by the shell all session (#556). */
  home: () => [...proposalKeys.all, 'home'] as const,
  /** Every booked game read in detail — the root a fill re-reads. */
  bookings: () => [...proposalKeys.all, 'booking'] as const,
  /** `GET /bookings/{id}` — one booked game in detail (#556), or a rescue from outside (#557). */
  booking: (bookingId: string) => [...proposalKeys.bookings(), bookingId] as const,
  /** Every game still filling read in detail — the root every answer re-reads. */
  proposals: () => [...proposalKeys.all, 'proposal'] as const,
  /** `GET /proposals/{id}` — one game still filling in detail, with what the reader may do (#557). */
  proposal: (proposalId: string) => [...proposalKeys.proposals(), proposalId] as const,
  /**
   * `GET /pools/{id}/fill-in?sport` — a group's *Seats to fill* (#557), under the group's root, so an
   * answer re-reads it with the decks and a changed limit with every deck.
   */
  fillIn: (groupId: string, sport: Sport) =>
    [...proposalKeys.group(groupId), 'fill-in', sport] as const,
  /**
   * Every posting read of one group (#558) — under the group's root, so an answer, a join and a post
   * in the group re-read the grid and its sheet with the decks, and a changed limit with every deck.
   */
  posting: (groupId: string) => [...proposalKeys.group(groupId), 'posting'] as const,
  /** `GET /pools/{id}/posting-grid` — one week of WHEN, keyed by everything the controls ask. */
  postingGrid: (groupId: string, ask: PostingAsk, week: PostingWeek) =>
    [...proposalKeys.posting(groupId), 'grid', ask, week] as const,
  /** `GET /pools/{id}/posting-grid/slot` — a cell's sheet, for the same ask. */
  postingSlot: (groupId: string, ask: PostingAsk, day: string, range: DayRange) =>
    [...proposalKeys.posting(groupId), 'slot', ask, day, range] as const,
  /**
   * Every friends-card read of one group (#757) — under the group's root, so an answer in the group
   * (a game at an hour now taken) re-reads the card and its courts with the decks.
   */
  friendsCards: (groupId: string) => [...proposalKeys.group(groupId), 'friends-card'] as const,
  /** `GET /pools/{id}/friends-card` — a line-up's card, keyed by everything it is asked. */
  friendsCard: (groupId: string, sport: Sport, ask: FriendsCardAsk) =>
    [...proposalKeys.friendsCards(groupId), 'card', sport, ask] as const,
  /** `GET /pools/{id}/friends-card/courts` — *Find a court* for the same friends. */
  friendsCourts: (groupId: string, sport: Sport, friendIds: readonly string[]) =>
    [...proposalKeys.friendsCards(groupId), 'courts', sport, friendIds] as const,
};
