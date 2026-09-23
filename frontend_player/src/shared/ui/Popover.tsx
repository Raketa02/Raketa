/**
 * The anchored popover and the mark that opens it, per design-system 7.6 and 6.5.
 *
 * ```
 * width 250   background surface   1pt line   radius 13   padding 12
 * shadow: the popover elevation
 * arrow: an 11 × 11 rotated square carrying TWO of its four borders
 * ```
 *
 * **The arrow carries two borders so it reads as a continuation of the outline rather than
 * a floating diamond.**
 *
 * ## Three decisions worth knowing
 *
 * **It sits on `ModalStage`, like the sheet, and that is what settles 5.2 and 9.3 at once.**
 * 7.6 requires the popover to render through the overlay root and never as a descendant of a
 * dark card, because the dark card repaints its children and `zIndex` is scoped to the
 * parent in React Native. On iOS the stage is a `Modal`, a separate native window that is not
 * in the layer order at all; on Android it is a layer 9.3's root-level host draws above
 * everything, ordered over a toast by `theme.layer.popover` (ADR-0178).
 *
 * **Position is measured from the trigger, and the trigger is one prop doing two jobs** —
 * the popover is anchored to it and focus returns to it on close. Measurement happens when
 * the popover opens: React Native resolves `measureInWindow` synchronously under the New
 * Architecture, so the first render is already anchored. Where it does not arrive — the
 * old architecture's next frame, and the test renderer, which never calls the callback —
 * **the card centres itself and draws no arrow**, rather than pointing at nothing.
 * Horizontal position is clamped inside the screen's gutters: a mark two-thirds across
 * would otherwise lose its right edge.
 *
 * **The backdrop dismisses but does not dim.** A popover explains a word on the screen
 * behind it; dimming that screen would make the explanation look like a decision. The
 * sheet dims because it *is* one.
 *
 * Accessibility (Part 13): `accessibilityViewIsModal` on iOS, siblings hidden on Android
 * by the screen spreading {@link behindOverlay}, an explicit close control, and focus moved
 * to the popover's heading on open and back to the mark on close.
 */

import { forwardRef, useEffect, useRef, useState } from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
  type LayoutRectangle,
} from 'react-native';

import { CloseControl } from './CloseControl';
import { InfoGlyph } from './InfoGlyph';
import { ModalStage } from './ModalStage';
import { moveAccessibilityFocus, useReducedMotion, type FocusTarget } from './overlay';
import { theme } from './theme';

export interface InfoMarkProps {
  readonly onPress: () => void;
  /** What it explains — "What the Level means", never "Info". */
  readonly accessibilityLabel: string;
  /** 5.2's repaint, for a mark inside a dark card. */
  readonly onDark?: boolean;
}

/**
 * The information mark: 6.5's 20pt info button, which is the shared 14pt glyph with the
 * 3pt of padding that makes up the difference, and a 44pt reachable area from `hitSlop`.
 *
 * The ref is forwarded because the popover both anchors to this control and returns focus
 * to it.
 */
export const InfoMark = forwardRef<View, InfoMarkProps>(function InfoMark(
  { onPress, accessibilityLabel, onDark = false },
  ref,
) {
  return (
    <Pressable
      ref={ref}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      onPress={onPress}
      hitSlop={theme.hit.infoMark}
      style={({ pressed }) => [s.mark, pressed ? s.markPressed : undefined]}
    >
      <InfoGlyph onDark={onDark} />
    </Pressable>
  );
});

export interface PopoverProps {
  readonly visible: boolean;
  /** The mark this belongs to: measured for position, focused again on close. */
  readonly trigger: FocusTarget | undefined;
  readonly title: string;
  readonly body: string;
  /** What closes — "Close what the Level means", never "Close". */
  readonly closeLabel: string;
  readonly onClose: () => void;
}

export function Popover({ visible, trigger, title, body, closeLabel, onClose }: PopoverProps) {
  const reducedMotion = useReducedMotion();
  const { width: screenWidth } = useWindowDimensions();
  const heading = useRef<View | null>(null);
  const [anchor, setAnchor] = useState<LayoutRectangle>();
  const wasVisible = useRef(visible);

  useEffect(() => {
    if (visible === wasVisible.current) return;
    wasVisible.current = visible;

    if (!visible) {
      setAnchor(undefined);
      moveAccessibilityFocus(trigger);
      return;
    }
    trigger?.current?.measureInWindow((x, y, width, height) => setAnchor({ x, y, width, height }));
    moveAccessibilityFocus(heading);
  }, [visible, trigger]);

  const width = theme.size.popoverWidth;
  const gutter = theme.size.gutter;
  const arrow = theme.size.popoverArrow;

  const centre = anchor === undefined ? screenWidth / 2 : anchor.x + anchor.width / 2;
  const left = clamp(centre - width / 2, gutter, Math.max(gutter, screenWidth - width - gutter));
  const arrowLeft = clamp(
    centre - left - arrow / 2,
    theme.radius.popover,
    width - theme.radius.popover - arrow,
  );

  return (
    <ModalStage
      visible={visible}
      // Android's hardware back. iOS never asks.
      onRequestClose={onClose}
      animationType={reducedMotion ? 'none' : 'fade'}
      layer="popover"
    >
      <View style={s.stage} testID="popover-stage">
        {/* Dismissal, not a control: the popover's close carries the name, and a second
            unnamed button spanning the screen is noise in the reading order. */}
        <Pressable
          style={StyleSheet.absoluteFill}
          onPress={onClose}
          accessibilityElementsHidden
          importantForAccessibility="no-hide-descendants"
        />

        <View
          accessibilityViewIsModal
          style={[
            s.card,
            { width },
            anchor === undefined
              ? undefined
              : { position: 'absolute', left, top: anchor.y + anchor.height + theme.space.xs },
          ]}
        >
          {anchor === undefined ? null : <View style={[s.arrow, { left: arrowLeft }]} />}

          <View style={s.head}>
            {/* `accessible` on the wrapper, not the Text: focus has to land on a host
                element this component holds a ref to. */}
            <View ref={heading} accessible accessibilityRole="header" style={s.titleBox}>
              <Text style={s.title}>{title}</Text>
            </View>
            <CloseControl onPress={onClose} accessibilityLabel={closeLabel} />
          </View>

          <Text style={s.body}>{body}</Text>
        </View>
      </View>
    </ModalStage>
  );
}

function clamp(value: number, low: number, high: number): number {
  return Math.min(Math.max(value, low), high);
}

const s = StyleSheet.create({
  mark: { padding: theme.space.xxs },
  markPressed: { opacity: 0.7 },
  // Centred, which is where the card sits until it knows where its mark is.
  stage: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  card: {
    backgroundColor: theme.color.surface,
    borderWidth: 1,
    borderColor: theme.color.line,
    borderRadius: theme.radius.popover,
    padding: theme.space.md,
    gap: theme.space.xs,
    ...theme.shadow.popover,
  },
  arrow: {
    position: 'absolute',
    top: -theme.size.popoverArrow / 2,
    width: theme.size.popoverArrow,
    height: theme.size.popoverArrow,
    backgroundColor: theme.color.surface,
    // Two of the four borders, so the arrow continues the card's outline instead of
    // floating beside it.
    borderTopWidth: 1,
    borderLeftWidth: 1,
    borderColor: theme.color.line,
    transform: [{ rotate: '45deg' }],
  },
  head: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  titleBox: { flex: 1 },
  title: { ...theme.type.cardTitle, color: theme.color.ink },
  body: { ...theme.type.tiny, color: theme.color.ink },
});
