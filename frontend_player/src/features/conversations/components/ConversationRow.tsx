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
 * `CandidatePhoto` is the photograph-or-poster switch and there is no monogram anywhere: #338 §5
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
 * which **has** moved and which this row reaches through `CandidatePhoto` rather than re-hashing.
 * `CandidatePhoto` itself cannot follow it without dragging `CANDIDATE_PANEL`, whose own docstring
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
 */

import { router } from 'expo-router';
import { StyleSheet, Text, View, useWindowDimensions } from 'react-native';

import { sportLabel } from '@/features/onboarding/types';
import { CandidatePhoto } from '@/features/play/types';
import { handleLine } from '@/shared/formatting/handleList';
import { playerName } from '@/shared/formatting/playerName';
import { PressableCard, theme } from '@/shared/ui';

import type { Conversation } from '../domain/conversation';
import { memberName, othersIn } from '../domain/membership';

import { conversationRowLabel } from './conversationAccessibility';
import { conversationRowLine } from './conversationPresentation';
import { FACE_OVERLAP, ROW_FACE, handleBudget } from './conversationGeometry';

/**
 * Where a row goes. Both segments under `/chats` carry a static kind above the id, because a
 * challenge id and a conversation id are different ids of different things and `/chats/[id]` for
 * both is one segment a router cannot resolve and a reader cannot read.
 */
export const CONVERSATION_ROUTE = '/chats/conversation/[conversationId]';

export interface ConversationRowProps {
  readonly conversation: Conversation;
  /** The reader. A row names **the others** in the room, so it is never derived here. */
  readonly playerId: string;
}

export function ConversationRow({ conversation, playerId }: ConversationRowProps) {
  const { width } = useWindowDimensions();

  const others = othersIn(conversation.members, playerId);
  const handles = others.map((member) => playerName(memberName(member)));

  const sport = sportLabel(conversation.sport);
  // Two readings of one line. The eye gets the row's — one line, and a place without its court;
  // the ear gets the whole value, because §20.4 is *the visible label truncates, the spoken one
  // never does*, and a shortened value is exactly that truncation one register over.
  const drawn = conversationRowLine(conversation, 'one-line');
  const spoken = conversationRowLine(conversation, 'full');

  return (
    <PressableCard
      accessibilityLabel={conversationRowLabel(handles, sport, spoken)}
      onPress={() =>
        router.push({
          pathname: CONVERSATION_ROUTE,
          params: { conversationId: conversation.conversationId },
        })
      }
      style={s.row}
    >
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
