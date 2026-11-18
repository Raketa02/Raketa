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
 * **Or it opens rightwards** (`opens`, [#821](https://github.com/Raketa02/Raketa/issues/821); ADR-0205
 * §5, Q19, Q37; home refactor 12, 13): Top 10's switcher stands first in its line's footer, so it
 * reads *Padel ›*, its chevron pointing the way it opens, and the bar grows **to the right** across
 * the footer — the current sport dark at its **left** end where the pill stood, its chevron turned
 * back to ‹, and the others sliding out after it in the page's order, nearest first. The same bar,
 * the same unfold, mirrored; a page's header keeps the leftward one.
 *
 * **The unfold runs on the UI thread** (ADR-0176 §2's rule for anything that moves per frame): one
 * shared value from 0 to 1 over `motion.unfold`, `easeDecel`, read by the bar's width and by each
 * sport's opacity and slide. Nothing is scaled — iOS rasterises a scaled layer blurred, which the
 * radar learned (ADR-0176 §2, amended) — the bar's **width** grows and a clip inside it reveals
 * the row, which is laid out once at its whole width against the end it opens from. The width is
 * two numbers the layout measures, the row's and the current pill's, so the bar is drawn at nothing
 * until both are in; that is one frame on a device, and a suite, which lays nothing out, still finds
 * every sport by its name. **Under reduced motion** the value starts at 1 and the bar is simply open.
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
 * **It can offer *All*** (#801): a page that lists people from every sport — New in Raketa's See all —
 * hands `ALL_SPORTS` among its choices, and the pill draws it as a sport with a two-toned dot. Which
 * choices it offers, and in what order, stays the page's.
 *
 * Never a `Modal`, and nothing here is one: the bar is a layer of the page (ADR-0178).
 */

import { useEffect, useId, useState, type ReactNode } from 'react';
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
import Svg, { Circle, Defs, LinearGradient, Stop } from 'react-native-svg';

import type { Sport } from '@/shared/vocabulary/sport';

import { useReducedMotion } from './overlay';
import { theme } from './theme';

/**
 * The bar's inset round its pills — named for the page that first drew the bar (#513), and the
 * bar's wherever it is drawn: `chip` + 2 × it is the bar's reachable 45.
 */
const PAD = theme.size.groupPage.filterPad;

/**
 * **Which way the bar opens** from the pill — `left`, over what stands before it, on a page's header;
 * `right`, across what stands after it, from Top 10's footer, where the pill stands first (#821).
 */
export type SportPillOpening = 'left' | 'right';

/**
 * The chevrons, by the way the bar opens: the pill's points the way it unfolds, and the current sport's
 * in the open bar the way it folds back.
 */
const CHEVRONS: Readonly<
  Record<SportPillOpening, { readonly unfold: string; readonly fold: string }>
> = {
  left: { unfold: '‹', fold: '›' },
  right: { unfold: '›', fold: '‹' },
};

/**
 * ***All*** — **every sport at once**, a choice beside the sports where a page lists people from all of
 * them (#801: New in Raketa's See all; the Home rows screens §5.3, home rows 12, 19). Drawn with a
 * two-toned dot, padel's into tennis's, as home rows 12 and 19 draw it: no sport's colour alone, since
 * it is none of them.
 */
export const ALL_SPORTS = 'all';

/** A choice the pill offers: a sport, or *All* where the page offers it. */
export type SportChoice = Sport | typeof ALL_SPORTS;

/** **What the pill says**, in the page's words — nothing here is the control's own. */
export interface SportPillWords<S extends SportChoice = Sport> {
  /** A sport's name: drawn beside its dot, and what its pill in the bar is called. */
  readonly sportName: (sport: S) => string;
  /** The pill, spoken — *Sport: Padel* — and the plain label's name for one sport. */
  readonly pillLabel: (sport: S) => string;
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
  readonly sport: SportChoice;
  readonly onInk?: boolean;
}) {
  return (
    <>
      {sport === ALL_SPORTS ? (
        <AllSportsDot />
      ) : (
        <View
          style={[s.dot, { backgroundColor: theme.sport[sport] }]}
          accessibilityElementsHidden
          importantForAccessibility="no"
        />
      )}
      <Text style={[s.label, onInk ? s.labelOnInk : undefined]} numberOfLines={1}>
        {name}
      </Text>
    </>
  );
}

/** *All*'s dot — padel's colour running into tennis's, corner to corner (home rows 12, 19). */
function AllSportsDot() {
  const gradient = useId();
  const r = theme.size.sportDot / 2;
  return (
    <View
      testID="all-sports-dot"
      style={s.dotBox}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <Svg width={theme.size.sportDot} height={theme.size.sportDot}>
        <Defs>
          <LinearGradient id={gradient} x1="0" y1="0" x2="1" y2="1">
            <Stop offset={0} stopColor={theme.sport.padel} />
            <Stop offset={1} stopColor={theme.sport.tennis} />
          </LinearGradient>
        </Defs>
        <Circle cx={r} cy={r} r={r} fill={`url(#${gradient})`} />
      </Svg>
    </View>
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

export interface SportPillProps<S extends SportChoice = Sport> {
  /** The sports it switches between. One is a plain label, unless there is another sport to offer. */
  readonly sports: readonly S[];
  readonly sport: S;
  readonly words: SportPillWords<S>;
  /** The bar ends with *+ Another sport* — so even one sport unfolds (#731). */
  readonly another?: AnotherSport;
  readonly onUnfold: () => void;
  /** Which way its bar opens, and so which way its chevron points — leftwards unless told. */
  readonly opens?: SportPillOpening;
}

export function SportPill<S extends SportChoice = Sport>({
  sports,
  sport,
  words,
  another,
  onUnfold,
  opens = 'left',
}: SportPillProps<S>) {
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
      <Chevron mark={CHEVRONS[opens].unfold} />
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

export interface SportBarProps<S extends SportChoice = Sport> {
  /** Every sport the pill lists, in the order the page hands them. */
  readonly sports: readonly S[];
  /** The one the page is on — drawn dark, at the end the bar opens from. */
  readonly sport: S;
  readonly words: SportPillWords<S>;
  /** A sport was tapped: another one picks it, the current one only folds. */
  readonly onChoose: (sport: S) => void;
  /**
   * What the open bar covers whole rather than ending across — absent where nothing is. Its two
   * widths are measured from the end the bar opens from; only a page's leftward bar hands one.
   */
  readonly cover?: BarCover;
  /** *+ Another sport* — absent where there is none to offer (#731). */
  readonly another?: AnotherSport;
  /**
   * Which way it opens from the pill — leftwards unless told, the current sport at its right end;
   * rightwards, the current sport at its left end and the others after it (#821).
   */
  readonly opens?: SportPillOpening;
}

/** The bar's open width: its sports', or past the tile whole where they would end across it. */
function openWidth(sports: number, cover: BarCover | undefined): number {
  return cover !== undefined && sports > cover.reaches ? Math.max(sports, cover.whole) : sports;
}

export function SportBar<S extends SportChoice = Sport>({
  sports,
  sport,
  words,
  onChoose,
  cover,
  another,
  opens = 'left',
}: SportBarProps<S>) {
  const reduced = useReducedMotion();
  const others = sports.filter((other) => other !== sport);
  // Everything that slides out from under the current sport: *+ Another sport*, the farthest, last.
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

  const anotherPill =
    another === undefined ? null : (
      // The farthest from the current sport, so the last out: where the row ends.
      <SlideOut key="another" order={sliding - 1} count={sliding} progress={progress} opens={opens}>
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
    );

  const otherPills = others.map((other, at) => (
    // Nearest the current sport moves first: the row reads outwards from it, whichever way it opens.
    <SlideOut
      key={other}
      order={opens === 'left' ? others.length - 1 - at : at}
      count={sliding}
      progress={progress}
      opens={opens}
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
  ));

  const current = (
    <Pressable
      key="current"
      accessibilityRole="button"
      accessibilityLabel={words.sportName(sport)}
      accessibilityState={{ selected: true }}
      onPress={() => onChoose(sport)}
      onLayout={(event) => setPillWidth(event.nativeEvent.layout.width)}
      hitSlop={theme.hit.chip}
      style={({ pressed }) => [s.pill, s.pillCurrent, pressed ? s.pressed : undefined]}
    >
      <SportName name={words.sportName(sport)} sport={sport} onInk />
      <Chevron mark={CHEVRONS[opens].fold} onInk />
    </Pressable>
  );

  return (
    <Animated.View testID="sport-bar" style={[s.bar, grow]}>
      <View style={s.clip}>
        <View
          testID="sport-bar-row"
          style={[s.row, opens === 'left' ? s.rowAtRight : s.rowAtLeft]}
          onLayout={(event) => setRowWidth(event.nativeEvent.layout.width)}
        >
          {opens === 'left'
            ? [anotherPill, ...otherPills, current]
            : [current, ...otherPills, anotherPill]}
        </View>
      </View>
    </Animated.View>
  );
}

interface SlideOutProps {
  /** 0 for the pill beside the current sport, counting away from it. */
  readonly order: number;
  /** How many pills slide out — the other sports, and *+ Another sport* where there is one. */
  readonly count: number;
  readonly progress: SharedValue<number>;
  /** The way the bar opens, and so the way each pill travels out from under the current sport. */
  readonly opens: SportPillOpening;
  readonly children: ReactNode;
}

/** One pill of the bar's row, sliding out from under the current sport in its turn. */
function SlideOut({ order, count, progress, opens, children }: SlideOutProps) {
  const step = count > 1 ? (1 - OPTION_SHARE) / (count - 1) : 0;
  const start = order * step;
  const end = start + OPTION_SHARE;
  // It starts towards the current sport — right of its place on a bar opening leftwards, left of it
  // on one opening rightwards.
  const from = opens === 'left' ? SLIDE : -SLIDE;

  const slide = useAnimatedStyle(
    () => ({
      opacity: interpolate(progress.value, [start, end], [0, 1], Extrapolation.CLAMP),
      transform: [
        {
          translateX: interpolate(progress.value, [start, end], [from, 0], Extrapolation.CLAMP),
        },
      ],
    }),
    [start, end, from],
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
  dotBox: { width: theme.size.sportDot, height: theme.size.sportDot },
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
  // Laid out once at its whole width, against the edge the bar opens from, so the growing bar
  // uncovers it away from there and the current pill never moves — and what the bar opens past it
  // is white.
  row: {
    position: 'absolute',
    top: PAD,
    flexDirection: 'row',
    alignItems: 'center',
  },
  // Opening leftwards: the current sport at the bar's right end.
  rowAtRight: { right: PAD },
  // Opening rightwards (#821): the current sport at its left end.
  rowAtLeft: { left: PAD },
});
