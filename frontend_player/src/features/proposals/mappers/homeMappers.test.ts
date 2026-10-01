import type { components } from '@/generated/schema';

import { toBookedGame, toHome } from './homeMappers';

type Wire = components['schemas'];

const tile = (extra: Partial<Wire['BookedTileSchema']> = {}): Wire['BookedTileSchema'] => ({
  player_id: 'p-1',
  is_you: false,
  name: 'Piotr Sowa',
  photo_id: null,
  photo_url: null,
  level: 2.95,
  paid: true,
  ...extra,
});

const homeGame = (extra: Partial<Wire['HomeGameSchema']> = {}): Wire['HomeGameSchema'] => ({
  booking_id: 'b-1',
  game_id: 'g-1',
  pool_id: 'group-1',
  sport: 'PADEL',
  kind: 'COMPETITIVE',
  status: 'BOOKED',
  needs_you: false,
  starts_at: '2026-10-03T14:00:00Z',
  club: { id: 'club-1', name: 'Bonarka Arena' },
  court_name: 'Court 2',
  sides: { yours: [tile({ player_id: 'me', is_you: true })], theirs: [tile()] },
  money: { share_grosze: 2800, paid: true, free_to_leave_until: '2026-10-02T14:00:00Z' },
  ...extra,
});

describe('toHome', () => {
  it('reads the badge, the clock and every card, the sides with their paid', () => {
    const home = toHome({ read_at: '2026-10-01T08:00:00Z', needing_you: 2, games: [homeGame()] });

    expect(home).toEqual({
      readAt: '2026-10-01T08:00:00Z',
      needingYou: 2,
      games: [
        {
          bookingId: 'b-1',
          gameId: 'g-1',
          groupId: 'group-1',
          sport: 'padel',
          kind: 'competitive',
          status: 'BOOKED',
          needsYou: false,
          startsAt: '2026-10-03T14:00:00Z',
          club: { id: 'club-1', name: 'Bonarka Arena' },
          courtName: 'Court 2',
          sides: {
            yours: [
              {
                playerId: 'me',
                isYou: true,
                isIn: false,
                paid: true,
                name: 'Piotr Sowa',
                level: 2.95,
              },
            ],
            theirs: [
              {
                playerId: 'p-1',
                isYou: false,
                isIn: false,
                paid: true,
                name: 'Piotr Sowa',
                level: 2.95,
              },
            ],
          },
          money: { shareGrosze: 2800, paid: true, freeToLeaveUntil: '2026-10-02T14:00:00Z' },
        },
      ],
    });
  });

  it('leaves off what the wire does not hold, rather than a null', () => {
    const [game] = toHome({
      read_at: '2026-10-01T08:00:00Z',
      needing_you: 0,
      games: [
        homeGame({
          club: { id: 'club-1', name: null },
          sides: {
            yours: [tile({ name: null, level: null, photo_url: null, paid: false })],
            theirs: [],
          },
          money: { share_grosze: 2800, paid: false, free_to_leave_until: null },
        }),
      ],
    }).games;

    expect(game?.club).toEqual({ id: 'club-1' });
    expect(game?.sides.yours[0]).toEqual({
      playerId: 'p-1',
      isYou: false,
      isIn: false,
      paid: false,
    });
    expect(game?.money).toEqual({ shareGrosze: 2800, paid: false });
  });

  it('drops a card in a sport this build cannot name, and keeps the rest', () => {
    const home = toHome({
      read_at: '2026-10-01T08:00:00Z',
      needing_you: 0,
      games: [homeGame({ sport: 'CURLING' as Wire['Sport'] }), homeGame({ booking_id: 'b-2' })],
    });

    expect(home.games.map((one) => one.bookingId)).toEqual(['b-2']);
  });
});

describe('toBookedGame', () => {
  const details = (
    extra: Partial<Wire['BookingDetailsResponse']> = {},
  ): Wire['BookingDetailsResponse'] => ({
    booking_id: 'b-1',
    game_id: 'g-1',
    pool_id: 'group-1',
    sport: 'PADEL',
    kind: 'FOR_FUN',
    read_at: '2026-10-03T08:00:00Z',
    status: 'BOOKED',
    needs_you: false,
    starts_at: '2026-10-03T14:00:00Z',
    ends_at: '2026-10-03T15:00:00Z',
    where: { id: 'club-1', name: 'Bonarka Arena', distance_km: 3.1 },
    court_name: 'Court 2',
    sides: { yours: [tile({ player_id: 'me', is_you: true })], theirs: [tile()] },
    money: { share_grosze: 2800, paid: true, free_to_leave_until: null },
    shows_forecast: true,
    check_in: { short_code: 'K7M2QX', qr_payload: 'RAKETA-CHECK-IN:1:b-1:me:K7M2QX' },
    ...extra,
  });

  it('reads the details, WHERE with its distance and the code for the desk', () => {
    expect(toBookedGame(details())).toMatchObject({
      bookingId: 'b-1',
      gameId: 'g-1',
      groupId: 'group-1',
      sport: 'padel',
      kind: 'forFun',
      readAt: '2026-10-03T08:00:00Z',
      endsAt: '2026-10-03T15:00:00Z',
      where: { id: 'club-1', name: 'Bonarka Arena', distanceKm: 3.1 },
      courtName: 'Court 2',
      money: { shareGrosze: 2800, paid: true },
      showsForecast: true,
      checkIn: { shortCode: 'K7M2QX', qrPayload: 'RAKETA-CHECK-IN:1:b-1:me:K7M2QX' },
    });
  });

  it('has no distance for a reader with no Location area, and no code off the day', () => {
    const game = toBookedGame(
      details({ where: { id: 'club-1', name: null, distance_km: null }, check_in: null }),
    );

    expect(game?.where).toEqual({ id: 'club-1' });
    expect(game).not.toHaveProperty('checkIn');
  });

  it('is nothing for a sport this build cannot name', () => {
    expect(toBookedGame(details({ sport: 'CURLING' as Wire['Sport'] }))).toBeUndefined();
  });
});
