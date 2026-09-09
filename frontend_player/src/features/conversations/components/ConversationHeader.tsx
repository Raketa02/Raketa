/**
 * **Back · the faces · the whole handles · the sport · Details.**
 *
 * 10.3's header with a `lead` slot, which arrived for this: a room is named by the people in it,
 * so their faces belong beside their handles rather than in the page under them, where the stream
 * would scroll them away.
 *
 * ## The subtitle is the sport and nothing else
 *
 * The prototype's is the sport **plus the card-state tag**, which is where the twenty-state
 * vocabulary leaks into the chat. ADR-0148 §6 already refuses a standing on a conversation row,
 * and this is the same fact one line up: the room does not ask `challenges` and `games` what it
 * is, and it does not need to.
 *
 * ## Details is drawn only when there is a game
 *
 * `game_id` is nullable, so a `LINE_UP_INCOMPLETE` room has no game and no plan — **nothing for
 * this door to open**, and a control drawn over that nothing is the disabled control
 * [#324](https://github.com/Raketa02/Raketa/issues/324) refused. The rule lives beside the
 * drawing rather than at the call site so there is no arrangement of props that draws a dead one.
 *
 * The visible word is the design's and the spoken one is the destination's — *Open the game*,
 * because *Details* is a word about a screen and every other door on this map is named by its act
 * (§24.4).
 *
 * ## The handles are whole, and the list drops names rather than shortening one
 *
 * §15 through `handleLine`, against the header's own budget: the row's arithmetic with a chevron
 * on one side and the `Details` control reserved on the other, **whether or not it is drawn**, so
 * a header does not reflow its handles the moment a line-up completes.
 */

import { StyleSheet, View, useWindowDimensions } from 'react-native';

import { sportLabel } from '@/features/onboarding/types';
import { CandidatePhoto } from '@/features/play/types';
import { handleLine } from '@/shared/formatting/handleList';
import { playerName } from '@/shared/formatting/playerName';
import { Button, ScreenHeader } from '@/shared/ui';

import { memberName, othersIn } from '../domain/membership';
import type { ConversationRoom } from '../domain/room';

import { OPEN_THE_GAME } from './conversationAccessibility';
import { FACE_OVERLAP, ROW_FACE, headerHandleBudget } from './conversationGeometry';
import { DETAILS } from './conversationPresentation';

export interface ConversationHeaderProps {
  readonly room: ConversationRoom;
  /** The reader. A header names **the others**, exactly as the row it was opened from does. */
  readonly playerId: string;
  readonly onBack: () => void;
  /** Called with the game this room completed into. Never called where there is none. */
  readonly onOpenGame: (gameId: string) => void;
}

export function ConversationHeader({
  room,
  playerId,
  onBack,
  onOpenGame,
}: ConversationHeaderProps) {
  const { width } = useWindowDimensions();

  const others = othersIn(room.members, playerId);
  const handles = others.map((member) => playerName(memberName(member)));
  const gameId = room.gameId;

  return (
    <ScreenHeader
      title={handleLine(handles, headerHandleBudget(width, others.length))}
      eyebrow={sportLabel(room.sport)}
      onBack={onBack}
      lead={
        <View style={s.faces}>
          {others.map((member, at) => (
            <View key={member.playerId} style={at === 0 ? undefined : s.behind}>
              <CandidatePhoto
                playerId={member.playerId}
                {...(member.photoUrl === undefined ? {} : { photoUrl: member.photoUrl })}
                box={{ kind: 'face', size: ROW_FACE }}
              />
            </View>
          ))}
        </View>
      }
      {...(gameId === undefined
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
