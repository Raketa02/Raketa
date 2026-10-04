/**
 * **Games, while a group is starting** — one dark card for the sport the page is filtered by
 * (play 14–17, 39; PRD #500 stories 60–65, ADR-0183 §13).
 *
 * The headline is `gamesCard`'s: *Just you so far*, *3 of 4* once others who play the sport are
 * in, or *Nothing picked right now* once the seats could be filled — the honest line while a group
 * cannot pick games. Under it, **a seat per player the court takes**: the faces of the first
 * members rated in the sport, in joining order, and a dashed seat for every one still missing —
 * one for tennis or squash, three for padel or badminton when you are alone. Then what the app is
 * waiting for, and the link's two doors.
 *
 * **The seats are the court's seats, drawn in a row**: `SeatFace` — the face and the ring every
 * court in the app draws, the photograph or the poster behind it, the dashed ring for a seat
 * nobody is in — at `groupPage.seat`. The mocks draw circles; this app has no round face
 * (#338 refused an avatar), so they are the face's own box. The row is **one element** to a
 * listener, play's court summary — *Padel, 1 of 4 seats filled.* — so this row and the Friends
 * court say a court's seats one way: the faces carry no name a sentence could not say better, and
 * the headline has already said who is missing. *3 of 4* is a count and is drawn in mono (1.4).
 */

import { StyleSheet, View } from 'react-native';

import { SeatFace } from '@/features/play/types';
import { courtSeatCount, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { Group } from '../domain/group';
import { gamesCard, rosterFor } from '../domain/groupPage';

import { gamesHeadline, gamesLine, seatsFilledLabel } from './groupsPresentation';
import { LinkCard } from './LinkCard';

const SEAT = theme.size.groupPage.seat;

export function GamesTab({ group, sport }: { readonly group: Group; readonly sport: Sport }) {
  const card = gamesCard(rosterFor(group, sport), courtSeatCount(sport));
  const empty = card.seats - card.faces.length;
  const line = gamesLine(card, sport, group.homeClub.name);

  return (
    <LinkCard
      group={group}
      headline={gamesHeadline(card)}
      // *3 of 4* is a count, and a count is mono (1.4); the other two headlines are words.
      headlineIsCount={card.kind === 'filling'}
      {...(line === undefined ? {} : { line })}
    >
      <View
        accessible
        accessibilityLabel={seatsFilledLabel(sport, card.faces.length, card.seats)}
        style={s.seats}
      >
        {card.faces.map((face) => (
          <View key={face.playerId} testID={`games-face-${face.playerId}`}>
            <SeatFace
              size={SEAT}
              occupant={{
                kind: 'player',
                playerId: face.playerId,
                ...(face.photoUrl === undefined ? {} : { photoUrl: face.photoUrl }),
              }}
              ring="seated"
            />
          </View>
        ))}
        {Array.from({ length: empty }, (_, at) => (
          <View key={at} testID="games-empty-seat">
            <SeatFace size={SEAT} occupant={{ kind: 'empty' }} ring="empty" />
          </View>
        ))}
      </View>
    </LinkCard>
  );
}

const s = StyleSheet.create({
  seats: { flexDirection: 'row', justifyContent: 'center', gap: theme.space.xs },
});
