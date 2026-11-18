/**
 * **What of a scrolled page is on screen** — the geometry a Home row's cards are seen by
 * ([#804](https://github.com/Raketa02/Raketa/issues/804); the Home rows mechanics §9.2, call 2).
 *
 * A card on a Home row is **on screen when at least half of it is visible** — across the page's own
 * scroll, which moves the row up and down, and the row's sideways one, which moves the card along
 * it. Both are clips of one rectangle by another, so what is seen of a card is the share of its
 * height inside the page's band times the share of its width inside the rail's: a card wholly across
 * the rail but only half up the screen is half seen, and so is one wholly up but half along.
 *
 * ## Read when wanted, never drawn
 *
 * The page's band moves at every frame of a scroll, and nothing on screen changes with it. So it is
 * a **followed value** — read when a rail wants it, and telling the rails that follow it when it
 * moves — rather than state: a page re-rendering every row at every frame to tell three of them
 * where it is would be the cost of a feature that draws nothing.
 *
 * ## Who says what
 *
 * - **The page** (`ShellScreen`, for the one screen that asks — Home) says its band, and says
 *   **nothing is on screen** while it is not the screen in view: a pushed screen over it, another
 *   tab, the app in the background. A page that does not watch never says a band at all.
 * - **`HomeRow`, FOR YOU and a folding line** each say where they stand on the page — **from their own
 *   layout, in their parent's coordinates, added to where the section around them stands**
 *   (`useTopOnPage`): a rail in an open line is measured through FOR YOU, the line and its fold, and
 *   a row standing directly in the page's column through nothing but itself (#820).
 * - **`HomeRowRail`** says where each card stands along it — the geometry is its own — and
 *   `useCardsOnScreen` says which are on screen to the row that asked (`onScreen`).
 *
 * It never imports a feature: what a row does with the cards it is told about is the row's.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import type {
  LayoutChangeEvent,
  LayoutRectangle,
  NativeScrollEvent,
  NativeSyntheticEvent,
} from 'react-native';

/** **At least half** of a card visible (call 2). */
export const ON_SCREEN_SHARE = 0.5;

/**
 * How often a scroller says where it is while it moves — ten times a second. A card that crosses
 * the screen faster than that was not seen; the end of a drag and of a fling are said whatever the
 * rate, so where a scroll comes to rest is always read.
 */
export const ON_SCREEN_SAMPLE_MS = 100;

/** A stretch of one axis — where it starts, and how long it is. */
export interface Span {
  readonly from: number;
  readonly size: number;
}

/** **How much of `item` lies inside `view`**, from 0 to 1 — none for an item with no size. */
export function shareInside(item: Span, view: Span): number {
  if (item.size <= 0) return 0;
  const start = Math.max(item.from, view.from);
  const end = Math.min(item.from + item.size, view.from + view.size);
  return Math.max(0, end - start) / item.size;
}

/** A rail's cards, laid along it — every card one width, one step after the one before. */
export interface RailCards {
  readonly count: number;
  /** Where the first card starts in the rail's content — the gutter it is padded by. */
  readonly lead: number;
  readonly cardWidth: number;
  /** A card and the gap after it. */
  readonly step: number;
}

/**
 * **Which of a rail's cards are on screen** — their places along it, in order — given the stretch
 * of the rail's content in view sideways, and the share of the rail's height on screen.
 */
export function cardsOnScreen(
  cards: RailCards,
  along: Span,
  uprightShare: number,
): readonly number[] {
  const seen: number[] = [];
  for (let at = 0; at < cards.count; at += 1) {
    const across = shareInside(
      { from: cards.lead + at * cards.step, size: cards.cardWidth },
      along,
    );
    if (across * uprightShare >= ON_SCREEN_SHARE) seen.push(at);
  }
  return seen;
}

/** A value read when wanted, that tells whoever follows it when it moves. */
export interface Followed<T> {
  /** What it is now — nothing while it is not known, or not on screen. */
  readonly get: () => T | undefined;
  /** Called each time it moves; answers how to stop. */
  readonly follow: (listener: () => void) => () => void;
}

/** A followed value, and the one hand that moves it. */
export interface Followable<T> extends Followed<T> {
  readonly set: (value: T | undefined) => void;
}

export function followable<T>(): Followable<T> {
  let value: T | undefined;
  const listeners = new Set<() => void>();
  return {
    get: () => value,
    follow: (listener) => {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
    set: (next) => {
      value = next;
      for (const listener of listeners) listener();
    },
  };
}

/**
 * **The page's band on screen**, in its content's coordinates — from how far it is scrolled, as
 * tall as it shows. Nothing while the page is not the screen in view, or not laid out yet; and no
 * provider at all outside a shell page, where no card is ever on screen.
 */
export const PageOnScreen = createContext<Followed<Span> | undefined>(undefined);

/**
 * **Where a section stands on its page** — the top of it, in the page's content: a `HomeRow`'s, FOR
 * YOU's, a folding line's, and the open line's content, each the one around a rail.
 */
export const SectionOnPage = createContext<Followed<number> | undefined>(undefined);

/** A view's top on its page, and the hand its layout feeds. */
export interface TopOnPage {
  /** What it provides as `SectionOnPage` to what it holds. */
  readonly top: Followed<number>;
  /** Its own layout's `y` — in its parent's coordinates, as a device reports it. */
  readonly laidOut: (y: number) => void;
}

/**
 * **Where a view stands on its page, from its own layout** (#820): its `y` in its parent added to where
 * the section around it stands, or — with none — the page's column itself, its parent. So a rail in a
 * line in FOR YOU is measured through each, as a device lays them out, and a `HomeRow` standing
 * directly in the page's column is measured as it always was. Nothing until both are known.
 */
export function useTopOnPage(): TopOnPage {
  return useTopWithin(useContext(SectionOnPage));
}

/**
 * **Where a view stands on its page, inside a section named here** rather than the one its context
 * provides — a view and one of its own children in one component, where the child's section is the
 * view's (a folding line's fold, under the line).
 */
export function useTopWithin(around: Followed<number> | undefined): TopOnPage {
  const [own] = useState(() => followable<number>());
  const top = useMemo<Followed<number>>(
    () =>
      around === undefined
        ? own
        : {
            get: () => {
              const outer = around.get();
              const y = own.get();
              return outer === undefined || y === undefined ? undefined : outer + y;
            },
            follow: (listener) => {
              const stops = [around.follow(listener), own.follow(listener)];
              return () => {
                for (const stop of stops) stop();
              };
            },
          },
    [around, own],
  );
  return { top, laidOut: own.set };
}

/**
 * **Brings a stretch of the page into view** — the page's, for what opens on it: a folding line asks
 * for its whole height once it has unfolded (#820; ADR-0205 §5: *the page eases down just enough*).
 * No provider outside a page that watches, where nothing is asked.
 */
export const PageReveal = createContext<((stretch: Span) => void) | undefined>(undefined);

/**
 * **Where a page scrolls to show a stretch of it** — just far enough that its foot stands at the
 * page's foot, or its head at the page's head when it is taller than the page shows; **nothing** when
 * its foot is already in view, or the page would have to scroll back up to show it.
 */
export function scrollToReveal(stretch: Span, band: Span): number | undefined {
  const foot = stretch.from + stretch.size;
  if (foot <= band.from + band.size) return undefined;
  const to = Math.min(stretch.from, foot - band.size);
  return to > band.from ? to : undefined;
}

type ScrollEvent = NativeSyntheticEvent<NativeScrollEvent>;

/** **A page that watches what is on it** — the band it hands its rows, and what feeds it. */
export interface WatchedPage {
  /** What the page provides as `PageOnScreen`. */
  readonly band: Followed<Span>;
  /** Spread on the page's scroller: its height, where it is scrolled, and where a scroll rests. */
  readonly scroller: {
    readonly onLayout: (event: LayoutChangeEvent) => void;
    readonly onScroll: (event: ScrollEvent) => void;
    readonly onScrollEndDrag: (event: ScrollEvent) => void;
    readonly onMomentumScrollEnd: (event: ScrollEvent) => void;
    readonly scrollEventThrottle: number;
  };
  /**
   * **Whether the page is the screen in view** — not with a screen pushed over it, another tab up,
   * or the app in the background. Coming back into view says the band again, so whatever stands on
   * screen then is seen.
   */
  readonly inView: (yes: boolean) => void;
}

/**
 * **The page's band, fed by its scroller** — one per page, for its life. Out of view until the page
 * says it is in view, so a page mounted under another is never seen for a frame; and a page whose
 * scroller is never handed `scroller` never says a band.
 */
export function useWatchedPage(): WatchedPage {
  const [page] = useState<WatchedPage>(() => {
    const band = followable<Span>();
    let top = 0;
    let height: number | undefined;
    let shown = false;
    const say = () =>
      band.set(shown && height !== undefined ? { from: top, size: height } : undefined);
    const scrolled = ({ nativeEvent }: ScrollEvent) => {
      top = nativeEvent.contentOffset.y;
      // A device reports the scroller's size with every scroll; a laid-out height stands without.
      height = nativeEvent.layoutMeasurement?.height ?? height;
      say();
    };
    return {
      band,
      scroller: {
        onLayout: ({ nativeEvent }) => {
          height = nativeEvent.layout.height;
          say();
        },
        onScroll: scrolled,
        onScrollEndDrag: scrolled,
        onMomentumScrollEnd: scrolled,
        scrollEventThrottle: ON_SCREEN_SAMPLE_MS,
      },
      inView: (yes) => {
        shown = yes;
        say();
      },
    };
  });
  return page;
}

/** A rail as it is drawn now — its cards, their geometry, and who asked to be told. */
export interface RailNow<Card> {
  readonly cards: readonly Card[];
  readonly lead: number;
  readonly cardWidth: number;
  readonly step: number;
  readonly onScreen: ((cards: readonly Card[]) => void) | undefined;
}

/** What a watching rail hands its scroller. */
export interface RailWatch {
  readonly laidOut: (event: LayoutChangeEvent) => void;
  readonly scrolled: (event: ScrollEvent) => void;
}

/**
 * **Which of a rail's cards are on screen, said to its row** — whenever the page moves or comes back
 * into view, the section or the rail is laid out, the rail is scrolled, or the cards change under a
 * still rail (a re-read put somebody new where the finger left it). The page's band and the
 * section's top are followed; the rail's own frame and scroll are kept as the rail reports them —
 * none of it state, since nothing drawn changes with it. Says nothing until all four are known, nor
 * while the page is out of view, nor for a rail no row asked of.
 */
export function useCardsOnScreen<Card>(now: RailNow<Card>): RailWatch {
  const page = useContext(PageOnScreen);
  const section = useContext(SectionOnPage);
  const frame = useRef<LayoutRectangle>();
  const scrolledTo = useRef(0);
  const latest = useRef(now);
  const watching = now.onScreen !== undefined;

  useEffect(() => {
    latest.current = now;
  });

  const tell = useCallback(() => {
    const { cards, lead, cardWidth, step, onScreen } = latest.current;
    const band = page?.get();
    const top = section?.get();
    const rail = frame.current;
    if (onScreen === undefined || band === undefined || top === undefined || rail === undefined) {
      return;
    }
    const uprightShare = shareInside({ from: top + rail.y, size: rail.height }, band);
    const along = { from: scrolledTo.current, size: rail.width };
    const seen = cardsOnScreen({ count: cards.length, lead, cardWidth, step }, along, uprightShare)
      .map((at) => cards[at])
      .filter((card): card is Card => card !== undefined);
    if (seen.length > 0) onScreen(seen);
  }, [page, section]);

  useEffect(() => {
    if (!watching) return undefined;
    const stops = [page?.follow(tell), section?.follow(tell)];
    return () => {
      for (const stop of stops) stop?.();
    };
  }, [watching, page, section, tell]);

  useEffect(() => {
    if (watching) tell();
  }, [watching, tell, now.cards, now.cardWidth]);

  return {
    laidOut: ({ nativeEvent }) => {
      frame.current = nativeEvent.layout;
      tell();
    },
    scrolled: ({ nativeEvent }) => {
      scrolledTo.current = nativeEvent.contentOffset.x;
      tell();
    },
  };
}
