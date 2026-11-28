/**
 * **`YOUR GAMES · n`, one card, swipe** — Home's rail of booked games and the games waiting for a
 * club ([#556](https://github.com/Rakieta02/Rakieta/issues/556); the screens A8).
 *
 * It was the old loop's rail with the booked cards handed in as a slot, until that loop was
 * removed ([#576](https://github.com/Rakieta02/Rakieta/issues/576)): Home is booked games only now, so
 * the rail is this feature's whole, and it looks as it did — the heading's count, the pager and its
 * dots, the empty state and the error note.
 *
 * ## A rail, not a list
 *
 * A game awaiting its club, one that is booked and one that needs a result are one thing at three
 * moments of its life, and **a rail keeps that by not being a list at all**: one heading, one card
 * on screen and a gesture, and nowhere to put a shelf.
 *
 * It is 7.7's **paging** geometry over [Part 8](../../../../docs/design-system.md#part-8--scrolling-patterns)'s
 * Strip: the card is `1.0 × content` and therefore has **no peek**, which is what makes
 * [7.18](../../../../docs/design-system.md#718-the-rails-dots)'s dots the affordance rather than
 * decoration — so they **track the scroll**, and a page indicator that did not move would be a
 * picture of a control. The heading, the scroller and the dots are Home's row frame (`HomeRow` and
 * its paging `HomeRowRail`, #798), which every row on Home shares: Part 8's snapping, gap 9 and
 * bleed live there, and the sentences this rail says in its place stand under the same heading.
 *
 * **The order is the read's — soonest first — and nothing re-sorts it.**
 *
 * ## Each card is handed what the surface already holds
 *
 * The read's clock, whether it is *new*, and whether its room is open, from one join over the rooms
 * by booking (`useBookingRooms`) — and reads nothing itself. *Open game* pushes the details over
 * Home, so *back* is Home; **the bubble pushes the room over Home** (Q100), with no details under
 * it, so *back* from the room is Home too — and marks the game opened, as the details do, so its
 * *New* goes.
 *
 * ## What it draws when it holds nothing, and when the read failed
 *
 * **Nothing until its read lands** ([#871](https://github.com/Rakieta02/Rakieta/issues/871); the
 * loading shimmer log §6, Q16): it never says *· 0*, nor that nothing is here, while it does not
 * know. Home shimmers in its place meanwhile (`YourGamesSkeleton`, drawn by the shell), so there is
 * no blank screen to hold anything back for. **This reverses the rail's first rule**, that the empty
 * sentences were *not gated on the read having landed* because they were true of everybody: true,
 * but the count over them was not.
 *
 * **The empty sentences are the tab's** and are handed down: they say what lands on this *screen*,
 * and the screen is the shell's — *every game you arrange shows up here* and *Play finds you one*.
 *
 * A failed read is a sentence rather than an emptiness — a rail that vanished on an error would be
 * indistinguishable from a player with no games, which is the one thing a list of your own games
 * must not be — and **a read waiting for a connection says so** in amber; under the heading, with
 * no count, either way. Each is said only while there is nothing to draw: a re-read that failed
 * behind cards already on screen leaves them, as every list here does. **A first read that failed
 * once and is retrying keeps the rail's skeleton in its place** (`YourGamesSkeleton`): Home stops
 * waiting for it (`useHomeReadFinished`) and reveals around it, and the rail comes in where the
 * skeleton stood when it lands or is refused — never drawn in later above FOR YOU, pushing it down.
 */

import { router } from 'expo-router';
import { StyleSheet, Text } from 'react-native';

import { useBookingRooms } from '@/features/conversations/types';
import { offlineMessage, recoveryMessage } from '@/shared/errors';
import { HomeRow, HomeRowRail, Note, theme } from '@/shared/ui';

import { chatIsOpen, isNew, lineCanRunOut, onHome } from '../domain/home';
import { useDismissedGames, useHome, useOpenedGames, useReadClock } from '../hooks/useHome';

import { HomeGameCard } from './HomeGameCard';
import { gamesHeading } from './homePresentation';
import { bookedChatRoute, bookedGameRoute } from './proposalRoutes';
import { YourGamesSkeleton } from './YourGamesSkeleton';

export interface HomeRailProps {
  /**
   * What Home says when it holds nothing — **the tab's sentences, not this feature's.**
   *
   * Two of them, because 10.1's empty-state rule is *present-tense, and name the act*: the first
   * says what the tab **is** and the second points at the one thing that fills it.
   */
  readonly empty: { readonly line: string; readonly act: string };
}

export function HomeRail({ empty }: HomeRailProps) {
  const home = useHome();
  const rooms = useBookingRooms();
  const { opened, open } = useOpenedGames();
  const { dismissed, dismiss } = useDismissedGames();

  const all = home.data?.games ?? [];
  // The clock runs while a cut-off or a time to pay is ahead, so *free to leave until …* and
  // *until …* leave the line by themselves.
  const ticking = all.some(lineCanRunOut);
  const now = useReadClock(home.data?.readAt, home.dataUpdatedAt, ticking);
  const games = all.filter((game) => onHome(game, now) && !dismissed?.has(game.bookingId));
  const failure = home.data === undefined ? home.error : null;
  const offline = home.data === undefined && failure === null && home.fetchStatus === 'paused';

  // Not drawn before its read lands — never *· 0* while it does not know (#871). Under Home's own
  // skeleton until Home reveals; once it has, a first read retrying keeps the rail's in its place.
  if (home.data === undefined && failure === null && !offline) {
    return home.failureCount > 0 ? <YourGamesSkeleton /> : null;
  }

  return (
    <HomeRow heading={gamesHeading(home.data === undefined ? undefined : games.length)}>
      {failure !== null ? (
        <Note variant="coral" accessibilityRole="alert">
          {recoveryMessage(failure)}
        </Note>
      ) : null}

      {offline ? <Note variant="amber">{offlineMessage('resumes')}</Note> : null}

      {home.data !== undefined && games.length === 0 ? (
        <>
          <Text style={s.empty}>{empty.line}</Text>
          <Text style={s.empty}>{empty.act}</Text>
        </>
      ) : null}

      {games.length === 0 ? null : (
        <HomeRowRail cards={games} geometry="paging">
          {(game, width) => (
            <HomeGameCard
              key={game.bookingId}
              game={game}
              now={now}
              fresh={isNew(game, opened)}
              onChat={
                chatIsOpen(game) && rooms.has(game.bookingId)
                  ? () => {
                      open(game.bookingId);
                      router.push(bookedChatRoute(game.bookingId));
                    }
                  : undefined
              }
              width={width}
              onOpen={() => router.push(bookedGameRoute(game.bookingId))}
              onDismiss={() => dismiss(game.bookingId)}
            />
          )}
        </HomeRowRail>
      )}
    </HomeRow>
  );
}

const s = StyleSheet.create({
  empty: { ...theme.type.tiny, color: theme.color.muted },
});
