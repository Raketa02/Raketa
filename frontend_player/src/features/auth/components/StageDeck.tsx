/**
 * **Sign-in's dealt deck** — three miniature Games-deck cards in the hero's room, dealt when the
 * screen opens ([#786](https://github.com/Raketa02/Raketa/issues/786), PRD #783; design system
 * 12.2, mock 2): a padel game waiting for a fourth in front, straight; a tennis single and a squash
 * Fill in turned either side of it. What each card says is `stageDeckPresentation`'s, and each is a
 * `MiniGameCard`, an illustration copied from the real card and never the live deck. This file is
 * the deal and the fit.
 *
 * ## The deal
 *
 * The three open stacked exactly on top of each other — only the front card shows — for
 * `motion.stageDeck.stacked`, then the two back cards slide out to their turned places either side
 * over `motion.stageDeck.deal`, decelerating, while the front card stays put. One value drives both
 * back cards, so they leave together as one hand dealing. Once, on open; the loop (#787) takes it
 * from there. `Animated`, which React Native ships, on the native driver — the yes screen's and the
 * deck's own choice, and nothing a sheet's `Modal` can trip on.
 *
 * **Under collapsed presentation the cards are dealt from the first frame and nothing moves** — the
 * app's one rule for reduced motion or a running screen reader (`useCollapsedPresentation`). The
 * value starts dealt when the rule is known on the first render, as reduced motion is (it is the
 * root's context); a screen reader's answer is a promise, and when it lands mid-stack the deal is
 * stopped and the cards are simply where they belong.
 *
 * ## The fit
 *
 * The room is whatever the wordmark and the headline leave, so it is **measured**, and the fan is
 * scaled into it whole (`stageDeckGeometry`'s `fitScale`): on a short phone, or with the headline at
 * the text cap's three lines, the deck gets smaller and never runs over either. Until the room is
 * measured nothing is drawn — a frame at the wrong size would be a jump.
 */

import { useEffect, useRef, useState } from 'react';
import { Animated, Easing, StyleSheet, View, type LayoutChangeEvent } from 'react-native';

import { theme, useCollapsedPresentation } from '@/shared/ui';

import { MiniGameCard } from './MiniGameCard';
import {
  DEALT,
  DECK_PLACES,
  FAN_BOX,
  STACKED,
  fitScale,
  type DeckPlace,
  type Size,
} from './stageDeckGeometry';
import { STAGE_DECK_CARDS } from './stageDeckPresentation';

const CARD = theme.size.stage.card;

/** `easeDecel`, the app's one curve for a thing arriving. */
const EASE = Easing.bezier(
  theme.motion.easeDecel.x1,
  theme.motion.easeDecel.y1,
  theme.motion.easeDecel.x2,
  theme.motion.easeDecel.y2,
);

/** From the deal (nought stacked, one dealt) to where the card at `place` stands. */
function dealTransform(place: DeckPlace, deal: Animated.Value) {
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

export function StageDeck() {
  const collapsed = useCollapsedPresentation();
  // Dealt from the first frame when the rule is already known — see the module note.
  const deal = useRef(new Animated.Value(collapsed ? 1 : 0)).current;
  const [room, setRoom] = useState<Size>({ width: 0, height: 0 });

  useEffect(() => {
    if (collapsed) {
      deal.setValue(1);
      return undefined;
    }

    const beat = theme.motion.stageDeck;
    const dealing = Animated.sequence([
      Animated.delay(beat.stacked),
      Animated.timing(deal, {
        toValue: 1,
        duration: beat.deal,
        easing: EASE,
        useNativeDriver: true,
      }),
    ]);
    dealing.start();

    // Left mid-deal — the screen popped, or the rule arrived: the next run, or the rule, puts the
    // cards where they belong.
    return () => dealing.stop();
  }, [collapsed, deal]);

  const onLayout = ({ nativeEvent }: LayoutChangeEvent) =>
    setRoom({ width: nativeEvent.layout.width, height: nativeEvent.layout.height });

  const measured = room.width > 0 && room.height > 0;

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
            transform: [{ scale: measured ? fitScale(room) : 1 }],
          },
        ]}
      >
        {/* Back to front: the two dealt cards under the one that stays. */}
        {DECK_PLACES.map((place) => (
          <Animated.View
            key={place}
            testID={`stage-card-${place}`}
            style={[s.card, { transform: dealTransform(place, deal) }]}
          >
            <MiniGameCard {...STAGE_DECK_CARDS[place]} />
          </Animated.View>
        ))}
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
});
