/**
 * **Fill in's and You’re in's skeleton** ([#875](https://github.com/Raketa02/Raketa/issues/875); PRD
 * #867; the loading shimmer log §10) — **rows**, where the boards' rows will stand while the tab's
 * first read is out: on the group page's reveal, and in the board's own place while that read
 * retries (`FillInBoard`, `YoureInBoard`).
 *
 * Each row is drawn as the row is (`FillInRow`): the white card, its padding and its stroke's room —
 * a stroke in no colour, since coral or mint would say *rescue* or *yours* about rows nobody has read —
 * with the title's bar and the club's line, then the squares a court's four seats take and the row's
 * button. The bars stand in their roles' lines at the phone's text size (`fontScale`), as the words
 * will, so a row that lands takes the room its skeleton held. Three rows: what a phone shows of a
 * board before it scrolls. Drawn on the page's `SkeletonGround`.
 */

import { StyleSheet, View, useWindowDimensions } from 'react-native';

import { SkeletonBlock, SkeletonLine, playerPhotoRadius, theme } from '@/shared/ui';

/** A court's four seats — the squares a doubles row draws. */
const SEATS = [0, 1, 2, 3] as const;
const ROWS = [0, 1, 2] as const;
const SEAT = theme.size.groupPage.seat;

/** A role's line at the phone's text size, as its words will stand. */
function scaled(role: { readonly fontSize: number; readonly lineHeight: number }, by: number) {
  return { fontSize: role.fontSize * by, lineHeight: role.lineHeight * by };
}

export function BoardSkeleton() {
  const { fontScale } = useWindowDimensions();
  const title = scaled(theme.type.h2, fontScale);
  const sub = scaled(theme.type.rlLabel, fontScale);
  return (
    <View style={s.rows} testID="board-skeleton">
      {ROWS.map((row) => (
        <View key={row} style={s.row}>
          <View style={s.head}>
            <SkeletonLine role={title} width="55%" />
            <SkeletonLine role={sub} width="75%" />
          </View>
          <View style={s.foot}>
            <View style={s.squares}>
              {SEATS.map((seat) => (
                <SkeletonBlock key={seat} style={s.seat} />
              ))}
            </View>
            <SkeletonBlock style={s.button} />
          </View>
        </View>
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  rows: { gap: theme.space.sm },
  // `FillInRow`'s card, its stroke's room kept in no colour.
  row: {
    backgroundColor: theme.color.surface,
    borderRadius: theme.radius.card,
    borderWidth: theme.size.fillInRow.stroke,
    borderColor: theme.color.surface,
    padding: theme.space.md,
    gap: theme.space.md,
  },
  head: { gap: theme.space.xxs },
  foot: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  squares: { flexDirection: 'row', gap: theme.space.xs },
  seat: { width: SEAT, height: SEAT, borderRadius: playerPhotoRadius(SEAT) },
  // The row's act — *Pay 27 zł*, *Withdraw* — a default button's height, a short word's width.
  button: { width: theme.size.btn * 3, height: theme.size.btn, borderRadius: theme.radius.btn },
});
