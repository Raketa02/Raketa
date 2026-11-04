/**
 * **The guide** — design-system 9.4: a few things on a screen explained one at a time, in order.
 * The screen dims, a spotlight cuts one element out of the dim, and a bubble beside it says what
 * it is.
 *
 * ```
 * dim      the scrim (9.1's night at 45 %), with a hole of radius.spotlight, the target + 6
 * bubble   7.6's card at the content's width — title cardTitle · body tiny ·
 *          "N of M" num.xs muted · Skip secondary sm · Next primary sm ("Got it" on the last)
 * arrow    7.6's, pointing at the hole from the side the bubble stands on
 * ```
 *
 * Built for *Your rating*'s three numbers
 * ([ADR-0200](../../../../docs/adr/0200-a-level-is-asked-where-play-begins.md) §8), and a
 * primitive because what it does is the shape of every guide: none of it knows a rating.
 *
 * ## Three decisions worth knowing
 *
 * **It sits on `ModalStage`, the popover's stage and layer**, so it is a native window on iOS and
 * the root host's layer on Android — never an Android `Modal` (ADR-0178). The device's back
 * button is the stage's request to close, and **the guide takes it as _Skip_** (a call made in the
 * spec, not grilled).
 *
 * **Modal, and the whole window is the dim.** One press surface spans the window under the
 * bubble, the hole included, so nothing beneath can be reached while the guide is up — a tap
 * anywhere off the bubble is **_Next_**, which is what a habitual tap should be rather than a way
 * to lose the guide. **The screen beneath declines touches as well** — its root takes
 * `pointerEvents="none"` while the guide is up, beside the `behindOverlay` every overlay asks of
 * it — so the guarantee does not rest on the stage alone.
 *
 * **The hole needs the target measured**, as the popover's arrow does: `measureInWindow` on each
 * step. Where no measurement arrives — the test renderer never answers one — the whole window is
 * dimmed and the bubble stands in its middle, with no arrow, rather than pointing at nothing.
 *
 * The step is the guide's own, and starts from the first each time it is shown. How it ended is
 * not reported: *Got it* and *Skip* both end it, and the one caller does the same with either.
 *
 * **For screen readers, the name is the whole job**
 * ([ADR-0198](../../../../docs/adr/0198-the-player-app-is-not-built-for-screen-readers-for-now.md)
 * §1): every control is named — *Skip the guide*, as 6.6 asks a close control to say what it
 * closes — and the modal semantics are the stage's, which this keeps rather than adds to. It moves
 * no focus and follows no setting: it fades in whatever reduced motion says, and nothing moves
 * between steps. The dim is hidden from a listener, as the popover's backdrop is, so it is not a
 * nameless button the size of the window.
 */

import { useLayoutEffect, useState, type RefObject } from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
  type ViewStyle,
} from 'react-native';
import Svg, { Path } from 'react-native-svg';

import { Button } from './Button';
import { guideLayout, spotlightPath, type GuideRect } from './guideGeometry';
import { ModalStage } from './ModalStage';
import { theme } from './theme';

export interface GuideStep {
  /** The element the spotlight cuts out — measured on the step, never focused. */
  readonly target: RefObject<View | null>;
  readonly title: string;
  readonly body: string;
}

export interface GuideProps {
  readonly visible: boolean;
  readonly steps: readonly GuideStep[];
  /** *Got it* on the last step, *Skip* on any, or the device's back. */
  readonly onDone: () => void;
}

/** The guide's own words — the same on every guide, so the primitive holds them. */
const GUIDE_COPY = {
  next: 'Next',
  last: 'Got it',
  skip: 'Skip',
  /** 6.6: a close control says what it closes. */
  skipName: 'Skip the guide',
  count: (step: number, of: number) => `${step} of ${of}`,
} as const;

export function Guide({ visible, steps, onDone }: GuideProps) {
  const viewport = useWindowDimensions();
  const [index, setIndex] = useState(0);
  /** Where this step's target was found in the window — `undefined` until it answers. */
  const [measured, setMeasured] = useState<GuideRect>();

  // Each showing starts from the first step: the step is reset in render, when `visible` turns,
  // so the first frame of a second showing is already step one.
  const [shown, setShown] = useState(visible);
  if (visible !== shown) {
    setShown(visible);
    if (visible) setIndex(0);
  }

  const step = steps[Math.min(index, steps.length - 1)];
  const target = step?.target;
  // Before paint: under the New Architecture the measurement answers at once, so a step never
  // draws its words around the last step's hole.
  useLayoutEffect(() => {
    if (!visible || target === undefined) return;
    setMeasured(undefined);
    target.current?.measureInWindow((x, y, width, height) => setMeasured({ x, y, width, height }));
  }, [visible, target]);

  if (step === undefined) return null;

  const last = index >= steps.length - 1;
  const next = () => (last ? onDone() : setIndex(index + 1));
  const layout = guideLayout(measured, viewport);

  const bubbleSpot: ViewStyle | undefined =
    layout === undefined
      ? undefined
      : layout.bubble.below
        ? {
            position: 'absolute',
            left: layout.bubble.left,
            width: layout.bubble.width,
            top: layout.bubble.top,
          }
        : {
            position: 'absolute',
            left: layout.bubble.left,
            width: layout.bubble.width,
            bottom: layout.bubble.bottom,
          };

  return (
    <ModalStage
      visible={visible}
      onRequestClose={onDone}
      // ADR-0198 §1: no timing that follows a setting.
      animationType="fade"
      layer="popover"
    >
      <View style={s.stage}>
        {/* The dim, and the one press surface under the bubble: a tap anywhere off it is Next.
            Hidden from a listener, as the popover's backdrop is — the bubble's controls carry
            the names, and a second unnamed button spanning the window is noise. */}
        <Pressable
          style={StyleSheet.absoluteFill}
          onPress={next}
          accessibilityElementsHidden
          importantForAccessibility="no-hide-descendants"
          testID="guide-dim"
        >
          {layout === undefined ? (
            <View style={[StyleSheet.absoluteFill, s.scrim]} />
          ) : (
            <Svg width={viewport.width} height={viewport.height} style={StyleSheet.absoluteFill}>
              <Path
                d={spotlightPath(layout.hole, viewport)}
                fill={theme.color.scrim}
                fillRule="evenodd"
              />
            </Svg>
          )}
        </Pressable>

        <View style={[s.bubble, layout === undefined ? s.bubbleCentred : bubbleSpot]}>
          {layout === undefined ? null : (
            <View
              style={[
                s.arrow,
                layout.bubble.below ? s.arrowAbove : s.arrowBelow,
                { left: layout.arrowLeft },
              ]}
            />
          )}

          <Text style={s.title}>{step.title}</Text>
          <Text style={s.body}>{step.body}</Text>

          <View style={s.foot}>
            <Text style={s.count}>{GUIDE_COPY.count(index + 1, steps.length)}</Text>
            <Button
              label={GUIDE_COPY.skip}
              accessibilityLabel={GUIDE_COPY.skipName}
              variant="secondary"
              size="sm"
              onPress={onDone}
            />
            <Button label={last ? GUIDE_COPY.last : GUIDE_COPY.next} size="sm" onPress={next} />
          </View>
        </View>
      </View>
    </ModalStage>
  );
}

const ARROW = theme.size.popoverArrow;

const s = StyleSheet.create({
  // Centred, which is where the bubble stands until it knows where its target is.
  stage: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  scrim: { backgroundColor: theme.color.scrim },
  bubble: {
    backgroundColor: theme.color.surface,
    borderWidth: 1,
    borderColor: theme.color.line,
    borderRadius: theme.radius.popover,
    padding: theme.space.md,
    gap: theme.space.xs,
    ...theme.shadow.popover,
  },
  bubbleCentred: { alignSelf: 'stretch', marginHorizontal: theme.size.gutter },
  // 7.6's arrow: two of its four borders, so it continues the outline rather than floating.
  arrow: {
    position: 'absolute',
    width: ARROW,
    height: ARROW,
    backgroundColor: theme.color.surface,
    borderColor: theme.color.line,
    transform: [{ rotate: '45deg' }],
  },
  arrowAbove: { top: -ARROW / 2, borderTopWidth: 1, borderLeftWidth: 1 },
  arrowBelow: { bottom: -ARROW / 2, borderBottomWidth: 1, borderRightWidth: 1 },
  title: { ...theme.type.cardTitle, color: theme.color.ink },
  body: { ...theme.type.tiny, color: theme.color.ink },
  foot: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    marginTop: theme.space.xs,
  },
  count: { ...theme.num.xs, ...theme.tabular, color: theme.color.muted, flex: 1 },
});
