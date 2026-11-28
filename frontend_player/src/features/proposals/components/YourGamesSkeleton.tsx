/**
 * **YOUR GAMES' skeleton** ([#871](https://github.com/Rakieta02/Rakieta/issues/871); PRD #867; the
 * loading shimmer log §6, Q15; design system 5.6) — what stands in the rail's place on Home while
 * the reads it waits on are out, and in the rail's place while its first read retries. **Only what
 * is always there**: the heading's bar, as wide as its words with a one-figure count — *YOUR GAMES ·
 * 1*, as nearly every Home's — and **one game card's block at the rail's real card size** — the content's width, as the
 * paging rail hands every card, and as tall as the rows every card draws (`homeCardHeight`). The dots, a
 * second card and the empty sentences are not guessed at.
 *
 * In `HomeRow`'s frame — `lg` above the heading, `sm` under it — so the reveal moves nothing it
 * need not. Drawn on the shell's `SkeletonGround`, hidden from a listener as every shape is.
 */

import { StyleSheet, View } from 'react-native';

import { SkeletonBlock, SkeletonWords, theme } from '@/shared/ui';

import { CARD_TAG } from './CardTag';
import { gamesHeading } from './homePresentation';

/** `HomeRow`'s heading: 3.3's section heading, `eyebrow` in capitals. */
const HEADING = { ...theme.type.eyebrow, textTransform: 'uppercase' } as const;

/** The facts every card draws: where, the day and the time. */
const FACTS = 3;

/**
 * **A Home card's height**, read off its drawing (`HomeGameCard`), for the rows every card draws: the
 * dark card's padding above and below; the tags' row; `md`; the facts, each its label over its value
 * `xxs` apart, `sm` between them (`GameFacts`); `md`; and the footer's large button.
 *
 * It and the heading's words are worked out at the call, never as the module loads: the barrels'
 * cycle can load this file while `homePresentation`'s copy is part way through loading.
 */
export const homeCardHeight = () =>
  2 * theme.space.lg +
  theme.type.tag.lineHeight +
  2 * CARD_TAG.padY +
  theme.space.md +
  FACTS * (theme.type.eyebrow.lineHeight + theme.space.xxs + theme.type.h2.lineHeight) +
  (FACTS - 1) * theme.space.sm +
  theme.space.md +
  theme.size.btnLg;

export function YourGamesSkeleton() {
  return (
    <View testID="your-games-skeleton" style={s.section}>
      {/* With a one-figure count, which is what nearly every Home draws. */}
      <SkeletonWords role={HEADING} words={gamesHeading(1)} />
      <SkeletonBlock
        testID="your-games-skeleton-card"
        style={[s.card, { height: homeCardHeight() }]}
      />
    </View>
  );
}

const s = StyleSheet.create({
  // `HomeRow`'s section.
  section: { gap: theme.space.sm, marginTop: theme.space.lg },
  card: { borderRadius: theme.radius.cardDark },
});
