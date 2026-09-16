/**
 * One row under `CHALLENGES` — **face(s) · the whole handle(s) · the sport · one line · the
 * stripe, or the tag**, and the whole of it is the door.
 *
 * Fully clickable and comfortably past 44pt by its own geometry: a 38pt face inside the card's
 * `space.md` padding is 62 before anything else is drawn, so there is no `hitSlop` here
 * ([`the-loop-screens.md`](../../../../../docs/specs/the-loop/the-loop-screens.md) §1.2).
 *
 * ## The face is a photograph or a poster, and there is no monogram
 *
 * #338 §5 refused the avatar outright — no element, no hue, no radius rule — because
 * `PlayerPhoto` already **is** the photograph-or-poster switch, a poster is a fact about an
 * id ([ADR-0134](../../../../../docs/adr/0134-the-poster-draws-a-player-and-no-value-is-invented.md)),
 * and initials are a derived familiar form ADR-0107 refuses. The cost is stated there: this row
 * loses the six coloured initial tiles `chat_tab.png` draws.
 *
 * **On this surface it is always the poster, and that is the contract rather than a shortcut.**
 * `GET /challenges` borrows a handle and nothing else about a person — *"a Level, a band, an
 * area and a photograph are a card's, and a card is drawn on the detail read alone"*
 * ([ADR-0143](../../../../../docs/adr/0143-the-challenge-is-the-gate-and-the-card-is-recomputed-for-the-reader.md)).
 * So no `photoUrl` is passed, and `PlayerPhoto` falls back exactly as it does for a player
 * who has no photograph.
 *
 * **It is reached through `features/play`'s public surface rather than copied**, and that is a
 * tension worth stating rather than glossing.
 * [`the-loop-components.md`](../../../../../docs/specs/the-loop/the-loop-components.md) §4.3
 * says the parts kit's smallest members are shared *"through `shared/`"* — but §5, which is the
 * authoritative list of what moves, names **one** promotion and it is `courtPosterFor()`.
 * `PlayerPhoto` cannot follow it without dragging `PHOTO_PANEL`, whose own docstring
 * argues it belongs to the card rather than to the system. So the row imports the component,
 * because the alternative today is a second box with a second `× 0.33` in it and one person
 * drawn at two corners — the drift having **one owner** exists to prevent. #361's card block is
 * the third caller that would make the promotion worth its cost.
 *
 * ## The words are `shared/`'s and the numbers are not
 *
 * §15's list rule — *drop whole names, never shorten one* — went to
 * `shared/formatting/handleList.ts` beside `playerName()` when the conversation row became the
 * **second** kind of Chats row ([#363](https://github.com/Raketa02/Raketa/issues/363)): naming
 * a person already lives there, and naming several of them is the plural of it. The **numbers**
 * did not follow, and `challengeRowGeometry.ts` carries the three homes that were tried and are
 * wrong.
 *
 * ## The stripe is presence, never magnitude
 *
 * `amber`, full height, and drawn on exactly the rows whose line is a duration — so there is
 * **none on the organiser's row**, where the clock is live but is not theirs to clear. It is
 * `size.semanticBar`, which is 5.4's note bar at one owner, and it is **hidden from the
 * accessibility tree** because the sentence beside it already carries the fact. A bar encoding
 * how much time is left would be a second spelling of the duration, which is the exact failure
 * the design commits with *"lapses Tomorrow · 17:00 17:00"*.
 *
 * Coral is refused: [1.2](../../../../docs/design-system.md#12-one-accent-used-sparingly) lists
 * six coral uses and says *nothing else*, the tab badge holds the sixth, and a coral stripe on
 * every row with a live clock is coral on most of a section at once. 1.3 reads amber as *watch
 * this — reversible, not yet wrong*, which is exactly a live answer window.
 *
 * ## The tag is the ending's word, on the one ending that has one
 *
 * A **`Called off`** tag in the kit's *bad* variant — red on red-soft, 1.3's *ended badly* — at
 * the trailing edge of a `CALLED_OFF` row and of no other
 * ([ADR-0172](../../../../../docs/adr/0172-the-court-ends-with-the-game-the-ending-says-who-and-a-called-off-card-can-be-cleared.md)
 * §7). It carries the state word the Now card carries, in the colour meaning picks, where a live
 * row carries its amber stripe; the two never share a row, because a called-off court has no
 * clock of anybody's. **The face is who the sentence names** — `othersOn`'s rule for the whole
 * shelf — so a row reading *Diego Fabregat left* draws Diego and nobody else, and an ended row
 * is never blank.
 *
 * ## The organiser's row, while nobody has joined, swipes left to reveal one thing
 *
 * *Remove the challenge* ([#428](https://github.com/Raketa02/Raketa/issues/428),
 * [ADR-0165](../../../../../docs/adr/0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)
 * §4, §6) — on the conversation row's own shape, 6.15's `SwipeRow` around the card, and the act
 * behind the revealed button a **door** that draws its own sheet: `RemovalDoor`, this feature's,
 * so nothing is composed in from outside as the conversation row's act has to be. **Which rows
 * move is `mayRemove`'s answer** — the reader organised it, it is still being arranged, and nobody
 * besides them holds an accepted seat — read off the row the list already holds, so no read is
 * made to decide it and the same rule gates the challenge screen's button.
 *
 * ## And the `Called off` row the reader is still on swipes left to reveal one other thing
 *
 * *Remove this row*
 * ([ADR-0173](../../../../../docs/adr/0173-a-called-off-court-is-cleared-from-both-lists-by-one-act.md))
 * — the Now card's dismissal met from this list through a door of the challenge's own
 * (ADR-0175 §5), behind `DismissalDoor`, which draws no sheet because the act removes the court
 * from the reader's own two lists and nothing from the record. **Which rows move is
 * `mayDismiss`'s answer**: `CALLED_OFF`, and the reader holding a seat the court closed on — an
 * accepted one, or one still deciding; a leaver's own row left at once. Every other challenge row
 * reveals nothing: an invitee's on a live court, the organiser's once somebody has joined, any
 * other ending on its shelf — *no dead controls* (#324), and a row handed nothing to reveal does
 * not move at all.
 *
 * **A swipe is never the only path.** Either door is the card's `accessibilityAction`, under the
 * act's own word, and the card is what the removal's sheet returns focus to.
 */

import { router } from 'expo-router';
import { StyleSheet, Text, View, useWindowDimensions } from 'react-native';

import { sportLabel } from '@/features/onboarding/types';
import { handleLine } from '@/shared/formatting/handleList';
import { playerName } from '@/shared/formatting/playerName';
import { PlayerPhoto, PressableCard, SwipeRow, Tag, theme } from '@/shared/ui';

import { mayDismiss, mayRemove, seatName, type Challenge } from '../domain/challenge';
import { othersOn } from '../domain/challengeInbox';
import type { ActDoor } from '../hooks/useActDoor';

import { challengeRowLabel } from './challengeAccessibility';
import {
  CALLED_OFF_TAG,
  challengeRowLine,
  rowHasAClockOfYours,
  rowWearsTheTag,
} from './challengePresentation';
import { FACE_OVERLAP, ROW_FACE, handleBudget } from './challengeRowGeometry';
import { DismissalDoor } from './DismissalDoor';
import { RemovalDoor } from './RemovalDoor';

/**
 * Where a row goes. Both segments under `/chats` carry a static kind above the id, because a
 * challenge id and a conversation id are different ids of different things and `/chats/[id]`
 * for both is one segment a router cannot resolve and a reader cannot read.
 */
export const CHALLENGE_ROUTE = '/chats/challenge/[challengeId]';

export interface ChallengeRowProps {
  readonly challenge: Challenge;
  /** The reader. Every rule on this row is about *their* seat, so it is never derived here. */
  readonly playerId: string;
}

export function ChallengeRow({ challenge, playerId }: ChallengeRowProps) {
  const { width } = useWindowDimensions();

  const others = othersOn(challenge, playerId);
  const handles = others.map((seat) => playerName(seatName(seat)));

  const sport = sportLabel(challenge.sport);
  const line = challengeRowLine(challenge, playerId);
  const tag = rowWearsTheTag(challenge) ? CALLED_OFF_TAG : undefined;

  /** The card — the door to the challenge — around whatever act it is handed, or around nothing. */
  const card = (door?: ActDoor) => (
    <PressableCard
      ref={door?.control}
      accessibilityLabel={challengeRowLabel(handles, sport, line, tag)}
      accessibilityActions={door === undefined ? undefined : [door.action]}
      onAccessibilityAction={door?.onAccessibilityAction}
      onPress={() =>
        router.push({ pathname: CHALLENGE_ROUTE, params: { challengeId: challenge.challengeId } })
      }
      style={s.row}
    >
      <View style={s.faces}>
        {others.map((seat, at) => (
          <View key={seat.playerId} style={at === 0 ? undefined : s.behind}>
            <PlayerPhoto playerId={seat.playerId} box={{ kind: 'face', size: ROW_FACE }} />
          </View>
        ))}
      </View>

      <View style={s.body}>
        <Text style={s.handles} numberOfLines={1}>
          {handleLine(handles, handleBudget(width, others.length))}
        </Text>
        <Text style={s.line} numberOfLines={1}>
          {sport} · {line}
        </Text>
      </View>

      {rowHasAClockOfYours(challenge, playerId) ? (
        <View
          style={s.stripe}
          accessibilityElementsHidden
          importantForAccessibility="no-hide-descendants"
        />
      ) : null}

      {/* Inside the row's one element, so a listener hears its word at the end of the row's
          name rather than as a second element. */}
      {tag === undefined ? null : <Tag label={tag} variant="bad" />}
    </PressableCard>
  );

  if (mayRemove(challenge, playerId)) {
    return (
      <RemovalDoor challengeId={challenge.challengeId}>
        {(door) => (
          <SwipeRow reveal={{ label: door.label, onPress: door.open }}>{card(door)}</SwipeRow>
        )}
      </RemovalDoor>
    );
  }

  if (mayDismiss(challenge, playerId)) {
    return (
      <DismissalDoor challengeId={challenge.challengeId} gameId={challenge.gameId}>
        {(door) => (
          <SwipeRow reveal={{ label: door.label, onPress: door.open }}>{card(door)}</SwipeRow>
        )}
      </DismissalDoor>
    );
  }

  return card();
}

const s = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', gap: theme.space.md },
  faces: { flexDirection: 'row' },
  // Each face after the first is pulled back over the one before it, so a doubles court reads
  // as a group rather than as three separate people the row happens to list.
  behind: { marginLeft: -ROW_FACE * FACE_OVERLAP },
  body: { flex: 1, gap: theme.space.xxs },
  handles: { ...theme.type.cardTitle, color: theme.color.ink },
  line: { ...theme.type.tiny, color: theme.color.muted },
  stripe: {
    width: theme.size.semanticBar,
    alignSelf: 'stretch',
    borderRadius: theme.radius.bar,
    backgroundColor: theme.color.amber,
  },
});
