/**
 * The game screen's **what's at stake** — the two figures a counted result on this court would
 * move, drawn as mock 7 draws them: *If you win* tinted mint, *If you lose* on the recessed
 * ground ([#415](https://github.com/Raketa02/Raketa/issues/415)).
 *
 * ```
 * If you win        If you lose
 * +0,08             −0,08
 * ```
 *
 * ## The box is shared and the placer is this surface's
 *
 * `StatBox`'s own rule — *what is shared is the box and never which boxes; each surface owns its
 * own placer* — read on the game screen. Play's `StakeBoxes` is the candidate card's placer: its
 * names are *Win, counted* and *Lose, counted*, it is untinted on 7.14's argument, and the rule
 * about when a card may print it (`stakeOnACard`) is a rule about a card drawn before the other
 * seats are known. None of the three holds here — the game names the tiles *If you win* / *If you
 * lose*, tints one of them, and prints them on every court because every seat on a game is known
 * and the figure is priced side against side (ADR-0161 §4). So this is a second placer over the
 * one box rather than a fork of the first, and nothing about the box is copied.
 *
 * ## Two or none, and the win tile is the only tinted thing
 *
 * The pair is the fact — the contract sends it together — and `AtStake` is the shape that keeps
 * it that way. The tint is 7.14's one amendment (Part 16, #415): the design wins, the lose tile is
 * `paper2` and never red, because nothing has ended.
 *
 * **It announces nothing of its own**: the block around it names both tiles as two clauses of one
 * element (`stakeLabel`).
 */

import { formatSignedLevel } from '@/shared/formatting/ratingFormat';
import { StatBox, StatFigure, StatRow } from '@/shared/ui';

import type { AtStake } from '../domain/pairing';

import { LOSE_TILE, WIN_TILE } from './gamePresentation';

export interface StakeTilesProps {
  readonly stake: AtStake;
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
