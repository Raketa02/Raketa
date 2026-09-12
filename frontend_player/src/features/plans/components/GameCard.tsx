/**
 * **One game on Now's rail** — a dark shell: header · slots + court · footer
 * ([#413](https://github.com/Raketa02/Raketa/issues/413),
 * [`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §4.2).
 *
 * It is handed `(game, plan | undefined)` plus the facts the screen already holds — who is
 * reading, where their room is, and the faces in it — and **reads no global state of its own**
 * ([`the-loop-components.md`](../../../../../docs/specs/the-loop/the-loop-components.md) §3.4).
 * The join is the rail's, over three lists.
 *
 * ## One shell for nine names, and no switch
 *
 * Every slot that differs by name is a **table lookup** on `GameCardName` — the tag's word, the
 * stage's dot, the accent and the door's verb, all in `nowPresentation.ts` — and the shell itself
 * branches on nothing. The Planning card is the first one drawn for real; every other name is
 * drawn by the same shell on the soft defaults #410 fixed, so the rail does not mix two visual
 * languages and a game flipping to *Game on* under your thumb does not jump layouts. When a
 * name's own design arrives it will be a row in those tables, or per-name **content** inside this
 * one shell — never a tenth card.
 *
 * ## Two doors, and the body is not a third
 *
 * **The card body is not pressable.** It used to go wherever the button went, on #336's argument
 * that a body always opening the details screen would be a second, quieter door disagreeing with
 * the first — and the design resolves that the other way: the two buttons are the only doors, so
 * there is nothing for the body to agree or disagree with. What the body is instead is **one
 * accessibility element with no action**: its name is the tag, the sport and the three slots as
 * sentences (`gameCardLabel`), in the shape the read-only plan tags already take — *one element,
 * because they are one fact in three parts with no action* (§24.5) — and the two doors follow it
 * as elements of their own. The wide door's verb is therefore **not** in the body's name: a body
 * ending in `Open` beside a button announcing `Open` is the double announcement 6.8 refuses, and
 * the drawn button is no longer hidden because it is no longer the sighted half of something else.
 *
 * **The wide door is the next thing to do** and its word changes with the stage — `Finish the
 * plan` on Planning, `Open` · `We played` · `Confirm the result` on the others, and none on an
 * ending — while its destination is the standing's, as it always was: `GAME_ROUTE`, and the
 * screen behind it lands on the arm the standing derives. **The bubble is the second door**,
 * because it goes somewhere else, and it is drawn only where there is a room to open: ADR-0149
 * §3's join fails soft, and an ending **destroys** a conversation rather than delisting it
 * (ADR-0153). A card with neither draws no footer at all rather than an empty row across the
 * bottom of it, and `doors={false}` draws none on purpose: it is how
 * [#414](https://github.com/Raketa02/Raketa/issues/414) draws this shell at the top of the game
 * screen — the screen *is* where both doors go, dark and full width under the plan card — and
 * #413 is where the shell's props were decided.
 *
 * ## The footer rides `marginTop: auto`, and that is what a rail is for
 *
 * 7.7 puts `marginTop: auto` on a rail card's footer **so footers align across cards of
 * differing height**. There is no hairline above it any more — the design draws none, and a fold
 * between three slots and the door that finishes them would cut the card in two — so the row
 * itself takes the margin. The card takes the height the row gives it and the footer falls to the
 * bottom of it; nothing here measures anything.
 */

import { router } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { CONVERSATION_ROUTE } from '@/features/conversations/types';
import { GAME_ROUTE, type Game } from '@/features/games/types';
import { sportLabel } from '@/features/onboarding/types';
import { Button, DarkCard, Tag, theme } from '@/shared/ui';

import { gameCardName } from '../domain/gameCard';
import { PLAN_SLOTS, type Plan } from '../domain/slots';

import { ChatDoor } from './ChatDoor';
import { GameCourt } from './GameCourt';
import {
  ACCENT,
  CARD_TAG,
  STAGE_DOT,
  cardCourtSummary,
  cardLine,
  doorLabel,
  gameCardLabel,
  sportWord,
} from './nowPresentation';
import { SlotRow } from './SlotRow';

export interface GameCardProps {
  readonly game: Game;
  /** What has been agreed, and `undefined` where nothing has. The two are one state. */
  readonly plan: Plan | undefined;
  /** The reader's own id — which seat is theirs, and which sentence they are told. */
  readonly playerId: string;
  /** Where the bubble goes, and `undefined` where there is no room to open. */
  readonly conversationId: string | undefined;
  /** Each seat's photograph by player id, from the room. Empty is posters, never an error. */
  readonly faces: ReadonlyMap<string, string>;
  /**
   * The content width, on the rail — 7.7's paging geometry: the card is `1.0 × content` and has no
   * peek, and a horizontal scroller does not stretch its children so the number is handed down.
   * **Absent at the top of the game screen** (#414), where the card is a column child and takes
   * the content width the way every card in a scroll does.
   */
  readonly width?: number;
  /** Whether the footer is drawn. Off on the game screen (#414), which is where both doors go. */
  readonly doors?: boolean;
}

export function GameCard({
  game,
  plan,
  playerId,
  conversationId,
  faces,
  width,
  doors = true,
}: GameCardProps) {
  const name = gameCardName(game, plan);
  const tag = CARD_TAG[name];
  const accent = ACCENT[name];
  const verb = doorLabel(name);
  const line = cardLine(name, { game, plan, playerId });
  const sportName = sportLabel(game.sport);

  const open = () => router.push({ pathname: GAME_ROUTE, params: { gameId: game.gameId } });

  return (
    <DarkCard style={[s.card, width === undefined ? undefined : { width }]}>
      {/* One element, one name, no action — the tag, the sport word, the slots and the court
          have no action of their own, and the two doors below are elements of their own. */}
      <View
        accessible
        accessibilityLabel={gameCardLabel({ name, sportName, game, plan, playerId })}
        style={s.body}
      >
        <View style={s.header}>
          {tag === undefined ? null : <Tag label={tag} variant="onDark" dot={STAGE_DOT[name]} />}
          <Text style={s.sport} numberOfLines={1}>
            {sportWord(game, sportName)}
          </Text>
        </View>

        <View style={s.plan}>
          <View style={s.slots}>
            {PLAN_SLOTS.map((slot) => (
              <SlotRow key={slot} slot={slot} plan={plan} accent={accent.bar} />
            ))}
          </View>

          <GameCourt
            sport={game.sport}
            seats={game.seats}
            playerId={playerId}
            faces={faces}
            summary={cardCourtSummary(sportName, game.seats.length)}
          />
        </View>

        {line === undefined ? null : <Text style={s.line}>{line}</Text>}
      </View>

      {!doors || (verb === undefined && conversationId === undefined) ? null : (
        <View style={s.footer}>
          {verb === undefined ? null : (
            <Button label={verb} variant={accent.button} size="lg" onPress={open} style={s.door} />
          )}

          {conversationId === undefined ? null : (
            <ChatDoor
              onPress={() =>
                router.push({ pathname: CONVERSATION_ROUTE, params: { conversationId } })
              }
            />
          )}
        </View>
      )}
    </DarkCard>
  );
}

const s = StyleSheet.create({
  card: { gap: theme.space.md },
  body: { gap: theme.space.md },
  header: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm },
  // `marginLeft: auto` rather than `space-between`, so the word stays right when there is no tag.
  sport: {
    ...theme.type.eyebrow,
    color: theme.color.onDarkEyebrow,
    textTransform: 'uppercase',
    marginLeft: 'auto',
    flexShrink: 1,
  },
  plan: { flexDirection: 'row', alignItems: 'flex-start', gap: theme.space.md },
  slots: { flex: 1, gap: theme.space.sm },
  line: { ...theme.type.tiny, color: theme.color.onDarkTiny },
  // 7.7: the footer takes `marginTop: auto`, so footers align across cards of differing height.
  // The rail stretches every card to the tallest one's height.
  footer: { flexDirection: 'row', alignItems: 'center', gap: theme.space.sm, marginTop: 'auto' },
  // The wide door takes the room the row has; the bubble is its own fixed width beside it.
  door: { flex: 1 },
});
