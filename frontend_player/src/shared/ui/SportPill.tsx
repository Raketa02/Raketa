/**
 * **The sport pill** — the pill in a page's header, and the bar it unfolds into: the group page's
 * fast filter (play 41–42, PRD #500 stories 52–58, [#513](https://github.com/Raketa02/Raketa/issues/513))
 * and Rankings' sport, **one control** since [#774](https://github.com/Raketa02/Raketa/issues/774).
 * A page draws it through `SportPillFrame`, which holds it open or folded; this is the drawing.
 *
 * **Every word is the caller's** (`SportPillWords`, `AnotherSport`) — a sport's name, the pill's
 * name and hint, and *+ Another sport*'s — because what pressing the pill does is the page's to
 * say: *Shows this group for another sport you play* is the group page's and no other's. The two
 * chevrons are the drawing's own, a direction rather than a word, and hidden.
 *
 * ## The pill
 *
 * The sport's dot, its name and a faint chevron pointing the way it unfolds. It is a **chip** in
 * everything but its fill — 6.2's height, corner, label role and `hit.chip` — because a filter
 * over what is on screen is what a chip is; it takes `paper2`, the header's recess, because it
 * sits on paper rather than on a card. **A player rated in one sport gets a plain label**: the
 * same dot and name, no chevron, and nothing to press, because a choice of one is not a choice —
 * **unless there is a sport left to offer**, when the pill unfolds onto *+ Another sport* alone.
 *
 * ## The bar
 *
 * A floating white bar with the popover's shadow — it floats, so 4.3 gives it one — that grows
 * **leftwards over the group's name** from where the pill was. The current sport sits dark at its
 * right end, exactly where the pill stood, with the chevron flipped to say which way it folds; the
 * other sports **slide out from under it one by one**, nearest first. A tap on another sport picks
 * it; a tap on the current one, or anywhere else on the page (the frame's backdrop), folds the bar
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
 * **It can end with *+ Another sport*** — the group page's, while there is a sport left to offer
 * ([#731](https://github.com/Raketa02/Raketa/issues/731), ADR-0200 §4): the farthest pill from the
 * current sport, the last to slide out, so it is where the row ends. It is no sport — no dot, the
 * plus in front — and its press is the page's: the group page opens *Which sports do you play?*
 * over the sports the reader is unrated in. A page that hands no `another` draws none.
 *
 * **Open, it never ends across what it must cover whole** — the group's tile (#529): where its
 * sports would stop somewhere over the tile, a sliver of it showed past the bar's round end, so the
 * bar opens that much further and covers it whole (`BarCover`, which the frame measures). Where they
 * stop short of the tile, the bar ends where they do. A page with nothing to cover hands nothing.
 *
 * Never a `Modal`, and nothing here is one: the bar is a layer of the page (ADR-0178).
 */

import { useEffect, useState, type ReactNode } from 'react';
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

import type { Sport } from '@/shared/vocabulary/sport';

import { useReducedMotion } from './overlay';
import { theme } from './theme';

/**
 * The bar's inset round its pills — named for the page that first drew the bar (#513), and the
 * bar's wherever it is drawn: `chip` + 2 × it is the bar's reachable 45.
 */
const PAD = theme.size.groupPage.filterPad;

/** The pill's faint chevron, and the bar's once it has unfolded — the fold's direction. */
const UNFOLD = '‹';
const FOLD = '›';

/** **What the pill says**, in the page's words — nothing here is the control's own. */
export interface SportPillWords {
  /** A sport's name: drawn beside its dot, and what its pill in the bar is called. */
  readonly sportName: (sport: Sport) => string;
  /** The pill, spoken — *Sport: Padel* — and the plain label's name for one sport. */
  readonly pillLabel: (sport: Sport) => string;
  /** What pressing the pill does, where there is another sport to switch to. */
  readonly pillHint: string;
}

/**
 * ***+ Another sport***, the bar's last way out (#731) — a page's that offers one, in its words:
 * drawn with its plus and spoken without it.
 */
export interface AnotherSport {
  /** Spoken — *Another sport*. */
  readonly label: string;
  /** Drawn — *+ Another sport*. */
  readonly drawn: string;
  /** What pressing it does. */
  readonly hint: string;
  /** What pressing the pill does where this is its only other choice — no sport to switch to. */
  readonly pillHint: string;
  readonly onPress: () => void;
}

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
function SportName({
  name,
  sport,
  onInk = false,
}: {
  readonly name: string;
  readonly sport: Sport;
  readonly onInk?: boolean;
}) {
  return (
    <>
      <View
        style={[s.dot, { backgroundColor: theme.sport[sport] }]}
        accessibilityElementsHidden
        importantForAccessibility="no"
      />
      <Text style={[s.label, onInk ? s.labelOnInk : undefined]} numberOfLines={1}>
        {name}
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
  /** The sports it switches between. One is a plain label, unless there is another sport to offer. */
  readonly sports: readonly Sport[];
  readonly sport: Sport;
  readonly words: SportPillWords;
  /** The bar ends with *+ Another sport* — so even one sport unfolds (#731). */
  readonly another?: AnotherSport;
  readonly onUnfold: () => void;
}

export function SportPill({ sports, sport, words, another, onUnfold }: SportPillProps) {
  const switches = sports.length > 1;
  const name = words.sportName(sport);
  if (!switches && another === undefined) {
    return (
      <View accessible accessibilityLabel={words.pillLabel(sport)} style={[s.pill, s.pillClosed]}>
        <SportName name={name} sport={sport} />
      </View>
    );
  }

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={words.pillLabel(sport)}
      accessibilityHint={switches || another === undefined ? words.pillHint : another.pillHint}
      onPress={onUnfold}
      hitSlop={theme.hit.chip}
      style={({ pressed }) => [s.pill, s.pillClosed, pressed ? s.pressed : undefined]}
    >
      <SportName name={name} sport={sport} />
      <Chevron mark={UNFOLD} />
    </Pressable>
  );
}

/**
 * **What the open bar must not end across**, as two of its own widths: the one at which its round
 * end reaches the thing — the group's tile — and the one that covers it whole.
 */
export interface BarCover {
  readonly reaches: number;
  readonly whole: number;
}

export interface SportBarProps {
  /** Every sport the pill lists, in the order the page hands them. */
  readonly sports: readonly Sport[];
  /** The one the page is on — drawn last, dark. */
  readonly sport: Sport;
  readonly words: SportPillWords;
  /** A sport was tapped: another one picks it, the current one only folds. */
  readonly onChoose: (sport: Sport) => void;
  /** What the open bar covers whole rather than ending across — absent where nothing is. */
  readonly cover?: BarCover;
  /** *+ Another sport* — absent where there is none to offer (#731). */
  readonly another?: AnotherSport;
}

/** The bar's open width: its sports', or past the tile whole where they would end across it. */
function openWidth(sports: number, cover: BarCover | undefined): number {
  return cover !== undefined && sports > cover.reaches ? Math.max(sports, cover.whole) : sports;
}

export function SportBar({ sports, sport, words, onChoose, cover, another }: SportBarProps) {
  const reduced = useReducedMotion();
  const others = sports.filter((other) => other !== sport);
  // Everything that slides out from under the current sport: *+ Another sport*, the farthest, first.
  const sliding = others.length + (another === undefined ? 0 : 1);

  const progress = useSharedValue(reduced ? 1 : 0);
  const [rowWidth, setRowWidth] = useState<number>();
  const [pillWidth, setPillWidth] = useState<number>();
  const measured = rowWidth !== undefined && pillWidth !== undefined;
  const closed = (pillWidth ?? 0) + 2 * PAD;
  const open = openWidth((rowWidth ?? 0) + 2 * PAD, cover);

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
          {another === undefined ? null : (
            // The farthest from the current sport, so the last out: where the row ends.
            <SlideOut order={sliding - 1} count={sliding} progress={progress}>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel={another.label}
                accessibilityHint={another.hint}
                onPress={another.onPress}
                hitSlop={theme.hit.chip}
                style={({ pressed }) => [s.pill, pressed ? s.pressed : undefined]}
              >
                <Text style={s.label} numberOfLines={1}>
                  {another.drawn}
                </Text>
              </Pressable>
            </SlideOut>
          )}
          {others.map((other, at) => (
            // Nearest the current sport moves first: the row reads leftwards out of it.
            <SlideOut
              key={other}
              order={others.length - 1 - at}
              count={sliding}
              progress={progress}
            >
              <Pressable
                accessibilityRole="button"
                accessibilityLabel={words.sportName(other)}
                accessibilityState={{ selected: false }}
                onPress={() => onChoose(other)}
                hitSlop={theme.hit.chip}
                style={({ pressed }) => [s.pill, pressed ? s.pressed : undefined]}
              >
                <SportName name={words.sportName(other)} sport={other} />
              </Pressable>
            </SlideOut>
          ))}
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={words.sportName(sport)}
            accessibilityState={{ selected: true }}
            onPress={() => onChoose(sport)}
            onLayout={(event) => setPillWidth(event.nativeEvent.layout.width)}
            hitSlop={theme.hit.chip}
            style={({ pressed }) => [s.pill, s.pillCurrent, pressed ? s.pressed : undefined]}
          >
            <SportName name={words.sportName(sport)} sport={sport} onInk />
            <Chevron mark={FOLD} onInk />
          </Pressable>
        </View>
      </View>
    </Animated.View>
  );
}

interface SlideOutProps {
  /** 0 for the pill beside the current sport, counting leftwards. */
  readonly order: number;
  /** How many pills slide out — the other sports, and *+ Another sport* where there is one. */
  readonly count: number;
  readonly progress: SharedValue<number>;
  readonly children: ReactNode;
}

/** One pill of the bar's row, sliding out from under the current sport in its turn. */
function SlideOut({ order, count, progress, children }: SlideOutProps) {
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

  return <Animated.View style={slide}>{children}</Animated.View>;
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
  // it leftwards and the current pill never moves — and what the bar opens past it is white.
  row: {
    position: 'absolute',
    top: PAD,
    right: PAD,
    flexDirection: 'row',
    alignItems: 'center',
  },
});
