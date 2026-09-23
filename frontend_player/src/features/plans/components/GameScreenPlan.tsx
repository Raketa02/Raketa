/**
 * **The plan, on the game screen's plan lead** — the chat's editable card, with the panel inside
 * it ([#414](https://github.com/Raketa02/Raketa/issues/414),
 * [ADR-0149](../../../../../docs/adr/0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md)
 * §4 as amended).
 *
 * **It is a child, and the screen that renders it knows nothing about it** — `GamePlan`'s shape
 * and `GamePlan`'s reason: `GameScreen` stays `features/games`' and receives this as a
 * `ReactNode`, so `features/games` never learns a plan exists and the ESLint ban stays a grep.
 * `GameScreenWithPlan` beside this file is where the two halves meet.
 *
 * ## The card is the room's, reused as it is, and the panel goes inside it
 *
 * ADR-0149 §4 drew the plan **read-only** wherever it was drawn outside the chat, and #410's design
 * reverses that for the two rungs whose door says *Finish the plan*: the button that brings you
 * here promises an errand, and a screen that then offered three tags and a door back to the room
 * would be a screen that did not keep it. So what is drawn is `PlanCard` — the eyebrow and the
 * counter, three `Chip`s with a sheet each, *Lock the plan* — **unchanged**, with one slot filled:
 * `PLAN_PANEL` (*Agreed between you — nothing is booked*) is drawn between the chips and the lock,
 * inside the card, which is where the design puts it. The room passes no note, so §3.2's *no
 * panel* stays true there, and the panel still has one home. The argument that **the room is
 * where the arranging happens** stands — the chat door is drawn under this card, dark and full
 * width — and this card is the same agreement offered one screen over.
 *
 * ## `refused` is folded here, off the same cache the room reads
 *
 * A hold is a fact about the account, met on whichever write met it, and `PlanCard` greys every
 * chip and the lock under it and draws no sentence of its own — *the screen owns the one note*.
 * On the game screen that screen is this component: it reads the plan's refusals off the mutation
 * cache exactly as the room does, folds them through the room's own `writeStanding`, and draws the
 * room's own sentence above the card, announced once as an `alert`. One fold and one constant,
 * because it is one fact said on two surfaces. What the room's note also covers — the send — has
 * no counterpart here; *We played* is the screen's and meets a hold on its own terms.
 *
 * It is handed `(game, plan | undefined)` by the composition that holds both lists, and reads
 * nothing else: the card's clock is the game's `readAt` (ADR-0148 §10), and the horizon is the
 * row's own anchor. **While the row has not landed, the card is drawn off the game's own anchor**:
 * once a game exists its plan's anchor *is* `planned_at` (ADR-0164 §4), so the row this draws in
 * the meantime — three empty slots, that anchor — is the row the list will answer with for a court
 * nobody has written on, and the held note and the panel stay where they were. The room cannot do
 * the same, because a room without a game has nothing to derive the anchor from; there, the row
 * is what says there is a card to draw. The line-up is complete here by construction — a game
 * screen is a court that has its game — so the lock is offered.
 */

import { StyleSheet, View } from 'react-native';

import { LIVE_NOTE, writeStanding } from '@/features/conversations/types';
import type { Game } from '@/features/games/types';
import { Note, theme } from '@/shared/ui';

import { LINE_UP_COMPLETE } from '../domain/lock';
import type { Plan } from '../domain/slots';
import { usePlanWriteRefusals } from '../hooks/usePlans';

import { PlanCard } from './PlanCard';
import { PLAN_PANEL } from './planPresentation';

export interface GameScreenPlanProps {
  /** The game whose plan this is — read for its clock. The plan is the challenge's, and it is found by the game's `challengeId` one component up. */
  readonly game: Game;
  /**
   * The court's row, or `undefined` while the list has not landed — drawn, in the meantime, as
   * the row it will be: nothing agreed, anchored at the game's `planned_at`.
   */
  readonly plan: Plan | undefined;
}

export function GameScreenPlan({ game, plan }: GameScreenPlanProps) {
  const held = writeStanding(usePlanWriteRefusals()) === 'held';

  const row: Plan = plan ?? { challengeId: game.challengeId, anchor: game.plannedAt };

  return (
    <View style={s.block}>
      {held ? (
        <Note variant="amber" accessibilityRole="alert">
          {LIVE_NOTE.held}
        </Note>
      ) : null}

      <PlanCard
        plan={row}
        readAt={game.readAt}
        lineUp={LINE_UP_COMPLETE}
        refused={held}
        note={
          <Note variant="info" title={PLAN_PANEL.title}>
            {PLAN_PANEL.body}
          </Note>
        }
      />
    </View>
  );
}

const s = StyleSheet.create({
  // The scroll already sits at the gutter, so the card takes no margin and meets the column's
  // edges like the dark card above it; the block's gap is the screen's own step between cards.
  block: { gap: theme.space.sm },
});
