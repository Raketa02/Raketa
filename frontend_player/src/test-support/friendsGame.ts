/**
 * **A friends game as the wire answers it** — the fixtures the friends game suites build on
 * ([#759](https://github.com/Rakieta02/Rakieta/issues/759),
 * [#760](https://github.com/Rakieta02/Rakieta/issues/760)).
 *
 * **An invitation** waits on the reader: tomek.k's Saturday 10:00 at Ogrody 33, Court 3, 25 zł a
 * seat, magda.p In, ania.k still to answer, the reader's 24 hours ending 1 h 35 after Home's read.
 * **The reader's own game**, sent by them on Home's booked game (`home.ts`): piotr.s In, ines.d
 * still to answer, bartek.l can't make it. Each suite moves only what it is about off these.
 */

import { BARTEK, INES, PIOTR } from './home';
import { GATE_USER } from './onboardingRouter';
import type { Wire } from './transport';

export const ME = GATE_USER.id;
export const TOMEK = 'f0000000-0000-4000-8000-000000000001';
export const ANIA = 'f0000000-0000-4000-8000-000000000002';
export const MAGDA = 'f0000000-0000-4000-8000-000000000003';
export const INVITED = 'b0000000-0000-4000-8000-000000000012';
/** The group every booked game of `home.ts` is in — its pool, filed under the group's id. */
export const GROUP = '3f2b8c1e-0000-4000-8000-0000000000d1';

/** Saturday 3 October, 10:00 in Warsaw. */
export const SATURDAY_10 = '2026-10-03T08:00:00Z';
/** The reader's 24 hours end 1 h 35 after the read. */
export const ANSWER_BY = '2026-10-01T09:35:00Z';

export const PADEL_RATING: Wire['RatingResponse'] = {
  sport: 'PADEL',
  mu: 2.71,
  sigma: 0.62,
  confidence: 28,
  range: { low: 2.09, high: 3.33 },
  band: { name: 'Established', lower: 2.7, upper: 3.8 },
  status: 'initial_estimate',
  engine_version: 'racketskill-v3',
  updated_at: '2026-08-14T09:00:00Z',
};

export const VISA: Wire['SavedMethodSchema'] = { brand: 'visa', last_four: '4312', wallet: null };

/** One seat — held by nobody to act on unless the suite says so. */
export function seat(
  playerId: string,
  state: Wire['SeatState'],
  extra: Partial<Wire['FriendsSeatSchema']> = {},
): Wire['FriendsSeatSchema'] {
  return {
    player_id: playerId,
    state,
    waiting_until: null,
    can_invite: false,
    can_open: false,
    ...extra,
  };
}

export function tile(
  playerId: string,
  nickname: string,
  extra: Partial<Wire['BookedTileSchema']> = {},
): Wire['BookedTileSchema'] {
  return {
    player_id: playerId,
    is_you: false,
    nickname,
    photo_id: null,
    photo_url: null,
    level: 2.7,
    paid: false,
    friend: true,
    ...extra,
  };
}

/** tomek.k's game, as it reads to the reader still invited: magda.p In, ania.k still to answer. */
export function invitedGame(
  extra: Partial<Wire['FriendsGameSchema']> = {},
): Wire['FriendsGameSchema'] {
  return {
    sender_id: TOMEK,
    sender_nickname: 'tomek.k',
    you_are_the_sender: false,
    pay_mode: 'SPLIT_THE_COST',
    seats: [
      seat(TOMEK, 'IN'),
      seat(ME, 'WAITING', { waiting_until: ANSWER_BY }),
      seat(MAGDA, 'IN'),
      seat(ANIA, 'WAITING', { waiting_until: '2026-10-01T20:00:00Z' }),
    ],
    friends_in: 1,
    friends_seated: 3,
    your_invitation_until: ANSWER_BY,
    can_call_off: false,
    ...extra,
  };
}

export function invitation(
  extra: Partial<Wire['HomeFriendsGameSchema']> = {},
): Wire['HomeFriendsGameSchema'] {
  return {
    booking_id: INVITED,
    pool_id: GROUP,
    sport: 'PADEL',
    kind: 'COMPETITIVE',
    starts_at: SATURDAY_10,
    club: { id: 'c0000000-0000-4000-8000-000000000033', name: 'Ogrody 33' },
    court_name: 'Court 3',
    indoor: true,
    share_grosze: 2500,
    sides: {
      yours: [tile(ME, 'ada', { is_you: true, friend: false }), tile(TOMEK, 'tomek.k')],
      theirs: [tile(MAGDA, 'magda.p'), tile(ANIA, 'ania.k')],
    },
    friends_game: invitedGame(),
    ...extra,
  };
}

/** The reader's own game, sent: piotr.s In, ines.d still to answer, bartek.l can't make it. */
export function sentGame(
  extra: Partial<Wire['FriendsGameSchema']> = {},
): Wire['FriendsGameSchema'] {
  return {
    sender_id: ME,
    sender_nickname: GATE_USER.nickname ?? 'ada',
    you_are_the_sender: true,
    pay_mode: 'SPLIT_THE_COST',
    seats: [
      seat(ME, 'IN'),
      seat(PIOTR, 'IN'),
      seat(INES, 'WAITING', { waiting_until: '2026-10-01T20:00:00Z' }),
      seat(BARTEK, 'CANT_MAKE_IT'),
    ],
    friends_in: 1,
    friends_seated: 3,
    your_invitation_until: null,
    can_call_off: true,
    ...extra,
  };
}
