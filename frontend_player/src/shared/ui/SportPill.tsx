/**
 * **The sport pill** — the pill in a page's header, and the bar it unfolds into: the group page's
 * fast filter (play 41–42, PRD #500 stories 52–58, [#513](https://github.com/Rakieta02/Rakieta/issues/513))
 * and Rankings' sport, **one control** since [#774](https://github.com/Rakieta02/Rakieta/issues/774).
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
 * **Or it opens rightwards** (`opens`, [#821](https://github.com/Rakieta02/Rakieta/issues/821); ADR-0205
 * §5, Q19, Q37; home refactor 12, 13): Top 10's switcher stands first in its line's footer, so it
 * reads *Padel ›*, its chevron pointing the way it opens, and the bar grows **to the right** across
 * the footer — the current sport dark at its **left** end where the pill stood, its chevron turned
 * back to ‹, and the others sliding out after it in the page's order, nearest first. The same bar,
 * the same unfold, mirrored; a page's header keeps the leftward one.
 *
 * **The unfold runs on the UI thread and moves nothing but transforms and opacity** (ADR-0176 §2's
 * rule for anything that moves per frame): one shared value from 0 to 1 over `motion.unfold`,
 * `easeDecel`. **The bar is laid out once, at the closed pill's width** — the current sport in its
 * flow — and drawn as **two white halves that meet under the current sport**: the half at the end
 * it opens from stays where the pill stood, and the other, longer than any bar opens, **slides out**
 * from under it until its round end stands where the row ends. Each half is cut where they meet,
 * shadow and all, so the two read as one bar. The other sports ride in a clip shaped like the
 * moving half, held still by an equal slide back, so its round end uncovers them where they lie;
 * each also fades and slides out from under the current sport in its turn. Nothing is scaled — iOS
 * rasterises a scaled layer blurred (ADR-0176 §2, amended).
 *
 * **Why not the bar's width**, which is what it animated until 2026-11-24: under the New
 * Architecture Reanimated 3.16 cannot write a layout prop onto the native view. Every frame went
 * through a shadow-tree commit — the tree cloned, laid out again, and every label in the bar
 * measured again through JNI, since the row was laid out against the growing width — about 10 ms of
 * an A32's 16.7 in a debug build; and that commit is skipped while React commits anywhere, so the
 * bar held and jumped (`RecordDetails` has the iPhone's numbers). Transforms and opacity are
 * written to the views directly.
 *
 * **It starts from the layout itself.** The bar needs two widths — its own, the closed pill's, and
 * the other sports' row — and both are shared values written by their layout events, so no render
 * stands between the measure and the first frame. Until both are in, the bar is drawn at nothing:
 * one frame on a device, and a suite, which lays nothing out, still finds every sport by its name.
 * **Under reduced motion** the value starts at 1 and the bar is simply open. **Folding is
 * immediate** — see `motion.unfold`.
 *
 * **It can end with *+ Another sport*** — the group page's, while there is a sport left to offer
 * ([#731](https://github.com/Rakieta02/Rakieta/issues/731), ADR-0200 §4): the farthest pill from the
 * current sport, the last to slide out, so it is where the row ends. It is no sport — no dot, the
 * plus in front — and its press is the page's: the group page opens *Which sports do you play?*
 * over the sports the reader is unrated in. A page that hands no `another` draws none.
 *
 * **Open, it never ends across what it must cover whole** — the group's tile (#529): where its
 * sports would stop somewhere over the tile, a sliver of it showed past the bar's round end, so the
 * bar opens that much further and covers it whole (`BarCover`, which the frame measures). Where they
 * stop short of the tile, the bar ends where they do. A page with nothing to cover hands nothing.
 *
 * **It can offer *All*** (#801): a page that lists people from every sport — New in Rakieta's See all —
 * hands `ALL_SPORTS` among its choices, and the pill draws it as a sport with a two-toned dot. Which
 * choices it offers, and in what order, stays the page's.
 *
 * Never a `Modal`, and nothing here is one: the bar is a layer of the page (ADR-0178).
 */

import { useEffect, useId, useRef, type ReactNode } from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
  type DimensionValue,
  type ViewStyle,
} from 'react-native';
import Animated, {
  Easing,
  Extrapolation,
  interpolate,
  useAnimatedStyle,
  useDerivedValue,
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

/** The bar's height: a chip and its inset above and below — the reachable 45. */
const BAR_HEIGHT = theme.size.chip + 2 * PAD;

/**
 * How far past a half the clip that cuts it reaches, above, below and at its round end — clear of
 * the popover shadow on both platforms, so the cut is only ever where the halves meet.
 */
const SHADOW_ROOM =
  theme.shadow.popover.shadowRadius +
  theme.shadow.popover.shadowOffset.height +
  theme.shadow.popover.elevation;

/**
 * **Where the two halves meet**, in from the end the bar opens from: past the round end and the
 * shadow's blur, so both halves are straight there and their shadows join without a seam — and
 * always under the current sport, whose ink hides the join itself. A number, never a percentage of
 * the bar: an absolute child's percentage resolves against the room the bar was offered (the whole
 * slot), not the width it took.
 */
const SEAM = BAR_HEIGHT / 2 + theme.shadow.popover.shadowRadius;

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
 * them (#801: New in Rakieta's See all; the Home rows screens §5.3, home rows 12, 19). Drawn with a
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
  'worklet';
  return cover !== undefined && sports > cover.reaches ? Math.max(sports, cover.whole) : sports;
}

/** A width the layout has not reported yet. */
const UNMEASURED = -1;

/**
 * A distance from one end of the bar — the end it opens **from**, where the current sport stands,
 * or the end it opens **towards** — as the inset that says it, whichever way it opens.
 */
function inset(
  opens: SportPillOpening,
  end: 'from' | 'towards',
  distance: DimensionValue,
): ViewStyle {
  const right = (opens === 'left') === (end === 'from');
  return right ? { right: distance } : { left: distance };
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
  // The sliding half's length: as long as any bar opens — the screen, and a round end more — so its
  // other end, and its clip's, stay behind the seam; and no longer, since a shadow-casting view the
  // RenderThread draws every frame costs it by its size (twice the screen tripled each frame's draw).
  const long = useWindowDimensions().width + BAR_HEIGHT;
  const others = sports.filter((other) => other !== sport);
  // Everything that slides out from under the current sport: *+ Another sport*, the farthest, last.
  const sliding = others.length + (another === undefined ? 0 : 1);
  // Which way the sliding half travels on screen: towards the end the bar opens to.
  const sign = opens === 'left' ? -1 : 1;

  const progress = useSharedValue(reduced ? 1 : 0);
  // The two widths the layout reports — the bar's own, which is the closed pill's, and the other
  // sports' row — written by their layout events rather than kept as state, so the unfold starts
  // with no render between the measure and its first frame. The JavaScript side keeps its own copy:
  // a shared value read here would be a synchronous hop to the UI thread.
  const closed = useSharedValue(UNMEASURED);
  const rest = useSharedValue(UNMEASURED);
  const covered = useSharedValue(cover);
  const widths = useRef({ closed: UNMEASURED, rest: UNMEASURED, started: false });

  useEffect(() => {
    covered.value = cover;
  }, [cover, covered]);

  function measure(part: 'closed' | 'rest', width: number) {
    (part === 'closed' ? closed : rest).value = width;
    const known = { ...widths.current, [part]: width };
    widths.current = known;
    if (known.closed === UNMEASURED || known.rest === UNMEASURED || known.started || reduced)
      return;
    widths.current = { ...known, started: true };
    progress.value = withTiming(1, { duration: theme.motion.unfold, easing: EASE });
  }

  // How far the sliding half has travelled: nothing until both widths are in, and at the end the
  // open width less the closed one.
  const travel = useDerivedValue(() =>
    closed.value === UNMEASURED || rest.value === UNMEASURED
      ? 0
      : (openWidth(closed.value + rest.value, covered.value) - closed.value) * progress.value,
  );

  // Transform and opacity only, every one: a layout prop here would send each frame through the
  // shadow-tree commit React pauses (the module note).
  const shown = useAnimatedStyle(() => ({
    opacity: closed.value === UNMEASURED || rest.value === UNMEASURED ? 0 : 1,
  }));
  // The sliding half and the clip the other sports ride in move together — one style each, since an
  // animated style is a view's own.
  const out = useAnimatedStyle(
    () => ({ transform: [{ translateX: sign * travel.value }] }),
    [sign],
  );
  const clipOut = useAnimatedStyle(
    () => ({ transform: [{ translateX: sign * travel.value }] }),
    [sign],
  );

  const anotherPill =
    another === undefined ? null : (
      // The farthest from the current sport, so the last out: where the row ends.
      <SlideOut
        key="another"
        order={sliding - 1}
        count={sliding}
        progress={progress}
        travel={travel}
        opens={opens}
      >
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
      travel={travel}
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

  // In the bar's own flow, so the bar is laid out at the closed pill's width and the current sport
  // stands exactly where the pill stood; drawn over both halves and the sports sliding from under it.
  const current = (
    <Pressable
      key="current"
      accessibilityRole="button"
      accessibilityLabel={words.sportName(sport)}
      accessibilityState={{ selected: true }}
      onPress={() => onChoose(sport)}
      hitSlop={theme.hit.chip}
      style={({ pressed }) => [s.pill, s.pillCurrent, s.current, pressed ? s.pressed : undefined]}
    >
      <SportName name={words.sportName(sport)} sport={sport} onInk />
      <Chevron mark={CHEVRONS[opens].fold} onInk />
    </Pressable>
  );

  return (
    <Animated.View
      testID="sport-bar"
      style={[s.bar, shown]}
      onLayout={(event) => measure('closed', event.nativeEvent.layout.width)}
    >
      {opens === 'right' ? current : null}
      {/* The half the bar opens from: still, where the pill stood, and cut where the halves meet. */}
      <View
        pointerEvents="none"
        style={[s.cut, inset(opens, 'from', -SHADOW_ROOM), { width: SHADOW_ROOM + SEAM }]}
      >
        <View style={[s.half, s.anchored, inset(opens, 'from', SHADOW_ROOM)]} />
      </View>
      {/* The half that slides out: its round end travels from the pill's end to the row's. */}
      <View
        pointerEvents="none"
        style={[s.cut, inset(opens, 'from', SEAM), inset(opens, 'towards', -long)]}
      >
        <Animated.View
          testID="sport-bar-end"
          style={[s.half, inset(opens, 'towards', long), { width: long }, out]}
        />
      </View>
      {/* The other sports, in a clip shaped like the sliding half; each holds itself still in it. */}
      <Animated.View
        pointerEvents="box-none"
        style={[s.reveal, inset(opens, 'towards', 0), { width: long }, clipOut]}
      >
        <View
          testID="sport-bar-row"
          style={[s.row, inset(opens, 'from', long - PAD)]}
          onLayout={(event) => measure('rest', event.nativeEvent.layout.width)}
        >
          {opens === 'left' ? [anotherPill, ...otherPills] : [...otherPills, anotherPill]}
        </View>
      </Animated.View>
      {opens === 'left' ? current : null}
    </Animated.View>
  );
}

interface SlideOutProps {
  /** 0 for the pill beside the current sport, counting away from it. */
  readonly order: number;
  /** How many pills slide out — the other sports, and *+ Another sport* where there is one. */
  readonly count: number;
  readonly progress: SharedValue<number>;
  /**
   * How far the clip the pill rides in has slid — taken back off its own slide, so it stands still
   * on the page while the clip's round end uncovers it.
   */
  readonly travel: SharedValue<number>;
  /** The way the bar opens, and so the way each pill travels out from under the current sport. */
  readonly opens: SportPillOpening;
  readonly children: ReactNode;
}

/** One pill of the bar's row, sliding out from under the current sport in its turn. */
function SlideOut({ order, count, progress, travel, opens, children }: SlideOutProps) {
  const step = count > 1 ? (1 - OPTION_SHARE) / (count - 1) : 0;
  const start = order * step;
  const end = start + OPTION_SHARE;
  // It starts towards the current sport — right of its place on a bar opening leftwards, left of it
  // on one opening rightwards.
  const from = opens === 'left' ? SLIDE : -SLIDE;
  // The clip slides towards the end the bar opens to; the pill takes that back.
  const sign = opens === 'left' ? -1 : 1;

  const slide = useAnimatedStyle(
    () => ({
      opacity: interpolate(progress.value, [start, end], [0, 1], Extrapolation.CLAMP),
      transform: [
        {
          translateX:
            interpolate(progress.value, [start, end], [from, 0], Extrapolation.CLAMP) -
            sign * travel.value,
        },
      ],
    }),
    [start, end, from, sign],
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
  // The bar's box: the closed pill's width — the current sport and its inset — and nothing drawn of
  // its own; the two halves draw it.
  bar: {
    height: BAR_HEIGHT,
    flexDirection: 'row',
    alignItems: 'center',
  },
  // The current sport's inset is a margin rather than the bar's padding: the halves and the clip are
  // placed from the bar's own edges.
  current: { marginHorizontal: PAD, zIndex: 1 },
  // What cuts a half where the two meet, reaching past it everywhere else to keep its shadow whole.
  cut: {
    position: 'absolute',
    top: -SHADOW_ROOM,
    bottom: -SHADOW_ROOM,
    overflow: 'hidden',
  },
  // A half: white, round at both ends, with the popover's shadow — only one end is ever in view.
  half: {
    position: 'absolute',
    top: SHADOW_ROOM,
    height: BAR_HEIGHT,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.color.surface,
    ...theme.shadow.popover,
  },
  // The still half only has to run straight past the seam, its far round end and its blur beyond it.
  anchored: { width: 2 * SEAM + BAR_HEIGHT },
  // The clip the other sports ride in, the sliding half's shape: the shadow is the half's and the
  // clip is this, since a view that clipped its own children would clip its own shadow on iOS.
  reveal: {
    position: 'absolute',
    top: 0,
    height: BAR_HEIGHT,
    borderRadius: theme.radius.pill,
    overflow: 'hidden',
  },
  // Laid out once, at its own width, against the current sport — so its labels are measured once,
  // never against a growing bar — and uncovered where it lies.
  row: {
    position: 'absolute',
    top: PAD,
    flexDirection: 'row',
    alignItems: 'center',
  },
});
