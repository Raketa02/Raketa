/**
 * **Rankings' skeleton** ([#870](https://github.com/Raketa02/Raketa/issues/870); PRD #867; the loading
 * shimmer log §8, Q6; design system 5.6) — what stands below the header while the page has nothing to
 * draw yet. **One fixed skeleton for both views and every sport**, which never predicts the page's
 * true shape (no card, *Nobody ranked*, or Friends' card alone):
 *
 * - **a card-sized block** where the place card or the not-listed card will be — the dark place card
 *   drawn as a skeleton-tone block, at the listed card's own height (`PLACE_CARD`) and the dark
 *   card's corner;
 * - **three podium steps**, second, first, third, at their real heights and where the podium stands
 *   them;
 * - **rows filling the screen on one white card** — the list's own card, drawn as itself because it
 *   is always there — each with the real row's padding, the place column's room, the row face's
 *   circle, and bars for the name and the level.
 *
 * While the view or the sport is still unknown, the switch's place holds a shape of the switch's
 * own size and corner (`RankingSwitchSkeleton`), so the page is never blank under its header.
 * Hidden from a listener, as every skeleton shape is; the header and the sport pill are the real ones
 * throughout.
 */

import { useState } from 'react';
import { StyleSheet, View, useWindowDimensions } from 'react-native';

import { ROW_FACE } from '@/features/groups/types';
import { SkeletonBlock, SkeletonCircle, SkeletonLine, theme } from '@/shared/ui';

/**
 * **The listed place card's height**, read off its drawing (`PlaceCard`): the dark card's padding
 * above and below; *YOUR PLACE* over the place, `xs` apart; the fold, `md` either side; one gap line.
 */
const PLACE_CARD =
  2 * theme.space.lg +
  theme.type.eyebrow.lineHeight +
  theme.space.xs +
  theme.num.levelHero.lineHeight +
  2 * theme.space.md +
  StyleSheet.hairlineWidth +
  theme.type.rlLabel.lineHeight;

/** The podium's steps, in the order it stands them: second, first, third. */
const STEPS = [
  theme.size.rankings.stepSecond,
  theme.size.rankings.stepFirst,
  theme.size.rankings.stepThird,
] as const;

/**
 * A row's height: the face, the row's padding above and below it, and the fold above it. Worked out
 * at the call, never as the module loads: `groups`' barrel is part way through loading when this one
 * is, so its `ROW_FACE` is not there yet (the barrels' cycle `RankingsScreen`'s `viewOptions` notes).
 */
const rowHeight = () => ROW_FACE + 2 * theme.space.sm + 1;

/**
 * **The level's bar**: four figures wide (*2,71*), in `num.m`. IBM Plex Mono draws every glyph 600 of
 * 1000 units wide, less the role's tracking.
 */
const LEVEL_FIGURES = 4;
const MONO_ADVANCE = 0.6;
const LEVEL_BAR = LEVEL_FIGURES * (MONO_ADVANCE * theme.num.m.fontSize + theme.num.m.letterSpacing);

/** **The view's place**: the card, the podium and the rows, filling the screen. */
export function RankingsSkeleton() {
  const window = useWindowDimensions();
  // Rows for the room under the podium — the whole window's worth until it is laid out, the page
  // clipping what falls past its foot — so no row stands off screen, moving with the band.
  const [room, setRoom] = useState<number>();
  const rows = Math.ceil((room ?? window.height) / rowHeight());

  return (
    <View testID="rankings-skeleton" style={s.page}>
      <SkeletonBlock style={s.card} />
      <View style={s.podium}>
        {STEPS.map((step, at) => (
          <SkeletonBlock key={`step-${at}`} style={[s.step, { height: step }]} />
        ))}
      </View>
      <View style={s.room} onLayout={(event) => setRoom(event.nativeEvent.layout.height)}>
        <View style={s.list}>
          {Array.from({ length: rows }, (_unused, at) => (
            <View key={`row-${at}`} style={[s.row, at > 0 ? s.divided : undefined]}>
              <View style={s.place} />
              <SkeletonCircle size={ROW_FACE} />
              <SkeletonLine role={theme.type.cardTitle} style={s.name} />
              <SkeletonLine role={theme.num.m} width={LEVEL_BAR} />
            </View>
          ))}
        </View>
      </View>
    </View>
  );
}

/** **The switch's place**, while the view or the sport is still unknown: the switch's size and corner. */
export function RankingSwitchSkeleton() {
  return <SkeletonBlock testID="rankings-switch-skeleton" style={s.switch} />;
}

const s = StyleSheet.create({
  // The list's own gutter, and the `sm` its header stands its parts apart by.
  page: {
    flex: 1,
    paddingHorizontal: theme.size.gutter,
    gap: theme.space.sm,
    overflow: 'hidden',
  },
  card: { height: PLACE_CARD, borderRadius: theme.radius.cardDark },
  // Where the podium stands its steps: `lg` in from its recess's sides, `sm` apart.
  podium: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: theme.space.sm,
    paddingHorizontal: theme.space.lg,
  },
  step: {
    flex: 1,
    borderTopLeftRadius: theme.radius.card,
    borderTopRightRadius: theme.radius.card,
    borderBottomLeftRadius: 0,
    borderBottomRightRadius: 0,
  },
  // The rest of the page under the podium: the rows' room.
  room: { flex: 1 },
  // The list's one white card — `Card`'s surface, border and radius — drawn as itself.
  list: {
    backgroundColor: theme.color.surface,
    borderWidth: 1,
    borderColor: theme.color.line,
    borderRadius: theme.radius.card,
    overflow: 'hidden',
  },
  // `RankingList`'s row: its padding and its gaps.
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    paddingVertical: theme.space.sm,
    paddingHorizontal: theme.space.lg,
  },
  // 5.3: `line2` folds one card into rows.
  divided: { borderTopWidth: 1, borderTopColor: theme.color.line2 },
  place: { width: theme.size.rankings.place },
  name: { flex: 1 },
  // The switch's track: a segment's height and the track's padding, its corner, its margins.
  switch: {
    height: theme.size.seg + 2 * theme.space.xxs,
    borderRadius: theme.radius.seg,
    marginHorizontal: theme.size.gutter,
    marginBottom: theme.space.sm,
  },
});
