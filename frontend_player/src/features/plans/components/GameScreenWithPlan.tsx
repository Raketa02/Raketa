/**
 * **The game screen with its plan composed into it** — the thing a route mounts, at both of the
 * screen's two addresses
 * ([#368](https://github.com/Raketa02/Raketa/issues/368),
 * [ADR-0149](../../../../../docs/adr/0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md)
 * §2).
 *
 * `GameScreen` stays `features/games`' and receives the plan as a **child**: *`games` owns the
 * frame, the court and the result arms, and `plans` renders the three slots into it. Neither type
 * crosses.* This is the one place that holds both halves, so it is the one place the join and the
 * fold happen — and it exists rather than being two lines in each route file because a composition
 * spelled twice is a composition that drifts once.
 *
 * ## It folds the arm as well as filling the slot
 *
 * [`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §5.2 lands
 * *Planning* and *Game on* on **the plan** and *Needs result* on **the score grid** — two
 * landings inside one standing — and
 * [`the-loop-components.md`](../../../../../docs/specs/the-loop/the-loop-components.md) §3.3 says
 * the ladder is read by *"the rail, the card, the gloss, **and the game screen's arm**"*. The
 * ladder reads a plan, so the arm is folded here and **a word crosses back**, never a rung:
 * `entryLeadOf` derives it from the card's own door, so the two tables cannot disagree about where
 * a button goes.
 *
 * ## Two reads, one clock, and neither is this component's to own
 *
 * `useGame` and `usePlan` are the same queries Now's rail and the room's card are mounted on, so on
 * a warm cache this costs nothing. Everything folds against `GET /games`' `read_at`: `GET /plans`
 * deliberately carries no instant, which is what makes *today* and the horizon one clock
 * ([ADR-0148](../../../../../docs/adr/0148-the-last-line-is-the-pill-and-the-plan-is-read-beside-the-game.md)
 * §10).
 *
 * A game the list cannot answer for **still mounts the screen**, because the sentence about an
 * address nothing matches is that screen's to say. The lead handed over in that moment names the
 * score, and it is never read: no arm renders until there is a game.
 *
 * ## Three children on the plan lead, and one join answers two of them
 *
 * [#414](https://github.com/Raketa02/Raketa/issues/414) redrew the plan lead as the Now card at
 * the top, the court's pairing under it and the chat's editable plan card under that, so the one
 * slot became three and this is where all three are filled. The **card** is `GameCard` with
 * `doors={false}` — the shell #413 built, on the same `useChatDoors` join the rail runs: the
 * room's address it does not draw and the faces it does, keyed by the challenge, failing soft
 * into posters. The **court** is `features/games`' own `CourtPairing`
 * ([#415](https://github.com/Raketa02/Raketa/issues/415)) — the forecast block and the players
 * card over the pairing read beside the game — handed the same faces map, because the players
 * card draws the same people off the same join and the screen may not read that list itself. The
 * **plan** is `GameScreenPlan` on the plan lead — the editable card, the panel
 * inside it — and `GamePlan` on the score lead, where the plan is read beside a score in `Tag`s
 * with the checklist and the door, as it always was. The screen draws whichever it is handed and
 * never learns which; the lead it is handed alongside is what decides here.
 *
 * ## And a fourth, which is another feature's act
 *
 * *Fill the seat* — the challenge screen's ⚡, handed the people **the game's** seats hold
 * (`seatedOthers`) — a **challenge** act reached from a game, because the seat that fills is the
 * challenge's ([ADR-0162](../../../../../docs/adr/0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md),
 * [#419](https://github.com/Raketa02/Raketa/issues/419)). So the control and its words are
 * `features/challenges`', read through its `types.ts` the way `useChatDoors` is, and this is where
 * it is handed into the screen's `fill` slot — directly under the card that says *needs a player*
 * ([ADR-0175](../../../../../docs/adr/0175-nobody-calls-a-game-off-the-court-ends-by-its-seats-or-by-its-hour.md)
 * §4) — and where the two rules about *whether* are applied: a seat is open, and the agreed moment
 * is ahead, which is the ladder's `momentHasPassed` over the plan this composition already holds
 * and the games list's own instant. On a stale tap the control asks this composition to re-read
 * the games list, because that read is the one clock every fold on the screen is against.
 *
 * Two acts stood beside it and are gone (ADR-0175 §1, §4). *Leave this game* — #418's — is the
 * Chats row's swipe alone now, so a player who wants out goes where every seat is left from. And
 * *Call it off* — the withdraw grown to a reopened court
 * ([ADR-0163](../../../../../docs/adr/0163-called-off-is-the-fourth-end-of-a-game.md)) — no
 * longer exists for anybody: a game with a seat open ends by its seats or by its hour, never by
 * one person's decision over the others.
 *
 * **A plan read still in flight leads with the plan, and that is the same answer as nothing
 * agreed.** *Not yet arrived* and *three empty slots* reach `entryLeadOf` identically — which is
 * the semantics `slots.ts` already relies on — and the plan is found **by the game's challenge**
 * (ADR-0164 §1), the id it was opened from. The cost is one case: a deep link straight to a game
 * whose moment has passed shows the plan lead until the second list lands, and then the grid
 * arrives. Both lists are read together by every surface that can *reach* this screen by tapping,
 * so that case is the link and not the journey.
 */

import { useCurrentUser } from '@/features/auth/types';
import { FillTheSeat } from '@/features/challenges/types';
import { useChatDoors } from '@/features/conversations/types';
import { CourtPairing, GameScreen, openSeats, seatedOthers, useGame } from '@/features/games/types';

import { entryLeadOf } from '../domain/gameCard';
import { momentHasPassed } from '../domain/ladder';
import { usePlan } from '../hooks/usePlans';

import { GameCard } from './GameCard';
import { GamePlan } from './GamePlan';
import { GameScreenPlan } from './GameScreenPlan';

export interface GameScreenWithPlanProps {
  /** Validated by `features/games`' route schema before it reaches either surface. */
  readonly gameId: string;
}

export function GameScreenWithPlan({ gameId }: GameScreenWithPlanProps) {
  const { game, refetch } = useGame(gameId);
  // The plan is the challenge's (ADR-0164 §1): the game finds it by the id it was opened from.
  const { plan } = usePlan(game?.challengeId);
  const rooms = useChatDoors();
  const playerId = useCurrentUser().data?.id;

  const entryLead = game === undefined ? 'the-score' : entryLeadOf(game, plan);
  /**
   * **The fill is offered only while the agreed moment is ahead** (#411 rule 1) — the ladder's
   * own test, read off the plan and the games list's instant, mirroring the rule the server
   * enforces with `game_moment_has_passed`: nobody may be seated into a game whose moment is
   * gone. The rung cannot say it alone: *Needs a player* outranks *Needs result*, so a short
   * court past its moment is on this lead with no act left — and the hour calls it off
   * (ADR-0175 §3).
   */
  const momentAhead = game !== undefined && !momentHasPassed(plan, game.readAt);
  /** **A seat is open** — the other half of whether there is anything to fill. */
  const seatOpen = game !== undefined && openSeats(game.seats).length > 0;

  /** What a stale tap on any of the acts costs: this composition's own games read, again. */
  const reRead = () => void refetch();

  // The same key the rail's join uses, and the same soft failure: no room is no faces, and the
  // seats draw their posters. The address is not drawn — `doors={false}` — but the card takes it.
  const room = game === undefined ? undefined : rooms.get(game.challengeId);

  return (
    <GameScreen
      gameId={gameId}
      entryLead={entryLead}
      card={
        game === undefined || playerId === undefined ? null : (
          <GameCard
            game={game}
            plan={plan}
            playerId={playerId}
            conversationId={room?.conversationId}
            faces={room?.faces ?? NO_FACES}
            doors={false}
          />
        )
      }
      court={
        game === undefined || playerId === undefined ? null : (
          <CourtPairing game={game} playerId={playerId} faces={room?.faces ?? NO_FACES} />
        )
      }
      plan={
        game === undefined ? null : entryLead === 'the-plan' ? (
          <GameScreenPlan game={game} plan={plan} />
        ) : (
          <GamePlan game={game} plan={plan} />
        )
      }
      fill={
        // The one challenge act reached from a game (ADR-0162, #419, ADR-0175 §4): the control
        // is `features/challenges`', composed here as the chat doors are, and the re-read it asks
        // for on a stale tap is this component's own games read — the one clock every fold on
        // the screen is against. The rule is handed in as `offered` rather than applied as a
        // mount, so an act in flight is not unmounted from under its own reply: a seat open, and
        // the moment ahead.
        game === undefined || playerId === undefined ? null : (
          <FillTheSeat
            challengeId={game.challengeId}
            sport={game.sport}
            accepted={seatedOthers(game.seats, playerId)}
            offered={seatOpen && momentAhead}
            onReRead={reRead}
          />
        )
      }
    />
  );
}

/** No room, no faces: one empty map rather than one per render. */
const NO_FACES: ReadonlyMap<string, string> = new Map();
