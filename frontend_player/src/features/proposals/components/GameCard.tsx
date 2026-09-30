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
 * ## A door to the game, and doors to the people on it
 *
 * A press anywhere on the card opens the game's details, and a press on a tile opens that player's
 * record (the screens A2.2). **The card is not one element to a listener**, as the Players card is:
 * its tiles are buttons of their own, and an element that swallowed them would take the records
 * out of a screen reader's reach. So the card's parts speak for themselves — the ribbon, each
 * tile, the forecast, the grid, the court block — and the details are reached by the **i** under
 * the stage, which is the accessible path the drag never is (ADR-0169 §3's rule, kept).
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
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { balanceTone } from '@/features/play/types';
import { formatPercent } from '@/shared/formatting/ratingFormat';
import { BalanceBar, theme, type BalanceBarTone } from '@/shared/ui';
import type { Weekday } from '@/shared/vocabulary/week';

import {
  completesIt,
  countdownOf,
  courtTagOf,
  foldOf,
  inAcrossVersions,
  ribbonOf,
  rowsOf,
  type DeckCard,
  type DeckPerson,
} from '../domain/deck';
import type { GameDay } from '../domain/when';

import { CourtBlock } from './CourtBlock';
import {
  barLabels,
  countdownSpoken,
  countdownWords,
  forecastSpoken,
  inOnGameLine,
  ribbonWords,
} from './deckPresentation';
import { GameGround } from './GameGround';
import { GameTiles } from './GameTiles';
import { OverlapGrid } from './OverlapGrid';

/** The forecast's figure on the card's ground — `BALANCE_INK`'s three, read for the dark (Part 16). */
const FIGURE: Readonly<Record<BalanceBarTone, string>> = {
  ok: theme.color.gameGreen,
  warn: theme.color.gameAmber,
  bad: theme.color.gameRed,
};

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
}

export function GameCard({ card, seatsPerSide, at, day, today, onOpen, onPerson }: GameCardProps) {
  const { top, bottom } = rowsOf(card, seatsPerSide);
  const ribbon = ribbonOf(card);
  const countdown = countdownOf(card.deadline, at);
  const counting = countdownWords(countdown);
  const urgent = countdown.kind === 'minutes' && ribbon.kind !== 'seatOpen';
  const labels = barLabels([top, bottom]);
  const acrossVersions = inAcrossVersions(card);

  const drawing = (
    <>
      <GameGround />

      <View
        style={[s.ribbon, ribbon.kind === 'seatOpen' ? s.ribbonRescue : s.ribbonGame]}
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

      <View style={s.body}>
        <GameTiles
          top={top}
          bottom={bottom}
          singles={seatsPerSide === 1}
          completes={completesIt(card)}
          fill
          {...(onPerson === undefined ? {} : { onPerson })}
        />

        {acrossVersions === undefined ? null : (
          <Text style={s.versions}>{inOnGameLine(acrossVersions)}</Text>
        )}

        <View style={s.hair} />

        {card.forecast === undefined ? null : (
          <Forecast pct={card.forecast.pct} fold={foldOf(card) ?? 0} labels={labels} />
        )}

        <OverlapGrid overlap={card.overlap} today={today} />

        <CourtBlock tag={courtTagOf(card)} day={day} card={card} />
      </View>
    </>
  );

  return (
    <View style={s.card}>
      {/* Not one element — see the module note. A press here opens the game; a tile's own press
          reaches the tile first. Behind the top card it is inert: no press, nothing to find. */}
      <Pressable
        style={s.clip}
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
      <Text style={[s.figure, { color: FIGURE[tone] }]}>{formatPercent(pct)}</Text>
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

const s = StyleSheet.create({
  card: { flex: 1, borderRadius: theme.radius.deckCard, ...theme.shadow.deckCard },
  clip: { flex: 1, borderRadius: theme.radius.deckCard, overflow: 'hidden' },
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
  body: { flex: 1, padding: theme.space.md, gap: theme.space.sm },
  versions: { ...theme.type.tiny, color: theme.color.onDarkTiny, textAlign: 'center' },
  hair: { height: StyleSheet.hairlineWidth, backgroundColor: theme.color.onDarkHair },
  forecast: { flexDirection: 'row', alignItems: 'center', gap: theme.space.md },
  figure: { ...theme.num.xl, ...theme.tabular },
  bar: { flex: 1 },
});
