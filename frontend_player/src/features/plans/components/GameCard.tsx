/**
 * **One game on Now's rail** — tag · eyebrow · figure · line · gloss · court · footer
 * ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §4.2).
 *
 * It is handed `(game, plan | undefined)` plus the two facts the screen already holds — who is
 * reading, and where their room is — and **reads no global state of its own**
 * ([`the-loop-components.md`](../../../../../docs/specs/the-loop/the-loop-components.md) §3.4).
 * The join is the rail's, over three lists.
 *
 * ## Two actions, and the named door is not a third
 *
 * **The button is a named door**: it carries the act's verb, it navigates, and it **never writes**
 * ([#336](https://github.com/Raketa02/Raketa/issues/336) §4). **The body goes wherever the button
 * goes** — a body that always opened the details screen would be a second, quieter door
 * disagreeing with the first — so the two are *one* action, and §24.5 makes them one accessibility
 * element whose name ends with the door's verb. The drawn button is therefore **hidden**: it is
 * the sighted half of something the card's own name already says, and a second element announcing
 * `Open` beside a card that announces `… Open` is the double announcement 6.8 refuses.
 *
 * **The ✉ is the second element**, because it goes somewhere else. It is drawn only where there is
 * a room to open — ADR-0149 §3's join fails soft, and an ending **destroys** a conversation rather
 * than delisting it (ADR-0153) — and a card with neither door draws no footer at all rather than
 * an empty rule across the bottom of it.
 *
 * ## The footer rides `marginTop: auto`, and that is what a rail is for
 *
 * 7.7 puts `marginTop: auto` on the last hairline of a rail card **so footers align across cards
 * of differing height**, which is the whole reason a rail can hold a card with a 40pt figure
 * beside one with none. The card takes the height the row gives it and the hairline falls to the
 * bottom of it; nothing here measures anything.
 *
 * ## The figure is one slot with two type roles, and the hour is printed once
 *
 * `num.levelHero` for an hour, because
 * [1.4](../../../../docs/design-system.md#14-numbers-are-monospaced-always) is categorical that
 * numbers are monospaced always; **3.3's `display`** for a weekday, which is the one sans role
 * above `h1` and exists for exactly this — the alternatives were a mono-only figure slot and a
 * day-only card leading with the court, and both answer a type problem with a layout one. Which of
 * the two it is comes off `cardFigure` rather than off a regular expression here.
 *
 * ## There is no checklist on the card
 *
 * Struck by the dev: the fuller account stays on the game screen, where `resultBody` and
 * `UNSCORED_FACTS` already live, and the gloss names only the **next** slot.
 */

import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { CONVERSATION_ROUTE } from '@/features/conversations/types';
import { GAME_ROUTE, type Game } from '@/features/games/types';
import { sportLabel } from '@/features/onboarding/types';
import { Button, Card, Hairline, Tag, theme } from '@/shared/ui';

import { doorOf, gameCardName } from '../domain/gameCard';
import type { Plan } from '../domain/slots';

import { ChatDoor } from './ChatDoor';
import { GameCourt } from './GameCourt';
import {
  CARD_TAG,
  DOOR_LABEL,
  cardCourtSummary,
  cardEyebrow,
  cardFigure,
  cardGloss,
  cardLine,
  gameCardLabel,
} from './nowPresentation';

export interface GameCardProps {
  readonly game: Game;
  /** What has been agreed, and `undefined` where nothing has. The two are one state. */
  readonly plan: Plan | undefined;
  /** The reader's own id — which seat is theirs, and which sentence they are told. */
  readonly playerId: string;
  /** Where the ✉ goes, and `undefined` where there is no room to open. */
  readonly conversationId: string | undefined;
  /** The content width. 7.7's paging geometry: the card is `1.0 × content` and has no peek. */
  readonly width: number;
}

export function GameCard({ game, plan, playerId, conversationId, width }: GameCardProps) {
  const name = gameCardName(game, plan);
  const door = doorOf(name);
  const tag = CARD_TAG[name];
  const figure = cardFigure(plan);
  const line = cardLine(plan);
  const sportName = sportLabel(game.sport);

  /**
   * **The card's own 5.1 pressed border, driven by the body.**
   *
   * The card is not the control — the body is, and the ✉ is a second control on the same surface —
   * so `PressableCard` cannot be used here without swallowing the ✉ into the card's one
   * accessibility element. What is kept is the *state*, and the **border is `Card`'s own**: a
   * coral outline spelled again here would be a second answer to a question 5.1 has settled, and a
   * body that dimmed itself instead would be a third.
   */
  const [pressed, setPressed] = useState(false);

  const open = () => router.push({ pathname: GAME_ROUTE, params: { gameId: game.gameId } });

  return (
    <Card pressed={pressed} style={[s.card, { width }]}>
      {/* One element, one action, one name — everything above the fold merges into it, which is
          §20.1 unchanged: the tag, the figure and the court have no action of their own. */}
      <Pressable
        accessible
        accessibilityRole="button"
        accessibilityLabel={gameCardLabel({ name, sportName, game, plan, playerId, door })}
        onPress={open}
        onPressIn={() => setPressed(true)}
        onPressOut={() => setPressed(false)}
        style={s.body}
      >
        {tag === undefined ? null : (
          <Tag label={tag.label} variant={tag.variant} dot={theme.sport[game.sport]} />
        )}

        <Text style={s.eyebrow}>{cardEyebrow(game)}</Text>

        {figure === undefined ? null : (
          <Text style={figure.kind === 'hour' ? s.hour : s.weekday}>{figure.value}</Text>
        )}

        {line === undefined ? null : <Text style={s.line}>{line}</Text>}

        <Text style={s.gloss}>{cardGloss(name, { game, plan, playerId })}</Text>

        <GameCourt
          sport={game.sport}
          seats={game.seats}
          playerId={playerId}
          summary={cardCourtSummary(sportName, game.seats.length)}
          caption={sportName}
        />
      </Pressable>

      {door === undefined && conversationId === undefined ? null : (
        <Hairline style={s.footer}>
          <View style={s.footerRow}>
            {door === undefined ? null : (
              // Hidden on both platforms — one prop hides it on one only — because the card's own
              // name already ends with this verb.
              <View
                style={s.doorBox}
                accessibilityElementsHidden
                importantForAccessibility="no-hide-descendants"
              >
                <Button label={DOOR_LABEL[door]} size="sm" onPress={open} />
              </View>
            )}

            {conversationId === undefined ? null : (
              <ChatDoor
                onPress={() =>
                  router.push({ pathname: CONVERSATION_ROUTE, params: { conversationId } })
                }
              />
            )}
          </View>
        </Hairline>
      )}
    </Card>
  );
}

const s = StyleSheet.create({
  card: { gap: theme.space.xs },
  body: { gap: theme.space.xs },
  eyebrow: { ...theme.type.eyebrow, color: theme.color.muted, textTransform: 'uppercase' },
  hour: { ...theme.num.levelHero, ...theme.tabular, color: theme.color.ink },
  weekday: { ...theme.type.display, color: theme.color.ink },
  line: { ...theme.type.tiny, color: theme.color.muted },
  // `rlValue` and not `tiny`: the gloss is the one sentence the card adds, so it reads above the
  // muted line under the figure and below the figure itself. There is no `body` role in 3.3.
  gloss: { ...theme.type.rlValue, color: theme.color.ink },
  // 7.7: the last hairline in a rail card takes `marginTop: auto`, so footers align across cards
  // of differing height. The rail stretches every card to the tallest one's height.
  footer: { marginTop: 'auto' },
  footerRow: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  // The named door takes the room the row has; the ✉ is its own fixed width beside it.
  doorBox: { flex: 1 },
});
