/**
 * **A count over a 16pt glyph** — 10.2's badge, the one count mark the system has, drawn by the tab
 * bar's Home column, by the bell on Home's header (7.29,
 * [#627](https://github.com/Raketa02/Raketa/issues/627)) and by the envelope beside it (10.3,
 * [#819](https://github.com/Raketa02/Raketa/issues/819)). The caller places it inside the glyph's own
 * `size.tabIcon` box, with `overflow: 'visible'` — Android clips a child drawn outside its parent,
 * and a clipped badge is a count disappearing on one platform.
 *
 * **The tone is the meaning, and the fill follows it** (1.2):
 *
 * - **`attend`** — things only the player can clear, the bar's Home badge: **`coralInk`** with a
 *   white figure at 5,89. White on `coral` is 3,89, the one pairing Rule C refuses outright and the
 *   exact correction the ⚡Play disc already took. It is 1.2's sixth coral entry.
 * - **`news`** — what is new since a visit: the bell's notices since the list was last opened, and
 *   the envelope's answers waiting since Needs your answer was last closed. **`ink`** with a white
 *   figure at 17,50. News is not an obligation, and 1.2 closes coral at six.
 *
 * The figure is mono and tabular, so 1 → 2 does not reflow, and a minimum width rather than a
 * diameter, so two figures — or the bell's *99+* — spread the mark into a lozenge. **The caller says
 * what to write**: the bar writes every count, the bell and the envelope cap at *99+*.
 *
 * It is **out of the layout**, like the bar's active ring and for the same reason: it rises
 * `badgeRise` above the icon — the 4pt the ring already spends out of the bar's 6pt top padding — and
 * sits back over the glyph's right edge by the smallest step on the grid, so it reads as attached to
 * the mark rather than floating beside it.
 *
 * **It announces nothing.** The count belongs on the control's own `accessibilityLabel` — a `<Text>`
 * inside an `accessible` column is swallowed — so a badge that announced itself would be either
 * silent or a second reading of one number.
 */

import { StyleSheet, Text, View } from 'react-native';

import { theme } from './theme';

export type CountBadgeTone = 'attend' | 'news';

export interface CountBadgeProps {
  /** What the mark writes — the caller's count, or its cap. */
  readonly figure: number | string;
  readonly tone: CountBadgeTone;
}

export function CountBadge({ figure, tone }: CountBadgeProps) {
  return (
    <View
      style={[s.badge, tone === 'attend' ? s.attend : s.news]}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <Text style={s.figure} maxFontSizeMultiplier={theme.size.tabBar.labelMaxScale}>
        {figure}
      </Text>
    </View>
  );
}

const s = StyleSheet.create({
  badge: {
    position: 'absolute',
    // Up by the ring's own overhang, and back over the glyph's right edge by the smallest
    // step on the grid — so the badge belongs to the mark rather than sitting beside it.
    bottom: theme.size.tabIcon - theme.size.tabBar.badge + theme.size.tabBar.badgeRise,
    left: theme.size.tabIcon - theme.space.xxs,
    height: theme.size.tabBar.badge,
    minWidth: theme.size.tabBar.badge,
    paddingHorizontal: theme.space.xxs,
    borderRadius: theme.radius.pill,
    alignItems: 'center',
    justifyContent: 'center',
  },
  // 6.1 `primary`'s fill: white on `coralInk` is 5.89, where white on `coral` is 3.89.
  attend: { backgroundColor: theme.color.coralInk },
  // White on `ink` is 17.50.
  news: { backgroundColor: theme.color.ink },
  figure: {
    ...theme.num.xs,
    ...theme.tabular,
    color: theme.color.surface,
    // The role's own line height is 17 inside an 18pt box; centring is the box's job, and the
    // text box must not add its own leading on top of it.
    lineHeight: theme.size.tabBar.badge,
  },
});
