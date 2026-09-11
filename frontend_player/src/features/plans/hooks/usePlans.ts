/**
 * The read, the lookup, the three slot writes and the lock — and the one thing the room reads
 * back off all four.
 *
 * | | |
 * | --- | --- |
 * | `usePlans` | `GET /plans` — every plan for a game you are on the court of |
 * | `usePlan` | one plan **out of that list**, because there is no `GET /plans/{id}` |
 * | `useSetSlot` | the three slot `PUT`s, as one hook holding three mutations |
 * | `useLockPlan` | `PUT /plans/{id}/lock` — the act, beside the three values |
 * | `usePlanWriteRefusals` | every refusal a plan write has met, off the mutation cache |
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
 * control that is waiting. **The lock pauses with them**, on the same test: *we are agreed* on
 * reconnect is the same agreement it would have been, and a lock carried no clock to begin with.
 *
 * ## The lock is the same write with no value, and the same cache effect
 *
 * `PUT /plans/{id}/lock` answers with the plan as it now stands, `locked_at` included, so the
 * reply is written in exactly as a slot's is and nothing is refetched. **A second lock records
 * nothing and answers `200`** — the same plan back, with the first lock's moment on it — so the
 * write-in is safe against a double tap for the same reason a repeated slot value is.
 *
 * ## One mutation key, so the room can read what was refused
 *
 * A hold is a fact about the **account** rather than about the act that met it, and the room
 * draws one amber note for every write on its screen — the send and the four here. The room owns
 * that fold and cannot see this hook's state, so every write here is made under
 * `planKeys.writing()` and {@link usePlanWriteRefusals} reads the errored ones back off the
 * mutation cache: the shape `useSendingMessages` already has for the optimistic bubbles, for the
 * same reason — a fact held in a mutation is read where the mutation is, never copied into a
 * second store. The refusal lives as long as the mutation, which is the lifetime `liveState.ts`
 * says is the honest one.
 */

import { useMutation, useMutationState, useQuery, useQueryClient } from '@tanstack/react-query';

import { AppError } from '@/shared/errors';

import type { Plan, PlanSlot } from '../domain/slots';
import { lockPlan, type LockPlanAsk } from '../use-cases/lockPlan';
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
 * **One plan write** — under the feature's one mutation key, with the reply written into the list.
 *
 * The four writes differ in what they send and in nothing about what they do with the answer, so
 * the shape is spelled once: a second `onSuccess` is how one of them stops writing the reply in.
 */
function usePlanWrite<Ask>(mutationFn: (ask: Ask) => Promise<Plan>) {
  const client = useQueryClient();

  return useMutation<Plan, AppError, Ask>({
    mutationKey: planKeys.writing(),
    mutationFn,
    onSuccess: (plan) => {
      client.setQueryData<readonly Plan[]>(planKeys.list(), (plans) =>
        plans === undefined ? [plan] : withPlan(plans, plan),
      );
    },
  });
}

/**
 * **The three slot writes, as one hook**, because a card holding three chips takes all three and
 * never one: a hook per slot would have the card mounting three of them and asking which is in
 * flight.
 */
export function useSetSlot() {
  return {
    place: usePlanWrite<SetPlaceAsk>(setPlace),
    day: usePlanWrite<SetDayAsk>(setDay),
    hour: usePlanWrite<SetHourAsk>(setHour),
  };
}

/**
 * **The lock** — the fourth write, and the one that is an act rather than a value
 * ([ADR-0155](../../../../../docs/adr/0155-the-plan-gains-a-lock-and-locking-is-an-act-rather-than-a-count.md)).
 *
 * Its own hook rather than a fourth member of `useSetSlot`, because a card reads the three as a
 * row keyed by slot and reads this one by name: the lock is not a slot, and putting it in a
 * `Record<PlanSlot, …>` would need a fourth key that `PLAN_SLOTS` must never have.
 */
export function useLockPlan() {
  return usePlanWrite<LockPlanAsk>(lockPlan);
}

/**
 * **Every refusal a plan write has met**, off the mutation cache — see the module note.
 *
 * The room is the one caller, and what it does with the list is fold *held*: `writeStanding` reads
 * the code, this reads nothing. Not keyed by game, because the one fact read off it is about the
 * account rather than a plan. The cache is untyped by construction, so what comes back is narrowed
 * to the class every write here rejects with rather than asserted.
 */
export function usePlanWriteRefusals(): readonly AppError[] {
  const refusals = useMutationState<unknown>({
    filters: { mutationKey: planKeys.writing(), status: 'error' },
    select: (mutation) => mutation.state.error,
  });

  return refusals.filter((refusal): refusal is AppError => refusal instanceof AppError);
}

/** The list with one plan replaced, or appended where the game had none. */
function withPlan(plans: readonly Plan[], plan: Plan): readonly Plan[] {
  return plans.some((one) => one.gameId === plan.gameId)
    ? plans.map((one) => (one.gameId === plan.gameId ? plan : one))
    : [...plans, plan];
}
