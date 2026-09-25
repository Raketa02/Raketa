/**
 * **The fast filter** — the sport pill in a group page's header, and the bar it unfolds into
 * (play 41–42, PRD #500 stories 52–58, [#513](https://github.com/Raketa02/Raketa/issues/513)).
 *
 * ## The pill
 *
 * The sport's dot, its name and a faint chevron pointing the way it unfolds. It is a **chip** in
 * everything but its fill — 6.2's height, corner, label role and `hit.chip` — because a filter
 * over what is on screen is what a chip is; it takes `paper2`, the header's recess, because it
 * sits on paper rather than on a card. **A player rated in one sport gets a plain label**: the
 * same dot and name, no chevron, and nothing to press, because a choice of one is not a choice.
 *
 * ## The bar
 *
 * A floating white bar with the popover's shadow — it floats, so 4.3 gives it one — that grows
 * **leftwards over the group's name** from where the pill was. The current sport sits dark at its
 * right end, exactly where the pill stood, with the chevron flipped to say which way it folds; the
 * other sports **slide out from under it one by one**, nearest first. A tap on another sport picks
 * it; a tap on the current one, or anywhere else on the page (the screen's backdrop), folds the bar
 * and changes nothing.
 *
 * **The unfold runs on the UI thread** (ADR-0176 §2's rule for anything that moves per frame): one
 * shared value from 0 to 1 over `motion.unfold`, `easeDecel`, read by the bar's width and by each
 * sport's opacity and slide. Nothing is scaled — iOS rasterises a scaled layer blurred, which the
 * radar learned (ADR-0176 §2, amended) — the bar's **width** grows and a clip inside it reveals
 * the row, which is laid out once at its whole width, right-aligned. The width is two numbers the
 * layout measures, the row's and the current pill's, so the bar is drawn at nothing until both are
 * in; that is one frame on a device, and a suite, which lays nothing out, still finds every
 * sport by its name. **Under reduced motion** the value starts at 1 and the bar is simply open.
 * **Folding is immediate** — see `motion.unfold`.
 *
 * Never a `Modal`, and nothing here is one: the bar is a layer of the page (ADR-0178).
 */

import { useEffect, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import Animated, {
  Easing,
  Extrapolation,
  interpolate,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
  type SharedValue,
} from 'react-native-reanimated';

import { sportColour, sportLabel } from '@/features/onboarding/types';
import { theme, useReducedMotion } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import { GROUPS_COPY } from './groupsCopy';
import { sportPillLabel } from './groupsPresentation';

const COPY = GROUPS_COPY.filter;

const PAD = theme.size.groupPage.filterPad;

const EASE = Easing.bezier(
  theme.motion.easeDecel.x1,
  theme.motion.easeDecel.y1,
  theme.motion.easeDecel.x2,
  theme.motion.easeDecel.y2,
);

/**
 * How much of the unfold each sliding sport takes — **half**, the first starting at once and the
 * last finishing with the bar, the rest spread evenly between. Three sports is a step of a
 * quarter, so each starts while the one before it is halfway out: *one by one*, and still one
 * movement.
 */
const OPTION_SHARE = 0.5;

/** How far a sport travels out from under the current one — `space.md`, a pill's own inset. */
const SLIDE = theme.space.md;

/** The sport's dot and its name — what the pill, the plain label and every pill in the bar draw. */
function SportName({ sport, onInk = false }: { readonly sport: Sport; readonly onInk?: boolean }) {
  return (
    <>
      <View
        style={[s.dot, { backgroundColor: sportColour(sport) }]}
        accessibilityElementsHidden
        importantForAccessibility="no"
      />
      <Text style={[s.label, onInk ? s.labelOnInk : undefined]} numberOfLines={1}>
        {sportLabel(sport)}
      </Text>
    </>
  );
}

/** The chevron — faint, a direction rather than a word, and hidden: the name says what it does. */
function Chevron({ mark, onInk = false }: { readonly mark: string; readonly onInk?: boolean }) {
  return (
    <Text
      style={[s.chevron, onInk ? s.chevronOnInk : undefined]}
      accessibilityElementsHidden
      importantForAccessibility="no"
    >
      {mark}
    </Text>
  );
}

export interface SportPillProps {
  /** The filter's sports. One is a plain label. */
  readonly sports: readonly Sport[];
  readonly sport: Sport;
  readonly onUnfold: () => void;
}

export function SportPill({ sports, sport, onUnfold }: SportPillProps) {
  if (sports.length <= 1) {
    return (
      <View accessible accessibilityLabel={sportPillLabel(sport)} style={[s.pill, s.pillClosed]}>
        <SportName sport={sport} />
      </View>
    );
  }

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={sportPillLabel(sport)}
      accessibilityHint={COPY.pillHint}
      onPress={onUnfold}
      hitSlop={theme.hit.chip}
      style={({ pressed }) => [s.pill, s.pillClosed, pressed ? s.pressed : undefined]}
    >
      <SportName sport={sport} />
      <Chevron mark={COPY.unfold} />
    </Pressable>
  );
}

export interface SportBarProps {
  /** Every sport the filter lists, in the registry's order. */
  readonly sports: readonly Sport[];
  /** The one the page is on — drawn last, dark. */
  readonly sport: Sport;
  /** A sport was tapped: another one picks it, the current one only folds. */
  readonly onChoose: (sport: Sport) => void;
}

export function SportBar({ sports, sport, onChoose }: SportBarProps) {
  const reduced = useReducedMotion();
  const others = sports.filter((other) => other !== sport);

  const progress = useSharedValue(reduced ? 1 : 0);
  const [rowWidth, setRowWidth] = useState<number>();
  const [pillWidth, setPillWidth] = useState<number>();
  const measured = rowWidth !== undefined && pillWidth !== undefined;
  const closed = (pillWidth ?? 0) + 2 * PAD;
  const open = (rowWidth ?? 0) + 2 * PAD;

  useEffect(() => {
    if (!measured || reduced) return;
    progress.value = withTiming(1, { duration: theme.motion.unfold, easing: EASE });
  }, [measured, reduced, progress]);

  const grow = useAnimatedStyle(
    () =>
      measured
        ? { opacity: 1, width: interpolate(progress.value, [0, 1], [closed, open]) }
        : { opacity: 0 },
    [measured, closed, open],
  );

  return (
    <Animated.View testID="sport-bar" style={[s.bar, grow]}>
      <View style={s.clip}>
        <View
          testID="sport-bar-row"
          style={s.row}
          onLayout={(event) => setRowWidth(event.nativeEvent.layout.width)}
        >
          {others.map((other, at) => (
            <BarOption
              key={other}
              sport={other}
              // Nearest the current sport moves first: the row reads leftwards out of it.
              order={others.length - 1 - at}
              count={others.length}
              progress={progress}
              onPress={() => onChoose(other)}
            />
          ))}
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={sportLabel(sport)}
            accessibilityState={{ selected: true }}
            onPress={() => onChoose(sport)}
            onLayout={(event) => setPillWidth(event.nativeEvent.layout.width)}
            hitSlop={theme.hit.chip}
            style={({ pressed }) => [s.pill, s.pillCurrent, pressed ? s.pressed : undefined]}
          >
            <SportName sport={sport} onInk />
            <Chevron mark={COPY.fold} onInk />
          </Pressable>
        </View>
      </View>
    </Animated.View>
  );
}

interface BarOptionProps {
  readonly sport: Sport;
  /** 0 for the sport beside the current one, counting leftwards. */
  readonly order: number;
  readonly count: number;
  readonly progress: SharedValue<number>;
  readonly onPress: () => void;
}

function BarOption({ sport, order, count, progress, onPress }: BarOptionProps) {
  const step = count > 1 ? (1 - OPTION_SHARE) / (count - 1) : 0;
  const start = order * step;
  const end = start + OPTION_SHARE;

  const slide = useAnimatedStyle(
    () => ({
      opacity: interpolate(progress.value, [start, end], [0, 1], Extrapolation.CLAMP),
      transform: [
        {
          translateX: interpolate(progress.value, [start, end], [SLIDE, 0], Extrapolation.CLAMP),
        },
      ],
    }),
    [start, end],
  );

  return (
    <Animated.View style={slide}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={sportLabel(sport)}
        accessibilityState={{ selected: false }}
        onPress={onPress}
        hitSlop={theme.hit.chip}
        style={({ pressed }) => [s.pill, pressed ? s.pressed : undefined]}
      >
        <SportName sport={sport} />
      </Pressable>
    </Animated.View>
  );
}

const s = StyleSheet.create({
  // 6.2's chip, less its border: the pill's fill says which of the three it is.
  pill: {
    minHeight: theme.size.chip,
    paddingHorizontal: theme.space.md,
    paddingVertical: theme.space.xxs,
    borderRadius: theme.radius.pill,
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.xs,
  },
  pillClosed: { backgroundColor: theme.color.paper2 },
  // Selected is ink-filled, as a selected chip is — a state, never coral.
  pillCurrent: { backgroundColor: theme.color.ink },
  pressed: { opacity: 0.7 },
  // Round, as the group's own dots are (`SportDots`), at the one size a sport dot has.
  dot: {
    width: theme.size.sportDot,
    height: theme.size.sportDot,
    borderRadius: theme.radius.dot,
  },
  label: { ...theme.type.chip, color: theme.color.ink },
  labelOnInk: { color: theme.color.surface },
  chevron: { ...theme.type.chip, color: theme.color.muted },
  chevronOnInk: { color: theme.color.onDarkTiny },
  bar: {
    height: theme.size.chip + 2 * PAD,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.color.surface,
    ...theme.shadow.popover,
  },
  // The shadow is the bar's and the clip is this: a view that clipped its own children would
  // clip its own shadow with them on iOS.
  clip: {
    ...StyleSheet.absoluteFillObject,
    borderRadius: theme.radius.pill,
    overflow: 'hidden',
  },
  // Laid out once at its whole width, against the bar's right edge, so the growing bar uncovers
  // it leftwards and the current pill never moves.
  row: {
    position: 'absolute',
    top: PAD,
    right: PAD,
    flexDirection: 'row',
    alignItems: 'center',
  },
});
