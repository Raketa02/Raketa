/**
 * **What's at stake** — the two figures a counted result on this court would move, drawn as the
 * designs draw them: *If you win* tinted mint, *If you lose* on the recessed ground
 * ([#415](https://github.com/Raketa02/Raketa/issues/415); for fun 3,
 * [#839](https://github.com/Raketa02/Raketa/issues/839)).
 *
 * ```
 * If you win        If you lose
 * +0,08             −0,08
 * ```
 *
 * ## The box is shared and this is the forecast block's placer
 *
 * `StatBox`'s own rule — *what is shared is the box and never which boxes; each surface owns its
 * own placer* — read on the forecast block, wherever the block is drawn: a booked game, a
 * competitive game's details. The names are *If you win* / *If you lose*, one of them is tinted,
 * and the pair is priced side against side because every seat is known (ADR-0161 §4, ADR-0207 §6).
 * It came to `shared/ui` with the block (#839).
 *
 * ## Two or none, and the win tile is the only tinted thing
 *
 * The pair is the fact — the contracts send it together — and `ForecastStake` is the shape that
 * keeps it that way. The tint is 7.14's one amendment (Part 16, #415): the design wins, the lose
 * tile is `paper2` and never red, because nothing has ended.
 *
 * **It announces nothing of its own**: the block around it names both tiles as two clauses of one
 * element (`stakeLabel`).
 */

import { formatSignedLevel } from '@/shared/formatting/ratingFormat';
import { LOSE_TILE, WIN_TILE, type ForecastStake } from '@/shared/vocabulary/forecastPresentation';

import { StatBox, StatFigure, StatRow } from './StatBox';

export interface StakeTilesProps {
  readonly stake: ForecastStake;
}

export function StakeTiles({ stake }: StakeTilesProps) {
  return (
    <StatRow>
      <StatBox label={WIN_TILE} variant="mint">
        <StatFigure>{formatSignedLevel(stake.winDelta)}</StatFigure>
      </StatBox>

      <StatBox label={LOSE_TILE}>
        <StatFigure>{formatSignedLevel(stake.lossDelta)}</StatFigure>
      </StatBox>
    </StatRow>
  );
}
