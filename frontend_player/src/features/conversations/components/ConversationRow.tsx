/**
 * One row under `CONVERSATIONS` — **the faces · the whole handles · the sport · the last entry**,
 * and the whole of it is the door.
 *
 * Fully clickable and comfortably past 44pt by its own geometry, exactly as the challenge row
 * above it is: a 38pt face inside the card's `space.md` padding is 62 before anything else is
 * drawn, so there is no `hitSlop` here
 * ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §1.3).
 *
 * ## It draws the members it has, never the court it will become
 *
 * Membership is derived from the accepted seats and **grows one acceptance at a time**
 * (ADR-0146 §7), so a padel four whose line-up is still filling is a two-face row. Padding it out
 * to a seat count would be drawing the court rather than the room — and the room is what this row
 * is a door to.
 *
 * ## The face is a photograph or a poster, and here it is often the photograph
 *
 * `PlayerPhoto` is the photograph-or-poster switch and there is no monogram anywhere: #338 §5
 * refused the avatar outright — no element, no hue, no radius rule — because a poster is a fact
 * about an id ([ADR-0134](../../../../../docs/adr/0134-the-poster-draws-a-player-and-no-value-is-invented.md))
 * and initials are a derived familiar form ADR-0107 refuses.
 *
 * **Unlike the challenge row, this one has a `photo_url` to pass**, and that is the contract
 * rather than a preference: `GET /challenges` borrows a handle and nothing else about a person,
 * while a conversation member is *"a handle and a face"* — these people have already agreed to
 * play. The link is short-lived and minted for the response it arrived on, and an expired one
 * falls back to the poster with nothing to report, which is what a player with no photograph has
 * in any case.
 *
 * The component is reached through `features/play`'s public surface rather than copied, which is
 * the tension `ChallengeRow` states at length and this row inherits whole.
 * [`the-loop-components.md`](../../../../../docs/specs/the-loop/the-loop-components.md) §5 is the
 * authoritative list of what moves to `shared/` and it names one promotion — `courtPosterFor()`,
 * which **has** moved and which this row reaches through `PlayerPhoto` rather than re-hashing.
 * `PlayerPhoto` itself cannot follow it without dragging `PHOTO_PANEL`, whose own docstring
 * argues it belongs to the card rather than to the system, so the alternative today is a second
 * box with a second `× 0.33` in it and one person drawn at two corners.
 *
 * ## No pill, and no state anywhere on it
 *
 * ADR-0148 §6's *the last line is what a pill would have said* is a **product** argument as well
 * as a wire one, and the only pill this client could draw would be joined client-side off the
 * games cache — which feature-first Clean Architecture refuses. The three the design draws are
 * gone, and *Settle up* went with ownership. **The last line is the state**, and it is one line,
 * tail-truncated: a row is a door and the line is a pointer *to* the room, not a preview of it.
 *
 * ## Swiped left, it reveals one thing — and the thing is composed onto it
 *
 * *Leave the game* ([#427](https://github.com/Raketa02/Raketa/issues/427),
 * [ADR-0165](../../../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
 * §6): every room is a court the reader is on, so every row reveals it. The row is a `SwipeRow`
 * — the swipe only uncovers a button — and the act behind the button, its sheet, its words and its
 * refusals are the **departure's**, which is a challenge act. This feature may not import that one:
 * `features/challenges` already imports this one, and a feature importing a feature that imports
 * it is the cycle Part 1 calls a defect. So the act arrives the way the plan arrives on the game
 * screen (ADR-0149 §1): **composed at the surface** — the shell, which owns the Chats tab and
 * already imports both features, hands the section an {@link RowAct}, and the row draws whatever
 * door it is handed. What a row needs from an act is declared **here**, as {@link RowActDoor} —
 * the word, a way to open it, the accessibility action and the focus ref — and the act's owner
 * satisfies the shape without either side naming the other. No act handed, no swipe: the row is
 * a door and only a door.
 *
 * **A swipe is never the only path.** A screen reader consumes the gesture before the row sees
 * it, so the same door is the row's `accessibilityAction`, offered in the rotor under the act's
 * own word; taking it opens the same sheet. The card is the element the sheet returns focus to,
 * because the control a swipe reveals has closed with the row by the time the sheet is up.
 */

import type { ComponentType, ReactNode, RefObject } from 'react';
import { router } from 'expo-router';
import {
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
  type AccessibilityActionEvent,
  type AccessibilityActionInfo,
} from 'react-native';

import { sportLabel } from '@/features/onboarding/types';
import { handleLine } from '@/shared/formatting/handleList';
import { playerName } from '@/shared/formatting/playerName';
import { PlayerPhoto, PressableCard, SwipeRow, theme } from '@/shared/ui';

import type { Conversation } from '../domain/conversation';
import { othersIn, personName } from '../domain/membership';

import { conversationRowLabel } from './conversationAccessibility';
import { conversationRowLine } from './conversationPresentation';
import { FACE_OVERLAP, ROW_FACE, handleBudget } from './conversationGeometry';

/**
 * Where a row goes. Both segments under `/chats` carry a static kind above the id, because a
 * challenge id and a conversation id are different ids of different things and `/chats/[id]` for
 * both is one segment a router cannot resolve and a reader cannot read.
 */
export const CONVERSATION_ROUTE = '/chats/conversation/[conversationId]';

/**
 * **What a row needs from an act composed onto it** — declared by the row, satisfied by the act's
 * owner, and named by neither.
 *
 * The word goes on the revealed control and in the rotor; `open` is what both do; `action` and
 * `onAccessibilityAction` are the listener's path, because a swipe is a gesture assistive
 * technology consumes; `control` is where the act's sheet returns focus, attached to the card
 * because the revealed control has closed with the row by then.
 */
export interface RowActDoor {
  readonly label: string;
  readonly open: () => void;
  readonly control: RefObject<View>;
  readonly action: AccessibilityActionInfo;
  readonly onAccessibilityAction: (event: AccessibilityActionEvent) => void;
}

export interface RowActProps {
  /** The court the row is a room of — the one id both contexts already share. */
  readonly challengeId: string;
  /** The row, drawn around the door it is handed. */
  readonly children: (door: RowActDoor) => ReactNode;
}

/**
 * An act composed onto a row: a component that takes the court and hands back a door, drawing
 * whatever the act needs beside it — a sheet, a note. The shell supplies one; this feature knows
 * only its shape.
 */
export type RowAct = ComponentType<RowActProps>;

export interface ConversationRowProps {
  readonly conversation: Conversation;
  /** The reader. A row names **the others** in the room, so it is never derived here. */
  readonly playerId: string;
  /** The act a swipe reveals, or nothing — and with nothing, the row does not move. */
  readonly act?: RowAct;
}

export function ConversationRow({ conversation, playerId, act: Act }: ConversationRowProps) {
  const { width } = useWindowDimensions();

  const others = othersIn(conversation.members, playerId);
  const handles = others.map((member) => playerName(personName(member)));

  const sport = sportLabel(conversation.sport);
  // Two readings of one line. The eye gets the row's — one line, and a place without its court;
  // the ear gets the whole value, because §20.4 is *the visible label truncates, the spoken one
  // never does*, and a shortened value is exactly that truncation one register over.
  const drawn = conversationRowLine(conversation, 'one-line');
  const spoken = conversationRowLine(conversation, 'full');

  const open = () =>
    router.push({
      pathname: CONVERSATION_ROUTE,
      params: { conversationId: conversation.conversationId },
    });

  /** The card — the door to the room — around whatever act it is handed, or around nothing. */
  const card = (door?: RowActDoor) => (
    <PressableCard
      ref={door?.control}
      accessibilityLabel={conversationRowLabel(handles, sport, spoken)}
      accessibilityActions={door === undefined ? undefined : [door.action]}
      onAccessibilityAction={door?.onAccessibilityAction}
      onPress={open}
      style={s.row}
    >
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

      <View style={s.body}>
        <Text style={s.handles} numberOfLines={1}>
          {handleLine(handles, handleBudget(width, others.length))}
        </Text>
        <Text style={s.line} numberOfLines={1}>
          {drawn === undefined ? sport : `${sport} · ${drawn}`}
        </Text>
      </View>
    </PressableCard>
  );

  if (Act === undefined) return card();

  return (
    <Act challengeId={conversation.challengeId}>
      {(door) => (
        <SwipeRow reveal={{ label: door.label, onPress: door.open }}>{card(door)}</SwipeRow>
      )}
    </Act>
  );
}

const s = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', gap: theme.space.md },
  faces: { flexDirection: 'row' },
  // Each face after the first is pulled back over the one before it, so a doubles room reads as
  // a group rather than as three separate people the row happens to list.
  behind: { marginLeft: -ROW_FACE * FACE_OVERLAP },
  body: { flex: 1, gap: theme.space.xxs },
  handles: { ...theme.type.cardTitle, color: theme.color.ink },
  line: { ...theme.type.tiny, color: theme.color.muted },
});
