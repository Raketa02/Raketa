/**
 * **The folding line** — FOR YOU's five quiet lines on Home, each a white card that opens to what it
 * holds, one at a time ([#820](https://github.com/Raketa02/Raketa/issues/820); ADR-0205 §5, §8,
 * §9.5; home refactor 3–13; design-system 7.37).
 *
 * ```
 * FOR YOU                                            ← FoldingLines: eyebrow · muted · uppercase
 * ┌──────────────────────────────────────────────┐
 * │ Groups heating up                          › │   ← closed: the title, h2, and the chevron
 * └──────────────────────────────────────────────┘   ← space.sm between lines
 * ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
 * ┃ Players at your level                      ⌄ ┃   ← open: ink border, shadow.openLine
 * ┃ ┌────────────────────────┐ ┌─────────────────┃   ← the rail, at the line's inset, bleeding to
 * ┃ │ a card                 │ │ the next        ┃     its inner edge (RailBounds)
 * ┃ └────────────────────────┘ └─────────────────┃
 * ┃                                   See all  › ┃   ← FoldingLineFooter, bottom right
 * ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
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
 * one shared value fades the content in from a `space.md` above its place and turns the chevron
 * down — opacity and transform, nothing else (`RecordDetails`' mechanics, for the reason it gives:
 * under the New Architecture Reanimated 3.16 cannot write a layout prop without React's commit, and
 * skips it while React commits elsewhere). **Opening is `motion.lineUnfold`, folding the shorter
 * `motion.lineFold`**, and only once it has run is the content let go. **Under Reduce motion nothing
 * moves**: the line is open or shut at once (ADR-0205 §8).
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
 * **Each line is a button named by its title**, saying whether it is expanded (ADR-0205 §8; its count
 * joins the name with #822). Each footer link is a button of its own.
 *
 * **It never imports a feature.** The title, the content and the footer are handed in.
 */

import Feather from '@expo/vector-icons/Feather';
import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { Pressable, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import Animated, {
  Easing,
  interpolate,
  LinearTransition,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from 'react-native-reanimated';

import { HomeRow, RailBoundsContext, type RailBounds } from './HomeRow';
import { PageOnScreen, PageReveal, SectionOnPage, useTopOnPage, useTopWithin } from './onScreen';
import { useReducedMotion } from './overlay';
import { theme } from './theme';

const EASE = Easing.bezierFn(
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
  readonly testID: string;
  /** What it unfolds — drawn only while it is open. */
  readonly content: ReactNode;
  /** At the foot of the open content — `FoldingLineFooter`. */
  readonly footer?: ReactNode;
}

export interface FoldingLineProps {
  readonly title: string;
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

  /** Whether the content is drawn — while open, and while it folds away. */
  const [drawn, setDrawn] = useState(open);
  if (open && !drawn) setDrawn(true);
  /** The content's own height, as last measured — nought until it is, and again once let go. */
  const [full, setFull] = useState(0);
  const [header, setHeader] = useState(0);
  const [pressed, setPressed] = useState(false);
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

  const progress = useSharedValue(open ? 1 : 0);
  useEffect(() => {
    const to = open ? 1 : 0;
    progress.value = reduced
      ? to
      : withTiming(to, {
          duration: open ? theme.motion.lineUnfold : theme.motion.lineFold,
          easing: EASE,
        });
  }, [open, reduced, progress]);

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
  useEffect(() => {
    if (!open) {
      revealed.current = false;
      return;
    }
    if (revealed.current || !reveals || full === 0 || reveal === undefined) return;
    const top = line.top.get();
    if (top === undefined) return;
    revealed.current = true;
    reveal({ from: top, size: 2 * BORDER + header + full });
  }, [open, reveals, full, header, reveal, line.top]);

  // Opacity and transform only: a layout prop here would send every frame through the commit React
  // pauses (the module note).
  const slide = useAnimatedStyle(() => ({
    opacity: progress.value,
    transform: [{ translateY: interpolate(progress.value, [0, 1], [-SLIDE, 0]) }],
  }));
  const turn = useAnimatedStyle(() => ({
    transform: [{ rotate: `${TURN * progress.value}deg` }],
  }));

  const bounds = useMemo<RailBounds>(
    () => ({
      content: screen - 2 * theme.size.gutter - 2 * (BORDER + PAD),
      bleed: PAD,
      snaps: true,
    }),
    [screen],
  );

  return (
    <Animated.View
      layout={transition}
      onLayout={({ nativeEvent }) => line.laidOut(nativeEvent.layout.y)}
      style={[s.line, open ? s.open : undefined, pressed ? s.pressed : undefined]}
      {...(testID === undefined ? {} : { testID })}
    >
      <View style={s.clip}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={title}
          accessibilityState={{ expanded: open }}
          onPress={onHeader}
          onPressIn={() => setPressed(true)}
          onPressOut={() => setPressed(false)}
          onLayout={({ nativeEvent }) => setHeader(nativeEvent.layout.height)}
          style={s.header}
        >
          <Text style={s.title} numberOfLines={1}>
            {title}
          </Text>
          <Animated.View
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
            <Animated.View
              testID={testID === undefined ? undefined : `${testID}-content`}
              style={[s.content, footer === undefined ? s.contentAlone : undefined, slide]}
              onLayout={({ nativeEvent }) => {
                const measured = nativeEvent.layout.height;
                // A sub-point difference is rounding, not a new height: no second move for it.
                setFull((was) => (Math.abs(was - measured) < 0.5 ? was : measured));
              }}
            >
              <SectionOnPage.Provider value={body.top}>
                {/* On the page once unfolded; folding away, on none: a closed line reports nobody. */}
                <PageOnScreen.Provider value={open && unfolded ? page : undefined}>
                  <RailBoundsContext.Provider value={bounds}>
                    {children}
                    {footer}
                  </RailBoundsContext.Provider>
                </PageOnScreen.Provider>
              </SectionOnPage.Provider>
            </Animated.View>
          </Animated.View>
        ) : null}
      </View>
    </Animated.View>
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
  /** **A control before the link** — Top 10's sport pill. */
  readonly control?: ReactNode;
  /** **The link at the right end** — *See all ›*. */
  readonly link?: FoldingLineLink;
  /** **A layer over the whole footer**, drawn last — Top 10's open sport bar and its backdrop. */
  readonly over?: ReactNode;
}

/**
 * **The footer row** — at the foot of an open line, on the right: an optional control, then the link,
 * each its own button, in a row `minTouch` tall so the link's target is 44 high. The section is the
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
  // ADR-0205 §5: the open line has an ink border and a soft shadow (4.3's seventh).
  open: { borderColor: theme.color.ink, ...theme.shadow.openLine },
  // 6.6: a card pressed is its border in coral.
  pressed: { borderColor: theme.color.coral },
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
  link: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.space.xxs,
    minHeight: theme.size.minTouch,
  },
  // 6.6's chip value, as the sign-in screen's link presses.
  linkPressed: { opacity: 0.7 },
  linkWords: { ...theme.type.rlValue, color: theme.color.ink },
});
