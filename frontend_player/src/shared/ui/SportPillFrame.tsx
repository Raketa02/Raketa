/**
 * **The sport pill, held open or folded on a page** — the pill in the page's header, and the bar
 * it unfolds into floating over the page (#513; shared since
 * [#774](https://github.com/Raketa02/Raketa/issues/774), so the group page's fast filter and
 * Rankings draw one control). A page hands it the sports to offer, in the order the bar lists
 * them, the sport it is on, and its words; it hears back a pick. **The state is the page's**: which
 * sports and which one are what the page decides — the group page's last sport, Rankings' own.
 *
 * **The bar floats over the header and the page under it**: a layer drawn last, laid over the
 * header's own box, with a backdrop across the whole page beneath it — so a tap anywhere but a
 * sport folds it and changes nothing, and so does the back button on Android while it is open.
 * The shell's tab bar is outside the page and stays live; leaving by it folds the bar too. It is
 * never a `Modal` (ADR-0178). The header's box is measured for it, because the bar has to stand
 * exactly where the pill stands — so the page is drawn **inside** the frame, header first.
 *
 * **What the open bar must cover whole rather than end across** — the group's tile (#529) — the
 * header wraps in `cover`, which measures where it stands, and the bar is told the two widths that
 * matter: the one at which it would reach the thing and the one that covers it with `space.xs` to
 * spare. A header that wraps nothing covers nothing.
 *
 * **A pick is another sport.** The current one tapped folds the bar and reports nothing, as the
 * backdrop does; *+ Another sport*, where the page offers one, folds it and hands the press back.
 */

import { useFocusEffect } from 'expo-router';
import { useCallback, useRef, useState, type ReactNode } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { useHardwareBack } from '@/shared/lib/platform/hardwareBack';
import type { Sport } from '@/shared/vocabulary/sport';

import {
  SportBar,
  SportPill,
  type AnotherSport,
  type BarCover,
  type SportChoice,
  type SportPillWords,
} from './SportPill';
import { theme } from './theme';

export { ALL_SPORTS, type AnotherSport, type SportChoice, type SportPillWords } from './SportPill';

/** Where the bar's right end stands in from the page's edge: the gutter, less its own inset. */
const BAR_INSET = theme.size.gutter - theme.size.groupPage.filterPad;

interface Box {
  readonly x: number;
  readonly width: number;
}

export interface SportPillFrameProps<S extends SportChoice = Sport> {
  /**
   * **The sports to offer**, in the order the bar lists them — `undefined` until the page knows. One
   * is a plain label, unless there is *+ Another sport*. *All* (`ALL_SPORTS`) where the page offers
   * it (#801).
   */
  readonly sports: readonly S[] | undefined;
  /** The sport the page is on — `undefined` until it is known. No pill is drawn until both are. */
  readonly sport: S | undefined;
  /** **Another sport was picked** — never the current one, which only folds the bar. */
  readonly onPick: (sport: S) => void;
  readonly words: SportPillWords<S>;
  /** *+ Another sport*, the bar's last pill — absent where the page offers none. */
  readonly another?: AnotherSport;
  /**
   * The page's header, with the pill for its right slot — `undefined` until there is a sport — and
   * `cover`, which the header wraps round what the open bar must cover whole rather than end across.
   * It measures the box it is given against the header's own left edge, so the header draws it as a
   * direct child of a root that spans the page, as `ScreenHeader` does its lead.
   */
  readonly header: (
    pill: ReactNode | undefined,
    cover: (node: ReactNode) => ReactNode,
  ) => ReactNode;
  /** Everything under the header. */
  readonly children: ReactNode;
}

export function SportPillFrame<S extends SportChoice = Sport>({
  sports,
  sport,
  onPick,
  words,
  another,
  header,
  children,
}: SportPillFrameProps<S>) {
  const [unfolded, setUnfolded] = useState(false);
  const [headerBox, setHeaderBox] = useState<{ readonly width: number; readonly height: number }>();
  const [covered, setCovered] = useState<Box>();
  const headerHeight = headerBox?.height;

  const fold = () => setUnfolded(false);

  function choose(chosen: S) {
    if (chosen !== sport) onPick(chosen);
    fold();
  }

  // Pressed, it folds the bar first: the page's answer is a page of its own.
  const folding: AnotherSport | undefined =
    another === undefined
      ? undefined
      : {
          ...another,
          onPress: () => {
            fold();
            another.onPress();
          },
        };

  const pill =
    sports === undefined || sport === undefined ? undefined : (
      <SportPill
        sports={sports}
        sport={sport}
        words={words}
        {...(folding === undefined ? {} : { another: folding })}
        onUnfold={() => setUnfolded(true)}
      />
    );

  const cover = (node: ReactNode) => (
    <View
      testID="sport-filter-cover"
      onLayout={(event) => {
        const { x, width } = event.nativeEvent.layout;
        setCovered({ x, width });
      }}
    >
      {node}
    </View>
  );

  const barCover = coverOf(headerBox?.width, covered);

  return (
    <View style={s.page}>
      <View
        testID="sport-filter-header"
        onLayout={(event) => {
          const { width, height } = event.nativeEvent.layout;
          setHeaderBox({ width, height });
        }}
      >
        {header(pill, cover)}
      </View>

      {children}

      {unfolded && sports !== undefined && sport !== undefined ? (
        <>
          <FoldAway onFold={fold} />
          <Pressable
            testID="sport-filter-backdrop"
            onPress={fold}
            accessible={false}
            importantForAccessibility="no"
            style={StyleSheet.absoluteFill}
          />
          <View
            pointerEvents="box-none"
            style={[s.barSlot, headerHeight === undefined ? undefined : { height: headerHeight }]}
          >
            <SportBar
              sports={sports}
              sport={sport}
              words={words}
              onChoose={choose}
              {...(barCover === undefined ? {} : { cover: barCover })}
              {...(folding === undefined ? {} : { another: folding })}
            />
          </View>
        </>
      ) : null}
    </View>
  );
}

/**
 * The two widths the open bar is told, from where the header stands and where the covered thing
 * does: the bar's right end is fixed at `BAR_INSET` in from the page's edge, so a width is a
 * distance back from there. Nothing until both are measured.
 */
function coverOf(headerWidth: number | undefined, covered: Box | undefined): BarCover | undefined {
  if (headerWidth === undefined || covered === undefined) return undefined;
  const rightEnd = headerWidth - BAR_INSET;
  return {
    reaches: rightEnd - (covered.x + covered.width),
    whole: rightEnd - (covered.x - theme.space.xs),
  };
}

/**
 * **What folds an open bar besides a tap** — mounted only while it is open. Android's back folds it
 * rather than leaving the page (closed, back is the navigator's again). And the page losing focus
 * folds it: the shell's tab bar is outside the page and the backdrop cannot cover it, so a tap
 * there leaves the page with the bar open, and it must not be open when the player comes back.
 */
export function FoldAway({ onFold }: { readonly onFold: () => void }) {
  useHardwareBack(onFold);

  // Through a ref, so the blur subscription is made once rather than on every render of a parent
  // whose `fold` is a new function each time — a cleanup per render would fold on every render.
  const latest = useRef(onFold);
  latest.current = onFold;
  useFocusEffect(useCallback(() => () => latest.current(), []));

  return null;
}

const s = StyleSheet.create({
  // The layer the bar is laid over: no padding of its own, so its top is the header's.
  page: { flex: 1 },
  // Over the header's box, right-aligned so the current sport stands where the pill stood: the
  // bar's inset is taken back out of the gutter.
  barSlot: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    justifyContent: 'center',
    alignItems: 'flex-end',
    paddingHorizontal: BAR_INSET,
  },
});
