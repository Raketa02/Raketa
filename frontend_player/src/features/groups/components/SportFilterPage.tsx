/**
 * **A page filtered by the fast filter** — the group page and Members
 * ([#513](https://github.com/Raketa02/Raketa/issues/513),
 * [#514](https://github.com/Raketa02/Raketa/issues/514)): its header with the sport pill, what is
 * under the header for the sport chosen, and the bar the pill unfolds into, floating over both.
 *
 * **One filter, one state**: the sport is `useGroupSport`'s, the one value last picked anywhere in
 * Play, so a sport picked on Members is the sport the group page is on when the player goes back,
 * and the other way round (story 58).
 *
 * **The bar floats over the header and the page under it**: a layer drawn last, laid over the
 * header's own box, with a backdrop across the whole page beneath it — so a tap anywhere but a
 * sport folds it and changes nothing, and so does the back button on Android while it is open.
 * The shell's tab bar is outside the page and stays live; leaving by it folds the bar too. It is
 * never a `Modal` (ADR-0178). The header's box is measured for it, because the bar has to stand
 * exactly where the pill stands.
 *
 * **The open bar covers the group's tile whole or not at all** (#529). The header hands the tile
 * to `cover`, which measures where it stands, and the bar is told the two widths that matter: the
 * one at which it would reach the tile and the one that covers it with `space.xs` to spare — which
 * stops short of the back arrow, a `space.sm` gap before the tile. Members has no tile, and covers
 * nothing.
 *
 * The page draws its own header and body, handed what they need: the header the pill, once there
 * is a sport to show, and the body the sport — `undefined` until the phone has answered, so
 * nothing is drawn for one sport and then another (ADR-0188 §4) — and, for an official group the
 * reader is rated in none of the sports of, what they would add to see it (#519).
 */

import { useFocusEffect } from 'expo-router';
import { useCallback, useRef, useState, type ReactNode } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { useHardwareBack } from '@/shared/lib/platform';
import { theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import { useGroupSport } from '../hooks/useGroupSport';

import { SportBar, SportPill, type BarCover } from './SportFilter';

/** Where the bar's right end stands in from the page's edge: the gutter, less its own inset. */
const BAR_INSET = theme.size.gutter - theme.size.groupPage.filterPad;

interface Box {
  readonly x: number;
  readonly width: number;
}

export interface SportFilterPageProps {
  /**
   * **What the group plays**, where it says: an official group's declared sports, which the filter
   * narrows to. `undefined` for a player group, and while the group is being read.
   */
  readonly declaredSports?: readonly Sport[];
  /**
   * The page's header, with the pill for its right slot — `undefined` until there is a sport — and
   * `cover`, which the header wraps round what the open bar must cover whole rather than end across:
   * the group's tile. It measures the box it is given against the header's own left edge, so the
   * header draws it as a direct child of a root that spans the page, as `ScreenHeader` does its lead.
   */
  readonly header: (
    pill: ReactNode | undefined,
    cover: (node: ReactNode) => ReactNode,
  ) => ReactNode;
  /**
   * Everything under the header, for the sport the page is on — `undefined` until it is known —
   * and the sports the reader would add to have one here: empty unless the group is an official
   * one they are rated in none of the sports of.
   */
  readonly children: (sport: Sport | undefined, toAdd: readonly Sport[]) => ReactNode;
}

export function SportFilterPage({ declaredSports, header, children }: SportFilterPageProps) {
  const { sports, sport, toAdd, choose } = useGroupSport(declaredSports);
  const [unfolded, setUnfolded] = useState(false);
  const [headerBox, setHeaderBox] = useState<{ readonly width: number; readonly height: number }>();
  const [covered, setCovered] = useState<Box>();
  const headerHeight = headerBox?.height;

  const fold = () => setUnfolded(false);

  function pick(picked: Sport) {
    if (picked !== sport) choose(picked);
    fold();
  }

  const pill =
    sports === undefined || sport === undefined ? undefined : (
      <SportPill sports={sports} sport={sport} onUnfold={() => setUnfolded(true)} />
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

      {children(sport, toAdd)}

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
              onChoose={pick}
              {...(barCover === undefined ? {} : { cover: barCover })}
            />
          </View>
        </>
      ) : null}
    </View>
  );
}

/**
 * The two widths the open bar is told, from where the header stands and where the tile does: the
 * bar's right end is fixed at `BAR_INSET` in from the page's edge, so a width is a distance back
 * from there. Nothing until both are measured.
 */
function coverOf(headerWidth: number | undefined, tile: Box | undefined): BarCover | undefined {
  if (headerWidth === undefined || tile === undefined) return undefined;
  const rightEnd = headerWidth - BAR_INSET;
  return {
    reaches: rightEnd - (tile.x + tile.width),
    whole: rightEnd - (tile.x - theme.space.xs),
  };
}

/**
 * **What folds an open bar besides a tap** — mounted only while it is open. Android's back folds it
 * rather than leaving the page (closed, back is the navigator's again). And the page losing focus
 * folds it: the shell's tab bar is outside the page and the backdrop cannot cover it, so a tap
 * there leaves the page with the bar open, and it must not be open when the player comes back.
 */
function FoldAway({ onFold }: { readonly onFold: () => void }) {
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
