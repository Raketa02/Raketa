/**
 * **Games** — the group's deck for the sport the page is on
 * ([#553](https://github.com/Raketa02/Raketa/issues/553); the screens A2), and, while it deals
 * nothing, the dark card a starting group has always drawn (play 14–17, 39; PRD #500 stories
 * 60–65, ADR-0183 §13).
 *
 * **The deck is `proposals`'**: the read, the switch, the stage, the card and the answers
 * (`GamesDeck`). What this tab hands it is what only the group page knows — the kind its switch
 * stands on, which Friends' switch shares (`gameIntent.store`), and the card to draw when this
 * segment deals nothing, which is about the group's roster rather than about any game.
 *
 * **The starting card** is `gamesCard`'s: *Just you so far*, *3 of 4* once others who play the sport
 * are in, or *Nothing picked right now* once the seats could be filled — the honest line while
 * nothing has been dealt. **Nothing picked right now gains *Post a game*** (Q96), a third door under
 * the link's two, which opens *Post a game* (#558) — the Fill in tab's own button, so the one door
 * has one drawing.
 *
 * Under the headline, **a seat per player the court takes**: the faces of the first members rated
 * in the sport, in joining order, and a dashed seat for every one still missing — one for tennis or
 * squash, three for padel or badminton when you are alone. Then what the app is waiting for, and
 * the link's two doors.
 *
 * **The seats are the court's seats, drawn in a row**: `SeatFace` — the face and the ring every
 * court in the app draws, the photograph or the poster behind it, the dashed ring for a seat
 * nobody is in — at `groupPage.seat`. The mocks draw circles; this app has no round face
 * (#338 refused an avatar), so they are the face's own box. The row is **one element** to a
 * listener, the court summary — *Padel, 1 of 4 seats filled.* — so this row and the Friends
 * court say a court's seats one way: the faces carry no name a sentence could not say better, and
 * the headline has already said who is missing. *3 of 4* is a count and is drawn in mono (1.4).
 */

import { StyleSheet, View } from 'react-native';

import { GamesDeck } from '@/features/proposals/types';
import { courtSeatCount, SeatFace, theme } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { Group } from '../domain/group';
import { gamesCard, rosterFor } from '../domain/groupPage';
import { useGameIntent } from '../store/gameIntent.store';

import { PostAGame } from './FillInTab';
import { gamesHeadline, gamesLine, seatsFilledLabel } from './groupsPresentation';
import { LinkCard } from './LinkCard';

const SEAT = theme.size.groupPage.seat;

export interface GamesTabProps {
  readonly group: Group;
  readonly sport: Sport;
  /** The card a notice opened the deck at (#559) — on top while it is dealt. */
  readonly onTop?: string;
}

export function GamesTab({ group, sport, onTop }: GamesTabProps) {
  const chosen = useGameIntent((state) => state.intent);
  const choose = useGameIntent((state) => state.choose);

  return (
    <GamesDeck
      groupId={group.id}
      sport={sport}
      chosen={chosen}
      onChoose={choose}
      empty={<StartingCard group={group} sport={sport} />}
      {...(onTop === undefined ? {} : { onTop })}
    />
  );
}

/** The group's own card while this segment deals nothing — see the module note. */
function StartingCard({ group, sport }: { readonly group: Group; readonly sport: Sport }) {
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
      {...(card.kind === 'nothing-picked' ? { foot: <PostAGame groupId={group.id} /> } : {})}
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
