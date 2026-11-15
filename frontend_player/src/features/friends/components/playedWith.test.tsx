/**
 * **PLAYED WITH on a booked game's result, walked through the real route tree**
 * ([#754](https://github.com/Raketa02/Raketa/issues/754), PRD #743 story 15; the friends screens
 * §3; Q26).
 *
 * The card lists the others on the game in Members' rows with Members' pills — *friend*, **+ Add**,
 * *request sent*, **Accept** — between the score and *How were they?*, after a Competitive game
 * and a For fun one alike, and is hidden once every one of them is the reader's friend. **+ Add**
 * asks from the result, naming the game's group and sport, and the row turns on the booking read
 * again; the rest of a row opens the record.
 */

import { fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import { RECORD_TITLE } from '@/features/player_record/types';
import { STARS_HEADING } from '@/features/sportsmanship/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { BOOKING, bookedSides, bookingDetails, homeGame, stubHomeGames } from '@/test-support/home';
import {
  FRIEND_REQUESTS_PATH,
  GATE_USER,
  bookingPath,
  launchSignedIn,
  stubGames,
  stubGate,
  stubOwnRecord,
  stubSportsmanship,
} from '@/test-support/onboardingRouter';
import { servedReliability } from '@/test-support/playerRecord';
import { installTransport, json, type Transport, type Wire } from '@/test-support/transport';

import { FRIENDS_COPY, acceptLabel, addLabel } from './friendsCopy';

const COPY = FRIENDS_COPY;

const GAME = '8f14e45f-ceea-467a-9dd1-4bd9c39d4a58';
const POOL = 'a0000000-0000-4000-8000-000000000011';
const READ_AT = '2026-10-03T16:00:00Z';
const RESULT_ROUTE = `/booking/${BOOKING}/result`;

const EWA = 'e0000000-0000-4000-8000-000000000001';
const MAGDA = 'e0000000-0000-4000-8000-000000000002';
const ANIA = 'e0000000-0000-4000-8000-000000000003';

type Relation = Wire['FriendRelation'];

function tile(id: string, name: string, level: number, friend = false): Wire['BookedTileSchema'] {
  return {
    player_id: id,
    is_you: false,
    nickname: name,
    photo_id: null,
    photo_url: null,
    level,
    paid: true,
    friend,
  };
}

/** Saturday's game: you + Ewa against Magda + Ania. */
function sides(): Wire['BookedSidesSchema'] {
  const you = bookedSides().yours[0]!;
  return {
    yours: [you, tile(EWA, 'ewa.m', 2.6, true)],
    theirs: [tile(MAGDA, 'magda.p', 2.66), tile(ANIA, 'ania.k', 2.68)],
  };
}

/** The game behind the booking, settled — so a star card can stand under the score. */
function settled(kind: Wire['GameSchema']['kind'] = 'COUNTED'): Wire['GameSchema'] {
  return {
    game_id: GAME,
    booking_id: BOOKING,
    sport: 'PADEL',
    kind,
    standing: 'CONFIRMED',
    planned_at: '2026-10-01T09:00:00Z',
    played_at: '2026-10-03T15:00:00Z',
    score: { sets: [{ a: 6, b: 4 }] },
    outcome: 'WIN',
    seats: [
      { side: 'A', player_id: GATE_USER.id, nickname: GATE_USER.nickname ?? 'ada' },
      { side: 'A', player_id: EWA, nickname: 'ewa.m' },
      { side: 'B', player_id: MAGDA, nickname: 'magda.p' },
      { side: 'B', player_id: ANIA, nickname: 'ania.k' },
    ],
    proposals: [],
    attendance: [],
  };
}

/**
 * **The booking, read from a small server** — `played_with` follows the relations, so an ask from
 * the card turns the row on the read that follows it.
 */
function bookingServer(
  initially: Readonly<Record<string, Relation>> = {
    [EWA]: 'FRIEND',
    [MAGDA]: 'NONE',
    [ANIA]: 'SENT',
  },
  kind: Wire['BookingDetailsResponse']['kind'] = 'COMPETITIVE',
) {
  const relations = new Map(Object.entries(initially));
  const details = () =>
    bookingDetails({
      game_id: GAME,
      pool_id: POOL,
      kind,
      status: 'COUNTED',
      sides: sides(),
      leaving: null,
      shows_forecast: false,
      played_with: [EWA, MAGDA, ANIA].map((id) => ({
        player_id: id,
        relation: relations.get(id) ?? 'NONE',
      })),
    });
  transport.on('GET', bookingPath(BOOKING), () => json(details()));
  transport.on('POST', FRIEND_REQUESTS_PATH, (request) => {
    const { player_id: id } = request.body as Wire['AskToBeFriendsRequest'];
    relations.set(id, 'SENT');
    return json<Wire['RelationResponse']>({ relation: 'SENT' });
  });
  for (const [id, name] of [
    [EWA, 'ewa.m'],
    [MAGDA, 'magda.p'],
    [ANIA, 'ania.k'],
  ] as const) {
    transport.on('GET', `/api/v1/players/${id}/record`, () =>
      json<Wire['PlayerRecordResponse']>({
        is_self: false,
        relation: relations.get(id) ?? 'NONE',
        can_add_friend: true,
        nickname: name,
        photos: [],
        area_code: 'A+050612+0019938',
        social_tags: [],
        sports: [{ sport: 'PADEL', level: 2.66, band: 'Established' }],
        reliability: servedReliability({ player_score: 95, is_new: false }),
      }),
    );
  }
  return details;
}

const PADEL_RATING: Wire['RatingResponse'] = {
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

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [PADEL_RATING], hasPlayerProfile: true });
  stubOwnRecord(transport);
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** Saturday's result screen, with this Game behind the booking. */
async function openResult(game: Wire['GameSchema'] = settled()) {
  stubHomeGames(transport, [homeGame({ game_id: GAME })]);
  stubGames(transport, [game], READ_AT);
  await launchSignedIn(RESULT_ROUTE);
  await waitFor(() => expect(screen).toHavePathname(RESULT_ROUTE));
  // A counted game's table is *The result*, a For fun one's *The score*.
  await screen.findByLabelText(/^The (result|score)\./);
}

const card = () => screen.queryByTestId('played-with');
const row = (id: string) => within(screen.getByTestId(`friend-row-${id}`));

/** Every text and spoken label on screen, in the order the tree draws them. */
function drawnInOrder(): string[] {
  const out: string[] = [];
  const walk = (node: unknown) => {
    if (node === null || typeof node !== 'object') {
      if (typeof node === 'string') out.push(node);
      return;
    }
    if (Array.isArray(node)) {
      node.forEach(walk);
      return;
    }
    const { props, children } = node as {
      props?: { accessibilityLabel?: unknown };
      children?: unknown;
    };
    if (typeof props?.accessibilityLabel === 'string') out.push(props.accessibilityLabel);
    walk(children ?? null);
  };
  walk(screen.toJSON());
  return out;
}

describe('PLAYED WITH', () => {
  it('lists the others in Members’ rows with Members’ pills', async () => {
    bookingServer();
    await openResult();

    expect(await screen.findByText(COPY.playedWith.heading)).toBeTruthy();
    expect(row(EWA).getByText(COPY.members.friend)).toBeTruthy();
    expect(row(MAGDA).getByRole('button', { name: addLabel('magda.p') })).toBeTruthy();
    expect(row(ANIA).getByText(COPY.members.sent)).toBeTruthy();
    // Members' row: the name over the sport's line.
    expect(row(MAGDA).getByText('magda.p')).toBeTruthy();
    expect(row(MAGDA).getByText('Padel 2,66')).toBeTruthy();
    // You are not on your own card.
    expect(screen.queryByTestId(`friend-row-${GATE_USER.id}`)).toBeNull();
  });

  it('offers Accept to somebody who asked you', async () => {
    bookingServer({ [EWA]: 'FRIEND', [MAGDA]: 'ASKED_YOU', [ANIA]: 'FRIEND' });
    await openResult();

    expect(await screen.findByRole('button', { name: acceptLabel('magda.p') })).toBeTruthy();
  });

  it('+ Add asks from the result, naming the game’s group and sport, and the row turns', async () => {
    bookingServer();
    await openResult();

    fireEvent.press(await screen.findByRole('button', { name: addLabel('magda.p') }));

    await waitFor(() => expect(transport.requestsTo('POST', FRIEND_REQUESTS_PATH)).toHaveLength(1));
    expect(transport.requestsTo('POST', FRIEND_REQUESTS_PATH)[0]!.body).toEqual({
      player_id: MAGDA,
      made_from: 'RESULT',
      group_id: POOL,
      sport: 'PADEL',
    });
    expect(await row(MAGDA).findByText(COPY.members.sent)).toBeTruthy();
  });

  it('opens the record from the rest of a row, and asks nobody', async () => {
    bookingServer();
    await openResult();

    fireEvent.press(await screen.findByTestId(`played-with-${MAGDA}`));

    expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
    expect(transport.requestsTo('POST', FRIEND_REQUESTS_PATH)).toHaveLength(0);
  });

  it('is hidden once every one of them is your friend', async () => {
    bookingServer({ [EWA]: 'FRIEND', [MAGDA]: 'FRIEND', [ANIA]: 'FRIEND' });
    await openResult();

    await waitFor(() =>
      expect(transport.requestsTo('GET', bookingPath(BOOKING)).length).toBeGreaterThan(0),
    );
    expect(card()).toBeNull();
    expect(screen.queryByText(COPY.playedWith.heading)).toBeNull();
  });

  it('is there after a For fun game too', async () => {
    bookingServer(undefined, 'FOR_FUN');
    await openResult(settled('FRIENDLY'));

    expect(await screen.findByText(COPY.playedWith.heading)).toBeTruthy();
    expect(screen.getByRole('button', { name: addLabel('magda.p') })).toBeTruthy();
  });

  it('stands between the score and How were they?', async () => {
    bookingServer();
    stubSportsmanship(transport, [{ game_id: GAME, players: [EWA, MAGDA, ANIA] }]);
    await openResult();
    await screen.findByText(STARS_HEADING);
    await screen.findByText(COPY.playedWith.heading);

    const drawn = drawnInOrder();
    const score = drawn.findIndex((text) => text.startsWith('The result.'));
    const playedWith = drawn.indexOf(COPY.playedWith.heading);
    const stars = drawn.indexOf(STARS_HEADING);
    expect(score).toBeGreaterThanOrEqual(0);
    expect(playedWith).toBeGreaterThan(score);
    expect(stars).toBeGreaterThan(playedWith);
  });
});
