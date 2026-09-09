/**
 * **`YOUR GAMES · n`, one card, swipe** — the Now tab's whole content
 * ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §4.1).
 *
 * ## A rail, not a list
 *
 * `GamesSection` refused shelves in writing — *"a game awaiting an entry, one awaiting an answer
 * and one that never happened are one thing at three moments of its life"* — and **a rail keeps
 * that refusal by not being a list at all**. There is one heading, one card on screen and a
 * gesture; there is nowhere to put a shelf.
 *
 * It is 7.7's **paging** geometry over [Part 8](../../../../docs/design-system.md#part-8--scrolling-patterns)'s
 * Strip: the card is `1.0 × content` and therefore has **no peek**, which is what makes
 * [7.18](../../../../docs/design-system.md#718-the-rails-dots)'s dots the affordance rather than
 * decoration — so they **track the scroll**, and a page indicator that did not move would be a
 * picture of a control. The scroller's numbers are Part 8's and are not restated: snapping, gap 9,
 * bleeding to the screen edge through a negative margin against the 15pt gutter.
 *
 * **The order is the server's — newest arrangement first — and nothing re-sorts it.** On a rail
 * you page through everything, so *which is first* carries far less weight than in a scannable
 * list, and newest-arrangement-first is **stable** where a clock sort silently re-orders a
 * player's cards between sessions. The cost is stated rather than hidden: a game arranged this
 * morning for next Saturday sits ahead of one arranged last week that is tonight.
 *
 * ## The join is here, over three lists, and the card reads none of them
 *
 * Games and plans, which is
 * [ADR-0149](../../../../../docs/adr/0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md)
 * §1's arrow — a card needs both halves, so the composition is this feature's and `features/games`
 * never learns a plan exists — plus the player's own rooms, which is §3's client join for the ✉.
 * Each card is handed `(game, plan | undefined)` and the address of its room, and **reads no
 * global state**.
 *
 * **Now has one clock by construction.** Every fold on this screen is against `GET /games`'
 * `read_at`: the ladder's, the gloss's duration and the shelf life. `GET /plans` deliberately
 * carries no instant of its own, so there is no second one here to use by mistake (ADR-0148 §10).
 *
 * ## What it draws when it holds nothing, and when the read failed
 *
 * **The empty sentences are the tab's** and are handed down, exactly as the Chats sections' line
 * is: they say what lands on this *screen*, and the screen is the shell's.
 *
 * **They are not gated on the read having landed, and that is the point of how they are worded.**
 * Every other empty state in this app waits — `nothing has been sent to you` is false for a frame
 * if it is drawn before the list arrives — but Now's two sentences assert **nothing about
 * emptiness**: *every game you arrange shows up here* and *Play finds you one* are true of a player
 * with five games and of a player with none. That is the test §4.4 set them and the reason the tab
 * has refused to say *nothing is happening* since it was built, so there is nothing to hold them
 * back for, and holding them back is what would leave a blank screen while a read is in flight.
 *
 * A failed read is a sentence rather than an emptiness — a rail that vanished on an error would be
 * indistinguishable from a player with no games, which is the one thing a list of your own games
 * must not be.
 */

import { useState } from 'react';
import { ScrollView, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import type { NativeScrollEvent, NativeSyntheticEvent } from 'react-native';

import { useCurrentUser } from '@/features/auth/types';
import { useChatDoors } from '@/features/conversations/types';
import { useGames } from '@/features/games/types';
import { recoveryMessage } from '@/shared/errors';
import { Note, PagerDots, theme } from '@/shared/ui';

import { belongsOnTheRail } from '../domain/gameCard';
import { usePlans } from '../hooks/usePlans';

import { GameCard } from './GameCard';
import { gamesHeading } from './nowPresentation';

export interface GamesRailProps {
  /**
   * What Now says when it holds nothing — **the tab's sentences, not this feature's.**
   *
   * Two of them, because 10.1's empty-state rule is *present-tense, and name the act*: the first
   * says what the tab **is** and the second points at the one thing that fills it. They are handed
   * down for the reason the Chats sections' lines are — they are about the *screen*, and the
   * screen is the shell's.
   */
  readonly empty: { readonly line: string; readonly act: string };
}

export function GamesRail({ empty }: GamesRailProps) {
  const games = useGames();
  const plans = usePlans();
  const rooms = useChatDoors();
  const playerId = useCurrentUser().data?.id;
  const { width: screen } = useWindowDimensions();

  /** Which card is on screen. Route-local, and the dots' only input. */
  const [current, setCurrent] = useState(0);

  const cardWidth = screen - 2 * theme.size.gutter;
  const step = cardWidth + STRIP_GAP;

  const rows = (games.data ?? []).filter(belongsOnTheRail);

  const onScroll = (event: NativeSyntheticEvent<NativeScrollEvent>) => {
    setCurrent(Math.round(event.nativeEvent.contentOffset.x / step));
  };

  return (
    <View style={s.section}>
      <Text style={s.heading} accessibilityRole="header">
        {gamesHeading(rows.length)}
      </Text>

      {games.error !== null ? (
        <Note variant="coral" accessibilityRole="alert">
          {recoveryMessage(games.error)}
        </Note>
      ) : null}

      {games.error === null && rows.length === 0 ? (
        <>
          <Text style={s.empty}>{empty.line}</Text>
          <Text style={s.empty}>{empty.act}</Text>
        </>
      ) : null}

      {/* The reader is what turns a seat into *you* and a game into a sentence addressed to
          somebody, so the cards wait for it — but the **heading does not**, because a count is
          true whoever is reading. `useCurrentUser` is seeded by bootstrap and answers before this
          list does, so the gap is a frame; hiding the heading for it would make the section itself
          flicker in, which is the larger of the two wrongs. */}
      {playerId === undefined || rows.length === 0 ? null : (
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
            {rows.map((game) => (
              <GameCard
                key={game.gameId}
                game={game}
                plan={plans.data?.find((one) => one.gameId === game.gameId)}
                playerId={playerId}
                conversationId={rooms.get(game.challengeId)}
                width={cardWidth}
              />
            ))}
          </ScrollView>

          <PagerDots count={rows.length} current={current} />
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
