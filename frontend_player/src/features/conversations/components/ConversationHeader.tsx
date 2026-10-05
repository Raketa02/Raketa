/**
 * **Back · the faces · the handles' stems · the sport and the game's state · Details.**
 *
 * 10.3's header with a `lead` slot, which arrived for this: a room is named by the people in it,
 * so their faces belong beside their handles rather than in the page under them, where the stream
 * would scroll them away. Two of the five are this ticket's and the other three are untouched
 * ([#401](https://github.com/Raketa02/Raketa/issues/401)).
 *
 * ## The title is the stems, and the name is the handles whole
 *
 * `headerTitle` draws each handle **up to its first word break** — `handleStem`, `Sergio.Sabater`
 * as `Sergio` — and that is not the first name ADR-0107 forbids. That record is against
 * *inventing* a familiar form; a stem is a prefix of the handle the person chose, cut at a
 * character they typed, and it is `the-words.md` §15's *a seat label may truncate visually; a
 * sentence may not* that permits it — `handleStem`'s docstring carries the argument and the two
 * conditions it comes with. Both hold here. **The spoken name keeps every handle whole**: the element is
 * `conversationHeaderLabel`'s — the handles joined with a final *and*, then the sport, then the
 * state — which is §20.4's *the visible label truncates, the spoken one never does*, and the
 * row's own dialect one screen on. And a handle that opens with a break keeps all of itself,
 * inside `handleStem` and not re-implemented here.
 *
 * **With nobody else to name, the title says what the room is doing** — `headerTitle` answers
 * *Waiting for others to join* for no handles, and `conversationHeaderLabel` speaks it in their
 * place. The organiser alone again is a real room ([#429](https://github.com/Raketa02/Raketa/issues/429)
 * E4), and this component draws no faces for it and passes an empty list on; the words are the
 * copy deck's, so there is no arrangement of props here that draws a blank at `h1`.
 *
 * The stems are shorter inputs to the rule that was already here: `handleLine` still gives way by
 * **dropping whole names** at a separator, never by cutting one (§15), against the header's own
 * budget — the row's arithmetic with a chevron on one side and the `Details` control reserved on
 * the other **whether or not it is drawn**, so a header does not reflow its handles the moment a
 * line-up completes. That budget is now counted at `h1`, which is what the title is set in; it
 * was counted at the rows' `cardTitle`, which promised a one-line title that wrapped, and
 * `conversationGeometry.ts` says so.
 *
 * ## The second line is the sport and the game's state — the Now card's, in lower case
 *
 * `Padel · planning`. This is a **reversal**, and it is recorded rather than absorbed: this
 * file's own docstring, `the-loop-screens.md` §3.1 and ADR-0148 §6 all refused a state here,
 * because the prototype's subtitle was the sport plus the **card-state tag** — the twenty-state
 * backend vocabulary leaking into the chat, read by making the room ask `challenges` and `games`
 * what it is. What lands is not that. It is the **four-rung client-side ladder Now already
 * draws**, plus its endings — `gameCardName`, folded from the two lists the screen already holds
 * for its plan card — and the word for it is `features/plans`' own, lowered where the words are
 * rather than at this call site. The design wins, and
 * [ADR-0157](../../../../../docs/adr/0157-the-conversation-header-names-its-people-by-their-stems-and-says-which-rung-the-game-is-on.md)
 * supersedes §6 for this one surface with that distinction as its argument.
 *
 * **A room with no game draws the sport alone.** `game_id` is nullable, so a `LINE_UP_INCOMPLETE`
 * room has no game — it has a plan, since ADR-0164, but the rung ladder is the game's — so no
 * state is drawn for it and none is invented, which is the same nothing the absent *Details* door
 * draws from the same field. The state is handed in as a word by the screen, which is where the
 * two reads it is folded from are already made.
 *
 * ## The two lines are the other way up from 10.3's eyebrow
 *
 * The sport used to be the eyebrow *above* the handles. The design is title above and a quieter
 * line below, and it is 10.3's new **sub-line** slot rather than a variant that inverts the pair:
 * a slot is the shape `lead` and `right` already have, and 10.3's own argument for `lead` is that
 * *the header holds an arrangement and the screen holds what goes in it*. `tiny` in `muted`, drawn
 * as given, and no new type role.
 *
 * ## Details is drawn only when there is a game
 *
 * `game_id` is nullable, so a `LINE_UP_INCOMPLETE` room has no game — **nothing for this door
 * to open**, whatever its plan says, and a control drawn over that nothing is the disabled control
 * [#324](https://github.com/Raketa02/Raketa/issues/324) refused. The rule lives beside the
 * drawing rather than at the call site so there is no arrangement of props that draws a dead one.
 *
 * The visible word is the design's and the spoken one is the destination's — *Open the game*,
 * because *Details* is a word about a screen and every other door on this map is named by its act
 * (§24.4).
 */

import { StyleSheet, View, useWindowDimensions } from 'react-native';

import { sportLabel } from '@/features/onboarding/types';
import { playerName } from '@/shared/formatting/playerName';
import { Button, PlayerPhoto, ScreenHeader } from '@/shared/ui';

import { othersIn, personName } from '../domain/membership';
import type { ConversationRoom } from '../domain/room';

import { OPEN_THE_GAME, conversationHeaderLabel } from './conversationAccessibility';
import { FACE_OVERLAP, ROW_FACE, headerHandleBudget } from './conversationGeometry';
import { DETAILS, headerSubline, headerTitle } from './conversationPresentation';

export interface ConversationHeaderProps {
  readonly room: ConversationRoom;
  /** The reader. A header names **the others**, exactly as the row it was opened from does. */
  readonly playerId: string;
  readonly onBack: () => void;
  /**
   * Called with the game this room completed into. Never called where there is none — and **absent
   * in a booked game's room** (#556), which is reached from the game's details and draws no
   * *Details* door back into them.
   */
  readonly onOpenGame?: (gameId: string) => void;
  /**
   * Where the game stands, as the Now card's own word in lower case — `features/plans`'
   * `cardStateWord`. Absent where there is no game, or no card to name yet; the line then says
   * the sport and stops.
   */
  readonly gameState?: string;
}

export function ConversationHeader({
  room,
  playerId,
  onBack,
  onOpenGame,
  gameState,
}: ConversationHeaderProps) {
  const { width } = useWindowDimensions();

  const others = othersIn(room.members, playerId);
  const handles = others.map((member) => playerName(personName(member)));
  const sport = sportLabel(room.sport);
  const gameId = room.gameId;

  return (
    <ScreenHeader
      title={headerTitle(handles, headerHandleBudget(width, others.length))}
      titleLabel={conversationHeaderLabel(handles, sport, gameState)}
      subline={headerSubline(sport, gameState)}
      onBack={onBack}
      lead={
        <View style={s.faces}>
          {others.map((member, at) => (
            <View key={member.playerId} style={at === 0 ? undefined : s.behind}>
              <PlayerPhoto
                playerId={member.playerId}
                {...(member.photoUrl === undefined ? {} : { photoUrl: member.photoUrl })}
                box={{ kind: 'face', size: ROW_FACE }}
              />
            </View>
          ))}
        </View>
      }
      {...(gameId === undefined || onOpenGame === undefined
        ? {}
        : {
            right: (
              <Button
                label={DETAILS}
                accessibilityLabel={OPEN_THE_GAME}
                variant="secondary"
                size="sm"
                onPress={() => onOpenGame(gameId)}
              />
            ),
          })}
    />
  );
}

const s = StyleSheet.create({
  faces: { flexDirection: 'row' },
  // The row's own overlap, so a doubles room reads as a group rather than as three people the
  // header happens to list.
  behind: { marginLeft: -ROW_FACE * FACE_OVERLAP },
});
