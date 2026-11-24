/**
 * **The tab's menu** — a small white card hanging from the tab that opens it, picking one of its
 * lines (design-system 9.5, [#861](https://github.com/Raketa02/Raketa/issues/861); PRD #859; tab menu
 * mocks 3 and 4, illustrations). A group page's **Friends** tab holds the kind of the game being built
 * in one, and Games' its deck's kind from #862 — where a row of *Competitive | For fun* under the tabs
 * once stood.
 *
 * ```
 *  [ Games | Fill in | You’re in | Friends ⌃ ]     ← the tab, its chevron turned up (`Segment`)
 *                         ┌───────────────────┐
 *                         │ (✓) Competitive   │    ← the selected line: a coralInk circle, the tick
 *                         │     For fun       │    ← the other keeps the tick's space empty
 *                         └───────────────────┘
 * ```
 *
 * ## A picker, not the anchored popover
 *
 * 7.6's popover **explains a word**: 250 across, an arrow, a close control, focus moved to its
 * heading. This **picks**: as wide as its lines, no arrow, no close — a line is the way out, and so is
 * a press anywhere else. Each **line** is a button at least the touch minimum tall, saying its words
 * and whether it is `selected`: its words, then an optional trailing **count** in muted mono, and
 * **the selected mark** before them — a `coralInk` circle with `Tick`'s drawn white tick (Archivo
 * has no ✓), whose space the other lines keep so the words line up. A line may be a **door** (6.3's):
 * its words `muted` at the segment door's opacity, **never disabled**, its press reported like any
 * other.
 *
 * ## Drawn in the page's tree, over the page
 *
 * **Never on the modal stage**, which would cover the tab bar and the app's bottom bar — and both stay
 * live. The page draws it as a layer over itself, last, and hands it two measured frames in that
 * layer: **the tab that opens it** (`trigger`), which the card hangs from by its start or end edge,
 * inside the gutters, and **the tab bar** (`bar`), which its catcher leaves uncovered
 * (`tabMenuGeometry`). Before either is measured — never, on a phone, by the time a finger can open
 * it — the card stands at the layer's top and the catcher covers the layer.
 *
 * ## What closes it
 *
 * - **A press on a line** closes it, then reports the line — the one already selected too: the page
 *   decides that is nothing.
 * - **A press anywhere else on the page** lands on the catcher, a transparent press round the tab
 *   bar, which closes it **and does nothing else**: the page under it never sees the press.
 * - **A press on another tab** reaches the bar, which the catcher leaves uncovered — and the tabs'
 *   reach past it, so a tap that 6.5's slop would carry to a tab still does — and the page closes the
 *   menu as it changes tab. A menu its page takes away while open reports no close: the page knew.
 * - **Android back**, which it claims while open, and **the page leaving view** — a screen pushed over
 *   it, or a press on the app's bottom bar, which is outside the page and stays live (`FoldAway`, the
 *   sport bar's).
 *
 * ## It moves, a little
 *
 * The card **fades in and drops `size.tabMenu.drop` into place** over `motion.tabMenu`, and folds away
 * the same way — opacity and transform only, on React Native's `Animated` and its native driver, as
 * FOR YOU's content is (`FoldingLine`). Folding away it is still drawn, and already out of reach: no
 * press, nothing heard, and its catcher gone, so the page answers at once. **Under reduced motion it
 * is simply open or shut.**
 *
 * **It speaks only through its lines' names** (ADR-0198): no announcement, and focus is not moved.
 */

import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { Animated as Motion, Easing, Pressable, StyleSheet, Text, View } from 'react-native';

import { useReducedMotion } from './overlay';
import { FoldAway } from './SportPillFrame';
import {
  TAB_REACH,
  catcherAround,
  tabMenuPlace,
  type MenuAlign,
  type MenuFrame,
  type MenuPlace,
} from './tabMenuGeometry';
import { theme } from './theme';
import { Tick } from './Tick';

export type { MenuAlign, MenuFrame } from './tabMenuGeometry';

const EASE = Easing.bezier(
  theme.motion.easeDecel.x1,
  theme.motion.easeDecel.y1,
  theme.motion.easeDecel.x2,
  theme.motion.easeDecel.y2,
);

const CATCHER_SIDES = ['above', 'below', 'start', 'end'] as const;

/** Before the bar is measured, the catcher is one box over the whole layer. */
const NO_BAR: MenuFrame = { x: 0, y: 0, width: 0, height: 0 };

export interface TabMenuLine<K extends string> {
  readonly key: K;
  /** What the line says. */
  readonly label: string;
  /** Defaults to `label` — the caller's sentence where the line says more than its words. */
  readonly accessibilityLabel?: string;
  /** A count after the words, in muted mono — the caller's figure, formatted. Absent, none. */
  readonly count?: string;
  /** **A door** — dimmed, never disabled, its press reported: see the module note. */
  readonly door?: boolean;
}

export interface TabMenuProps<K extends string> {
  readonly open: boolean;
  readonly lines: readonly TabMenuLine<K>[];
  /** The line ticked — none, where the page's choice is no line's. */
  readonly selected: K | undefined;
  /** The tab that opens it, in the layer — what it hangs from. */
  readonly trigger: MenuFrame | undefined;
  /** The tab bar, in the layer — what its catcher leaves uncovered. */
  readonly bar: MenuFrame | undefined;
  /** Which of the tab's edges it stands on: Games' start, Friends' end. */
  readonly align: MenuAlign;
  /** A line was pressed — after `onClose`. */
  readonly onPick: (key: K) => void;
  /** Anything that closes it: a line, the catcher, back, the page leaving view. */
  readonly onClose: () => void;
}

export function TabMenu<K extends string>({
  open,
  lines,
  selected,
  trigger,
  bar,
  align,
  onPick,
  onClose,
}: TabMenuProps<K>) {
  const reduced = useReducedMotion();
  /** Whether the card is drawn — while open, and while it folds away. */
  const [drawn, setDrawn] = useState(open);
  if (open && !drawn) setDrawn(true);
  // Measured as the page mounts it, so the first opening already stands in place.
  const [layerWidth, setLayerWidth] = useState(0);
  // `FoldAway` folds on its way out as well as on a blur. Once shut, that is no second close; and a
  // menu taken away while open — its tab gone — was closed by whoever took it, so neither is that.
  const openNow = useRef(open);
  openNow.current = open;
  useEffect(
    () => () => {
      // Runs before `FoldAway`'s own cleanup: a parent's effects are let go before its children's.
      openNow.current = false;
    },
    [],
  );
  const foldAway = () => {
    if (openNow.current) onClose();
  };

  const progress = useRef(new Motion.Value(0)).current;
  useEffect(() => {
    const to = open ? 1 : 0;
    if (reduced) {
      progress.setValue(to);
      if (!open) setDrawn(false);
      return undefined;
    }
    const motion = Motion.timing(progress, {
      toValue: to,
      duration: theme.motion.tabMenu,
      easing: EASE,
      useNativeDriver: true,
      // A fade is no interaction: it must never hold back work queued after interactions — a
      // list's next rows — and under jest, where the native driver never says it ended, it would
      // hold them back for good.
      isInteraction: false,
    });
    motion.start();
    // Folded away, it is let go — the timer beside the motion, so a test's clock moves both.
    const letGo = open ? undefined : setTimeout(() => setDrawn(false), theme.motion.tabMenu);
    return () => {
      motion.stop();
      if (letGo !== undefined) clearTimeout(letGo);
    };
  }, [open, reduced, progress]);

  // Opacity and transform only — a layout prop cannot ride the native driver.
  const slide = useMemo(
    () => ({
      opacity: progress,
      transform: [
        {
          translateY: progress.interpolate({
            inputRange: [0, 1],
            outputRange: [-theme.size.tabMenu.drop, 0],
          }),
        },
      ],
    }),
    [progress],
  );

  const layer = (children?: ReactNode) => (
    <View
      style={StyleSheet.absoluteFill}
      pointerEvents="box-none"
      onLayout={({ nativeEvent }) => setLayerWidth(nativeEvent.layout.width)}
    >
      {children}
    </View>
  );

  // Shut, the layer is kept — empty, and taking no touch — so its width is known before an opening.
  if (!drawn) return layer();

  const place: MenuPlace =
    trigger === undefined
      ? {
          top: 0,
          ...(align === 'start' ? { left: theme.size.gutter } : { right: theme.size.gutter }),
          maxWidth: layerWidth - 2 * theme.size.gutter,
        }
      : tabMenuPlace(trigger, layerWidth, align);
  // The tabs' reach is left uncovered too, so a tap just past a tab still reaches it.
  const boxes = bar === undefined ? catcherAround(NO_BAR, 0) : catcherAround(bar, TAB_REACH);

  return layer(
    <>
      {open ? (
        <>
          <FoldAway onFold={foldAway} />
          {CATCHER_SIDES.map((side) => (
            <Pressable
              key={side}
              testID={`tab-menu-catcher-${side}`}
              onPress={onClose}
              accessible={false}
              importantForAccessibility="no"
              style={[s.catcher, boxes[side]]}
            />
          ))}
        </>
      ) : null}
      <Motion.View
        testID="tab-menu"
        style={[s.card, place, slide]}
        pointerEvents={open ? 'auto' : 'none'}
        accessibilityElementsHidden={!open}
        importantForAccessibility={open ? 'auto' : 'no-hide-descendants'}
      >
        {lines.map((line) => (
          <MenuLine
            key={line.key}
            line={line}
            selected={line.key === selected}
            onPress={() => {
              onClose();
              onPick(line.key);
            }}
          />
        ))}
      </Motion.View>
    </>,
  );
}

function MenuLine<K extends string>({
  line,
  selected,
  onPress,
}: {
  readonly line: TabMenuLine<K>;
  readonly selected: boolean;
  readonly onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={line.accessibilityLabel ?? line.label}
      // Never `disabled`, a door included: a door that read as shut is one nobody opens (6.3).
      accessibilityState={{ selected }}
      onPress={onPress}
      // 6.6's opacity, as the segment's press.
      style={({ pressed }) => [s.line, pressed ? s.pressed : undefined]}
    >
      {selected ? (
        <View testID="tab-menu-tick" style={s.tick}>
          <Tick />
        </View>
      ) : (
        <View testID="tab-menu-tick-space" style={s.tickSpace} />
      )}
      <Text style={[s.words, line.door === true ? s.wordsDoor : undefined]} numberOfLines={1}>
        {line.label}
      </Text>
      {line.count === undefined ? null : <Text style={s.count}>{line.count}</Text>}
    </Pressable>
  );
}

const { tick, padX, padY, gap } = theme.size.tabMenu;

const s = StyleSheet.create({
  // Transparent: the page shows through it, and only its press is its own.
  catcher: { position: 'absolute' },
  card: {
    position: 'absolute',
    paddingVertical: padY,
    backgroundColor: theme.color.surface,
    borderRadius: theme.radius.tabMenu,
    borderWidth: 1,
    borderColor: theme.color.line,
    // It floats (4.3): the popover's elevation, the anchored overlay's — no eighth shadow.
    ...theme.shadow.popover,
  },
  line: {
    flexDirection: 'row',
    alignItems: 'center',
    gap,
    minHeight: theme.size.minTouch,
    paddingHorizontal: padX,
  },
  pressed: { opacity: 0.7 },
  // A circle round the drawn tick: `coralInk`, as every white mark on a coral fill is (Rule C).
  tick: {
    width: tick,
    height: tick,
    borderRadius: tick / 2,
    backgroundColor: theme.color.coralInk,
    alignItems: 'center',
    justifyContent: 'center',
  },
  tickSpace: { width: tick, height: tick },
  words: { ...theme.type.inlineTitle, color: theme.color.ink },
  wordsDoor: { color: theme.color.muted, opacity: theme.size.segDoorOpacity },
  count: { ...theme.num.tiny, color: theme.color.muted },
});
