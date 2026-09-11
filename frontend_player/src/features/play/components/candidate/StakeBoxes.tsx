/**
 * The competitive card's **what's at stake** — the two figures a counted game against this
 * person would move ([#312](https://github.com/Raketa02/Raketa/issues/312)).
 *
 * ```
 * Win, counted      Lose, counted
 * +0,08             −0,05
 * ```
 *
 * They are the rating engine's own update rule read forward
 * ([ADR-0139](../../../../../../docs/adr/0139-a-confirmed-result-is-evidence-and-a-level-moves-by-what-it-taught.md)),
 * so the pair printed is the pair the game will deliver if it is played — and this component
 * draws them exactly as served. No rounding, no rescaling, no deriving one from the other, and
 * the minus on the loss is the figure's own.
 *
 * ## The two absences that reach it, and the one that does not
 *
 * `at_stake` is **omitted in for fun**, where a counted result is *meaningless* rather than
 * unavailable, and omitted in competitive where either of the two holds no rating in this
 * sport. Both arrive here as no value and draw nothing, which is *hidden, never blank* again.
 *
 * The third is **not** an absence and is decided before this component sees anything: on a
 * **doubles** seat the figures are real and must not be printed, because *a win against one
 * named person isn't a thing that exists until the other three seats are known*. That is
 * `stakeOnACard`'s rule, keyed off the sport's own seat count, and it is in `domain/` precisely
 * because it is a thing somebody could be wrong about.
 *
 * ## Two boxes or none, and no tone on either
 *
 * The pair is the fact: one figure alone tells a reader what a win is worth and not what a
 * loss costs. The contract sends the two together, and `AtStake` is the shape that keeps them
 * that way.
 *
 * **Neither box is tinted.** `mint` is *settled, safe, covered* and `red` is *ended badly*, and
 * neither is true of a result nobody has played —
 * [1.3](../../../../../docs/design-system.md#13-semantic-colour-is-never-decorative). The sign
 * carries the direction, the label carries the word, and
 * [Part 13](../../../../../docs/design-system.md#part-13--accessibility) is satisfied without a
 * colour being asked to mean anything.
 *
 * **It announces nothing of its own**, on §20.1's merge: both boxes reach the listener as two
 * clauses of the card body's name.
 */

import { formatSignedLevel } from '@/shared/formatting/ratingFormat';
import { StatBox, StatFigure, StatRow } from '@/shared/ui';

import type { AtStake } from '../../domain/candidate';
import { LOSS_STAKE_BLOCK, WIN_STAKE_BLOCK } from '../playerCardPresentation';

export interface StakeBoxesProps {
  /**
   * The pair the card may draw — `stakeOnACard`'s answer and never a component's.
   *
   * Absent covers all three cases above, so this component holds no rule: it is handed a pair
   * or it is handed nothing, and there is no seat count in it to get wrong a second time.
   */
  readonly stake?: AtStake;
}

export function StakeBoxes({ stake }: StakeBoxesProps) {
  if (stake === undefined) return null;

  return (
    <StatRow>
      <StatBox label={WIN_STAKE_BLOCK}>
        <StatFigure>{formatSignedLevel(stake.winDelta)}</StatFigure>
      </StatBox>

      <StatBox label={LOSS_STAKE_BLOCK}>
        <StatFigure>{formatSignedLevel(stake.lossDelta)}</StatFigure>
      </StatBox>
    </StatRow>
  );
}
