/**
 * **A game card** — one proposal as the reader is dealt it: their own version of the game (the
 * screens A2.3; mocks 2–8, 10; [#553](https://github.com/Raketa02/Raketa/issues/553)).
 *
 * ```
 * ┌───────────────────────────────────────────┐
 * │ Picked for you                  ⏱ 21 h 00 │  the ribbon — dark teal, or coral on a rescue
 * ├───────────────────────────────────────────┤
 * │ [ tile ] [ tile ]                         │  GameTiles — the sides as rows (Q70)
 * │ ── KAROL + ZOFIA  VS  ANIA + YOU ──       │
 * │ [ tile ] [ tile ]                         │
 * │ 4 people are In on this game              │  only when dealt in versions
 * │ 87%  [ You + Zofia │ Ania + Ewa ]         │  the forecast: the server's figure, your side left
 * │ 67%  [ Social vibe ██████████░░░░ ]       │  — or, on For fun, its Social vibe (`headlineOf`)
 * │            Slim overlap                   │  OverlapGrid
 * │  M  T  W  T  F  S  S …                    │
 * │ ┌ Court available            32 zł ┐     │  CourtBlock
 * │ └ Saturday 16:00 · Bonarka Arena   ┘     │
 * └───────────────────────────────────────────┘
 * ```
 *
 * ## The fourth dark surface, on a ground of its own
 *
 * The mocks draw the card as a gradient from `gameGroundTop` under the ribbon to `gameGroundFoot`
 * at its foot — the night's family, measured, and fenced in the theme as this card's alone (Part 16
 * 2026-09-30). `GameGround` draws it, one gradient in the card's own box, as the Players card draws
 * its wash, so its stops are shares of whatever height the stage gives it.
 *
 * ## Its tiles have one shape, and the height they leave is shared
 *
 * The card fills its stage — the three stacked cards are one size — and its tiles no longer take
 * whatever height is left (#864). **`deckCardGeometry` decides**: a tile 1.75 : 1 on doubles and
 * 3:4 on singles, as wide as its column or, where the card's height runs out, as tall as the room
 * allows at that shape; the height left over goes in equal shares to the gaps between the blocks.
 * It decides from **what the card measures**, never from what a block is assumed to be: the stage
 * (this card's own box, which is the stage's), and the ribbon, the *vs* line, the forecast or vibe
 * row, the grid's words, the court block and the versions line, each as laid out at the phone's text
 * size and wrap (`useCardRoom`).
 *
 * **Where the room is short, every box shrinks in proportion and no word does** (#865): the tiles,
 * the body's padding above and below, the gaps and the grid's cells, at the geometry's `scale`, down
 * to the floor — the narrowest tile, which its foot's capped words fill. **Where even that does not
 * fit, the card tells the deck how short it can get** (`onLeast`), and the deck lays its stage out
 * at that and scrolls.
 *
 * **A card is drawn unseen until it has measured itself once.** Its blocks have to be laid out to be
 * measured, so it cannot draw nothing, as the sign-in hero does (`useMeasuredRoom`); a card drawn
 * at the wrong size first would jump a frame later — the court block sliding down 29pt on a tall
 * phone. Until then, and always under Jest, which lays nothing out, its tiles are their column's
 * width at their shape and its gaps at rest, so every part of it is there to find and press. Once
 * measured it is never unseen again: a block that appears later keeps the last size until it
 * answers. **On a deck it also waits for a stage that holds it** (#865): a card at its floor in a
 * stage shorter than its least would show cut off at the foot for the frames the deck takes to lay
 * the stage out at it, then grow — so it stays unseen until then.
 *
 * ## A door to the game, and doors to the people on it
 *
 * A press anywhere on the card opens the game's details, and a press on a tile opens that player's
 * record (the screens A2.2). **The card is not one element to a listener**, as the Players card is:
 * its tiles are buttons of their own, and an element that swallowed them would take the records
 * out of a screen reader's reach. So the card's parts speak for themselves — the ribbon, each
 * tile, the forecast or the Social vibe, the grid, the court block — and the details are reached
 * by the **i** under the stage, which is the accessible path the drag never is (ADR-0169 §3's
 * rule, kept).
 *
 * ## Each kind leads with its own number
 *
 * Below the vs line a competitive card draws its forecast and a For-fun card its Social vibe
 * (ADR-0207 §5, #838) — `headlineOf` decides, and a For-fun card draws no forecast even if one is
 * sent. The row is `shared/ui`'s `SocialVibeRow`, in the forecast row's place and height, so the
 * rest of the card is the card it was. The forecast's name says the sides and the row's does not,
 * so where no forecast is drawn the vs line is spoken instead (`speaksSides`).
 *
 * ## The countdown runs from the read
 *
 * Under 24 hours the ribbon counts down to the deadline (`countdownOf`), from the instant the deck
 * was read and on with the deck's clock (`useDeckClock`); under an hour it is `gameCoral`, coral
 * lifted to carry words on the ribbon. At the deadline the card leaves silently — `standingCards`,
 * before it is ever drawn.
 *
 * ## What a card behind the top one is
 *
 * The same drawing with no doors: no press, no tile buttons, hidden from a listener by the stage.
 * One component for both, so the card coming forward is the element it already was.
 */

import Feather from '@expo/vector-icons/Feather';
import { useEffect, useMemo, useRef, useState } from 'react';
import {
  PixelRatio,
  Pressable,
  StyleSheet,
  Text,
  View,
  type LayoutChangeEvent,
} from 'react-native';

import { formatPercent } from '@/shared/formatting/ratingFormat';
import { BALANCE_FIGURE, BalanceBar, SocialVibeRow, theme } from '@/shared/ui';
import { balanceTone } from '@/shared/vocabulary/balancePresentation';
import type { Weekday } from '@/shared/vocabulary/week';

import {
  completesIt,
  countdownOf,
  courtTagOf,
  foldOf,
  headlineOf,
  inAcrossVersions,
  ribbonOf,
  rowsOf,
  type DeckCard,
  type DeckPerson,
} from '../domain/deck';
import { isRescue } from '../domain/fill';
import type { GameDay } from '../domain/when';

import { CourtBlock } from './CourtBlock';
import {
  BASE,
  blocksLaidOut,
  cardGeometry,
  sameLength,
  tileRatio,
  type CardGeometry,
  type CourtShape,
  type MeasuredBlock,
  type Size,
} from './deckCardGeometry';
import {
  barLabels,
  countdownSpoken,
  countdownWords,
  forecastSpoken,
  inOnGameLine,
  ribbonWords,
  shareWords,
} from './deckPresentation';
import { GameGround } from './GameGround';
import { GameTiles } from './GameTiles';
import { OverlapGrid } from './OverlapGrid';

export interface GameCardProps {
  readonly card: DeckCard;
  /** How many stand on a side in the card's sport — the court's, handed in. */
  readonly seatsPerSide: number;
  /** The deck's clock — the read's instant, moving on while a card counts down (`useDeckClock`). */
  readonly at: number;
  /** The game's day as the court block names it, against the same read. */
  readonly day: GameDay | undefined;
  /** The weekday the deck was read on — the grid's white letter. */
  readonly today: Weekday | undefined;
  /** The card is the top one: a press opens the game, a tile its player. Absent behind. */
  readonly onOpen?: () => void;
  readonly onPerson?: (person: DeckPerson) => void;
  /**
   * The least height this card is drawn at, once it has measured itself and whenever that changes,
   * and `undefined` once it no longer stands — the deck lays its stage out at no less, and scrolls
   * where that is more than the page leaves (#865, `deckCardGeometry`). Given, the card stays unseen
   * until its stage holds it (see the module note).
   */
  readonly onLeast?: (proposalId: string, least: number | undefined) => void;
}

/** The card's boxes at rest — what it draws before it has measured itself. */
const AT_REST = {
  scale: 1,
  padX: BASE.pad,
  padY: BASE.pad,
  underTiles: BASE.underTiles,
  aroundHair: BASE.aroundHair,
  between: BASE.between,
} as const;

export function GameCard({
  card,
  seatsPerSide,
  at,
  day,
  today,
  onOpen,
  onPerson,
  onLeast,
}: GameCardProps) {
  const { top, bottom } = rowsOf(card, seatsPerSide);
  const ribbon = ribbonOf(card);
  const countdown = countdownOf(card.deadline, at);
  const counting = countdownWords(countdown);
  const urgent = countdown.kind === 'minutes' && ribbon.kind !== 'seatOpen';
  const labels = barLabels([top, bottom]);
  const acrossVersions = inAcrossVersions(card);
  const headline = headlineOf(card);
  const shape: CourtShape = seatsPerSide === 1 ? 'singles' : 'doubles';
  const { geometry, laidOut, seen } = useCardRoom(
    shape,
    { versions: acrossVersions !== undefined, headline: headline !== undefined },
    onLeast !== undefined,
  );
  // At rest until the card has been laid out — see the module note.
  const gaps = geometry ?? AT_REST;

  // How short this card can get — the deck's to lay its stage out at (see the module note).
  const least = geometry?.least;
  const { proposalId } = card;
  useEffect(() => {
    if (least === undefined || onLeast === undefined) return undefined;
    onLeast(proposalId, least);
    return () => onLeast(proposalId, undefined);
  }, [least, proposalId, onLeast]);

  const drawing = (
    <>
      <GameGround />

      <View
        style={[s.ribbon, ribbon.kind === 'seatOpen' ? s.ribbonRescue : s.ribbonGame]}
        onLayout={laidOut.ribbon}
        accessible
        accessibilityRole="header"
        accessibilityLabel={[ribbonWords(ribbon), countdownSpoken(countdown)]
          .filter((part) => part !== undefined)
          .join(', ')}
      >
        <Text style={s.ribbonWords} numberOfLines={1}>
          {ribbonWords(ribbon)}
        </Text>
        {counting === undefined ? null : (
          <View style={s.countdown} testID="game-countdown">
            <Feather
              name="clock"
              size={theme.size.infoGlyph}
              color={urgent ? theme.color.gameCoral : theme.color.surface}
            />
            <Text style={[s.countdownWords, urgent ? s.urgent : undefined]}>{counting}</Text>
          </View>
        )}
      </View>

      {/* Every gap is the geometry's, so the body sets them one by one rather than as one `gap`. */}
      <View
        style={[s.body, { paddingHorizontal: gaps.padX, paddingVertical: gaps.padY }]}
        testID="game-card-body"
      >
        <GameTiles
          top={top}
          bottom={bottom}
          singles={shape === 'singles'}
          completes={completesIt(card)}
          ratio={tileRatio(shape)}
          onVsLaidOut={laidOut.vs}
          speaksSides={headline?.kind !== 'forecast'}
          {...(geometry === undefined ? {} : { geometry: geometry.tiles })}
          {...(isRescue(card) ? { rescue: { share: shareWords(card) } } : {})}
          {...(onPerson === undefined ? {} : { onPerson })}
        />

        {acrossVersions === undefined ? null : (
          <Text style={[s.versions, { marginTop: gaps.underTiles }]} onLayout={laidOut.versions}>
            {inOnGameLine(acrossVersions)}
          </Text>
        )}

        <View style={[s.hair, { marginVertical: gaps.aroundHair }]} />

        {headline === undefined ? null : (
          <View style={{ marginBottom: gaps.between }} onLayout={laidOut.headline}>
            {headline.kind === 'vibe' ? (
              <SocialVibeRow pct={headline.pct} />
            ) : (
              <Forecast pct={headline.pct} fold={foldOf(card) ?? 0} labels={labels} />
            )}
          </View>
        )}

        <View style={{ marginBottom: gaps.between }}>
          <OverlapGrid
            overlap={card.overlap}
            today={today}
            scale={gaps.scale}
            onWordsLaidOut={laidOut.gridWords}
          />
        </View>

        <View onLayout={laidOut.court}>
          <CourtBlock tag={courtTagOf(card)} day={day} card={card} />
        </View>
      </View>
    </>
  );

  return (
    <View style={s.card} onLayout={laidOut.stage}>
      {/* Not one element — see the module note. A press here opens the game; a tile's own press
          reaches the tile first. Behind the top card it is inert: no press, nothing to find. */}
      <Pressable
        // Unseen until it has measured itself — see the module note.
        style={[s.clip, seen ? undefined : s.unmeasured]}
        accessible={false}
        disabled={onOpen === undefined}
        {...(onOpen === undefined ? {} : { onPress: onOpen })}
        testID={`game-card-${card.proposalId}`}
      >
        {drawing}
      </Pressable>
    </View>
  );
}

/**
 * *87%* and the bar, your side on the left (Q70). The figure is the server's and the fold is the
 * Levels' (`foldOf`); the bar is one element named by the word and the figure, the sides with it.
 */
function Forecast({
  pct,
  fold,
  labels,
}: {
  readonly pct: number;
  readonly fold: number;
  readonly labels: readonly [string, string];
}) {
  const tone = balanceTone(pct);
  return (
    <View
      style={s.forecast}
      accessible
      accessibilityRole="image"
      accessibilityLabel={forecastSpoken(pct, labels)}
      testID="game-forecast"
    >
      <Text style={[s.figure, { color: BALANCE_FIGURE[tone] }]}>{formatPercent(pct)}</Text>
      {/* Hidden: the row is the one element, and it already says the word, the figure and the
          sides — the bar's own name would be the second reading of one fact. */}
      <View
        style={s.bar}
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
      >
        <BalanceBar
          advantage={fold}
          tone={tone}
          size="md"
          variant="onDark"
          labels={labels}
          accessibilityLabel={forecastSpoken(pct, labels)}
        />
      </View>
    </View>
  );
}

type OnLayout = (event: LayoutChangeEvent) => void;

/** As laid out: the card's own box, which is its stage's, and each measured block's height. */
interface Laid {
  readonly stage?: Size;
  readonly heights: Readonly<Partial<Record<MeasuredBlock, number>>>;
}

/**
 * **The card's room, as it was laid out**, and the geometry it gives once every block the card draws
 * has answered (see the module note).
 *
 * - **A layout within a pixel of the last is the same layout** (`sameLength`): the gaps moving a
 *   block onto another fraction of a pixel must not move the gaps again.
 * - **A block that has just appeared keeps the card at its last size until it answers** — a
 *   forecast arriving on a live card, the versions line on a second version — rather than dropping
 *   it back to the size it stood at before it had measured itself, which would jump it twice.
 * - **It is seen once it has a geometry** — and, where the stage will be laid out at its least
 *   (`waitsForStage`), a stage within a pixel and a half of it — and never unseen again.
 */
function useCardRoom(
  shape: CourtShape,
  drawn: { readonly versions: boolean; readonly headline: boolean },
  waitsForStage: boolean,
): {
  readonly geometry: CardGeometry | undefined;
  readonly laidOut: Readonly<Record<MeasuredBlock | 'stage', OnLayout>>;
  readonly seen: boolean;
} {
  const [laid, setLaid] = useState<Laid>({ heights: {} });

  // One handler a part for the card's life: `setLaid` never changes, nor does the phone's pixel.
  const laidOut = useMemo(() => {
    const pixel = 1 / PixelRatio.get();
    const heightOf =
      (part: MeasuredBlock): OnLayout =>
      ({ nativeEvent }) => {
        const height = nativeEvent.layout.height;
        setLaid((was) =>
          sameLength(was.heights[part], height, pixel)
            ? was
            : { ...was, heights: { ...was.heights, [part]: height } },
        );
      };
    return {
      stage: ({ nativeEvent }: LayoutChangeEvent) => {
        const { width, height } = nativeEvent.layout;
        setLaid((was) =>
          sameLength(was.stage?.width, width, pixel) && sameLength(was.stage?.height, height, pixel)
            ? was
            : { ...was, stage: { width, height } },
        );
      },
      ribbon: heightOf('ribbon'),
      vs: heightOf('vs'),
      versions: heightOf('versions'),
      headline: heightOf('headline'),
      gridWords: heightOf('gridWords'),
      court: heightOf('court'),
    };
  }, []);

  const { versions, headline } = drawn;
  const fresh = useMemo(() => {
    const blocks = blocksLaidOut(
      laid.heights,
      { shape, versions, headline },
      StyleSheet.hairlineWidth,
    );
    return laid.stage === undefined || blocks === undefined
      ? undefined
      : cardGeometry({ stage: laid.stage, shape, blocks });
  }, [laid, shape, versions, headline]);

  // The last geometry the card had, while a block that has just appeared is measured. Written in
  // render, and only ever with this render's own answer, so a render thrown away leaves it true.
  const kept = useRef<CardGeometry | undefined>(undefined);
  if (fresh !== undefined) kept.current = fresh;

  // Seen from the first geometry whose stage holds it, and for good — written in render as `kept` is.
  const seenOnce = useRef(false);
  const short =
    waitsForStage &&
    fresh !== undefined &&
    laid.stage !== undefined &&
    laid.stage.height + 1.5 / PixelRatio.get() < fresh.least;
  if (fresh !== undefined && !short) seenOnce.current = true;

  return { geometry: fresh ?? kept.current, laidOut, seen: seenOnce.current };
}

const s = StyleSheet.create({
  card: { flex: 1, borderRadius: theme.radius.deckCard, ...theme.shadow.deckCard },
  clip: { flex: 1, borderRadius: theme.radius.deckCard, overflow: 'hidden' },
  // The ground is inside the clip, so the card's shadow, which needs it, goes too.
  unmeasured: { opacity: 0 },
  ribbon: {
    height: theme.size.gameCard.ribbon,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: theme.space.lg,
    gap: theme.space.sm,
  },
  ribbonGame: { backgroundColor: theme.color.gameRibbon },
  // White on coralInk is 5,89; the mock's own coral carries it at 4,31 (Part 16).
  ribbonRescue: { backgroundColor: theme.color.coralInk },
  ribbonWords: { ...theme.type.h2, color: theme.color.surface, flexShrink: 1 },
  countdown: { flexDirection: 'row', alignItems: 'center', gap: theme.space.xxs },
  countdownWords: { ...theme.num.xs, ...theme.tabular, color: theme.color.surface },
  urgent: { color: theme.color.gameCoral },
  // Its padding and every gap in it are `deckCardGeometry`'s.
  body: { flex: 1 },
  versions: { ...theme.type.tiny, color: theme.color.onDarkTiny, textAlign: 'center' },
  hair: { height: StyleSheet.hairlineWidth, backgroundColor: theme.color.onDarkHair },
  forecast: { flexDirection: 'row', alignItems: 'center', gap: theme.space.md },
  figure: { ...theme.num.xl, ...theme.tabular },
  bar: { flex: 1 },
});
