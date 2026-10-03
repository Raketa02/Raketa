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

import { SportBar, SportPill } from './SportFilter';

export interface SportFilterPageProps {
  /**
   * **What the group plays**, where it says: an official group's declared sports, which the filter
   * narrows to. `undefined` for a player group, and while the group is being read.
   */
  readonly declaredSports?: readonly Sport[];
  /**
   * **The sport a notice opened the page in** (#559) — stood on until the player picks another, and
   * never saved as a pick. Absent for a page opened by the player.
   */
  readonly opening?: Sport;
  /** The page's header, with the pill for its right slot — `undefined` until there is a sport. */
  readonly header: (pill: ReactNode | undefined) => ReactNode;
  /**
   * Everything under the header, for the sport the page is on — `undefined` until it is known —
   * and the sports the reader would add to have one here: empty unless the group is an official
   * one they are rated in none of the sports of.
   */
  readonly children: (sport: Sport | undefined, toAdd: readonly Sport[]) => ReactNode;
}

export function SportFilterPage({
  declaredSports,
  opening,
  header,
  children,
}: SportFilterPageProps) {
  const { sports, sport, toAdd, choose } = useGroupSport(declaredSports, opening);
  const [unfolded, setUnfolded] = useState(false);
  const [headerHeight, setHeaderHeight] = useState<number>();

  const fold = () => setUnfolded(false);

  function pick(picked: Sport) {
    if (picked !== sport) choose(picked);
    fold();
  }

  const pill =
    sports === undefined || sport === undefined ? undefined : (
      <SportPill sports={sports} sport={sport} onUnfold={() => setUnfolded(true)} />
    );

  return (
    <View style={s.page}>
      <View onLayout={(event) => setHeaderHeight(event.nativeEvent.layout.height)}>
        {header(pill)}
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
            <SportBar sports={sports} sport={sport} onChoose={pick} />
          </View>
        </>
      ) : null}
    </View>
  );
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
    paddingHorizontal: theme.size.gutter - theme.size.groupPage.filterPad,
  },
});
