/**
 * **The group page's skeleton above the body** ([#875](https://github.com/Raketa02/Raketa/issues/875);
 * PRD #867; the loading shimmer log §10) — what stands while the group and the sport are read: **a
 * monogram circle and a bar for the name** in the header, beside its real way back
 * (`GroupHeader`'s `shimmering`), and **the tab bar's shape** under it. The body's skeleton is the
 * tab's own (`proposals`' `DeckSkeleton`, `BoardSkeleton`).
 *
 * Each stands in the room what replaces it takes, at the phone's text size (`fontScale`), so the
 * reveal moves nothing: the name's bar is centred in the height of the name and the line under it, and
 * the bar's shape is the track's height round a segment. Drawn on the page's `SkeletonGround`, hidden
 * from a listener as every shape is.
 */

import { StyleSheet, View, useWindowDimensions } from 'react-native';

import { SkeletonBlock, SkeletonCircle, SkeletonLine, theme } from '@/shared/ui';

/** How much of the content width the name's bar spans — a name, not a sentence. */
const NAME_SHARE = 0.45;

/** **The header's lead while it shimmers**: the group's tile as a circle, and the name's bar. */
export function GroupHeaderSkeleton() {
  const { width, fontScale } = useWindowDimensions();
  const { h2, tiny } = theme.type;
  // The name and the line under it, as the compact header stands them (`ScreenHeader`).
  const titles = (h2.lineHeight + tiny.lineHeight) * fontScale + theme.space.xxs;
  return (
    <View style={s.lead} testID="group-header-skeleton">
      <SkeletonCircle size={theme.size.monogram.header} />
      <View style={[s.titles, { height: titles }]}>
        <SkeletonLine
          role={{ fontSize: h2.fontSize * fontScale, lineHeight: h2.lineHeight * fontScale }}
          width={(width - 2 * theme.size.gutter) * NAME_SHARE}
        />
      </View>
    </View>
  );
}

/** **The tab bar's shape**: the track, as tall as it stands round a segment's label. */
export function GroupTabsSkeleton() {
  const { fontScale } = useWindowDimensions();
  const height = theme.size.seg * Math.max(1, fontScale) + 2 * theme.space.xxs;
  // At the gutter, as the page stands the bar it reveals (`GroupScreen`'s `tabs`).
  return <SkeletonBlock testID="group-tabs-skeleton" style={[s.track, { height }]} />;
}

const s = StyleSheet.create({
  lead: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  titles: { justifyContent: 'center' },
  track: { borderRadius: theme.radius.seg },
});
