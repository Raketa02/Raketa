/**
 * **`BALANCE FORECAST`** — a game's full forecast on paper: each side's level and the gap, the bar,
 * the % and its word, what a confirmed score does, and what is at stake
 * ([#415](https://github.com/Rakieta02/Rakieta/issues/415),
 * [ADR-0161](../../../../docs/adr/0161-the-game-screen-draws-its-courts-pairing.md); for fun 3,
 * [#839](https://github.com/Rakieta02/Rakieta/issues/839), ADR-0207 §6).
 *
 * ```
 * BALANCE FORECAST                                  eyebrow
 * 2,70              gap               2,71          num.l · tag + num.xs · num.l
 *                   −0,01
 * [ You + Zofia ▓▓▓▓▓▓▓░░░░░░ Kuba + Ola ]          BalanceBar md, labels = stems
 * 90%   Very even                                   num.xl in the tone's ink · cardTitle
 *       A counted game — a confirmed score moves    tiny, muted
 *       everybody's level.
 * ┌ If you win ──┐  ┌ If you lose ──┐               StakeTiles — two or none
 * │ +0,08        │  │ −0,08         │
 * └──────────────┘  └───────────────┘
 * ```
 *
 * ## Two features, one block
 *
 * `games` draws it through `GamePairingCard`, which a booked game's details compose while the full
 * game awaits its entry; **a competitive game's details open on it** (`proposals`, #839), the top
 * card a player reads before saying yes. Two features that may not import each other draw it, so
 * it came here from `games` — ADR-0207 §6's own decision — with its tiles and its words
 * (`shared/vocabulary/forecastPresentation.ts`), and draws the same for both. What each hands it is
 * its own read's: the booked game the Game's pairing, the details `GET /proposals/{id}`.
 *
 * ## It is handed a forecast, or it is not drawn
 *
 * ADR-0161 §4 omits the forecast and the split together when the pairing cannot be computed, and
 * **there is deliberately no reason beside the absence**: the surface that composes this draws
 * nothing and says nothing. So the props require both halves, and this component holds no branch
 * for their absence — a block that could be mounted with nothing to draw would be a block somebody
 * eventually gives a sentence to. Whether it is drawn at all is the composer's: **never on For
 * fun** (ADR-0207 §5) — the details open on the Social vibe card, and a booked For-fun game draws
 * that card in this block's place (#841), so *A friendly — nothing moves.* is said nowhere.
 *
 * ## No arithmetic, and the bar is fed the served gap
 *
 * `the-play-screens.md` §5: the gap, the percentage and the deltas are the server's. The bar takes
 * the **signed** gap as its `advantage` and maps it on 7.11's one fixed scale, and the tone is the
 * served figure's through `balanceTone`. The word beside the figure is `balanceWord`'s, because the
 * bar is a colour and Part 13 forbids colour as the only signal. Those three are cited from
 * `shared/vocabulary` rather than re-spelled: three copies of §B9's breaks is where one of them
 * becomes `>`.
 *
 * ## Four elements, and the bar is not one of them
 *
 * §20.1: the eyebrow is a `header`; the split row is one element naming both sides whole and the
 * gap; the reading is one element — the word, the figure, the sentence; the tiles are one element
 * of two clauses. The bar is drawn **hidden**, on the builder's own argument: the row above it
 * prints all three of its numbers, so its name would be the fourth reading of one fact.
 */

import { StyleSheet, Text, View } from 'react-native';

import { formatLevel, formatPercent } from '@/shared/formatting/ratingFormat';
import { balanceLabel, balanceTone, balanceWord } from '@/shared/vocabulary/balancePresentation';
import {
  BALANCE_FORECAST,
  GAP_WORD,
  readingLabel,
  splitLabel,
  stakeLabel,
  type ForecastSplit,
  type ForecastStake,
} from '@/shared/vocabulary/forecastPresentation';

import { BALANCE_INK, BalanceBar } from './BalanceBar';
import { Card } from './Card';
import { StakeTiles } from './StakeTiles';
import { theme } from './theme';

export interface ForecastBlockProps {
  /** How even the game is forecast to be, in your direction — the served figure, whole or not. */
  readonly forecast: { readonly pct: number };
  readonly split: ForecastSplit;
  /** Absent on a friendly and where the rule has nothing to price: no tile is drawn. */
  readonly stake?: ForecastStake;
  /** The bar's two labels — stems, yours then theirs. */
  readonly labels: readonly [string, string];
  /** The same two sides as a sentence names them, for the split row's spoken name. */
  readonly names: readonly [string, string];
  /** What a confirmed score does, or nothing for a kind this build cannot read. */
  readonly sentence: string | undefined;
}

export function ForecastBlock({
  forecast,
  split,
  stake,
  labels,
  names,
  sentence,
}: ForecastBlockProps) {
  const tone = balanceTone(forecast.pct);

  return (
    <Card style={s.card}>
      <Text accessibilityRole="header" style={s.eyebrow}>
        {BALANCE_FORECAST}
      </Text>

      {/* **Signed, as it was served.** The sign is which way the game leans, and taking it off
          would be this block doing arithmetic over a number it was handed. */}
      <View accessible accessibilityLabel={splitLabel(names, split)} style={s.split}>
        <Text style={[s.side, s.sideLevel]}>{formatLevel(split.yourSide)}</Text>
        <View style={s.gap}>
          <Text style={s.gapWord}>{GAP_WORD}</Text>
          <Text style={s.gapLevel}>{formatLevel(split.gap)}</Text>
        </View>
        <Text style={[s.side, s.sideLevel, s.theirs]}>{formatLevel(split.theirSide)}</Text>
      </View>

      <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
        <BalanceBar
          advantage={split.gap}
          tone={tone}
          size="md"
          labels={labels}
          accessibilityLabel={balanceLabel(forecast.pct)}
        />
      </View>

      {/* The figure and the words that read out of it, left to right as one claim: *90% — very
          even, and a confirmed score moves everybody.* */}
      <View accessible accessibilityLabel={readingLabel(forecast.pct, sentence)} style={s.reading}>
        <Text style={[s.figure, { color: BALANCE_INK[tone] }]}>{formatPercent(forecast.pct)}</Text>
        <View style={s.words}>
          <Text style={s.word}>{balanceWord(forecast.pct)}</Text>
          {sentence === undefined ? null : <Text style={s.sentence}>{sentence}</Text>}
        </View>
      </View>

      {stake === undefined ? null : (
        <View accessible accessibilityLabel={stakeLabel(stake)}>
          <StakeTiles stake={stake} />
        </View>
      )}
    </Card>
  );
}

const s = StyleSheet.create({
  card: { gap: theme.space.sm },
  eyebrow: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  split: { flexDirection: 'row', alignItems: 'flex-end' },
  side: { flex: 1 },
  sideLevel: { ...theme.num.l, ...theme.tabular, color: theme.color.ink },
  theirs: { textAlign: 'right' },
  gap: { alignItems: 'center' },
  gapWord: { ...theme.type.tag, color: theme.color.muted },
  gapLevel: { ...theme.num.xs, ...theme.tabular, color: theme.color.muted },
  reading: { flexDirection: 'row', alignItems: 'center', gap: theme.space.md },
  figure: { ...theme.num.xl, ...theme.tabular },
  words: { flex: 1, gap: theme.space.xxs },
  word: { ...theme.type.cardTitle, color: theme.color.ink },
  sentence: { ...theme.type.tiny, color: theme.color.muted },
});
