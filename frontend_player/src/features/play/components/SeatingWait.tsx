/**
 * **The engine seating a court, drawn under the court it is seating.**
 *
 * `SearchingLatch` is the other wait in this tab, and the difference between them is the whole
 * of this file. A search on *Find a game* has nothing on screen to show — the answer is a
 * ranked list that lives on a screen the player has not reached — so its wait covers the
 * screen and lifts onto the court. A **fill** has the answer's own subject already drawn:
 * `POST /lineups` seats people on a court the player is looking at, so covering that court
 * with a full-screen latch takes away the one thing the wait is about, and hands it back
 * complete a second and a half later as though nothing had happened.
 *
 * So this is a **block in the page**, and the seats land behind it one at a time
 * (`seatReveal`). The stagger `motion.hold` has always booked to *"the animation it drives"*
 * is that arrival, and this is the drawing it drives.
 *
 * ## What it says, and what it does not
 *
 * `engineFillStatus`' two lines and nothing else. There is **no control**, for the latch's
 * reason: the player is not trapped in a wait bound to a request, a refusal takes it down over
 * ⚡ — which is still on the screen, one block below — and a cancel would promise an escape
 * from something already ending. There is no back, because this was never a destination.
 *
 * The count is `players_in_range` **off the response**, so it is absent while the request is
 * in flight and the block states what it is doing with no number it could not have
 * (`searchingPresentation`). §20.11: the region announces the **result** once and never a
 * stage.
 *
 * ## The ring, and the one loop in the app
 *
 * `motion.ripple` is one of the two looping animations in this codebase — the typing indicator's
 * pulse is the other, and the argued exception — and this is its only caller.
 * A ring expanding out of nothing says *something is being looked for*, where a spinner says
 * *something is loading* — and what is happening is a search. It is **decoration and is hidden
 * from the tree**: §20.1's merge rule, and a listener already has both sentences.
 *
 * Under `useCollapsedPresentation()` the ring is drawn **at rest** rather than removed: the
 * shape is what makes the two sentences read as a block rather than as loose text, and the
 * player who asked the OS to calm things down asked for less motion, not less layout.
 */

import { useEffect, useRef } from 'react';
import { Animated, Easing, StyleSheet, Text, View } from 'react-native';

import { theme, useCollapsedPresentation, useLiveRegion } from '@/shared/ui';

import { PLAY_LIVE_REGIONS } from './accessibilityPresentation';
import type { SearchingStatus } from './searchingPresentation';

export interface SeatingWaitProps {
  /** The headline, and the count once the response has one. */
  readonly status: SearchingStatus;
}

export function SeatingWait({ status }: SeatingWaitProps) {
  const collapsed = useCollapsedPresentation();
  const cycle = useRef(new Animated.Value(0)).current;

  // The result, once. `null` is a region with nothing in it, which is silence rather than an
  // empty sentence — and a stage has no result to announce.
  useLiveRegion(status.count ?? null, PLAY_LIVE_REGIONS.searching);

  useEffect(() => {
    if (collapsed) return;

    const loop = Animated.loop(
      Animated.timing(cycle, {
        toValue: 1,
        duration: theme.motion.ripple,
        easing: Easing.out(Easing.quad),
        useNativeDriver: true,
      }),
    );
    loop.start();

    return () => loop.stop();
  }, [collapsed, cycle]);

  return (
    <View style={s.block}>
      <View
        style={s.stage}
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
      >
        <Animated.View
          style={[
            s.ring,
            collapsed
              ? undefined
              : {
                  transform: [
                    { scale: cycle.interpolate({ inputRange: [0, 1], outputRange: RING_SCALE }) },
                  ],
                  opacity: cycle.interpolate({ inputRange: [0, 1], outputRange: RING_OPACITY }),
                },
          ]}
        />
      </View>

      <Text style={s.headline} accessibilityRole="header">
        {status.headline}
      </Text>

      {status.count === undefined ? null : <Text style={s.count}>{status.count}</Text>}
    </View>
  );
}

/** The ring grows from half its box to the whole of it, and fades out as it goes. */
const RING_SCALE = [0.45, 1];
const RING_OPACITY = [1, 0];

const s = StyleSheet.create({
  block: { alignItems: 'center', gap: theme.space.xxs, paddingVertical: theme.space.sm },
  stage: {
    width: theme.size.ripple,
    height: theme.size.ripple,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: theme.space.xs,
  },
  ring: {
    width: theme.size.ripple,
    height: theme.size.ripple,
    borderRadius: theme.radius.pill,
    borderWidth: theme.size.rippleStroke,
    borderColor: theme.color.coral,
  },
  headline: { ...theme.type.h2, color: theme.color.ink, textAlign: 'center' },
  count: { ...theme.type.tiny, color: theme.color.muted, textAlign: 'center' },
});
