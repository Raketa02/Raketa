/**
 * **The folding line** — FOR YOU's five quiet lines on Home, each a white card that opens to what it
 * holds, one at a time ([#820](https://github.com/Rakieta02/Rakieta/issues/820); ADR-0205 §5, §8,
 * §9.5; home refactor 3–13; design-system 7.37).
 *
 * ```
 * FOR YOU                                            ← FoldingLines: eyebrow · muted · uppercase
 * ┌──────────────────────────────────────────────┐
 * │ Groups heating up                     (6)  › │   ← closed: the title, h2, the count pill (#822)
 * └──────────────────────────────────────────────┘     and the chevron · space.sm between lines
 * ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
 * ┃ Players at your level                (14)  ⌄ ┃   ← open: ink border, shadow.openLine; the
 * ┃ ┌────────────────────────┐ ┌─────────────────┃     count stays · the rail, at the line's inset,
 * ┃ │ a card                 │ │ the next        ┃     bleeding to its inner edge (RailBounds)
 * ┃ └────────────────────────┘ └─────────────────┃
 * ┃                                See all 14  › ┃   ← FoldingLineFooter, bottom right
 * ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
 * ┃ ● Padel ›              Open the rankings  › ┃   ← Top 10's: its switcher at the left (#821)
 * ```
 *
 * ## What opens it, and what closes it
 *
 * **The page says which line is open** — one at a time is the page's rule (`open`), and a press on a
 * line's header is all this reports (`onHeader`). Closed, the line *is* its header, so a tap anywhere
 * on it opens it; open, **only the header closes it**: a tap on a tile, a swipe along the rail, a
 * footer link or Top 10's pill is the content's own, and never reaches the header.
 *
 * ## A closed line draws nothing
 *
 * **Its content is drawn only while it is open**, and for the fold back — so a closed line's tiles
 * are never on screen, never reported as on screen, and cost Home nothing to draw. While it folds
 * away it is hidden from a screen reader, takes no touch, and tells no rail it is on a page.
 *
 * ## It moves, and no size is animated frame by frame
 *
 * Opening is **one** change to the fold's height — nought, then the content's measured height — and a
 * Reanimated layout transition moves the frames there: the fold's, the line's, and **every line
 * below it**, which `FoldingLines` hands the same beat, so they slide rather than jump. Over that beat
 * the content fades in from a `space.md` above its place and the chevron turns down — opacity and
 * transform, nothing else (`RecordDetails`' mechanics, for the reason it gives: under the New
 * Architecture Reanimated 3.16 cannot write a layout prop without React's commit, and skips it while
 * React commits elsewhere). **The content's fade and slide are React Native's `Animated` on the native
 * driver, never a Reanimated style**: a Reanimated style above a rail cost every press the rail had
 * scrolled in, on Android (2026-11-21; `progress` below says how). **Opening is
 * `motion.lineUnfold`, folding the shorter `motion.lineFold`**, and only once it has run is the
 * content let go. **Under Reduce motion nothing moves**: the line is open or shut at once (ADR-0205
 * §8).
 *
 * **As it unfolds, the page shows it** (`PageReveal`): once its content is measured — the start of the
 * unfold, its height known — if its foot would stand below the page's, the page scrolls just far
 * enough, on the same beat. Once per opening, never again while it stays open, and **never for a line
 * opened by nobody's press** (`reveals`): Groups heating up, open from the start for a player in no
 * group, must not scroll Home under a reader who touched nothing.
 *
 * **Its cards are on the page once it has unfolded** — `motion.lineUnfold` after it opens, at once under
 * Reduce motion or for a line drawn open from the start — so a card is never counted as seen while it
 * is still fading in at no height. **A line let go draws its rail anew when it opens again**, at its
 * first card: a closed line draws nothing, so its scroll is not kept (`HomeRow`'s *never remounted*
 * holds while a line stays open).
 *
 * ## Spoken
 *
 * **Each line is a button named by its title and its count** — *Players at your level, 14* — saying
 * whether it is expanded (ADR-0205 §8, [#822](https://github.com/Rakieta02/Rakieta/issues/822)). Each
 * footer link is a button of its own.
 *
 * ## Its count
 *
 * **How many there are to explore**, handed in as the read served it (`count`) and drawn in the count
 * pill between the title and the chevron, open or closed — *99+* past 99 (`countFigure`), and no pill
 * without one (Top 10). A fenced pill (design-system 7.37, Part 16).
 *
 * **It never imports a feature.** The title, the content and the footer are handed in.
 */

import Feather from '@expo/vector-icons/Feather';
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import {
  Animated as Motion,
  Easing as MotionEasing,
  Pressable,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
} from 'react-native';
import Animated, {
  Easing,
  LinearTransition,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from 'react-native-reanimated';

import { countFigure, withCount } from '@/shared/formatting/countFigure';

import { HomeRow, RailBoundsContext, RailDrawsAll, type RailBounds } from './HomeRow';
import { PageOnScreen, PageReveal, SectionOnPage, useTopOnPage, useTopWithin } from './onScreen';
import { useReducedMotion } from './overlay';
import { theme } from './theme';

const EASE = Easing.bezierFn(
  theme.motion.easeDecel.x1,
  theme.motion.easeDecel.y1,
  theme.motion.easeDecel.x2,
  theme.motion.easeDecel.y2,
);

/** The same curve for the content's fade and slide, which run on React Native's `Animated`. */
const SLIDE_EASE = MotionEasing.bezier(
  theme.motion.easeDecel.x1,
  theme.motion.easeDecel.y1,
  theme.motion.easeDecel.x2,
  theme.motion.easeDecel.y2,
);

const UNFOLD = LinearTransition.duration(theme.motion.lineUnfold).easing(EASE);
const FOLD = LinearTransition.duration(theme.motion.lineFold).easing(EASE);

const { pad: PAD, border: BORDER } = theme.size.foldingLine;

/** How far the content travels into place as it opens — `space.md`, the record's fold's slide. */
const SLIDE = theme.space.md;

/** A quarter turn: the chevron points right shut and down open. */
const TURN = 90;

/** 5.1's card bounded by `line`; ADR-0205 §5's open line in `ink`; 6.6's pressed card in `coral`. */
const BORDER_SHUT = theme.color.line;
const BORDER_OPEN = theme.color.ink;
const BORDER_PRESSED = theme.color.coral;

/**
 * **Whether the page's last move folded a line** — what every line in a `FoldingLines` moves its frame
 * by, so the lines below one that folds slide on its beat. Nothing outside one: a line alone moves
 * by its own.
 */
const LinesFolding = createContext<boolean | undefined>(undefined);

export interface FoldingLinesProps {
  /** The section's heading — *For you*, drawn uppercase. */
  readonly heading: string;
  /** Whether the page's last move folded a line rather than unfolding one. */
  readonly folding: boolean;
  readonly testID?: string;
  /** The lines. */
  readonly children: ReactNode;
}

/**
 * **A section of folding lines** — FOR YOU: the row frame's section (`HomeRow`) — `space.lg` under the
 * row above, its eyebrow heading, what it holds `space.sm` apart, where it stands on the page said to
 * the rails inside — holding lines rather than a rail, and handing them the page's beat.
 */
export function FoldingLines({ heading, folding, testID, children }: FoldingLinesProps) {
  return (
    <HomeRow heading={heading} {...(testID === undefined ? {} : { testID })}>
      <LinesFolding.Provider value={folding}>{children}</LinesFolding.Provider>
    </HomeRow>
  );
}

/** **A line as its feature hands it to the page** — what the page draws it with. */
export interface FoldingLineParts {
  readonly title: string;
  /** **How many there are to explore**, as served — its count pill. None on Top 10. */
  readonly count?: number;
  readonly testID: string;
  /** What it unfolds — drawn only while it is open. */
  readonly content: ReactNode;
  /** At the foot of the open content — `FoldingLineFooter`. */
  readonly footer?: ReactNode;
}

export interface FoldingLineProps {
  readonly title: string;
  /**
   * **Its count** — the served total, drawn in the count pill between the title and the chevron, *99+*
   * past 99, and said after the title. No pill without one.
   */
  readonly count?: number;
  /** **Whether it is open** — the page's to say, one line at a time. */
  readonly open: boolean;
  /** **A press on its header**: the whole of a closed line, the title row of an open one. */
  readonly onHeader: () => void;
  /** At the foot of the open content, under what it holds. */
  readonly footer?: ReactNode;
  /**
   * **Whether opening it asks the page to show it** — a line the reader pressed open, the default; not
   * one a page opened by itself.
   */
  readonly reveals?: boolean;
  readonly testID?: string;
  /** What it unfolds — drawn only while it is open, or folding away. */
  readonly children: ReactNode;
}

export function FoldingLine({
  title,
  count,
  open,
  onHeader,
  footer,
  reveals = true,
  testID,
  children,
}: FoldingLineProps) {
  const reduced = useReducedMotion();
  const groupFolding = useContext(LinesFolding);
  const reveal = useContext(PageReveal);
  const page = useContext(PageOnScreen);
  const { width: screen } = useWindowDimensions();
  const transition = reduced ? undefined : (groupFolding ?? !open) ? FOLD : UNFOLD;
  const figure = count === undefined ? undefined : countFigure(count);

  /** Whether the content is drawn — while open, and while it folds away. */
  const [drawn, setDrawn] = useState(open);
  if (open && !drawn) setDrawn(true);
  /** The content's own height, as last measured — nought until it is, and again once let go. */
  const [full, setFull] = useState(0);
  const [header, setHeader] = useState(0);
  // A line drawn open from the start was opened under nobody: nothing to show, and its cards already
  // stand where they will.
  const revealed = useRef(open);
  /** Whether it has unfolded — its cards on the page from then. */
  const [unfolded, setUnfolded] = useState(open);

  // Where the line stands in FOR YOU, and its fold under the line's header: the fold's section is the
  // line, not the one the line stands in.
  const line = useTopOnPage();
  const body = useTopWithin(line.top);

  useEffect(() => {
    if (open || !drawn) return undefined;
    const letGo = () => {
      setDrawn(false);
      setFull(0);
    };
    if (reduced) {
      letGo();
      return undefined;
    }
    const timer = setTimeout(letGo, theme.motion.lineFold);
    return () => clearTimeout(timer);
  }, [open, drawn, reduced]);

  /**
   * **The content's fade and slide** — on the commit that draws it, on React Native's own `Animated`
   * and its native driver, **never a Reanimated style** (2026-11-21). The content stands above the
   * rail, and on Android (React Native 0.76.9, Reanimated 3.16.7) a Reanimated style fading a view
   * above a horizontal scroll view — opacity alone will do, and taking it off after the unfold undoes
   * nothing — leaves that scroll view's offset out of what `measure` reads: a card measured where it
   * stood before the rail scrolled (the line's border colour, a Reanimated style above it too, measured
   * harmless). A press tests each move of the finger against that measure, and a real
   * thumb reports moves while it rests, so every tile, face and button the rail had scrolled in took
   * the press and dropped it. The same fade and slide on the native driver leave the measure true.
   */
  const progress = useRef(new Motion.Value(open ? 1 : 0)).current;
  /** The header's answer — where it is headed (the ink border) and its chevron's turn there. */
  const aimed = useSharedValue(open ? 1 : 0);
  const lit = useSharedValue(open ? 1 : 0);
  /** Whether a finger is on the header — its border coral, with no render for it. */
  const pressing = useSharedValue(0);
  useEffect(() => {
    const to = open ? 1 : 0;
    const duration = open ? theme.motion.lineUnfold : theme.motion.lineFold;
    // Already on its way there when the press said so; this is the page's word, and the same.
    if (aimed.value !== to) {
      aimed.value = to;
      lit.value = reduced ? to : withTiming(to, { duration, easing: EASE });
    }
    if (reduced) {
      progress.setValue(to);
      return undefined;
    }
    const motion = Motion.timing(progress, {
      toValue: to,
      duration,
      easing: SLIDE_EASE,
      useNativeDriver: true,
    });
    motion.start();
    return () => motion.stop();
  }, [open, reduced, progress, aimed, lit]);

  /**
   * **The header answers the press at once**, on the UI thread, before the page has drawn anything:
   * the chevron turns and the border goes ink, or back. A press always heads where the header can
   * tell — the open line closes, and any other opens, at once or once the open one has folded — and
   * the page's `open` then lands on the same. Until 2026-11-21 nothing moved until the commit that
   * draws the content, which on a Galaxy A32 came 350 ms after the finger.
   */
  const answerPress = () => {
    const to = open ? 0 : 1;
    aimed.value = to;
    lit.value = reduced
      ? to
      : withTiming(to, {
          duration: open ? theme.motion.lineFold : theme.motion.lineUnfold,
          easing: EASE,
        });
  };

  useEffect(() => {
    if (!open) {
      setUnfolded(false);
      return undefined;
    }
    if (reduced) {
      setUnfolded(true);
      return undefined;
    }
    const timer = setTimeout(() => setUnfolded(true), theme.motion.lineUnfold);
    return () => clearTimeout(timer);
  }, [open, reduced]);

  // As it unfolds, the page shows it — once per opening, and only a line pressed open.
  const showOnPage = useCallback(
    (content: number) => {
      if (!open || revealed.current || !reveals || content === 0 || reveal === undefined) return;
      const top = line.top.get();
      if (top === undefined) return;
      revealed.current = true;
      reveal({ from: top, size: 2 * BORDER + header + content });
    },
    [open, reveals, reveal, line.top, header],
  );
  useEffect(() => {
    if (!open) revealed.current = false;
  }, [open]);
  // The content's layout asks first (below), on the beat the unfold starts; this is for a measure
  // already in hand when the line opens again.
  useEffect(() => showOnPage(full), [showOnPage, full]);

  // Opacity and transform only: a layout prop cannot ride the native driver, and here would move the
  // rail under the finger frame by frame.
  const slide = useMemo(
    () => ({
      opacity: progress,
      transform: [
        { translateY: progress.interpolate({ inputRange: [0, 1], outputRange: [-SLIDE, 0] }) },
      ],
    }),
    [progress],
  );
  const turn = useAnimatedStyle(() => ({
    transform: [{ rotate: `${TURN * lit.value}deg` }],
  }));
  // A colour, not a size: drawn on the UI thread with no commit, so a finger on the header costs
  // the page no render — a render here once held every press back by a whole commit.
  const frame = useAnimatedStyle(() => ({
    borderColor:
      pressing.value === 1 ? BORDER_PRESSED : aimed.value === 1 ? BORDER_OPEN : BORDER_SHUT,
  }));

  const bounds = useMemo<RailBounds>(
    () => ({
      content: screen - 2 * theme.size.gutter - 2 * (BORDER + PAD),
      bleed: PAD,
      snaps: true,
      // The line's card, a little wider than the page's (2026-11-26).
      cardRatio: theme.size.lineCardRatio,
    }),
    [screen],
  );

  return (
    <Animated.View
      layout={transition}
      onLayout={({ nativeEvent }) => line.laidOut(nativeEvent.layout.y)}
      // No hole in the array: Reanimated's test reading walks every entry.
      style={open ? [s.line, s.open, frame] : [s.line, frame]}
      {...(testID === undefined ? {} : { testID })}
    >
      <View style={s.clip}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={withCount(title, count)}
          accessibilityState={{ expanded: open }}
          onPress={() => {
            answerPress();
            onHeader();
          }}
          onPressIn={() => {
            pressing.value = 1;
          }}
          onPressOut={() => {
            pressing.value = 0;
          }}
          onLayout={({ nativeEvent }) => setHeader(nativeEvent.layout.height)}
          style={s.header}
        >
          <Text style={s.title} numberOfLines={1}>
            {title}
          </Text>
          {figure === undefined ? null : <CountPill figure={figure} line={testID} />}
          <Animated.View
            testID={testID === undefined ? undefined : `${testID}-chevron`}
            style={turn}
            accessibilityElementsHidden
            importantForAccessibility="no-hide-descendants"
          >
            <Feather name="chevron-right" size={theme.size.tabIcon} color={theme.color.muted} />
          </Animated.View>
        </Pressable>

        {drawn ? (
          <Animated.View
            testID={testID === undefined ? undefined : `${testID}-fold`}
            layout={transition}
            // In the clip, which stands inside the line's border: the fold is that much further down.
            onLayout={({ nativeEvent }) => body.laidOut(BORDER + nativeEvent.layout.y)}
            style={[s.fold, { height: open ? full : 0 }]}
            pointerEvents={open ? 'auto' : 'none'}
            accessibilityElementsHidden={!open}
            importantForAccessibility={open ? 'auto' : 'no-hide-descendants'}
          >
            <Motion.View
              testID={testID === undefined ? undefined : `${testID}-content`}
              style={[s.content, footer === undefined ? s.contentAlone : undefined, slide]}
              onLayout={({ nativeEvent }) => {
                const measured = nativeEvent.layout.height;
                // A sub-point difference is rounding, not a new height: no second move for it.
                setFull((was) => (Math.abs(was - measured) < 0.5 ? was : measured));
                // The page shows it now, with the unfold, rather than a render later: that render
                // queued behind the rest of the opening and scrolled the page half a second after the
                // line had opened (2026-11-21).
                showOnPage(measured);
              }}
            >
              <SectionOnPage.Provider value={body.top}>
                {/* On the page once unfolded; folding away, on none: a closed line reports nobody. */}
                <PageOnScreen.Provider value={open && unfolded ? page : undefined}>
                  <RailBoundsContext.Provider value={bounds}>
                    {/* The cards nobody can see yet, once the motion has run — not during it. */}
                    <RailDrawsAll.Provider value={unfolded}>
                      {children}
                      {footer}
                    </RailDrawsAll.Provider>
                  </RailBoundsContext.Provider>
                </PageOnScreen.Provider>
              </SectionOnPage.Provider>
            </Motion.View>
          </Animated.View>
        ) : null}
      </View>
    </Animated.View>
  );
}

/**
 * **The count pill** (#822; 7.37; home refactor 3, 4, 7) — how many there are to explore, between the
 * title and the chevron, open or closed. A grey lozenge: `line2`, the fold inside one thing, under
 * the figure in `muted` mono at 4,62 — quieter than the title it follows, since it says how much
 * there is, not that anything needs doing. **A fenced pill** (Part 16): the chip's shape, and no
 * chip — it is not pressed, and the line it stands in is the button. Hidden from a listener: its
 * figure is in the line's name.
 */
function CountPill({ figure, line }: { readonly figure: string; readonly line?: string }) {
  return (
    <View
      testID={line === undefined ? undefined : `${line}-count`}
      style={s.count}
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <Text style={s.countFigure} numberOfLines={1}>
        {figure}
      </Text>
    </View>
  );
}

/** A footer's link — *See all ›*, *Rankings ›* — in the line's words. */
export interface FoldingLineLink {
  /** Drawn, before the frame's chevron — *See all*. */
  readonly words: string;
  /** Spoken — what it opens: *See all players at your level*. */
  readonly label: string;
  readonly onPress: () => void;
}

export interface FoldingLineFooterProps {
  /** **A control at the left end** — Top 10's sport switcher (#821). */
  readonly control?: ReactNode;
  /** **The link at the right end** — *See all ›*. */
  readonly link?: FoldingLineLink;
  /** **A layer over the whole footer**, drawn last — Top 10's open sport bar and its backdrop. */
  readonly over?: ReactNode;
}

/**
 * **The footer row** — at the foot of an open line: an optional control at the left end and the link
 * at the right, each its own button, in a row `minTouch` tall so the link's target is 44 high. The
 * link takes the room before it, so it ends the row with a control or without one (#821: Top 10's
 * switcher at the left, *Open the rankings ›* at the right; home refactor 12, 13). The section is the
 * box of what lies over it, its top-left the row's, which is where Top 10's bar stands on its pill.
 */
export function FoldingLineFooter({ control, link, over }: FoldingLineFooterProps) {
  return (
    <View testID="folding-line-footer" style={s.footer}>
      {control}
      {link === undefined ? null : <LineLink link={link} />}
      {over}
    </View>
  );
}

/**
 * The words drawn with a chevron after them, a direction rather than a word and hidden; the name is
 * what is spoken, and names what it opens, since three *See all*s on one screen would otherwise be
 * one name for three places. A **link** to a screen reader: it opens another screen. Ink `rlValue`,
 * as the row frame's link was, now a whole 44 tall.
 */
function LineLink({ link }: { readonly link: FoldingLineLink }) {
  return (
    <Pressable
      accessibilityRole="link"
      accessibilityLabel={link.label}
      onPress={link.onPress}
      style={({ pressed }) => [s.link, pressed ? s.linkPressed : undefined]}
    >
      <Text style={s.linkWords}>{link.words}</Text>
      <Text style={s.linkWords} accessibilityElementsHidden importantForAccessibility="no">
        {CHEVRON}
      </Text>
    </Pressable>
  );
}

/** The link's chevron — `SportPill`'s fold mark, pointing to where it goes. */
const CHEVRON = '›';

const s = StyleSheet.create({
  // 5.1's card: white on paper, `line` bounding it, `radius.card`. The shadow and the clip are on two
  // views, since iOS draws no shadow outside a view that clips.
  line: {
    backgroundColor: theme.color.surface,
    borderColor: theme.color.line,
    borderWidth: BORDER,
    borderRadius: theme.radius.card,
  },
  // ADR-0205 §5: the open line has an ink border and a soft shadow (4.3's seventh). The border is
  // also the `frame` style's, which draws it — and 6.6's coral while pressed — from the press itself.
  open: { borderColor: theme.color.ink, ...theme.shadow.openLine },
  clip: { borderRadius: theme.radius.card - BORDER, overflow: 'hidden' },
  // The h2 line and space.md above and below it: minTouch exactly.
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.sm,
    minHeight: theme.size.minTouch,
    paddingHorizontal: PAD,
    paddingVertical: theme.space.md,
  },
  // 3.3: h2 titles a card.
  title: { ...theme.type.h2, color: theme.color.ink, flex: 1 },
  // 7.37's count pill: the figure's own line box, `space.xs` each side of it — a lozenge. A least
  // height rather than a fixed one: the header grows with the OS text size, and the pill grows with
  // its figure rather than clipping it.
  count: {
    minHeight: theme.size.foldingLine.count,
    paddingHorizontal: theme.space.xs,
    borderRadius: theme.radius.pill,
    backgroundColor: theme.color.line2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  // 1.4: mono and tabular, so 9 → 10 does not reflow the header.
  countFigure: { ...theme.num.tiny, ...theme.tabular, color: theme.color.muted },
  fold: { overflow: 'hidden' },
  // Laid out at its whole height whatever the fold's is, so the measure is the content's own.
  content: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    paddingHorizontal: PAD,
    paddingBottom: theme.space.xs,
    gap: theme.space.sm,
  },
  // With no footer, the card's inset under the rail too, as over it.
  contentAlone: { paddingBottom: PAD },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
    gap: theme.space.sm,
    minHeight: theme.size.minTouch,
  },
  // The room before it is the link's, so it ends the row whatever stands at the left.
  link: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.xxs,
    minHeight: theme.size.minTouch,
    marginLeft: 'auto',
  },
  // 6.6's chip value, as the sign-in screen's link presses.
  linkPressed: { opacity: 0.7 },
  linkWords: { ...theme.type.rlValue, color: theme.color.ink },
});
