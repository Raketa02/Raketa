/**
 * **The yes screen's one motion** — the two sides slide in from the edges and meet, the word
 * rises in, the buttons fade in last, and one soft buzz lands with the word
 * ([ADR-0167](../../../../../docs/adr/0167-a-yes-lands-on-its-own-screen-and-the-room-is-opened-by-a-tap.md)
 * §2). It moves once; nothing loops.
 *
 * ## The durations are the theme's, composed and not invented
 *
 * `motion.yesEntrance` is three beats on the two durations the app already has — `rise` for
 * the sides and again for the word, `fade` for the buttons — with the word starting half-way
 * through the sides' travel so it lands as they meet, and the buttons starting as it lands.
 * What is this file's own is the geometry: the sides start beyond the phone's edges (the
 * window's width, so a wider phone slides further rather than starting on screen) and the word
 * rises through one `space.xxl`.
 *
 * ## It waits for its faces
 *
 * Nothing starts until the screen says `ready` — the reader's own face is a read, and a tile
 * that swapped from poster to photograph mid-slide is the one thing the record forbids. Before
 * that everything is drawn at its start: the sides off the edges, the word and the doors
 * invisible, over the ground alone. On a warm cache that is no frame at all.
 *
 * ## Collapsed presentation is the end state, and the buzz is not a picture
 *
 * `useCollapsedPresentation()` is one condition satisfied by **either** reduced motion or a
 * running screen reader (§20.11), and under it everything is simply there. The haptic is keyed
 * on **reduced motion alone**: under it nothing buzzes, which is the record's word; under a
 * screen reader with motion left on, the one buzz still fires, at once, because a listener who
 * has not asked for calm is owed the one signal the screen has that is not a picture.
 *
 * `Animated`, which React Native ships — `DeckStage`'s own choice, and no library added.
 */

import { useEffect, useRef, type ReactNode } from 'react';
import { Animated, StyleSheet, View, useWindowDimensions } from 'react-native';

import { useHaptics } from '@/shared/lib/platform';
import { theme, useCollapsedPresentation, useReducedMotion } from '@/shared/ui';

export interface YesEntranceProps {
  /** The faces are in. Nothing moves before this, and the beat runs once after it. */
  readonly ready: boolean;
  /**
   * The picture and the word as one sentence — the header's spoken name, built from whole
   * handles. The tiles, the `vs` and the word merge into it; the doors stay outside it, because
   * a button inside a named element is a button a listener cannot reach.
   */
  readonly label: string;
  /** The reader's side — slides in from the left. */
  readonly left: ReactNode;
  /** What sits between the sides — the `vs`. Lands with the word. */
  readonly between?: ReactNode;
  /** The other side — slides in from the right. */
  readonly right: ReactNode;
  /** The one word. Rises in. */
  readonly word: ReactNode;
  /** The two doors. Fade in last. */
  readonly buttons: ReactNode;
}

export function YesEntrance({
  ready,
  label,
  left,
  between,
  right,
  word,
  buttons,
}: YesEntranceProps) {
  const collapsed = useCollapsedPresentation();
  const reducedMotion = useReducedMotion();
  const haptics = useHaptics();
  const { width } = useWindowDimensions();

  // One value per beat, and each drives every transform in it — a side is one object moving.
  const meet = useRef(new Animated.Value(0)).current;
  const rise = useRef(new Animated.Value(0)).current;
  const fade = useRef(new Animated.Value(0)).current;
  // Once per mount, whichever way the word landed. A ref rather than state: it is a fact about
  // the motor, and re-rendering for it would be a render for nothing drawn.
  const buzzed = useRef(false);

  useEffect(() => {
    if (!ready) return undefined;

    const landed = () => {
      if (buzzed.current || reducedMotion) return;
      buzzed.current = true;
      haptics.success();
    };

    if (collapsed) {
      meet.setValue(1);
      rise.setValue(1);
      fade.setValue(1);
      landed();
      return undefined;
    }

    const beat = theme.motion.yesEntrance;
    const sides = Animated.timing(meet, {
      toValue: 1,
      duration: beat.sides,
      useNativeDriver: true,
    });
    const theWord = Animated.sequence([
      Animated.delay(beat.wordAfter),
      Animated.timing(rise, { toValue: 1, duration: beat.word, useNativeDriver: true }),
    ]);
    const doors = Animated.sequence([
      Animated.delay(beat.buttonsAfter),
      Animated.timing(fade, { toValue: 1, duration: beat.buttons, useNativeDriver: true }),
    ]);

    sides.start();
    theWord.start(({ finished }) => {
      if (finished) landed();
    });
    doors.start();

    // Left mid-beat — a door pressed early, or the screen popped. Stopping is what keeps the
    // buzz from landing on a screen that is no longer there.
    return () => {
      sides.stop();
      theWord.stop();
      doors.stop();
    };
  }, [ready, collapsed, reducedMotion, haptics, meet, rise, fade]);

  return (
    <View style={s.column}>
      <View style={s.column} accessible accessibilityRole="header" accessibilityLabel={label}>
        <View style={s.picture}>
          <Animated.View
            testID="yes-left"
            style={{ transform: [{ translateX: meet.interpolate(from(-width)) }] }}
          >
            {left}
          </Animated.View>
          {between === undefined ? null : (
            <Animated.View testID="yes-between" style={{ opacity: rise }}>
              {between}
            </Animated.View>
          )}
          <Animated.View
            testID="yes-right"
            style={{ transform: [{ translateX: meet.interpolate(from(width)) }] }}
          >
            {right}
          </Animated.View>
        </View>

        <Animated.View
          testID="yes-word"
          style={{ opacity: rise, transform: [{ translateY: rise.interpolate(RISE_THROUGH) }] }}
        >
          {word}
        </Animated.View>
      </View>

      <Animated.View testID="yes-buttons" style={{ opacity: fade }}>
        {buttons}
      </Animated.View>
    </View>
  );
}

/** A side's travel: from beyond the edge to where it belongs. */
const from = (edge: number) => ({ inputRange: [0, 1], outputRange: [edge, 0] });

/** The word rises through one large step and lands where it is drawn. */
const RISE_THROUGH = { inputRange: [0, 1], outputRange: [theme.space.xxl, 0] };

const s = StyleSheet.create({
  // The three things, stacked and centred, at the mock's gap: one large step between each.
  column: { alignItems: 'center', gap: theme.space.xl },
  // The two sides and the `vs`, one row, the gap at `vs` the gutter's own 15 either side.
  picture: { flexDirection: 'row', alignItems: 'center', gap: theme.space.lg },
});
