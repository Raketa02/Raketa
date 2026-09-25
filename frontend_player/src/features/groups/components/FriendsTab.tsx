/**
 * **Friends, while a group is starting** — the court a game with friends would be built on, and the
 * way to the Friends screen (play 49–53; PRD #500 stories 68–70).
 *
 * - **Competitive · For fun**, the game's intent — held in memory while the app is open
 *   (`gameIntent.store`, ADR-0188 §5), and nothing reads it yet.
 * - **The court for the sport the page is on** — `Court`, the one court drawing every surface in
 *   the app shares, at `court.build`, the width a seat is 46 at. The reader stands in the first
 *   seat, their face labelled *You 2,71*; every other seat is **empty and pressable**, a dashed
 *   ring with a white plus, and opens the Friends screen. The drawing is `play`'s — `SeatFace` and
 *   `SeatCaption` through its public surface, as `plans` and `games` read them — restyled only in
 *   the plus, which is white on this court (`PlusOnMedia`) because volt on a court means *picked
 *   for a swap*.
 * - **+ Friends**, the same door as an empty seat.
 *
 * **Side labels are drawn where the mocks draw them — padel and badminton.** Squash has no halves:
 * both players stand on one. On tennis the far seat stands at the top centre (28 of 132), which is
 * where the label would be written. **Every seat still says its side to a listener**, in play's own
 * sentences over play's own rule (`seatPlaces`, `seatLabel`): a side is a team rather than a half
 * of the drawing, so squash's other seat is *their side* too, and where a seat is does not depend
 * on whether the court prints it.
 */

import { router } from 'expo-router';
import { Pressable, StyleSheet, View } from 'react-native';

import { useSkillRatings } from '@/features/onboarding/types';
import { SeatCaption, SeatFace, seatBox, seatPlaces, type BuildSeat } from '@/features/play/types';
import { useOwnFace } from '@/features/player_record/types';
import {
  Button,
  Court,
  courtSeatCount,
  courtSeatSize,
  PlusOnMedia,
  Segment,
  theme,
} from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import type { Group } from '../domain/group';
import { faceIn, rosterFor, type GameIntent } from '../domain/groupPage';
import { useReaderId } from '../hooks/useReaderId';
import { useGameIntent } from '../store/gameIntent.store';

import { groupFriendsRoute } from './groupRoutes';
import { GROUPS_COPY } from './groupsCopy';
import { emptySeatLabel, seatsFilledLabel, yourSeatLabel } from './groupsPresentation';

const COPY = GROUPS_COPY.friends;

const WIDTH = theme.size.court.build;

/** The courts the mocks print *YOUR SIDE* / *THEIR SIDE* on — see the module note. */
const LABELLED_SIDES: ReadonlySet<Sport> = new Set(['padel', 'badminton']);

/** The line-up this court draws: the reader, and every other seat still open. */
function lineUp(seats: number): readonly BuildSeat[] {
  return Array.from({ length: seats }, (_, at) => (at === 0 ? { kind: 'you' } : { kind: 'empty' }));
}

export function FriendsTab({ group, sport }: { readonly group: Group; readonly sport: Sport }) {
  const intent = useGameIntent((state) => state.intent);
  const choose = useGameIntent((state) => state.choose);
  const readerId = useReaderId();
  const level = useSkillRatings().data?.find((rating) => rating.sport === sport)?.level;

  const seats = courtSeatCount(sport);
  const size = courtSeatSize(WIDTH);
  const places = seatPlaces(lineUp(seats));

  // The reader's own photograph: off the group's roster when they are among the sport's first
  // rated — the read the page already holds — and off their own record when they joined after a
  // court's worth, which is the one case that costs a read (`useOwnFace`, asked only then).
  const rostered = faceIn(rosterFor(group, sport), readerId);
  const own = useOwnFace(rostered === undefined ? readerId : undefined);
  const photoUrl = rostered?.photoUrl ?? own.photoUrl;

  const openFriends = () => router.push(groupFriendsRoute(group.id, sport));

  const intents: readonly { key: GameIntent; label: string }[] = [
    { key: 'competitive', label: COPY.competitive },
    { key: 'forFun', label: COPY.forFun },
  ];

  return (
    <View style={s.tab}>
      <Segment options={intents} selected={intent} onSelect={choose} style={s.intent} />

      <Court
        sport={sport}
        width={WIDTH}
        summary={seatsFilledLabel(sport, 1, seats)}
        {...(LABELLED_SIDES.has(sport)
          ? { sideLabels: [COPY.yourSide, COPY.theirSide] as const }
          : {})}
      >
        {places.map((place, seat) =>
          seat === 0 ? (
            <View
              key={seat}
              accessible
              accessibilityLabel={yourSeatLabel(place, level)}
              style={seatBox(size)}
            >
              <SeatFace
                size={size}
                occupant={
                  readerId === undefined
                    ? { kind: 'you' }
                    : {
                        kind: 'player',
                        playerId: readerId,
                        ...(photoUrl === undefined ? {} : { photoUrl }),
                      }
                }
                ring="seated"
              />
              <SeatCaption
                size={size}
                name={COPY.you}
                {...(level === undefined ? {} : { level })}
              />
            </View>
          ) : (
            <Pressable
              key={seat}
              accessibilityRole="button"
              accessibilityLabel={emptySeatLabel(place)}
              accessibilityHint={COPY.emptySeatHint}
              onPress={openFriends}
              style={({ pressed }) => [seatBox(size), pressed ? s.pressed : undefined]}
            >
              <SeatFace size={size} occupant={{ kind: 'empty' }} ring="empty">
                <PlusOnMedia />
              </SeatFace>
            </Pressable>
          ),
        )}
      </Court>

      <Button
        label={COPY.addFriends}
        accessibilityLabel={COPY.addFriendsLabel}
        variant="secondary"
        onPress={openFriends}
      />
    </View>
  );
}

const s = StyleSheet.create({
  tab: { alignItems: 'center', gap: theme.space.lg },
  intent: { alignSelf: 'center', minWidth: WIDTH },
  // 6.6's photo-tile value, as a court seat's own press is.
  pressed: { opacity: 0.7 },
});
