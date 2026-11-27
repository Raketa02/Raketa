/**
 * **How many are waiting, over a thing's top-right corner** — the Chats badge at a segment's size
 * (`size.segmentBadge`): the same `coralInk` pill with a white tabular figure, overlapping the
 * corner of what it counts so it belongs to that thing rather than sitting beside it. `Segment`
 * draws it over a segment (a group page's Games, Fill in and You’re in — on Fill in and You’re in
 * what is **new since the player last looked**, and on no tab while it is the one shown, #849), and
 * a group's page over the group's tile, counting the requests waiting on its Owner (#529, moved
 * there from the Info tab by Q125). One mark, one meaning — a count of things only you can clear,
 * by acting or, on a tab, by looking — which is why 1.2's sixth coral entry does not widen for it. It is `CountBadge`'s `attend` mark at a segment's size and placed on
 * a corner: `CountBadge` sits on a glyph, risen 4 above its box, at `num.xs`; this one
 * overlaps the corner of a box at `num.tiny`, so the two keep their own geometry.
 *
 * The parent places it: it is absolutely positioned, out of the layout, so a count arriving moves
 * nothing, and the parent sets `overflow: 'visible'` — Android clips a child drawn outside its
 * parent, and a clipped badge is a count disappearing on one platform.
 *
 * **It announces nothing**: the caller puts the count in the counted thing's own name, as the tab
 * bar puts it on the column's, and a badge that spoke too would be one number read twice.
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme } from './theme';

export interface CornerBadgeProps {
  /** How many are waiting. The caller draws no badge for none. */
  readonly count: number;
}

export function CornerBadge({ count }: CornerBadgeProps) {
  return (
    <View
      style={s.badge}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      {/* The tab bar's cap on the OS text size, because this is the tab bar's mark: past it the
          digit would outgrow a box whose height is fixed so the thing under it never moves. */}
      <Text style={s.count} maxFontSizeMultiplier={theme.size.tabBar.labelMaxScale}>
        {count}
      </Text>
    </View>
  );
}

const s = StyleSheet.create({
  // Up by the smallest steps on the grid, so it overlaps the corner rather than floating off it.
  badge: {
    position: 'absolute',
    top: -theme.space.xs,
    right: -theme.space.xxs,
    height: theme.size.segmentBadge,
    minWidth: theme.size.segmentBadge,
    paddingHorizontal: theme.space.xxs,
    borderRadius: theme.radius.pill,
    alignItems: 'center',
    justifyContent: 'center',
    // The Chats badge's fill: white on `coralInk` is 5.89, where white on `coral` is 3.89.
    backgroundColor: theme.color.coralInk,
  },
  count: {
    ...theme.num.tiny,
    ...theme.tabular,
    color: theme.color.surface,
    lineHeight: theme.size.segmentBadge,
  },
});
