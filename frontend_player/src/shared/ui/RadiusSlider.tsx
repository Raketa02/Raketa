/**
 * The radius slider, per design-system 6.10 — one number, on a track, in whole steps.
 *
 * ## The row is the control, not the thumb
 *
 * A press anywhere on the 44pt row moves the value to that point and the pan continues from
 * there. That is what gets the control to the touch minimum without a `hitSlop` entry, and
 * it is also the behaviour a thumb-only slider gets wrong: the player who taps the far end
 * of the track expects the far end of the range, not nothing.
 *
 * ## It is adjustable, and that is not decoration
 *
 * `adjustable`, with an `increment` and a `decrement` action, because **a drag-only slider
 * is unusable with a screen reader and with a hardware keyboard** — and this is the control
 * that most often ships that way. The two actions are the whole mechanism; no visible
 * plus and minus are drawn, since two more 44pt targets beside a slider would be a second
 * control competing for the same value.
 *
 * The announced `text` carries **both** the figure and the plain words, as one value. They
 * are one fact rendered twice for whoever is looking, and reading them as two values would
 * say the control has two — which is why the figure and the line beneath it are hidden from
 * assistive technology here rather than read a second time on the way past.
 *
 * ## Every number is the caller's, and so is every word
 *
 * This file holds no minimum, no maximum, no step and no default: they are served, they are
 * re-validated on the write path, and they are product's to retune without a client release
 * (6.10). What arrives instead is where the thumb goes and what the figure says — so the
 * snapping stays a rule with its own tests, and the same control draws a served range today
 * and whatever it becomes tomorrow. `onSlideTo` reports **where along the track a finger
 * is**; what radius that is remains the caller's answer.
 *
 * The thumb does not animate. It tracks the finger, and an accessibility action changes the
 * value at once — there is nothing here for reduced motion to switch off.
 */

import { useRef, useState } from 'react';
import {
  PanResponder,
  StyleSheet,
  Text,
  View,
  type LayoutChangeEvent,
  type ViewStyle,
} from 'react-native';

import { theme } from './theme';

const slider = theme.size.radiusSlider;

/** The thumb and its ring together — 26pt, and the width the track is inset by at each end. */
const THUMB_OUTER = slider.thumb + 2 * slider.thumbRing;

export interface RadiusSliderProps {
  /** The value itself, for what assistive technology is told. Never drawn from directly. */
  readonly value: number;
  readonly minimum: number;
  readonly maximum: number;
  /** Where the thumb sits: 0 at the start of the track, 1 at its end. The caller's scale. */
  readonly fraction: number;
  /**
   * Where along the track the finger is, on a press and on every move of a pan.
   *
   * Reported unclamped — a pan that leaves the row sideways still means an end of it, and
   * which value that is belongs to whoever owns the bounds.
   */
  readonly onSlideTo: (fraction: number) => void;
  readonly onIncrement: () => void;
  readonly onDecrement: () => void;
  /** The value as words, e.g. `12 km`. */
  readonly figure: string;
  /**
   * The widest the figure can get, drawn invisibly so the box reserves its width.
   *
   * Dragging from 9 to 10 must not move the text under the finger that is moving it, and a
   * box sized to the value it currently holds would do exactly that.
   */
  readonly widestFigure: string;
  /** One line beneath the figure: what this distance means, in plain words. */
  readonly words: string;
  /** What the control is called. */
  readonly accessibilityLabel: string;
  /** The figure and the words as **one** announcement — see above. */
  readonly accessibilityValueText: string;
}

export function RadiusSlider({
  value,
  minimum,
  maximum,
  fraction,
  onSlideTo,
  onIncrement,
  onDecrement,
  figure,
  widestFigure,
  words,
  accessibilityLabel,
  accessibilityValueText,
}: RadiusSliderProps) {
  const [rowWidth, setRowWidth] = useState(0);

  /**
   * Where the touch began, in both frames of reference.
   *
   * `locationX` is measured against the **touch's target**, not against whoever ends up
   * responding to it — so a press that landed on the track or the thumb would arrive in
   * that child's coordinates and read low by the track's inset, or as nearly zero anywhere
   * on the thumb. `pointerEvents="box-only"` on the row below is what stops that: it makes
   * the row itself the target and its children untouchable, which is also the truth about
   * them — the track and the thumb are drawings of the value, not controls.
   *
   * A move then reports a **page** coordinate rather than a row one. Carrying the grant's
   * own two numbers turns every later page position back into a row position by
   * subtraction, with nothing to measure.
   */
  const origin = useRef({ inTheRow: 0, onThePage: 0 });

  /**
   * The pan handlers are created once, so they must not close over a render's props. A ref
   * holding the current one is what keeps a drag reporting against the width and the
   * callback that are on screen rather than the ones that were there when the touch began.
   */
  const slideTo = (x: number) => {
    const travel = rowWidth - THUMB_OUTER;
    // Before layout there is no track to have pressed, and a division by nothing is not a
    // position. A press then is a press on a control that is not on screen yet.
    if (travel <= 0) return;
    onSlideTo((x - THUMB_OUTER / 2) / travel);
  };
  const latest = useRef(slideTo);
  latest.current = slideTo;

  const responder = useRef(
    PanResponder.create({
      // The press itself moves the value: the row is the control (6.10).
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,
      // The scroll view above may not take the gesture back mid-drag. A slider that lost
      // the finger to a scroll would leave the value wherever the drag was interrupted.
      onPanResponderTerminationRequest: () => false,
      onPanResponderGrant: (event) => {
        origin.current = {
          inTheRow: event.nativeEvent.locationX,
          onThePage: event.nativeEvent.pageX,
        };
        latest.current(event.nativeEvent.locationX);
      },
      onPanResponderMove: (_event, gesture) => {
        latest.current(origin.current.inTheRow + (gesture.moveX - origin.current.onThePage));
      },
    }),
  ).current;

  // Clamped for drawing only: a radius recorded under bounds that have since been narrowed
  // is still a fact about the player, and it arrives here as a fraction off the end.
  const onTheTrack = Math.min(Math.max(fraction, 0), 1);
  const travel = Math.max(rowWidth - THUMB_OUTER, 0);

  return (
    <View>
      {/* Hidden from assistive technology, both of them: the control below announces the
          figure and the words as one value, and read again here they would be a second and
          a third reading of the same number. */}
      <View
        style={s.reading}
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
      >
        <View style={s.figureBox}>
          <Text style={[s.figure, s.figureReserve]}>{widestFigure}</Text>
          <Text style={[s.figure, s.figureValue]}>{figure}</Text>
        </View>
        {/* One line, and its height is reserved whether or not the words fill it — the
            band changes under a moving finger, and a line that appeared would push the
            track away from it. */}
        <Text style={s.words} numberOfLines={1}>
          {words}
        </Text>
      </View>

      <View
        {...responder.panHandlers}
        onLayout={(event: LayoutChangeEvent) => setRowWidth(event.nativeEvent.layout.width)}
        accessibilityRole="adjustable"
        accessibilityLabel={accessibilityLabel}
        accessibilityValue={{
          min: minimum,
          max: maximum,
          now: value,
          text: accessibilityValueText,
        }}
        accessibilityActions={ACTIONS}
        // The row is the control and its children are drawings: this makes the row the
        // touch target, so `locationX` is measured against the surface being pressed.
        pointerEvents="box-only"
        onAccessibilityAction={(event) => {
          if (event.nativeEvent.actionName === 'increment') onIncrement();
          if (event.nativeEvent.actionName === 'decrement') onDecrement();
        }}
        style={s.row}
      >
        {/* Inset by half a thumb at each end, so the thumb stays inside the row at both
            ends and the fill still measures from the track's own start — which is what
            makes a zero-length fill at the minimum correct rather than a missing one. */}
        <View style={s.track}>
          <View style={[s.fill, { width: `${onTheTrack * 100}%` }]} />
        </View>
        <View style={[s.thumb, thumbAt(onTheTrack * travel)]}>
          <View style={s.thumbDisc} />
        </View>
      </View>
    </View>
  );
}

/** Each moves exactly one step. The label is what a screen reader offers in its rotor. */
const ACTIONS = [
  { name: 'increment', label: 'Further out' },
  { name: 'decrement', label: 'Closer in' },
];

function thumbAt(left: number): ViewStyle {
  return { left };
}

const s = StyleSheet.create({
  reading: { marginBottom: theme.space.xs },
  // Content-sized, so the reserved box is the figure's width and not the screen's.
  figureBox: { alignSelf: 'flex-start' },
  figure: { ...theme.num.xl, ...theme.tabular, color: theme.color.ink },
  /** In flow and invisible: this is what gives the box its width. */
  figureReserve: { opacity: 0 },
  /** Over it, so the value never decides how wide its own box is. */
  figureValue: { ...StyleSheet.absoluteFillObject },
  words: { ...theme.type.tiny, color: theme.color.muted, minHeight: theme.type.tiny.lineHeight },
  // The whole of this is the touch surface — 44pt, with nothing granted to it.
  row: { height: slider.row, justifyContent: 'center' },
  track: {
    height: slider.trackHeight,
    marginHorizontal: THUMB_OUTER / 2,
    borderRadius: theme.radius.bar,
    backgroundColor: theme.color.line2,
    overflow: 'hidden',
  },
  // `night` and not `coral`: a filled portion states a value somebody set, and coral is for
  // actions (1.2). The meter fills in `night` for the same reason (7.3).
  fill: { height: '100%', borderRadius: theme.radius.bar, backgroundColor: theme.color.night },
  /** The ring is the entire reason the thumb reads: the fill behind it is `night` too. */
  thumb: {
    position: 'absolute',
    width: THUMB_OUTER,
    height: THUMB_OUTER,
    borderRadius: THUMB_OUTER / 2,
    backgroundColor: theme.color.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  thumbDisc: {
    width: slider.thumb,
    height: slider.thumb,
    borderRadius: slider.thumb / 2,
    backgroundColor: theme.color.night,
  },
});
