/**
 * **FOR YOU's skeleton** ([#871](https://github.com/Rakieta02/Rakieta/issues/871); PRD #867; the
 * loading shimmer log §6, Q15; design system 5.6) — what stands in FOR YOU's place on Home while the
 * reads its lines wait on are out: **the heading's bar**, as wide as its words, and **four closed
 * lines at the line's real height** — the `h2` line and `space.md` above and below it, `minTouch`
 * exactly, inside the line's border (`foldingLine`) — at the card's corner. Four, as the log settles
 * them (Q15), whichever of the five come.
 *
 * In `FoldingLines`' frame — `HomeRow`'s, `lg` above the heading and `sm` between everything under it —
 * so the reveal moves nothing it need not. Drawn on Home's `SkeletonGround`, hidden from a listener.
 */

import { StyleSheet, View } from 'react-native';

import { SkeletonBlock, SkeletonWords, theme } from '@/shared/ui';

import { HOME_COPY } from './shellCopy';

/** `HomeRow`'s heading: 3.3's section heading, `eyebrow` in capitals. */
const HEADING = { ...theme.type.eyebrow, textTransform: 'uppercase' } as const;

/** The closed lines drawn (the log's Q15). */
const LINES = 4;

/** **A closed line's height**: its header, `minTouch` exactly, inside its border above and below. */
const CLOSED_LINE = theme.size.minTouch + 2 * theme.size.foldingLine.border;

export function ForYouSkeleton() {
  return (
    <View testID="for-you-skeleton" style={s.section}>
      <SkeletonWords role={HEADING} words={HOME_COPY.forYou} />
      {Array.from({ length: LINES }, (_unused, at) => (
        <SkeletonBlock key={`line-${at}`} testID="for-you-skeleton-line" style={s.line} />
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  // `HomeRow`'s section.
  section: { gap: theme.space.sm, marginTop: theme.space.lg },
  line: { height: CLOSED_LINE, borderRadius: theme.radius.card },
});
