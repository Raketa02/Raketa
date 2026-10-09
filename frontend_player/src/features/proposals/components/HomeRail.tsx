/**
 * **`YOUR GAMES · n`, one card, swipe** — Home's rail of booked games and the games waiting for a
 * club ([#556](https://github.com/Raketa02/Raketa/issues/556); the screens A8).
 *
 * It was the old loop's rail with the booked cards handed in as a slot, until that loop was
 * removed ([#576](https://github.com/Raketa02/Raketa/issues/576)): Home is booked games only now, so
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
 * picture of a control. The scroller's numbers are Part 8's and are not restated: snapping, gap 9,
 * bleeding to the screen edge through a negative margin against the 15pt gutter.
 *
 * **The order is the read's — soonest first — and nothing re-sorts it.**
 *
 * ## Each card is handed what the surface already holds
 *
 * The read's clock, whether it is *new*, and whether its room is open, from one join over the rooms
 * by booking (`useBookingRooms`) — and reads nothing itself. *Open game* pushes the details over
 * Home, so *back* is Home.
 *
 * ## What it draws when it holds nothing, and when the read failed
 *
 * **The empty sentences are the tab's** and are handed down: they say what lands on this *screen*,
 * and the screen is the shell's. **They are not gated on the read having landed**, and that is the
 * point of how they are worded: *every game you arrange shows up here* and *Play finds you one* are
 * true of a player with five games and of a player with none, so there is nothing to hold them back
 * for, and holding them back is what would leave a blank screen while a read is in flight.
 *
 * A failed read is a sentence rather than an emptiness — a rail that vanished on an error would be
 * indistinguishable from a player with no games, which is the one thing a list of your own games
 * must not be. It is said only while there is nothing to draw: a re-read that failed behind cards
 * already on screen leaves them, as every list here does.
 */

import { router } from 'expo-router';
import { useState } from 'react';
import { ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import type { NativeScrollEvent, NativeSyntheticEvent } from 'react-native';

import { useBookingRooms } from '@/features/conversations/types';
import { recoveryMessage } from '@/shared/errors';
import { Note, PagerDots, theme } from '@/shared/ui';

import { chatIsOpen, isNew, lineCanRunOut, onHome } from '../domain/home';
import { useHome, useOpenedGames, useReadClock } from '../hooks/useHome';

import { HomeGameCard } from './HomeGameCard';
import { gamesHeading } from './homePresentation';
import { bookedGameRoute } from './proposalRoutes';

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
  const { opened } = useOpenedGames();
  const { width: screen } = useWindowDimensions();

  /** Which card is on screen. Route-local, and the dots' only input. */
  const [current, setCurrent] = useState(0);

  const all = home.data?.games ?? [];
  // The clock runs while a cut-off or a club's deadline is ahead, so *back if you leave by …* and
  // *answers by …* leave the line by themselves.
  const ticking = all.some(lineCanRunOut);
  const now = useReadClock(home.data?.readAt, home.dataUpdatedAt, ticking);
  const games = all.filter((game) => onHome(game, now));
  const failure = home.data === undefined ? home.error : null;

  const cardWidth = screen - 2 * theme.size.gutter;
  const step = cardWidth + STRIP_GAP;

  const onScroll = (event: NativeSyntheticEvent<NativeScrollEvent>) => {
    setCurrent(Math.round(event.nativeEvent.contentOffset.x / step));
  };

  return (
    <View style={s.section}>
      <Text style={s.heading} accessibilityRole="header">
        {gamesHeading(games.length)}
      </Text>

      {failure !== null ? (
        <Note variant="coral" accessibilityRole="alert">
          {recoveryMessage(failure)}
        </Note>
      ) : null}

      {failure === null && games.length === 0 ? (
        <>
          <Text style={s.empty}>{empty.line}</Text>
          <Text style={s.empty}>{empty.act}</Text>
        </>
      ) : null}

      {games.length === 0 ? null : (
        <>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            snapToInterval={step}
            decelerationRate="fast"
            onScroll={onScroll}
            scrollEventThrottle={SCROLL_THROTTLE_MS}
            style={s.strip}
            contentContainerStyle={s.stripContent}
          >
            {games.map((game) => (
              <HomeGameCard
                key={game.bookingId}
                game={game}
                now={now}
                fresh={isNew(game, opened)}
                chat={chatIsOpen(game.status) && rooms.has(game.bookingId)}
                width={cardWidth}
                onOpen={() => router.push(bookedGameRoute(game.bookingId))}
              />
            ))}
          </ScrollView>

          <PagerDots count={games.length} current={current} />
        </>
      )}
    </View>
  );
}

/** Part 8's Strip gap, and the whole of what this file borrows from that section. */
const STRIP_GAP = theme.space.sm;

/** One frame at 60 Hz. The dots track the scroll, so they are told about every frame of it. */
const SCROLL_THROTTLE_MS = 16;

const s = StyleSheet.create({
  section: { gap: theme.space.sm, marginTop: theme.space.lg },
  // 3.3 as amended: a section heading is `eyebrow` / `muted` / uppercase, and `h2` titles a card.
  heading: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  empty: { ...theme.type.tiny, color: theme.color.muted },
  // Part 8: the negative margin is what lets the strip bleed to the screen edge while its content
  // still aligns to the gutter.
  strip: { marginHorizontal: -theme.size.gutter },
  stripContent: { paddingHorizontal: theme.size.gutter, gap: STRIP_GAP },
});
