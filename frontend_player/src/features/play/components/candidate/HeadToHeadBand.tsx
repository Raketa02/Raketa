/**
 * The competitive card's **head-to-head band** — one block where the card used to draw three
 * ([#309](https://github.com/Raketa02/Raketa/issues/309)).
 *
 * ```
 * You 2,71            Fairly even · 74%            2,83
 * [========= you =========|========== them ==========]
 * ```
 *
 * The two-`Side` row, a bare `BalanceBar` and a *Predicted balance* `FactRow` were three
 * elements saying one thing, stacked. What replaces them is one object: **your level on the
 * left, theirs on the right, and the forecast with its word in the middle, tinted.**
 *
 * ## No names above the bar
 *
 * The identity row has already named them, and the row above the bar is a comparison rather
 * than an introduction. What survives is *You* — which is not a name but the answer to *whose
 * number is the left one*, and the bar's own `you` / `them` seals it under the figures.
 *
 * ## The bar draws its segment labels here, and `sm` is not changed to make it
 *
 * `BalanceBar` drops labels at `sm` because *"at `sm` there is no room beside the fold for a
 * 9,5pt line"* — a floor #219 B4 put there and a finding about the size rather than about this
 * surface. The band is taller than the column the bar used to sit in, so it takes **`md`**: the
 * size decides whether there is a label, and the caller picks the size that carries one.
 *
 * ## The bar and the figure are two facts, and the component says so
 *
 * **The bar takes the level advantage; the printed percentage is the forecast.** The bar says
 * *which side*, the figure says *how even*, and nothing here derives either from the other —
 * `the-play-screens.md` §11.3 is *no forecast arithmetic on the client*, and `BALANCE_SCALE` is
 * *one mapping, one constant, one clamp*, which is 7.11's whole finding. Neither is re-derived:
 * the fold is `balanceShare`'s and the tone is `balanceTone`'s.
 *
 * The reading beside them is `balanceReading` — the word **then** the figure, which is
 * [`the-words.md`](../../../../../../docs/specs/matchmaking/the-words.md) §B9's one spelling of
 * that pair. The designs write it the other way round; one spelling wins, because the card's
 * **spoken** name is composed from this same string and a second order would put the reader and
 * the listener on different sentences. The tint is `BALANCE_INK`, which is paper ink and this
 * is a white card — and Part 13's *never colour alone* is satisfied by the word standing in
 * front of the number rather than by the tint.
 *
 * ## A term that stood down takes its own half of the band with it
 *
 * Three conditions where the old card had three independent ones, and hidden rather than blank
 * in every branch:
 *
 * - **Both** — the band, whole.
 * - **`LEVEL_FIT` only** — the two figures and no bar. There is no tone without a forecast, and
 *   a bar drawn in a default colour would be a tint standing for nothing.
 * - **`PREDICTED_BALANCE` only** — the reading as a labelled row, which is exactly what the card
 *   drew before this band existed. There is no advantage without two μ, and **inventing one is
 *   the client computing a level**.
 * - **Neither** — nothing at all.
 *
 * That last-but-one branch is why the fallback is here rather than in the card: the term is in
 * `COMPETITIVE_CARD_DRAWS`, so its reason line is filtered off **whether or not the band could
 * draw it**, and a band that simply vanished would take a fact off the card in both registers
 * at once.
 *
 * **It announces nothing, and only the bar has to be told so.** §20.1 merges an actionless
 * element into the nearest action above it, which the figures do by carrying no name of their
 * own. The **bar** is the exception: it sets `accessible` and an `image` role on itself, so
 * inside a card body it would be a fourth element — §20.4 gives it that name on the **court**,
 * where it sits on a screen rather than inside a button. Its reading reaches the listener as a
 * clause of the card body's name instead, exactly once.
 */

import { StyleSheet, Text, View } from 'react-native';

import { playerName } from '@/shared/formatting/playerName';
import { formatLevel } from '@/shared/formatting/ratingFormat';
import { BALANCE_INK, BalanceBar, theme } from '@/shared/ui';
import { balanceLabel, balanceReading, balanceTone } from '@/shared/vocabulary/balancePresentation';

import type { LevelFitEvidence, PredictedBalanceEvidence } from '../../domain/evidence';
import { BALANCE_ROW_LABEL } from '../playerCardPresentation';

import { FactRow } from './FactRow';

/**
 * *you* / *them*, in the bar's own two segments.
 *
 * Lower case and not the row's *You*: these sit inside the fill as captions on a shape, where
 * the figure above starts a phrase. They are the bar's, so they are given to it as a pair.
 */
const SEGMENTS: readonly [string, string] = ['you', 'them'];

export interface HeadToHeadBandProps {
  /** Absent where the term stood down — there is no second source for the searcher's own μ. */
  readonly levelFit?: LevelFitEvidence;
  /** Absent where the term stood down. The forecast is the server's and is never derived. */
  readonly balance?: PredictedBalanceEvidence;
}

export function HeadToHeadBand({ levelFit, balance }: HeadToHeadBandProps) {
  if (levelFit === undefined) {
    if (balance === undefined) return null;
    return <FactRow label={BALANCE_ROW_LABEL} value={balanceReading(balance.pct)} />;
  }

  // Once, and handed to both: the word beside the figure and the bar's fill are the same
  // reading of the same number, and two calls is where somebody eventually passes one of them
  // a different percentage.
  const tone = balance === undefined ? undefined : balanceTone(balance.pct);

  return (
    <View style={s.band}>
      <View style={s.figures}>
        <View style={s.side}>
          <Text style={s.sideLabel}>{playerName({ kind: 'you' })}</Text>
          <Text style={s.level}>{formatLevel(levelFit.myMu)}</Text>
        </View>

        {balance === undefined || tone === undefined ? null : (
          <Text style={[s.reading, { color: BALANCE_INK[tone] }]}>
            {balanceReading(balance.pct)}
          </Text>
        )}

        <Text style={s.level}>{formatLevel(levelFit.theirMu)}</Text>
      </View>

      {balance === undefined || tone === undefined ? null : (
        <View accessibilityElementsHidden importantForAccessibility="no-hide-descendants">
          <BalanceBar
            advantage={levelFit.myMu - levelFit.theirMu}
            tone={tone}
            size="md"
            labels={SEGMENTS}
            accessibilityLabel={balanceLabel(balance.pct)}
          />
        </View>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  band: { gap: theme.space.xs },
  figures: {
    flexDirection: 'row',
    alignItems: 'baseline',
    justifyContent: 'space-between',
    gap: theme.space.xs,
  },
  side: { flexDirection: 'row', alignItems: 'baseline', gap: theme.space.xxs, flexShrink: 1 },
  sideLabel: { ...theme.type.rlLabel, color: theme.color.muted },
  level: { ...theme.num.xs, ...theme.tabular, color: theme.color.ink },
  // It shrinks before either figure does: the two levels are the comparison, and the reading
  // is the sentence about it — a wrapped word is legible where a wrapped 2,71 is not.
  reading: { ...theme.type.rlValue, flexShrink: 1, textAlign: 'center' },
});
