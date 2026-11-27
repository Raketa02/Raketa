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
 *
 * **The same block stands in the stack's place while a kind picked from the tab's menu is read**
 * (`SwapSkeleton`, [#876](https://github.com/Raketa02/Raketa/issues/876); the loading shimmer log
 * §10, Q26) — where today's spinner stood.
 */

import { StyleSheet, View } from 'react-native';

import { SkeletonBlock, theme, useTabBarReach } from '@/shared/ui';

/** The buttons' row the block leaves bare, to a test. */
const BARE_BUTTONS = 'deck-skeleton-buttons';

export function DeckSkeleton() {
  // Ends at the bar's reach, its own gap clear of it (10.1, ADR-0210 §3, #881).
  const reach = useTabBarReach();
  return (
    <View style={[s.page, { paddingBottom: reach + theme.size.gutter }]} testID="deck-skeleton">
      <SkeletonBlock style={s.card} />
      {/* The three buttons' row, as tall as its tallest — the ball — and drawn by nothing. */}
      <View style={s.buttons} testID={BARE_BUTTONS} />
    </View>
  );
}

export interface SwapSkeletonProps {
  /** The deck draws no buttons under the stack's place — their row is left bare, as above. */
  readonly bareButtons: boolean;
}

/**
 * **The block in the stack's place, during a swap** — `SwapStack` stands it over the stage's box, which
 * is already in the page's gutter and already stops at the stage's step, so the block fills that box.
 * **Where the deck draws no buttons under it** — the swap left the group's starting card, or the kind
 * picked promised no card — **it leaves their row bare** inside the box, as the tab's own block does:
 * either way it ends where the card coming in will.
 */
export function SwapSkeleton({ bareButtons }: SwapSkeletonProps) {
  return (
    <View style={s.stack} testID="deck-skeleton">
      <SkeletonBlock style={s.block} />
      {bareButtons ? <View style={s.buttons} testID={BARE_BUTTONS} /> : null}
    </View>
  );
}

const s = StyleSheet.create({
  // `GamesDeck`'s page: the gutter, and the stacked-card step between the stage and its buttons.
  page: { flexGrow: 1, padding: theme.size.gutter, gap: theme.space.sm },
  // The stage, and the step under it the deck's stage keeps (`GamesDeck`'s `stage`).
  card: { flexGrow: 1, borderRadius: theme.radius.deckCard, marginBottom: theme.space.sm },
  buttons: { height: theme.size.deckAnswer.accept },
  // The stage's own box, which keeps that step outside it: the block, and the bare row a step under.
  stack: { flexGrow: 1, gap: theme.space.sm },
  block: { flexGrow: 1, borderRadius: theme.radius.deckCard },
});
