/**
 * **Back · the faces · the handles' stems · the sport and the booking's word.**
 *
 * 10.3's header with a `lead` slot, which arrived for this: a room is named by the people in it,
 * so their faces belong beside their handles rather than in the page under them, where the stream
 * would scroll them away. Two of the five are this ticket's and the other three are untouched
 * ([#401](https://github.com/Rakieta02/Rakieta/issues/401)).
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
 * place. The organiser alone again is a real room ([#429](https://github.com/Rakieta02/Rakieta/issues/429)
 * E4), and this component draws no faces for it and passes an empty list on; the words are the
 * copy deck's, so there is no arrangement of props here that draws a blank at `h1`.
 *
 * The stems are shorter inputs to the rule that was already here: `handleLine` still gives way by
 * **dropping whole names** at a separator, never by cutting one (§15), against the header's own
 * budget — the row's arithmetic with a chevron on one side and the width of the old loop's
 * `Details` control still reserved on the other, though nothing draws it any more (#576): giving
 * that width back would reflow every booked room's title, which is a change to look at on a device
 * rather than one to make in a removal. That budget is now counted at `h1`, which is what the title is set in; it
 * was counted at the rows' `cardTitle`, which promised a one-line title that wrapped, and
 * `conversationGeometry.ts` says so.
 *
 * ## The second line is the sport and the game's state
 *
 * `Padel · booked` — the booking's own word, lowered where the words are, and handed in by the
 * booked game's chat, which has just read the booking. A state here was refused once, because the
 * prototype's subtitle was the backend's twenty-state vocabulary leaking into the chat;
 * [ADR-0157](../../../../../docs/adr/0157-the-conversation-header-names-its-people-by-their-stems-and-says-which-rung-the-game-is-on.md)
 * reversed that for a word the player already reads on the game's own card, and the booking's
 * status is that word.
 *
 * ## The two lines are the other way up from 10.3's eyebrow
 *
 * The sport used to be the eyebrow *above* the handles. The design is title above and a quieter
 * line below, and it is 10.3's new **sub-line** slot rather than a variant that inverts the pair:
 * a slot is the shape `lead` and `right` already have, and 10.3's own argument for `lead` is that
 * *the header holds an arrangement and the screen holds what goes in it*. `tiny` in `muted`, drawn
 * as given, and no new type role.
 */

import { StyleSheet, View, useWindowDimensions } from 'react-native';

import { sportLabel } from '@/features/onboarding/types';
import { playerName } from '@/shared/formatting/playerName';
import { PlayerPhoto, ScreenHeader } from '@/shared/ui';

import { othersIn, personName } from '../domain/membership';
import type { ConversationRoom } from '../domain/room';

import { conversationHeaderLabel } from './conversationAccessibility';
import { FACE_OVERLAP, ROW_FACE, headerHandleBudget } from './conversationGeometry';
import { headerSubline, headerTitle } from './conversationPresentation';

export interface ConversationHeaderProps {
  readonly room: ConversationRoom;
  /** The reader. A header names **the others**, exactly as the row it was opened from does. */
  readonly playerId: string;
  readonly onBack: () => void;
  /** Where the game stands — the booking's own word, in lower case (*booked*). */
  readonly gameState: string;
}

export function ConversationHeader({ room, playerId, onBack, gameState }: ConversationHeaderProps) {
  const { width } = useWindowDimensions();

  const others = othersIn(room.members, playerId);
  const handles = others.map((member) => playerName(personName(member)));
  const sport = sportLabel(room.sport);

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
    />
  );
}

const s = StyleSheet.create({
  faces: { flexDirection: 'row' },
  // The row's own overlap, so a doubles room reads as a group rather than as three people the
  // header happens to list.
  behind: { marginLeft: -ROW_FACE * FACE_OVERLAP },
});
