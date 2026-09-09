/**
 * **The plan, on the game screen** — the panel, the three read-only tags, the checklist, and the
 * chat door under them
 * ([#368](https://github.com/Raketa02/Raketa/issues/368),
 * [`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §5).
 *
 * **It is a child, and the screen that renders it knows nothing about it.** `GameScreen` stays
 * `features/games`' and receives this as a `ReactNode`
 * ([ADR-0149](../../../../../docs/adr/0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md)
 * §2): *`games` owns the frame, the court and the result arms, and `plans` renders the three slots
 * into it. Neither type crosses.* `GameScreenWithPlan` beside this file is where the two halves
 * meet, so `features/games` never learns a plan exists and the ESLint ban stays a grep rather than
 * a judgement.
 *
 * **It is handed `(game, plan | undefined)` and reads no global state of its own** beyond the one
 * join no route provides —
 * [`the-loop-components.md`](../../../../../docs/specs/the-loop/the-loop-components.md) §3.4's rule
 * for the card, one surface over.
 *
 * ## It is the same block on all four entry arms, and it is not told which one
 *
 * §22.6 settles it: *the rungs differ by the clock and not by the arrangement*. So the checklist is
 * one rule on all four, and *how long is left to say you played* is the screen's own standing line,
 * drawn above this and never spelled again here. What the arm decides is on the screen around this
 * — whether the grid is open — and nothing inside it, which is why no arm reaches this component.
 *
 * **The door is `secondary` on every arm, and on two of them nothing on the screen is accented.**
 * §5.1 makes the chat door *Planning* and *Game on*'s primary act, and 6.1's fill is the wrong way
 * to say so here: the accent would sit in the scroller while the pinned slot — the thing that
 * exists so an act cannot scroll away — held a quieter control. **A plan arm asks for nothing**, so
 * nothing on it wears the one accent; what says the door is the point is that it is under the plan
 * it is the remedy for, and that the score is behind a control rather than on the screen. The
 * coral comes back on the two arms that *are* asking, where `Send this score` is pinned.
 *
 * ## It is the whole of what the design's plan panel becomes, and eight things it does not draw
 *
 * Drawn to `details1.png` / `details2.png`, which is the **pre-ADR product**. Each correction is a
 * record read out (§5.4):
 *
 * 1. ***Part of day* is not a slot** — the three are `where · day · hour`, and ADR-0145 §2 deleted
 *    the part-of-day bands *"deleted, not repurposed"*.
 * 2. ***Lock it in · set all three first* is deleted** — filling the third slot **is** the lock.
 * 3. **The coral outline around the plan goes with it**: it was the locked state's border, and 5.1
 *    already spends a coral outline on the *pressed* state.
 * 4. **The panel inverts** — `PLAN_PANEL`, which names an absence rather than explaining one.
 * 5. **The three slots are `Tag`s, not `Chip`s** — `PlanTags`, and ADR-0149 §4's reason.
 * 6. ***Sun 9* is a date**, and this app has none: the horizon is seven chips, so a weekday is
 *    exact and `dayChipName` is what draws one.
 * 7. ***60 min* is a duration nothing in this build holds** — no booking, no court, no slot
 *    length — so there is no such line.
 * 8. ***COMPETITIVE* is a search's mode**: a game carries a `GameKind`, `FRIENDLY` is the marked
 *    case, and what this block says about it is `worthLine`'s one sentence.
 *
 * **And *press and hold anyone for the full record* is gone**, on #285's argument: *a hold is a
 * gesture with no affordance, no announcement, and no equivalent in the accessibility API at all.*
 * Nothing here is pressable but the door.
 *
 * **No pairing forecast and no player rows.** ADR-0143 §8 refused both *for the only standing a
 * game exists in* — *"a card here would be a second, worse copy of the game screen"* — and §5.5
 * upholds it with an argument of its own: **a forecast exists to help you decide whether to play
 * somebody, and on this screen you have already decided.** Reversing it is a fresh decision
 * extending ADR-0143 a second time, filed as
 * [#346](https://github.com/Raketa02/Raketa/issues/346) rather than taken here.
 *
 * ## The door is always drawn, whichever door you came in by
 *
 * §5.1: arriving from Now it is the whole point, and arriving from **Details** it is the way back.
 * **Drawing it conditionally on the route would make the surface depend on its door**, which is
 * the one thing ADR-0149 §5 bought by having a single screen — so it is not told which address
 * mounted it and cannot be.
 *
 * What it *is* conditional on is there being a room, which is ADR-0149 §3's client join failing
 * soft: a conversation is **destroyed** when the episode ends (ADR-0153), so a game at *Needs
 * result* usually has none and **no door is drawn rather than a dead one**. That hole is the
 * ADR's own stated consequence and not this component's to fix.
 *
 * ## Its one read is the join, and it folds nothing against a clock
 *
 * The game and the plan are handed down by `GameScreenWithPlan`, which holds both lists; what is
 * read here is `useChatDoor`, the client join ADR-0149 §3 settles, over a list the Chats tab
 * fetches anyway. Nothing here folds anything against the phone: a plan is **drawn literally and
 * never counted down**, so `GET /plans` carries no instant and this block needs none.
 */

import { router } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { CONVERSATION_ROUTE, OPEN_THE_CHAT, useChatDoor } from '@/features/conversations/types';
import { worthLine, type Game } from '@/features/games/types';
import { Button, Note, theme } from '@/shared/ui';

import type { Plan } from '../domain/slots';

import { checklistLines, PLAN_PANEL } from './planPresentation';
import { PlanTags } from './PlanTags';

export interface GamePlanProps {
  /** The game this plan belongs to. A plan has no id of its own, for ever. */
  readonly game: Game;
  /** What has been agreed, and `undefined` where nothing has. The two are one state. */
  readonly plan: Plan | undefined;
}

export function GamePlan({ game, plan }: GamePlanProps) {
  const conversationId = useChatDoor(game.challengeId);

  const checklist = checklistLines(plan, worthLine(game.kind));

  return (
    <View style={s.block}>
      <Note variant="info" title={PLAN_PANEL.title}>
        {PLAN_PANEL.body}
      </Note>

      <PlanTags plan={plan} />

      {/* One element, its three lines in order (§24.5) — a checklist has no action of its own, so
          §20.1 merges it into one thing a listener hears as a list rather than as three
          unattached sentences. */}
      <View style={s.checklist} accessible accessibilityLabel={checklist.join(' ')}>
        {checklist.map((line) => (
          <Text key={line} style={s.line}>
            {line}
          </Text>
        ))}
      </View>

      {conversationId === undefined ? null : (
        <Button
          label={OPEN_THE_CHAT}
          variant="secondary"
          onPress={() => router.push({ pathname: CONVERSATION_ROUTE, params: { conversationId } })}
        />
      )}
    </View>
  );
}

const s = StyleSheet.create({
  block: { gap: theme.space.sm },
  checklist: { gap: theme.space.xxs },
  line: { ...theme.type.tiny, color: theme.color.ink },
});
