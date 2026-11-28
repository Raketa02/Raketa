/**
 * **Sign-in's dealt deck** — three miniature Games-deck cards in the hero's room
 * ([#786](https://github.com/Rakieta02/Rakieta/issues/786), [#787](https://github.com/Rakieta02/Rakieta/issues/787),
 * PRD #783; design system 12.2, mock 2): a padel game waiting for a fourth in front, straight; a
 * tennis single and a squash Fill in turned either side of it. What each card says is
 * `stageDeckPresentation`'s, and each is a `MiniGameCard`, an illustration copied from the real card
 * and never the live deck. This file draws where they stand; **when they move is the loop's**
 * (`useStageLoop`), handed in as two values.
 *
 * ## The deal, and the swipe
 *
 * `deal` takes the two back cards from exactly under the front one (nought) out to their turned
 * places either side (one), and nothing else moves them. `swipe` takes the front card from its place
 * (nought) a little right and turned, with **I'M IN** on it (one) — the real deck's stamp, in volt,
 * clockwise and top-right where mock 2 draws it, with no price — and on off past the right edge of the
 * screen, turning further and fading in its last stretch (two). The flight is the window's width at
 * the deck's scale, so the card leaves the phone whatever the room's size.
 *
 * ## The fit
 *
 * The room is whatever the wordmark and the headline leave, so it is **measured**, and the fan is
 * scaled into it whole (`stageDeckGeometry`'s `fitScale`): on a short phone, or with the headline at
 * the text cap's three lines, the deck gets smaller and never runs over either. Until the room is
 * measured nothing is drawn — a frame at the wrong size would be a jump.
 */

import { Animated, StyleSheet, Text, View, useWindowDimensions } from 'react-native';

import { theme } from '@/shared/ui';

import { MiniGameCard } from './MiniGameCard';
import { DEALT, FAN_BOX, STACKED, fitScale, type DeckPlace } from './stageDeckGeometry';
import { STAGE_DECK_CARDS } from './stageDeckPresentation';
import { STAGE_STAMP } from './stageHeroCopy';
import { useMeasuredRoom } from './useMeasuredRoom';
import type { StageDeckMotion } from './useStageLoop';

/** The two cards the deal moves, drawn under the front one: back to front, left then right. */
const BACK_CARDS = ['left', 'right'] as const satisfies readonly DeckPlace[];

const CARD = theme.size.stage.card;
const SWIPE = theme.size.stage.swipe;
const STAMP = theme.size.stage.stamp;
const CAP = theme.size.stage.textMaxScale;

/** From the deal to where a back card at `place` stands. */
function dealTransform(place: (typeof BACK_CARDS)[number], deal: Animated.Value) {
  const to = DEALT[place];
  const along = (from: number, end: number) =>
    deal.interpolate({ inputRange: [0, 1], outputRange: [from, end] });
  return [
    { translateX: along(STACKED.x, to.x) },
    { translateY: along(STACKED.y, to.y) },
    {
      rotate: deal.interpolate({
        inputRange: [0, 1],
        outputRange: [`${STACKED.turn}deg`, `${to.turn}deg`],
      }),
    },
  ];
}

/** From the swipe to where the front card stands, and how much of it shows. */
function swipeStyle(swipe: Animated.Value, flight: number) {
  return {
    // Picked up at one and gone at two; it fades over the last stretch of the way off.
    opacity: swipe.interpolate({
      inputRange: [0, 1 + SWIPE.fadesFrom, 2],
      outputRange: [1, 1, 0],
      extrapolate: 'clamp',
    }),
    transform: [
      {
        translateX: swipe.interpolate({
          inputRange: [0, 1, 2],
          outputRange: [STACKED.x, SWIPE.across, SWIPE.across + flight],
        }),
      },
      { translateY: STACKED.y },
      {
        rotate: swipe.interpolate({
          inputRange: [0, 1, 2],
          outputRange: [`${STACKED.turn}deg`, `${SWIPE.turn}deg`, `${SWIPE.outTurn}deg`],
        }),
      },
    ],
  };
}

export function StageDeck({ deal, swipe }: StageDeckMotion) {
  const { width: windowWidth } = useWindowDimensions();
  const { room, measured, onLayout } = useMeasuredRoom();
  const scale = measured ? fitScale(room) : 1;
  // The window's width in the deck's own points: from wherever it was picked up, that is off the phone.
  const flight = windowWidth / scale;

  return (
    <View style={StyleSheet.absoluteFill} onLayout={onLayout} testID="stage-deck">
      {/* The fan's box at its drawn size, centred on the room and scaled about its centre into it. */}
      <View
        testID="stage-deck-plate"
        style={[
          s.plate,
          {
            left: (room.width - FAN_BOX.width) / 2,
            top: (room.height - FAN_BOX.height) / 2,
            opacity: measured ? 1 : 0,
            transform: [{ scale }],
          },
        ]}
      >
        {/* Back to front: the two dealt cards under the one that stays. */}
        {BACK_CARDS.map((place) => (
          <Animated.View
            key={place}
            testID={`stage-card-${place}`}
            style={[s.card, { transform: dealTransform(place, deal) }]}
          >
            <MiniGameCard {...STAGE_DECK_CARDS[place]} />
          </Animated.View>
        ))}
        <Animated.View testID="stage-card-front" style={[s.card, swipeStyle(swipe, flight)]}>
          <MiniGameCard {...STAGE_DECK_CARDS.front} />
          <Animated.View
            testID="stage-stamp"
            style={[
              s.stamp,
              {
                opacity: swipe.interpolate({
                  inputRange: [0, 1],
                  outputRange: [0, 1],
                  extrapolate: 'clamp',
                }),
              },
            ]}
          >
            <Text style={s.stampWords} numberOfLines={1} maxFontSizeMultiplier={CAP}>
              {STAGE_STAMP}
            </Text>
          </Animated.View>
        </Animated.View>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  plate: { position: 'absolute', width: FAN_BOX.width, height: FAN_BOX.height },
  // Every card stands on the front card's place; the deal moves the two behind it.
  card: {
    position: 'absolute',
    left: FAN_BOX.centre.x - CARD.width / 2,
    top: FAN_BOX.centre.y - CARD.height / 2,
  },
  // The real deck's stamp — its outline, its corner, its type — set where mock 2 sets it: the card's
  // top-right, astride the ribbon's foot, turned clockwise. Mock 2 fills it with the dark the tiles'
  // scrim is, so the volt reads over a poster.
  stamp: {
    position: 'absolute',
    top: STAMP.top,
    right: theme.space.xl,
    borderWidth: STAMP.stroke,
    borderColor: theme.color.volt,
    borderRadius: theme.radius.btn,
    backgroundColor: theme.color.photoScrim,
    paddingVertical: theme.space.xs,
    paddingHorizontal: theme.space.md,
    transform: [{ rotate: `${STAMP.tilt}deg` }],
  },
  stampWords: {
    ...theme.type.deckStamp,
    color: theme.color.volt,
    textTransform: 'uppercase',
  },
});
