/**
 * **The reveal, for a screen with one read** (design system 5.6; PRD #867,
 * [#870](https://github.com/Raketa02/Raketa/issues/870); the loading shimmer log §4, §5) — how a
 * screen's content takes its skeleton's place.
 *
 * - **The content is drawn underneath the skeleton**, laid out and hidden — from sight, and from a
 *   listener — so the reveal shows a finished screen and nothing rearranges.
 * - **The reveal is one cross-fade on `motion.fade`** (200 ms), opacity only: the content comes in
 *   as the skeleton goes, and the skeleton is unmounted once it has, its clock with it. **Under
 *   reduced motion it is a cut** — only the sweep is Part 13's exception, not the fade.
 * - **A skeleton is drawn only if, at the first draw, the read has nothing**: a screen whose read is
 *   cached is simply drawn, with no skeleton and no fade. **Once the content is in, it never goes
 *   back** to its skeleton during this mount, whatever its read does next — a pull, a background
 *   re-read.
 * - **No delay before the skeleton, and no minimum time on screen**: it stands from the first frame,
 *   and a read that lands at once fades at once — the fade is what turns a short wait into a soft one.
 *
 * **Two words are the caller's.** **Finished**: the read has landed, been refused, or is held for a
 * connection — so the failure or the offline note is revealed in the content's place as the content
 * would be. **Landed**: what it finished with is the content. A refusal or the offline note is not
 * the content, so when the read sets out again — *Try again*, or the connection back — with still
 * nothing to draw, the skeleton stands again rather than a blank page.
 *
 * The skeleton is the screen's own layout of `Skeleton`'s shapes, drawn over the content's place and
 * taking no touch: a pull still reaches the list beneath it.
 *
 * **A screen with several parts** ([#871](https://github.com/Raketa02/Raketa/issues/871)) gives each
 * part a `Reveal` and asks **`useRevealParts`** which of them to show — together before the ceiling,
 * top-down from it (`revealParts.ts`'s rule) — handing each part *shown* as both its words: a part is
 * revealed once, and never taken back. **A part of a scrolling column is `sizedBy` its skeleton**
 * while it waits: there the content is nothing until its read lands, and a skeleton drawn over
 * nothing would be clipped to nothing. So the skeleton stands in the column, holding the part's place,
 * the content laid out over it unseen and untouchable; at the reveal the content takes the column
 * back and the skeleton fades over it.
 *
 * **It passes on where it stands on its page** (`SectionOnPage`): a row revealed inside it, on a page
 * that watches what is on screen, is still measured on the page, through it.
 */

import { useEffect, useState, type ReactNode } from 'react';
import {
  StyleSheet,
  View,
  type LayoutChangeEvent,
  type StyleProp,
  type ViewStyle,
} from 'react-native';
import Animated, {
  ReduceMotion,
  cancelAnimation,
  runOnJS,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
  type SharedValue,
} from 'react-native-reanimated';

import { SectionOnPage, useTopOnPage } from './onScreen';
import { useReducedMotion } from './overlay';
import { REVEAL_CEILING, partsToShow } from './revealParts';
import { theme } from './theme';

export interface RevealProps {
  /** Whether the read has finished — landed, refused, or held for a connection. */
  readonly finished: boolean;
  /** Whether it finished with the content — once it has, the skeleton never comes back. */
  readonly landed: boolean;
  /** The screen's skeleton: its shapes, laid out where the content will stand. */
  readonly skeleton: ReactNode;
  /** The content, drawn underneath until the reveal. */
  readonly children: ReactNode;
  /** The area the content and its skeleton share. */
  readonly style?: StyleProp<ViewStyle>;
  /**
   * **What gives the area its height while the skeleton stands** — the content, laid out underneath
   * (the default: a screen's flex area), or **the skeleton**, for a part of a scrolling column whose
   * content may draw nothing until its read lands (see the module note).
   */
  readonly sizedBy?: 'content' | 'skeleton';
  readonly testID?: string;
}

/** What a listener is kept from while the content waits under its skeleton. */
const HIDDEN = {
  accessibilityElementsHidden: true,
  importantForAccessibility: 'no-hide-descendants',
} as const;

export function Reveal({
  finished,
  landed,
  skeleton,
  children,
  style,
  sizedBy = 'content',
  testID,
}: RevealProps) {
  // Once the content is in, it stays in for the rest of the mount.
  const [settled, setSettled] = useState(landed);
  if (landed && !settled) setSettled(true);
  // The read is out with nothing to draw: the skeleton stands, from the first draw or again.
  const waiting = !settled && !finished;
  // How far the content has come in: the content's opacity, and the skeleton's the other way.
  const shown = useSharedValue(waiting ? 0 : 1);
  const contentFade = useAnimatedStyle(() => ({ opacity: shown.value }));
  // A part of a column: the skeleton holds its place while it waits, the content laid out over it.
  const holdsPlace = sizedBy === 'skeleton' && waiting;
  const placed = sizedBy === 'content' ? s.content : holdsPlace ? s.aside : undefined;
  // The content stands at the area's top either way, so where the area stands is where it does.
  const page = useTopOnPage();
  const onLayout = (event: LayoutChangeEvent) => page.laidOut(event.nativeEvent.layout.y);

  return (
    <View style={style} onLayout={onLayout} {...(testID === undefined ? {} : { testID })}>
      <Animated.View
        testID="reveal-content"
        style={[placed, contentFade]}
        {...(holdsPlace ? { pointerEvents: 'none' as const } : {})}
        {...(waiting ? HIDDEN : {})}
      >
        <SectionOnPage.Provider value={page.top}>{children}</SectionOnPage.Provider>
      </Animated.View>
      <FadingSkeleton waiting={waiting} shown={shown} holdsPlace={holdsPlace}>
        {skeleton}
      </FadingSkeleton>
    </View>
  );
}

/** Which of a screen's parts are shown, and whether its ceiling has passed. */
export interface PartsRevealed {
  /** How many parts, from the top, are shown — each part is revealed when this reaches it. */
  readonly shown: number;
  /** Whether the ceiling has passed since the screen mounted. */
  readonly pastCeiling: boolean;
}

/**
 * **Which of a screen's parts to show** — `partsToShow`'s rule over each part's finished flag,
 * top-down, with **the ceiling's one timer per mount**: `REVEAL_CEILING` from the screen's mount,
 * set only while something waits and stopped once everything is shown. A screen whose reads have all
 * finished at its first draw shows everything at once and sets no timer.
 */
export function useRevealParts(finished: readonly boolean[]): PartsRevealed {
  const [pastCeiling, setPastCeiling] = useState(false);
  const [shown, setShown] = useState(() => partsToShow({ finished, pastCeiling, shown: 0 }));
  const next = partsToShow({ finished, pastCeiling, shown });
  if (next !== shown) setShown(next);
  const all = next === finished.length;

  // Started at the mount, and once only: everything shown is for good, so `all` turns true once.
  useEffect(() => {
    if (all) return undefined;
    const ceiling = setTimeout(() => setPastCeiling(true), REVEAL_CEILING);
    return () => clearTimeout(ceiling);
  }, [all]);

  return { shown: next, pastCeiling };
}

/**
 * **The skeleton over the content's place**: up while the read is out with nothing to draw, faded out
 * once it has finished, and unmounted once gone — its clock with it. It owns its coming and going so
 * that the content is not drawn again at the fade's end.
 */
function FadingSkeleton({
  waiting,
  shown,
  holdsPlace,
  children,
}: {
  readonly waiting: boolean;
  readonly shown: SharedValue<number>;
  /** Standing in the column rather than over the content's place — a part's, while it waits. */
  readonly holdsPlace: boolean;
  readonly children: ReactNode;
}) {
  const reduced = useReducedMotion();
  const [up, setUp] = useState(waiting);
  // Back at once when the read sets out again with nothing drawn — no delay before a skeleton.
  if (waiting && !up) setUp(true);

  useEffect(() => {
    if (waiting) {
      cancelAnimation(shown);
      shown.value = 0;
      return;
    }
    if (!up) return;
    // `Never`: whether to fade was decided here, from the app's own reduced-motion answer. Under
    // reduced motion it is a cut, but still a timing, so the skeleton goes only once the UI thread has
    // drawn the content whole — never a frame with neither.
    shown.value = withTiming(
      1,
      { duration: reduced ? 0 : theme.motion.fade, reduceMotion: ReduceMotion.Never },
      (done) => {
        if (done === true) runOnJS(setUp)(false);
      },
    );
  }, [waiting, up, reduced, shown]);

  const fade = useAnimatedStyle(() => ({ opacity: 1 - shown.value }));

  if (!up) return null;
  return (
    <Animated.View
      testID="reveal-skeleton"
      pointerEvents="none"
      style={[holdsPlace ? undefined : s.skeleton, fade]}
      {...HIDDEN}
    >
      {children}
    </Animated.View>
  );
}

const s = StyleSheet.create({
  content: { flex: 1 },
  // A part's content while its skeleton holds the place: laid out at the column's width, over it.
  aside: { position: 'absolute', top: 0, left: 0, right: 0 },
  // Over the content's place, clipped to it: a skeleton that fills the screen stops at its edge.
  skeleton: { ...StyleSheet.absoluteFillObject, overflow: 'hidden' },
});
