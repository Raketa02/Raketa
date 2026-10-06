/**
 * **The squares under a Fill in row** — the posters of the people on the game, then a dashed square
 * per open seat ([#557](https://github.com/Raketa02/Raketa/issues/557); the screens A3; mocks 12, 13).
 *
 * The group page's own seat (`SeatFace` at `groupPage.seat`, the faces its starting cards draw): a
 * photograph or the poster behind it, ringed as seated; an open seat the dashed empty ring — with a
 * **?** in it on a rescue, whose seat is the reader's to take (A3.1), and plain on a yes's game,
 * where it is somebody's still to come (A3.2).
 *
 * **A poster is held for its player's record** (A3.1: *long-press a poster → record*): the hold, and
 * the standard `longpress` action for VoiceOver and TalkBack, which cannot hold — the Members list's
 * own shape. The reader's own poster opens nothing.
 */

import { Pressable, StyleSheet, Text, View } from 'react-native';

import { SeatFace, theme } from '@/shared/ui';

import type { DeckPerson } from '../domain/deck';

import { tileName } from './deckPresentation';
import { FILL_IN_COPY } from './fillInCopy';

const COPY = FILL_IN_COPY;
const SEAT = theme.size.groupPage.seat;

export interface FillInSquaresProps {
  readonly people: readonly DeckPerson[];
  /** Dashed squares after the posters. */
  readonly open: number;
  /** A rescue's open seats carry a **?**. */
  readonly question: boolean;
  /** A held poster — that player's record. */
  readonly onHold: (person: DeckPerson) => void;
}

export function FillInSquares({ people, open, question, onHold }: FillInSquaresProps) {
  return (
    <View style={s.squares}>
      {people.map((person) =>
        person.isYou ? (
          <View
            key={person.playerId}
            accessible
            accessibilityLabel={tileName(person)}
            testID={`fill-in-poster-${person.playerId}`}
          >
            <SeatFace
              size={SEAT}
              occupant={{ kind: 'you', playerId: person.playerId }}
              ring="seated"
            />
          </View>
        ) : (
          <Pressable
            key={person.playerId}
            accessibilityLabel={tileName(person)}
            accessibilityHint={COPY.holdHint}
            onLongPress={() => onHold(person)}
            accessibilityActions={[{ name: 'longpress' }]}
            onAccessibilityAction={(event) => {
              if (event.nativeEvent.actionName === 'longpress') onHold(person);
            }}
            hitSlop={theme.hit.peopleRow}
            style={({ pressed }) => (pressed ? s.pressed : undefined)}
            testID={`fill-in-poster-${person.playerId}`}
          >
            <SeatFace
              size={SEAT}
              occupant={{
                kind: 'player',
                playerId: person.playerId,
                ...(person.photoUrl === undefined ? {} : { photoUrl: person.photoUrl }),
              }}
              ring="seated"
            />
          </Pressable>
        ),
      )}
      {Array.from({ length: open }, (_, at) => (
        <View
          key={at}
          accessible
          accessibilityLabel={COPY.openSeatSpoken}
          testID="fill-in-open-seat"
        >
          <SeatFace size={SEAT} occupant={{ kind: 'empty' }} ring="empty">
            {question ? <Text style={s.question}>{COPY.openSeat}</Text> : null}
          </SeatFace>
        </View>
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  squares: { flexDirection: 'row', flexWrap: 'wrap', gap: theme.space.xs, flexShrink: 1 },
  question: { ...theme.type.cardTitle, color: theme.color.muted },
  // 6.6's photo-tile value.
  pressed: { opacity: 0.7 },
});
