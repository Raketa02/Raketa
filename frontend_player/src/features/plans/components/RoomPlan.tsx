/**
 * **The join, and the whole of what the room hands down is its challenge, its clock and its
 * count.**
 *
 * The card needs the court's plan and no route serves it beside the room: the plan is deliberately
 * not a field on a room or on a game — *a game is a record of an evening and a plan is an agreement
 * about a future, and the two contexts do not read each other* — so it is one list beside the
 * others, joined at the surface **by challenge id**
 * ([ADR-0148](../../../../../docs/adr/0148-the-last-line-is-the-pill-and-the-plan-is-read-beside-the-game.md)
 * §8,
 * [ADR-0164](../../../../../docs/adr/0164-a-plan-is-the-challenges-and-a-room-without-a-game-lives-as-long-as-its-challenge.md)
 * §1). The room has carried `challengeId` from its opening, so **the card is pinned in every room**
 * — two of four in, three of four — and not only in one whose line-up has completed; the game is
 * no longer read here at all, because the row carries the anchor the day chips run from and the
 * room's own `read_at` is *today*.
 *
 * **`features/plans` may import `features/games`, and never the reverse.** That is the direction
 * ADR-0148 already pays for on the server, and it keeps the client half of ADR-0145 §4's clause
 * true for free: `features/games` never learns a plan exists. The rule is one-way, it is stated as
 * such so a future reader cannot read the existing edge as symmetry, and `eslint.config.mjs`
 * enforces the half that is a grep rather than a judgement.
 *
 * **A list that has not landed draws nothing**, and so does a court this reader holds no seat on
 * — both are no row. The same nothing on purpose: the row is what says there is a plan to draw and
 * carries the anchor to draw it with, and a card that announced its own loading would be chrome
 * flickering above a stream. The read is not this component's to own — it is the app's list, shared
 * with Now and with the game screen, so on a warm cache this costs nothing at all.
 *
 * **The lock waits for the court** (ADR-0164 §5). The room says so by handing down the court's
 * count exactly while it has no game — its members over the sport's seats — and the card draws
 * the count line where the button will be; the room passes none once it has its game, and the
 * button is drawn. The rule of what stands there is `domain/lock.ts`'; what is the room's to know
 * is who is in and whether the court has completed.
 *
 * **The room passes no note** — the panel that explains the slots is not chrome above a composer
 * (ADR-0145 §6); the game screen draws the same card with it inside
 * ([#414](https://github.com/Raketa02/Raketa/issues/414)) — and it is the room that puts the card
 * at the gutter, because where a card sits is the surface's to say.
 */

import { StyleSheet, View } from 'react-native';

import { theme } from '@/shared/ui';

import type { CourtCount } from '../domain/lock';
import { usePlan } from '../hooks/usePlans';

import { PlanCard } from './PlanCard';

export interface RoomPlanProps {
  /** The challenge this room is arranging — the plan's own key, on the room from its opening. */
  readonly challengeId: string;
  /** The instant the room was folded against — *today* on the day row. */
  readonly readAt: string;
  /**
   * **Who is in against how many the court takes — given exactly while the room has no game.**
   * With it the card draws the count line where the lock will be; without it, the button.
   */
  readonly court?: CourtCount;
  /** The account may not write here. Every chip greys, and the screen owns the one note. */
  readonly refused?: boolean;
}

export function RoomPlan({ challengeId, readAt, court, refused = false }: RoomPlanProps) {
  const { plan } = usePlan(challengeId);

  if (plan === undefined) return null;

  return (
    <View style={s.pinned}>
      <PlanCard
        plan={plan}
        readAt={readAt}
        {...(court === undefined ? {} : { court })}
        refused={refused}
      />
    </View>
  );
}

const s = StyleSheet.create({
  // Pinned under the header at the gutter, with the gutter's own step below it so the stream's
  // first separator is not flush against the border. **No device has drawn this**: the numbers
  // are the system's steps read off the mock's proportions, and Part 16 says so. The game screen
  // draws the same card with no margin, in a scroll that already sits at the gutter (#414).
  pinned: { marginHorizontal: theme.size.gutter, marginBottom: theme.space.sm },
});
