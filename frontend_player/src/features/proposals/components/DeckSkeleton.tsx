/**
 * **The Games tab's skeleton** ([#875](https://github.com/Raketa02/Raketa/issues/875); PRD #867; the
 * loading shimmer log §10) — **one deck-card block filling the stage**, where the deck will stand
 * while its first read is out: on the group page's reveal, and in the deck's own place while that
 * read retries (`GamesDeck`).
 *
 * It stands in the deck's own frame (`GamesDeck`'s page): the gutter round it, the block taking what
 * the page leaves above the three buttons, at the deck card's corner, and **the buttons' row left
 * bare** — so the card that replaces it lands where the block stood, and the buttons come in under it.
 * Drawn on the page's `SkeletonGround`; hidden from a listener, as every shape is.
 */

import { StyleSheet, View } from 'react-native';

import { SkeletonBlock, theme } from '@/shared/ui';

export function DeckSkeleton() {
  return (
    <View style={s.page} testID="deck-skeleton">
      <SkeletonBlock style={s.card} />
      {/* The three buttons' row, as tall as its tallest — the ball — and drawn by nothing. */}
      <View style={s.buttons} />
    </View>
  );
}

const s = StyleSheet.create({
  // `GamesDeck`'s page: the gutter, and the stacked-card step between the stage and its buttons.
  page: { flexGrow: 1, padding: theme.size.gutter, gap: theme.space.sm },
  // The stage, and the step under it the deck's stage keeps (`GamesDeck`'s `stage`).
  card: { flexGrow: 1, borderRadius: theme.radius.deckCard, marginBottom: theme.space.sm },
  buttons: { height: theme.size.deckAnswer.accept },
});
