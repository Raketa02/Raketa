/**
 * **The Home row frame** — every row on Home draws its heading and its sideways rail through this
 * one frame ([#798](https://github.com/Raketa02/Raketa/issues/798); the Home rows screens §2;
 * Part 16, 2026-11-14).
 *
 * ```
 * FRIEND REQUESTS · 2                    [control]  See all ›   ← eyebrow · muted · uppercase; the link ink
 * ┌──────────────────────────┐ ┌──────────                     ← space.sm under the heading
 * │ a card, 0.74 × content   │ │ the next one peeks            ← 7.7's peeking rail, Part 8's Strip
 * └──────────────────────────┘ └──────────                     ← bleeding to the screen edge
 * ```
 *
 * ## Two parts, so a row can say something instead of a rail
 *
 * **`HomeRow`** is the section: `space.lg` under the row above, the heading, and on the heading's
 * line an optional **control** (Top 10's sport pill) and an optional **link** (*See all ›*, Top 10's
 * *Rankings ›*). Under it, whatever the row draws — almost always **`HomeRowRail`**, but *Your games*
 * says its empty sentences or its failure there instead, and Top 10 will say *Nobody ranked in
 * squash yet*. A frame that owned the rail outright would have to grow a slot for each of those.
 *
 * **`HomeRowRail`** is the rail, in 7.7's two geometries over Part 8's Strip — neither restated
 * here: the gap 9, the bleed through a negative margin against the gutter.
 *
 * - **Peeking** (the default): a card is `railCardRatio` of the content width, so the next one's
 *   edge is the affordance; **a lone card takes the content width**, since there is nothing to
 *   peek at. It scrolls freely unless the row asks it to **snap** a card at a time.
 * - **Paging**: every card the content width, snapping one at a time, and 7.18's dots under it,
 *   tracking the scroll — a paging rail takes the dots always.
 *
 * The rail hands each card its width; the cards are the row's.
 *
 * ## The rail is never remounted
 *
 * **Scroll position must survive a re-render** (Part 8): in React Native that is keeping the
 * `ScrollView` the same one. It stands at one place in the tree whatever the count, the geometry's
 * width or the heading's line hold, so a row whose cards come and go stays where the finger left it.
 *
 * ## The link
 *
 * **The row hands in its words and its name**, as the sport pill takes its words — nothing here is
 * the frame's own. The words are drawn with a chevron after them, a direction rather than a word and
 * hidden; the name is what is spoken, and names what it opens (*See all same competitive level
 * players*), since three *See all*s on one screen would otherwise be one name for three places. It
 * is a **link** to a screen reader: it opens another screen. Ink on paper, the sign-in screen's link
 * (`rlValue`), its reach `hit.rowLink` — under 44 tall, on purpose (6.5).
 *
 * **It stands on the heading's line without making it taller.** Its 16pt line overhangs the
 * eyebrow's 12 by 2 above and 2 below, so a row with a link stands exactly where a row without one
 * does — as the mocks draw them, one under another at the same spacing.
 *
 * **It never imports a feature.** Every word, every press and every card is handed in.
 */

import { useState, type ReactNode } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
  type NativeScrollEvent,
  type NativeSyntheticEvent,
} from 'react-native';

import { PagerDots } from './PagerDots';
import { theme } from './theme';

/** A heading's link — *See all ›*, *Rankings ›* — in the row's words. */
export interface HomeRowLink {
  /** Drawn, before the frame's chevron — *See all*. */
  readonly words: string;
  /** Spoken — what it opens: *See all same competitive level players*. */
  readonly label: string;
  readonly onPress: () => void;
}

export interface HomeRowProps {
  /** The row's heading as the row words it, its count included — drawn uppercase. */
  readonly heading: string;
  /** **A control on the heading's line**, before the link — Top 10's sport pill. */
  readonly control?: ReactNode;
  /** **The link at the heading's right end** — *See all ›*. */
  readonly link?: HomeRowLink;
  readonly testID?: string;
  /** Under the heading: the rail, or what the row says instead of one. */
  readonly children: ReactNode;
}

export function HomeRow({ heading, control, link, testID, children }: HomeRowProps) {
  return (
    <View style={s.section} {...(testID === undefined ? {} : { testID })}>
      <View style={s.head}>
        <Text style={s.heading} accessibilityRole="header">
          {heading}
        </Text>
        {control}
        {link === undefined ? null : <RowLink link={link} />}
      </View>
      {children}
    </View>
  );
}

function RowLink({ link }: { readonly link: HomeRowLink }) {
  return (
    <Pressable
      accessibilityRole="link"
      accessibilityLabel={link.label}
      onPress={link.onPress}
      hitSlop={theme.hit.rowLink}
      style={({ pressed }) => [s.link, pressed ? s.pressed : undefined]}
    >
      <Text style={s.linkWords}>{link.words}</Text>
      <Text style={s.linkWords} accessibilityElementsHidden importantForAccessibility="no">
        {CHEVRON}
      </Text>
    </Pressable>
  );
}

/** 7.7's two geometries. */
export type HomeRowRailGeometry = 'peeking' | 'paging';

export interface HomeRowRailProps<Card> {
  /** **The cards' data**, in the order drawn — a peeking rail draws a lone one at the content width. */
  readonly cards: readonly Card[];
  /** **Peeking** unless the card needs the width (7.7's *choose by whether the card fits*). */
  readonly geometry?: HomeRowRailGeometry;
  /** A peeking rail that snaps a card at a time. A paging rail always does. */
  readonly snap?: boolean;
  /** **One card**, drawn at the width handed in — keyed by the row, as any list's element is. */
  readonly children: (card: Card, cardWidth: number) => ReactNode;
}

export function HomeRowRail<Card>({
  cards,
  geometry = 'peeking',
  snap = false,
  children,
}: HomeRowRailProps<Card>) {
  const { width: screen } = useWindowDimensions();
  /** Which card is on screen — the dots' only input, on a paging rail. */
  const [current, setCurrent] = useState(0);

  const paging = geometry === 'paging';
  const content = screen - 2 * theme.size.gutter;
  const cardWidth = paging || cards.length === 1 ? content : content * theme.size.railCardRatio;
  const step = cardWidth + STRIP_GAP;

  const onScroll = (event: NativeSyntheticEvent<NativeScrollEvent>) => {
    setCurrent(Math.round(event.nativeEvent.contentOffset.x / step));
  };

  return (
    <>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        {...(paging || snap ? { snapToInterval: step, decelerationRate: 'fast' as const } : {})}
        {...(paging ? { onScroll, scrollEventThrottle: SCROLL_THROTTLE_MS } : {})}
        style={s.strip}
        contentContainerStyle={s.stripContent}
      >
        {cards.map((card) => children(card, cardWidth))}
      </ScrollView>
      {paging ? <PagerDots count={cards.length} current={current} /> : null}
    </>
  );
}

/** The link's chevron — `SportPill`'s fold mark, pointing to where it goes. */
const CHEVRON = '›';

/** How far the link's line overhangs the heading's, above and below — so it never grows it. */
const LINK_OVERHANG = (theme.type.rlValue.lineHeight - theme.type.eyebrow.lineHeight) / 2;

/** Part 8's Strip gap. */
const STRIP_GAP = theme.space.sm;

/** One frame at 60 Hz. The dots track the scroll, so they are told about every frame of it. */
const SCROLL_THROTTLE_MS = 16;

const s = StyleSheet.create({
  section: { gap: theme.space.sm, marginTop: theme.space.lg },
  head: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  // 3.3 as amended: a section heading is `eyebrow` / `muted` / uppercase, and `h2` titles a card.
  // It takes the line's width, wrapping as it did standing alone, and leaves the rest to the link.
  heading: {
    ...theme.type.eyebrow,
    color: theme.color.muted,
    textTransform: 'uppercase',
    flex: 1,
  },
  link: { flexDirection: 'row', gap: theme.space.xxs, marginVertical: -LINK_OVERHANG },
  // 6.6's chip value, as the sign-in screen's link presses.
  pressed: { opacity: 0.7 },
  linkWords: { ...theme.type.rlValue, color: theme.color.ink },
  // Part 8: the negative margin is what lets the strip bleed to the screen edge while its content
  // still aligns to the gutter.
  strip: { marginHorizontal: -theme.size.gutter },
  stripContent: { paddingHorizontal: theme.size.gutter, gap: STRIP_GAP },
});
