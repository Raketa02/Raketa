/**
 * The read, the lookup, and the three writes — one per slot, because ADR-0144 has three events.
 *
 * | | |
 * | --- | --- |
 * | `usePlans` | `GET /plans` — every plan for a game you are on the court of |
 * | `usePlan` | one plan **out of that list**, because there is no `GET /plans/{id}` |
 * | `useSetSlot` | the three `PUT`s, as one hook holding three mutations |
 *
 * ## No optimistic write, and this is the file that would have been where one went
 *
 * **A slot change writes a system line other people read**, and *pending, never optimistic* is
 * this map's rule for everything that reaches another person
 * ([#366](https://github.com/Raketa02/Raketa/issues/366)). The one optimistic act on the whole
 * loop is a chat message, and what makes that one safe is that a message cannot be **wrong**:
 * there is no derived standing to guess at. A plan has three — the slot count four cards are keyed
 * on, the agreed point a conversation's own end is measured from, and the ladder that names them —
 * so the chip shows pending and the value it draws stays the one the server last answered with.
 *
 * **The reply is written in rather than refetched.** `PUT` answers with *the plan as it now
 * stands*, which is the whole of what this list holds about that game — so a read to learn what
 * the reply already said would be a request asking a question this client can answer. That is not
 * optimism: nothing is drawn until the server has spoken.
 *
 * **And nothing here invalidates the room.** The line a slot change writes arrives through the
 * live channel like any other entry
 * ([ADR-0147](../../../../../docs/adr/0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md)),
 * which is the same path every other member's copy of that line takes — the writer is a member,
 * so there is no second mechanism for the person who tapped. A cross-feature invalidation here
 * would also be this feature reaching into the one that composes it, which is the arrow
 * `features/plans` exists on the other side of.
 *
 * ## `networkMode` is the app's, and the test is the app's own
 *
 * *Does this act carry a deadline the player chose?* `challenges`' send does — an answer window is
 * derived at the tap. A slot does not: **the plan is drawn literally and never counted down**, and
 * a day recorded on reconnect is the same day it would have been. So all three writes **pause**
 * like everything else in the app, and the sheet renders `offlineMessage('resumes')` at the
 * control that is waiting.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { Plan, PlanSlot } from '../domain/slots';
import { readPlans } from '../use-cases/readPlans';
import { setDay, type SetDayAsk } from '../use-cases/setDay';
import { setHour, type SetHourAsk } from '../use-cases/setHour';
import { setPlace, type SetPlaceAsk } from '../use-cases/setPlace';

import { planKeys } from './planKeys';

export function usePlans() {
  return useQuery<readonly Plan[], AppError>({
    queryKey: planKeys.list(),
    queryFn: ({ signal }) => readPlans({ signal }),
  });
}

/**
 * One game's plan, found in the list — and `undefined` where there is none.
 *
 * **That absence is the ordinary state rather than a failure**: a plan is born by being used, so
 * a game nobody has arranged anything on has no row here at all, and *no plan* is what the card
 * draws as three empty slots. A game id this player is not on the court of has no row either, and
 * the two are deliberately one answer — `plan_not_found` is one code for two cases on the wire for
 * the same reason.
 *
 * A game id of `undefined` is a room whose line-up has not completed, which has no game and
 * therefore no plan. The read still runs, because it is the list every other surface shares.
 */
export function usePlan(gameId: string | undefined) {
  const plans = usePlans();

  return {
    ...plans,
    plan: gameId === undefined ? undefined : plans.data?.find((one) => one.gameId === gameId),
  };
}

/** Which slot a write is about — the key the card draws *pending* on. */
export type SettingSlot = PlanSlot | undefined;

/**
 * **The three writes, as one hook**, because a card holding three chips takes all three and never
 * one: a hook per slot would have the card mounting three of them and asking which is in flight.
 */
export function useSetSlot() {
  const client = useQueryClient();

  const held = (plan: Plan) => {
    client.setQueryData<readonly Plan[]>(planKeys.list(), (plans) =>
      plans === undefined ? [plan] : withPlan(plans, plan),
    );
  };

  const place = useMutation<Plan, AppError, SetPlaceAsk>({
    mutationFn: setPlace,
    onSuccess: held,
  });

  const day = useMutation<Plan, AppError, SetDayAsk>({ mutationFn: setDay, onSuccess: held });

  const hour = useMutation<Plan, AppError, SetHourAsk>({ mutationFn: setHour, onSuccess: held });

  return { place, day, hour };
}

/** The list with one plan replaced, or appended where the game had none. */
function withPlan(plans: readonly Plan[], plan: Plan): readonly Plan[] {
  return plans.some((one) => one.gameId === plan.gameId)
    ? plans.map((one) => (one.gameId === plan.gameId ? plan : one))
    : [...plans, plan];
}
