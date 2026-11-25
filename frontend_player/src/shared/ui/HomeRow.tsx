/**
 * **The Home row frame** — a row in Needs your answer and *Your games* draws its heading and its
 * sideways rail through this one frame ([#798](https://github.com/Raketa02/Raketa/issues/798); the
 * Home rows screens §2; Part 16, 2026-11-14), and FOR YOU's open lines draw their rails on its rail
 * (`FoldingLine`, [#820](https://github.com/Raketa02/Raketa/issues/820)).
 *
 * ```
 * FRIEND REQUESTS · 2                                ← eyebrow · muted · uppercase
 * ┌──────────────────────────┐ ┌──────────          ← space.sm under the heading
 * │ a card, 0.74 × content   │ │ the next one peeks ← 7.7's peeking rail, Part 8's Strip
 * └──────────────────────────┘ └──────────          ← bleeding to the screen edge
 * ```
 *
 * ## Two parts, so a row can say something instead of a rail
 *
 * **`HomeRow`** is the section: `space.lg` under the row above, and the heading. Under it, whatever
 * the row draws — almost always **`HomeRowRail`**, but *Your games* says its empty sentences or its
 * failure there instead. A frame that owned the rail outright would have to grow a slot for each.
 * **The heading's line holds the heading alone** since #820: *See all ›*, Top 10's sport pill and
 * *Rankings ›* were the five discovery rows', and went with them to FOR YOU's footers
 * (`FoldingLineFooter`).
 *
 * **`HomeRowRail`** is the rail, in 7.7's geometries over Part 8's Strip — neither restated here: the
 * gap 9, the bleed through a negative margin against the gutter.
 *
 * - **Peeking** (the default): a card is `railCardRatio` of the content width, so the next one's
 *   edge is the affordance; **a lone card takes the content width**, since there is nothing to
 *   peek at. It scrolls freely unless the row asks it to **snap** a card at a time.
 * - **Wide** (#816): the peeking rail at the request card's wider share, `requestCardRatio` — a
 *   friend request and an ask for a level in Needs your answer. A lone card takes the content
 *   width, as on the peeking rail. It scrolls freely.
 * - **Paging**: every card the content width, snapping one at a time, and 7.18's dots under it,
 *   tracking the scroll — a paging rail takes the dots always, but for Needs your answer's *FRIENDS
 *   GAME*, which draws them from two (`dotsAlone`, #817).
 * - **Tiles** (#801; 7.31): New in Raketa's portrait tiles, each the peeking card's
 *   `railCardRatio` of the content width since 2026-11-24 — one whole and the next peeking, as
 *   Players at your level's cards stand on the line above. **A lone tile keeps its width**: a
 *   portrait the width of the screen would be a poster, not a tile. It scrolls freely.
 * - **Numbered** (#805; 7.36): Top 10's cards, each `topTen.railRatio` of the content width — the
 *   width handed is the card's, and the numeral the row stands beside it is the row's own, so the
 *   rail's items are wider than the width it hands: the row says how wide (`itemWidth`). A lone card
 *   keeps its width. It scrolls freely.
 *
 * The rail hands each card its width; the cards are the row's.
 *
 * ## Inside a folding line
 *
 * **The content is the line's, not the page's** (#820): a rail in an open FOR YOU line takes its
 * shares of the line's content width and bleeds to the line's inner edge, its first card at the
 * line's inset — what `RailBounds` says, which the line provides. Outside a line it is the page's:
 * the screen less the gutters, bleeding through the gutter. **There every rail snaps** to its cards'
 * edges (the brief: *the tiles swipe sideways and settle on tile edges*).
 *
 * ## The rail is never remounted
 *
 * **Scroll position must survive a re-render** (Part 8): in React Native that is keeping the
 * `ScrollView` the same one. It stands at one place in the tree whatever the count, the geometry's
 * width or the heading's line hold, so a row whose cards come and go stays where the finger left it.
 * **In a FOR YOU line that holds while the line stays open**: a closed line draws nothing, so a line
 * opened again draws a new rail, at its first card (#820).
 *
 * ## What is drawn first
 *
 * **The cards that can be seen, and the rest a moment later.** A Home rail holds up to ten cards, and
 * a card is a face or four — a generated poster each, a dozen native views apiece — so drawing every
 * card at once was most of what Home cost: a device spent seconds creating views a finger had not
 * reached. So the rail's first frame draws only the cards that can be on screen (`cardsDrawnFirst`,
 * one past the rail's visible edge), and a stand-in of the same width for each of the rest; right
 * after it, a second pass draws the rest, once the first is on its way to the screen. The content is
 * its full width from the first frame, so the step, the snap, the dots and what is on screen are
 * measured exactly as before.
 *
 * ## What is on screen
 *
 * **A rail handed `onScreen` is told which of its cards are at least half on screen** (#804;
 * `onScreen.ts`), on a page that watches. The section says where it stands on the page **from its
 * own layout** (`useTopOnPage`): in its parent's coordinates, added to where the section around it
 * stands — a folding line's content in FOR YOU — or the page's column when there is none. The rail
 * stands directly in the section, which is what lets the two tops add up.
 *
 * **It never imports a feature.** Every word, every press and every card is handed in.
 */

import {
  createContext,
  isValidElement,
  memo,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react';
import {
  ScrollView,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
  type NativeScrollEvent,
  type NativeSyntheticEvent,
} from 'react-native';

import { ON_SCREEN_SAMPLE_MS, SectionOnPage, useCardsOnScreen, useTopOnPage } from './onScreen';
import { PagerDots } from './PagerDots';
import { theme } from './theme';

export interface HomeRowProps {
  /** The row's heading as the row words it, its count included — drawn uppercase. */
  readonly heading: string;
  readonly testID?: string;
  /** Under the heading: the rail, or what the row says instead of one. */
  readonly children: ReactNode;
}

export function HomeRow({ heading, testID, children }: HomeRowProps) {
  /** Where the section stands on its page — what a watching rail in it is measured from. */
  const { top, laidOut } = useTopOnPage();
  return (
    <View
      style={s.section}
      onLayout={({ nativeEvent }) => laidOut(nativeEvent.layout.y)}
      {...(testID === undefined ? {} : { testID })}
    >
      <SectionOnPage.Provider value={top}>
        <Text style={s.heading} accessibilityRole="header">
          {heading}
        </Text>
        {children}
      </SectionOnPage.Provider>
    </View>
  );
}

/**
 * **What a rail stands in** — the width its shares are of, and how far it bleeds past it each side,
 * which is also where its first card starts. A folding line provides its own (#820); with none, the
 * page's: the screen less the gutters, bleeding through the gutter.
 */
export interface RailBounds {
  readonly content: number;
  readonly bleed: number;
  /** **Every card snaps** — a rail in a folding line settles on its cards' edges. */
  readonly snaps: boolean;
}

export const RailBoundsContext = createContext<RailBounds | undefined>(undefined);

/**
 * **Whether a rail may draw its cards past the screen's edge yet** — at once anywhere but in a folding
 * line, which says so once it has unfolded (2026-11-21): drawn mid-unfold, the seven or so cards
 * nobody can see yet were a commit that held the JavaScript thread through the whole motion on a
 * Galaxy A32, and every press with it.
 */
export const RailDrawsAll = createContext(true);

/**
 * 7.7's two geometries, Needs your answer's wider peeking card (7.7 as amended by #816), New in
 * Raketa's portrait tiles (7.31) and Top 10's numbered cards (7.36).
 */
export type HomeRowRailGeometry = 'peeking' | 'wide' | 'paging' | 'tiles' | 'numbered';

export interface HomeRowRailProps<Card> {
  /** **The cards' data**, in the order drawn — a peeking rail draws a lone one at the content width. */
  readonly cards: readonly Card[];
  /** **Peeking** unless the card needs the width (7.7's *choose by whether the card fits*). */
  readonly geometry?: HomeRowRailGeometry;
  /** A peeking rail that snaps a card at a time. A paging rail always does, and so does a line's. */
  readonly snap?: boolean;
  /**
   * **How wide an item stands, given the width the rail hands its card** — Top 10's, whose numeral
   * stands beside the card (#805): what the rail steps, snaps and draws first by. A card's width when
   * not said.
   */
  readonly itemWidth?: (cardWidth: number) => number;
  /**
   * **Whether a paging rail of one draws its one dot** — 7.18's *always*, the default. Needs your
   * answer's *FRIENDS GAME* draws its dots from two (#817, Q46; 7.18 as amended): one big tile in a
   * sheet has nothing to page to, and its heading counts it.
   */
  readonly dotsAlone?: boolean;
  /**
   * **Told which cards are on screen** — at least half of each visible, across the page's scroll and
   * the rail's (#804) — whenever either moves, the rail is laid out, the cards change, or the page
   * comes back into view. Only on a page that watches (`PageOnScreen`); a row that does not ask is
   * never measured.
   */
  readonly onScreen?: (cards: readonly Card[]) => void;
  /** **One card**, drawn at the width handed in — keyed by the row, as any list's element is. */
  readonly children: (card: Card, cardWidth: number) => ReactNode;
}

export function HomeRowRail<Card>({
  cards,
  geometry = 'peeking',
  snap = false,
  itemWidth,
  dotsAlone = true,
  onScreen,
  children,
}: HomeRowRailProps<Card>) {
  const { width: screen } = useWindowDimensions();
  const bounds = useContext(RailBoundsContext) ?? {
    content: screen - 2 * theme.size.gutter,
    bleed: theme.size.gutter,
    snaps: false,
  };
  /** Which card is on screen — the dots' only input, on a paging rail. */
  const [current, setCurrent] = useState(0);

  const paging = geometry === 'paging';
  const { content, bleed } = bounds;
  const cardWidth =
    geometry === 'tiles'
      ? content * theme.size.railCardRatio
      : geometry === 'numbered'
        ? content * theme.size.topTen.railRatio
        : paging || cards.length === 1
          ? content
          : geometry === 'wide'
            ? content * theme.size.requestCardRatio
            : content * theme.size.railCardRatio;
  const step = (itemWidth?.(cardWidth) ?? cardWidth) + STRIP_GAP;
  const snaps = paging || snap || bounds.snaps;
  const watching = onScreen !== undefined;
  const seen = useCardsOnScreen({ cards, lead: bleed, cardWidth, step, onScreen });

  /**
   * Whether the cards past the screen's edge are drawn yet — once the rail has had cards for a frame,
   * and, in a folding line, once the line has unfolded (`RailDrawsAll`). Keyed on *having* cards
   * rather than on mounting, because a row's rail can stand empty while its read is in flight, and
   * the cards arriving are the moment that costs.
   */
  const [allDrawn, setAllDrawn] = useState(false);
  const hasCards = cards.length > 0;
  const mayDrawAll = useContext(RailDrawsAll);
  useEffect(() => {
    // A plain update from the effect, never `startTransition`: React Native 0.76's renderer threw
    // on a transition started here (`Cannot read property 'add' of undefined`) and took Home down.
    if (hasCards && !allDrawn && mayDrawAll) setAllDrawn(true);
  }, [hasCards, allDrawn, mayDrawAll]);
  const drawn = allDrawn
    ? cards.length
    : cardsDrawnFirst({ count: cards.length, screen: content + 2 * bleed, step });

  const onScroll = (event: NativeSyntheticEvent<NativeScrollEvent>) => {
    if (paging) setCurrent(Math.round(event.nativeEvent.contentOffset.x / step));
    seen.scrolled(event);
  };

  return (
    <>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        {...(snaps ? { snapToInterval: step, decelerationRate: 'fast' as const } : {})}
        {...(paging || watching
          ? {
              onScroll,
              scrollEventThrottle: paging ? SCROLL_THROTTLE_MS : ON_SCREEN_SAMPLE_MS,
            }
          : {})}
        {...(watching
          ? {
              onLayout: seen.laidOut,
              onScrollEndDrag: seen.scrolled,
              onMomentumScrollEnd: seen.scrolled,
            }
          : {})}
        style={{ marginHorizontal: -bleed }}
        contentContainerStyle={[s.stripContent, { paddingHorizontal: bleed }]}
      >
        {cards.map((card, at) => {
          if (at >= drawn)
            return <View key={`${STAND_IN_KEY}${at}`} style={{ width: cardWidth }} />;
          const element = children(card, cardWidth);
          return (
            <DrawnCard
              key={isValidElement(element) && element.key !== null ? element.key : at}
              card={card}
              width={cardWidth}
              draw={children}
              element={element}
            />
          );
        })}
      </ScrollView>
      {paging && (dotsAlone || cards.length > 1) ? (
        // Held inside the rail: a card that leaves from the end — an invitation answered or run out —
        // shortens it with no scroll to say where the rail now stands.
        <PagerDots count={cards.length} current={Math.min(current, cards.length - 1)} />
      ) : null}
    </>
  );
}

/**
 * **How many of a rail's cards its first frame draws** — every card that can be on screen, and the
 * one past the screen's edge, so the first a finger drags in is already there. A rail of fewer draws
 * them all.
 */
export function cardsDrawnFirst({
  count,
  screen,
  step,
}: {
  readonly count: number;
  readonly screen: number;
  readonly step: number;
}): number {
  return Math.min(count, Math.ceil(screen / step) + 1);
}

interface DrawnCardProps {
  readonly card: unknown;
  readonly width: number;
  readonly draw: unknown;
  readonly element: ReactNode;
}

/**
 * **A card the rail has drawn, drawn again only when it changes** — its card, its width, or the row's
 * way of drawing it (2026-11-21). A rail re-renders on its own account — the page it is on coming or
 * going as its folding line opens and closes, the rest of its cards drawn — and it used to draw every
 * card anew each time: ten cards, each with its posters, its comparison bar and a friend button's four
 * writes and two sheets, on every open and close of a FOR YOU line. A row that draws again hands a new
 * `draw`, and every card follows, as before: nothing a card shows can be left behind.
 */
const DrawnCard = memo(
  function DrawnCard({ element }: DrawnCardProps) {
    return <>{element}</>;
  },
  (was, now) => was.card === now.card && was.width === now.width && was.draw === now.draw,
);

/** A stand-in's key, which no row's own key can be: a row keys its cards by their ids. */
const STAND_IN_KEY = 'drawn-in-a-moment-';

/** Part 8's Strip gap. */
const STRIP_GAP = theme.space.sm;

/** One frame at 60 Hz. The dots track the scroll, so they are told about every frame of it. */
const SCROLL_THROTTLE_MS = 16;

const s = StyleSheet.create({
  section: { gap: theme.space.sm, marginTop: theme.space.lg },
  // 3.3 as amended: a section heading is `eyebrow` / `muted` / uppercase, and `h2` titles a card.
  heading: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  // Part 8: the negative margin (the bounds' bleed) is what lets the strip bleed to the edge while
  // its content still aligns to the gutter. Every card as tall as the tallest — the row's own
  // default, said aloud because Needs your answer's tiles hold their buttons at their foot, level
  // across the rail (#816, Q3).
  stripContent: { gap: STRIP_GAP, alignItems: 'stretch' },
});
