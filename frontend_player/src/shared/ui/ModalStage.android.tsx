/**
 * **The modal stage, on Android** — a layer in the tree, hosted at the root by
 * `overlay.tsx`'s `OverlayHost`, standing in for React Native's `Modal`. The contract and the
 * reason are on `ModalStage.tsx` and on the host; this file is the mechanics.
 *
 * ## What the native window gave, and how each is kept
 *
 * - **Above everything, in 9.3's order.** The host is a sibling of the whole route tree, after
 *   it, so the layer paints over every screen and the tab bar; the toast host is a sibling of
 *   the layers, so `zIndex` from `theme.layer` keeps a sheet beneath a toast and a popover
 *   over one, as the native windows never could. With no host — a unit test rendering an
 *   overlay alone — the layer is drawn in place, which is where a test finds it anyway.
 * - **The hardware back.** Subscribed while the stage is up; the newest `onRequestClose` is
 *   what answers, and the answer is always *handled*, so the gesture never falls through to
 *   the screen beneath.
 * - **The motion.** `slide` is the layer rising from the bottom of the window over
 *   `motion.sheet`, `fade` its opacity over `motion.popover`, both on the native driver;
 *   `none` is the overlay's reduced-motion call and the layer is simply there. Only the
 *   arrival: an overlay is unmounted the moment it closes, as every caller does, and the
 *   window's slide-out was the one thing the native window did that this does not.
 * - **Touch.** Ordinary: the stage is laid out like any view, so the scrim takes the tap, the
 *   controls take their presses and the sheet's scroll view scrolls.
 * - **A window over a window.** A stage rendered inside another stage's children — a sheet opened
 *   from a sheet — is the host's next layer up, and the one under it is hidden from a screen
 *   reader while it is (`useCoveredLayer`); the back answers the newer first, being the newer
 *   subscription.
 *
 * The layer is re-stated on every render because it is an element the host renders, not a
 * subtree this component renders — a portal's trade, and the host keeps the layer's position
 * stable so its state survives the re-statement.
 */

import { useEffect, useId, useRef } from 'react';
import { Animated, BackHandler, Easing, StyleSheet, useWindowDimensions } from 'react-native';

import type { ModalStageProps } from './ModalStage';
import { behindOverlay, useCoveredLayer, useOverlayLayers } from './overlay';
import { theme } from './theme';

export type { ModalStageProps } from './ModalStage';

export function ModalStage({
  visible,
  onRequestClose,
  animationType,
  layer: order,
  children,
}: ModalStageProps) {
  const layers = useOverlayLayers();
  const key = useId();
  const covered = useCoveredLayer(key);
  const { height } = useWindowDimensions();
  const progress = useRef(new Animated.Value(0)).current;

  // The newest answer to the back gesture, without re-subscribing on every render.
  const answer = useRef(onRequestClose);
  useEffect(() => {
    answer.current = onRequestClose;
  }, [onRequestClose]);
  useEffect(() => {
    if (!visible) return undefined;
    const subscription = BackHandler.addEventListener('hardwareBackPress', () => {
      answer.current();
      return true;
    });
    return () => subscription.remove();
  }, [visible]);

  useEffect(() => {
    if (!visible) return undefined;
    if (animationType === 'none') {
      progress.setValue(1);
      return undefined;
    }
    progress.setValue(0);
    const arrival = Animated.timing(progress, {
      toValue: 1,
      duration: animationType === 'slide' ? theme.motion.sheet : theme.motion.popover,
      easing: Easing.bezier(
        theme.motion.easeDecel.x1,
        theme.motion.easeDecel.y1,
        theme.motion.easeDecel.x2,
        theme.motion.easeDecel.y2,
      ),
      useNativeDriver: true,
    });
    arrival.start();
    return () => arrival.stop();
  }, [visible, animationType, progress]);

  const motion =
    animationType === 'slide'
      ? {
          transform: [
            { translateY: progress.interpolate({ inputRange: [0, 1], outputRange: [height, 0] }) },
          ],
        }
      : animationType === 'fade'
        ? { opacity: progress }
        : undefined;

  // 9.3's order, against the toast host beside the layers: a sheet beneath a toast, a popover
  // over one.
  // Hidden from a screen reader while a newer layer is up over it — a native window over a
  // native window did that on its own.
  const layer = visible ? (
    <Animated.View
      style={[StyleSheet.absoluteFill, { zIndex: theme.layer[order] }, motion]}
      testID="modal-stage"
      {...behindOverlay(covered)}
    >
      {children}
    </Animated.View>
  ) : null;

  // Re-stated every render: the layer is this render's element, and the host draws it.
  useEffect(() => {
    if (layers === undefined) return;
    if (layer === null) layers.remove(key);
    else layers.set(key, layer);
  });
  useEffect(() => () => layers?.remove(key), [layers, key]);

  return layers === undefined ? layer : null;
}
