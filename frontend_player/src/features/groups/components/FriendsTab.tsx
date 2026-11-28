/**
 * **The Friends tab** — the court a game with friends is built on, and the card under it once
 * every seat is filled ([#757](https://github.com/Rakieta02/Rakieta/issues/757); play 49–53; the
 * friends screens §7.1–§7.2; friends 7, 8).
 *
 * ```
 *   [ Games | Fill in | You’re in | Friends ⌄ ]   the page's tabs: this game's kind is the menu's
 *   ┌───────────── THEIR SIDE ─────────────┐
 *   │   [Mag]×                 [Ani]×      │   a seated friend: their face, *nickname level*, a ×
 *   │ ──────────────────────────────────── │
 *   │   [You]                  [ + ]       │   an empty seat: a dashed ring and a white plus
 *   └───────────── YOUR SIDE ──────────────┘
 *             Seat 1 more friend                with a seat open — and no card
 *              [ + Friends ]
 *   ┌ the friends card ─────────────────────┐  every seat filled: `proposals`' card
 * ```
 *
 * - **The kind is picked in the Friends tab's menu** (`TabMenu`, #861, PRD #859; tab menu mocks 2
 *   and 4), not on a row above the court: the court sits right under the tabs, at its own size. It
 *   sets **this game's kind only** (`friendsGame.store`) — never the Games deck's kind, never the
 *   Play intent (ADR-0202; the README's defaults). The menu is the page's, drawn over the page; a
 *   pick asks this tab (`FriendsTabHandle`), because a kind changed keeps the sides the court shows
 *   (`chooseKind`), and only the court knows what it shows.
 * - **The court** is `Court` at `court.build`, a seat 60. The reader stands in the first seat,
 *   *You 2,71*. **A seated friend** is their face, the seat's three letters over their Level, and
 *   6.9's remove control at its corner (7.12's seat-clear badge): the × takes them off. **An empty
 *   seat** is a dashed ring and a white plus, and opens the picker, as *+ Friends* does.
 * - **A swap**: tap one friend's face — its ring turns volt, *picked for a swap* (`seatRing`) — then
 *   another's, and the two trade seats; tap the first again to let it go. The reader's own seat
 *   never moves: they stand first on their side, as the card reads it.
 * - **Every seat filled**: the card (`proposals`' `FriendsCard`) under the court, in the page's
 *   scroller with it (friends 8). **The court draws the card's sides**: Done asks the card for the
 *   evenest ones and the court follows its answer; a swap asks again with the sides the player
 *   stood (`friendsLineUp`). **A seat open**: *Seat 1 more friend*, *+ Friends*, and no card.
 * - **Sent** (#759): the card's *Send game and pay* books the court, and the court is empty again —
 *   the game is in Your games on Home.
 *
 * **Side labels are drawn where the mocks draw them — padel and badminton.** Squash has no halves:
 * both players stand on one. On tennis the far seat stands at the top centre (28 of 132), which is
 * where the label would be written. **Every seat still says its side to a listener**, in the seat's
 * own sentences over its own rule (`seatPlaces`, `seatLabel`, both `shared/vocabulary`'s).
 *
 * **The faces are the picker's read** (`friends`' `useFriendsIn`) — the same list, so a face on the
 * court is the row it was picked from. **A friend no longer one leaves an empty seat** once that
 * list is read again (the mechanics §7.5): a card refused for one of the four, or for a Level gone,
 * reads it again.
 */

import { router } from 'expo-router';
import { useImperativeHandle, useState, type Ref } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { useReaderId } from '@/features/auth/types';
import { levelIn, type Friend } from '@/features/friends/types';
import { useSkillRatings } from '@/features/onboarding/types';
import { useOwnFace } from '@/features/player_record/types';
import { FriendsCard, type CardPerson } from '@/features/proposals/types';
import {
  Button,
  Court,
  courtSeatCount,
  courtSeatSize,
  PlusOnMedia,
  SeatCaption,
  SeatFace,
  seatBox,
  theme,
} from '@/shared/ui';
import { seatPlaces, type LineUpSeat, type SeatPlace } from '@/shared/vocabulary/seatPlace';
import type { Sport } from '@/shared/vocabulary/sport';

import type { Group } from '../domain/group';
import { openSeatsOf, seatedOf, type FriendSeat } from '../domain/friendsLineUp';
import { faceIn, rosterFor, type GameIntent } from '../domain/groupPage';
import { useFriendsGameOn } from '../hooks/useFriendsGame';

import { groupFriendsRoute } from './groupRoutes';
import { GROUPS_COPY } from './groupsCopy';
import {
  emptySeatLabel,
  friendSeatLabel,
  seatMoreLine,
  seatsFilledLabel,
  takeOffLabel,
  yourSeatLabel,
} from './groupsPresentation';

const COPY = GROUPS_COPY.friends;

const WIDTH = theme.size.court.build;

/** The courts the mocks print *YOUR SIDE* / *THEIR SIDE* on — see the module note. */
const LABELLED_SIDES: ReadonlySet<Sport> = new Set(['padel', 'badminton']);

/** The court's seats as their places read them: the reader, then each seat beside them. */
function lineUpSeats(shown: readonly FriendSeat[]): readonly LineUpSeat[] {
  return [
    { kind: 'you' },
    ...shown.map((seat) => ({ kind: seat === null ? 'empty' : 'player' }) as const),
  ];
}

/** What the page's menu asks of the court — see the module note. */
export interface FriendsTabHandle {
  /** Make the game being built this kind, keeping the sides the court shows. */
  readonly chooseKind: (kind: GameIntent) => void;
}

export function FriendsTab({
  group,
  sport,
  handle,
}: {
  readonly group: Group;
  readonly sport: Sport;
  readonly handle?: Ref<FriendsTabHandle>;
}) {
  const readerId = useReaderId();
  const level = useSkillRatings().data?.find((rating) => rating.sport === sport)?.level;

  const seats = courtSeatCount(sport);
  const size = courtSeatSize(WIDTH);
  const game = useFriendsGameOn(group.id, sport, seats - 1);
  const { shown } = game;
  const open = openSeatsOf(shown);

  // The face picked for a swap — dropped if they leave the court.
  const [picked, setPicked] = useState<string>();
  const swapping = picked !== undefined && shown.includes(picked) ? picked : undefined;

  const onFace = (playerId: string) => {
    if (swapping === undefined) return setPicked(playerId);
    setPicked(undefined);
    if (swapping !== playerId) game.swap(swapping, playerId);
  };
  const onTakeOff = (playerId: string) => {
    setPicked(undefined);
    game.takeOff(playerId);
  };
  const openFriends = () => {
    setPicked(undefined);
    router.push(groupFriendsRoute(group.id, sport));
  };

  // The reader's own photograph: off the group's roster when they are among the sport's first
  // rated — the read the page already holds — and off their own record when they joined after a
  // court's worth, which is the one case that costs a read (`useOwnFace`, asked only then).
  const rostered = faceIn(rosterFor(group, sport), readerId);
  const own = useOwnFace(rostered === undefined ? readerId : undefined);
  const photoUrl = rostered?.photoUrl ?? own.photoUrl;

  const places = seatPlaces(lineUpSeats(shown));
  const friendOf = (playerId: string) => game.friends?.find((one) => one.playerId === playerId);
  const people: readonly CardPerson[] = seatedOf(shown).map((playerId) => {
    const friend = friendOf(playerId);
    const known = levelIn(friend, sport)?.level;
    return {
      playerId,
      name: friend?.nickname ?? '',
      ...(known === undefined ? {} : { level: known }),
    };
  });

  // The page's menu picks the kind; the court keeps the sides it shows as it changes.
  useImperativeHandle(handle, () => ({ chooseKind: game.chooseKind }));

  return (
    <View style={s.tab}>
      <Court
        sport={sport}
        width={WIDTH}
        summary={seatsFilledLabel(sport, seats - open, seats)}
        {...(LABELLED_SIDES.has(sport)
          ? { sideLabels: [COPY.yourSide, COPY.theirSide] as const }
          : {})}
      >
        <View
          accessible
          accessibilityLabel={yourSeatLabel(places[0] ?? 'YOUR_SIDE', level)}
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
          <SeatCaption size={size} name={COPY.you} {...(level === undefined ? {} : { level })} />
        </View>
        {shown.map((seat, at) => {
          const place = places[at + 1] ?? 'THEIR_SIDE';
          if (seat === null) {
            return <EmptySeat key={at} place={place} size={size} onPress={openFriends} />;
          }
          const friend = friendOf(seat);
          return (
            <FriendInSeat
              key={at}
              playerId={seat}
              {...(friend === undefined ? {} : { friend })}
              level={levelIn(friend, sport)?.level}
              place={place}
              size={size}
              selected={swapping === seat}
              swapping={swapping !== undefined}
              canSwap={seatedOf(shown).length > 1}
              onPress={() => onFace(seat)}
              onTakeOff={() => onTakeOff(seat)}
            />
          );
        })}
      </Court>

      {open > 0 ? (
        <>
          <Text style={s.more}>{seatMoreLine(open)}</Text>
          <Button
            label={COPY.addFriends}
            accessibilityLabel={COPY.addFriendsLabel}
            variant="secondary"
            onPress={openFriends}
          />
        </>
      ) : game.cardAsk === undefined ? null : (
        <FriendsCard
          groupId={group.id}
          sport={sport}
          ask={game.cardAsk}
          people={people}
          readerId={readerId}
          yourLevel={level}
          onPickCourt={game.pickCourt}
          onCourtGone={game.courtGone}
          onSent={game.sent}
        />
      )}
    </View>
  );
}

/** An open seat: a dashed ring and a white plus, opening the picker. */
function EmptySeat({
  place,
  size,
  onPress,
}: {
  readonly place: SeatPlace;
  readonly size: number;
  readonly onPress: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={emptySeatLabel(place)}
      accessibilityHint={COPY.emptySeatHint}
      onPress={onPress}
      style={({ pressed }) => [seatBox(size), pressed ? s.pressed : undefined]}
    >
      <SeatFace size={size} occupant={{ kind: 'empty' }} ring="empty">
        <PlusOnMedia />
      </SeatFace>
    </Pressable>
  );
}

/**
 * **A seated friend** — the face, a press for the swap, and the × beside it as a sibling, never
 * inside the face's press, so each is its own button to a listener.
 */
function FriendInSeat({
  playerId,
  friend,
  level,
  place,
  size,
  selected,
  swapping,
  canSwap,
  onPress,
  onTakeOff,
}: {
  readonly playerId: string;
  readonly friend?: Friend;
  readonly level: number | undefined;
  readonly place: SeatPlace;
  readonly size: number;
  readonly selected: boolean;
  readonly swapping: boolean;
  readonly canSwap: boolean;
  readonly onPress: () => void;
  readonly onTakeOff: () => void;
}) {
  const name = friend?.nickname ?? '';
  return (
    <View style={seatBox(size)}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={friendSeatLabel(place, name, level)}
        accessibilityHint={
          canSwap ? (swapping && !selected ? COPY.swapWithHint : COPY.swapHint) : undefined
        }
        accessibilityState={{ selected, disabled: !canSwap }}
        disabled={!canSwap}
        onPress={onPress}
        style={({ pressed }) => [seatBox(size), pressed ? s.pressed : undefined]}
        testID={`seat-${playerId}`}
      >
        <SeatFace
          size={size}
          occupant={{
            kind: 'player',
            playerId,
            ...(friend?.photoUrl === undefined ? {} : { photoUrl: friend.photoUrl }),
          }}
          ring={selected ? 'selected' : 'seated'}
        />
        <SeatCaption size={size} name={name} {...(level === undefined ? {} : { level })} />
      </Pressable>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={takeOffLabel(place, name)}
        onPress={onTakeOff}
        hitSlop={theme.hit.photoRemove}
        style={({ pressed }) => [s.clear, pressed ? s.pressed : undefined]}
      >
        <Text style={s.clearMark} accessibilityElementsHidden importantForAccessibility="no">
          {'×'}
        </Text>
      </Pressable>
    </View>
  );
}

const s = StyleSheet.create({
  tab: { alignItems: 'center', gap: theme.space.lg },
  // 6.6's photo-tile value, as a court seat's own press is.
  pressed: { opacity: 0.7 },
  more: { ...theme.type.rlLabel, color: theme.color.muted },
  // 7.12's seat-clear badge — 6.9's remove square, at the face's top-right corner, half over it:
  // solid night, a white mark, the tag's radius, grown to 44 by its own slop.
  clear: {
    position: 'absolute',
    top: -theme.size.photoTile.remove / 2,
    right: -theme.size.photoTile.remove / 2,
    width: theme.size.photoTile.remove,
    height: theme.size.photoTile.remove,
    borderRadius: theme.radius.tag,
    backgroundColor: theme.color.night,
    alignItems: 'center',
    justifyContent: 'center',
  },
  clearMark: { ...theme.type.h2, color: theme.color.surface },
});
