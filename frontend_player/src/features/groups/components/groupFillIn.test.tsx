/**
 * **A group's Fill in tab, walked** — the rescues the reader is offered, the tab's badge, its empty
 * line and its own read, and a rescue taken from its row
 * ([#557](https://github.com/Raketa02/Raketa/issues/557), split by
 * [#847](https://github.com/Raketa02/Raketa/issues/847); the screens A1, A3, A3.1; split mock 1;
 * mocks 12 and 14; the mechanics §10). The reader's own yeses are the tab beside it, You’re in
 * (`groupYoureIn.test.tsx`).
 *
 * The real route tree from Play › Groups, with `fetch`, the payment provider's phone half and the
 * platform edges faked. **The ten seconds are walked by advancing the fake clock past them, never by
 * polling** (`theFill.test.tsx`'s rule). The rows are read at `DECK_READ_AT` — Wednesday 30 September
 * 2026, 10:00 in Warsaw — so a Saturday game is *Saturday*.
 */

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { onlineManager } from '@tanstack/react-query';
import { RefreshControl } from 'react-native';

import { RECORD_TITLE } from '@/features/player_record/types';
import { FILL_COPY, FILL_IN_COPY, PROPOSALS_COPY, proposalKeys } from '@/features/proposals/types';
import { offlineMessage } from '@/shared/errors';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { theme } from '@/shared/ui';
import {
  ANIA,
  DECK_READ_AT,
  KAROL,
  KUBA,
  fillIn,
  fillInPath,
  groupDeck,
  liveYes,
  seatToFill,
  seatsPath,
  stubFillIn,
  stubGroupDeck,
} from '@/test-support/groupDeck';
import { clearanceAbove, pageOf } from '@/test-support/tabBarReach';
import { bookedSides, bookingDetails } from '@/test-support/home';
import {
  LIVE_YESES_PATH,
  bookingPath,
  launchSignedIn,
  resetClipboard,
  resetHaptics,
  resetPayments,
  resetShare,
  stubClipboard,
  stubGate,
  stubHaptics,
  stubLiveYeses,
  stubMyGroups,
  stubPaymentMethod,
  stubPayments,
  stubProfileOptions,
  stubProfileSurface,
  stubShare,
} from '@/test-support/onboardingRouter';
import { fakeClipboard, fakeHaptics, fakePayments, fakeShare } from '@/test-support/platform';
import { servedReliability } from '@/test-support/playerRecord';
import {
  errorResponse,
  installTransport,
  json,
  neverResponds,
  type Responder,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { GROUPS_COPY } from './groupsCopy';

const COPY = FILL_IN_COPY;

/** A skeleton is hidden from a listener, so it is found with the hidden elements too. */
const HIDDEN_TOO = { includeHiddenElements: true } as const;
const SECOND = 1_000;

const GAME_ID = 'a1000000-0000-4000-8000-000000000007';

const RATING: Wire['RatingResponse'] = {
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

const CREW: Wire['MyGroupSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000005',
  kind: 'PLAYER',
  name: 'Kazimierz crew',
  monogram: { letters: 'Kc', colour: 1 },
  sports: ['PADEL'],
  member_count: 10,
  home_club: { id: 'c0000000-0000-4000-8000-000000000001', name: 'Centrum Ruchu' },
};

const PAGE: Wire['GroupResponse'] = {
  ...CREW,
  link: 'https://rakieta.app/join/K7PQ2MXA',
  join_policy: 'ANYONE',
  is_owner: false,
  rated_by_sport: [{ sport: 'PADEL', rated_count: 10, first_rated: [] }],
  member_faces: [],
  administrator_nickname: null,
  is_administrator: false,
};

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [RATING], hasPlayerProfile: true });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  stubShare(fakeShare());
  stubClipboard(fakeClipboard());
  stubHaptics(fakeHaptics());
  stubPayments(fakePayments());
  stubPaymentMethod(transport, { brand: 'visa', last_four: '4312', wallet: null });
  useToastQueue.setState({ queue: [] });
});

afterEach(async () => {
  onlineManager.setOnline(true);
  transport.restore();
  resetShare();
  resetClipboard();
  resetHaptics();
  resetPayments();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** The crew's page, its Fill in reading these rows; the tabs as the page opens them, on Games. */
async function openPage(rows: () => readonly Wire['SeatToFillSchema'][] = () => []) {
  stubMyGroups(transport, [CREW]);
  transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(PAGE));
  stubGroupDeck(transport, CREW.id, groupDeck());
  stubFillIn(transport, CREW.id, () => fillIn(rows()));
  await launchSignedIn();
  jest.setSystemTime(DECK_READ_AT);
  fireEvent.press(await screen.findByLabelText('Play'));
  fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));
  await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));
}

/** The crew's page with Fill in answered by this responder — refused, held — rather than rows. */
async function openPageServing(responder: Responder) {
  stubMyGroups(transport, [CREW]);
  transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(PAGE));
  stubGroupDeck(transport, CREW.id, groupDeck());
  transport.on('GET', fillInPath(CREW.id), responder);
  await launchSignedIn();
  jest.setSystemTime(DECK_READ_AT);
  fireEvent.press(await screen.findByLabelText('Play'));
  fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));
  await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));
}

const FILL_IN = /^Fill in/;

async function pressFillIn() {
  fireEvent.press(await screen.findByRole('button', { name: FILL_IN }));
  expect(await screen.findByRole('button', { name: FILL_IN, selected: true })).toBeTruthy();
}

async function openFillIn(rows?: () => readonly Wire['SeatToFillSchema'][]) {
  await openPage(rows);
  await pressFillIn();
}

/** The floating *+ Post a game* — You’re in's alone since #847. */
const fab = () => screen.queryByTestId('post-a-game-fab');

const toasts = () => useToastQueue.getState().queue.map((toast) => [toast.message, toast.tone]);

// ---------------------------------------------------------------------------
// The tab
// ---------------------------------------------------------------------------

describe('the Fill in tab (split mock 1)', () => {
  // What it counts is what the reader hasn't seen (#849) — `groupBadges.test.tsx` walks the rest.
  it('counts the seats to fill on its tab, new until the tab is visited', async () => {
    await openPage(() => [seatToFill()]);

    expect(await screen.findByRole('button', { name: 'Fill in, 1 new seat to fill' })).toBeTruthy();
  });

  it('draws only the rescues, with no heading and nothing floating — the yeses are You’re in’s', async () => {
    const row = seatToFill();
    const yes = liveYes({ pool_id: CREW.id });
    stubLiveYeses(transport, [yes]);
    await openFillIn(() => [row]);

    const rescue = await screen.findByTestId(`seat-to-fill-${row.booking_id}`);
    expect(within(rescue).getByText('Padel · Saturday 16:00')).toBeTruthy();
    expect(within(rescue).getByText('fills by Fri 16:00')).toBeTruthy();
    expect(within(rescue).getAllByTestId(/^fill-in-poster-/)).toHaveLength(3);
    expect(within(rescue).getByText(COPY.openSeat)).toBeTruthy();
    // It moves money, so it says Pay (Q124), and aloud what the share does (Q113).
    expect(within(rescue).getByText('Pay 27 zł')).toBeTruthy();
    expect(
      within(rescue).getByRole('button', { name: 'Pay 27 zł, held until the cut-off' }),
    ).toBeTruthy();

    expect(screen.queryByRole('header', { name: /Seats to fill|You’re In/i })).toBeNull();
    expect(screen.queryByTestId(`youre-in-${yes.proposal_id}`)).toBeNull();
    expect(fab()).toBeNull();
  });

  it('says No seats to fill right now with nothing to fill — never the starting card, nor Post a game', async () => {
    await openFillIn();

    expect(await screen.findByText(COPY.noSeats)).toBeTruthy();
    expect(screen.queryByText(GROUPS_COPY.youreIn.others)).toBeNull();
    expect(screen.queryByText(GROUPS_COPY.youreIn.postAGameDrawn)).toBeNull();
    expect(fab()).toBeNull();
  });

  // #875: a tab switched to with nothing read shimmers on its own — its body, and nothing above it.
  it('shimmers only its own rows when switched to with nothing read, and fades them in as they land', async () => {
    const row = seatToFill();
    stubMyGroups(transport, [CREW]);
    transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(PAGE));
    stubGroupDeck(transport, CREW.id, groupDeck());
    stubFillIn(transport, CREW.id, () => fillIn([row]));
    await launchSignedIn();
    jest.setSystemTime(DECK_READ_AT);
    fireEvent.press(await screen.findByLabelText('Play'));
    await waitFor(() => expect(screen).toHavePathname('/play'));
    // Fill in's read sets out as the page opens, for its badge — and is held on its way.
    const rescues = transport.hold('GET', fillInPath(CREW.id));
    fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));
    // Games revealed the page, and its fade has run.
    expect(await screen.findByText(GROUPS_COPY.games.nothingPicked)).toBeTruthy();
    act(() => jest.advanceTimersByTime(theme.motion.fade + 16));

    await pressFillIn();

    const body = screen.getByTestId('group-body-reveal', HIDDEN_TOO);
    const standing = within(body).getByTestId('reveal-skeleton', HIDDEN_TOO);
    expect(within(standing).getByTestId('board-skeleton', HIDDEN_TOO)).toBeTruthy();
    expect(screen.queryByTestId(`seat-to-fill-${row.booking_id}`)).toBeNull();
    // The header and the tab bar stay as they were: nothing above the body shimmers again.
    expect(screen.queryByTestId('group-header-skeleton', HIDDEN_TOO)).toBeNull();
    expect(screen.getByHintText(GROUPS_COPY.group.openInfo)).toBeTruthy();
    expect(
      within(screen.getByTestId('group-tabs-reveal')).queryByTestId('reveal-skeleton', HIDDEN_TOO),
    ).toBeNull();

    await act(async () => rescues.land());

    expect(await screen.findByTestId(`seat-to-fill-${row.booking_id}`)).toBeTruthy();
    act(() => jest.advanceTimersByTime(theme.motion.fade + 16));
    expect(
      within(screen.getByTestId('group-body-reveal')).queryByTestId('reveal-skeleton', HIDDEN_TOO),
    ).toBeNull();
  });

  // #875: its rows shimmer, where a muted spinner stood — here in the tab's own place, the read
  // timed out by the navigation and asked again.
  it('shimmers its rows while its read is on its way', async () => {
    await openPageServing(neverResponds());
    await pressFillIn();

    expect(await screen.findAllByTestId('board-skeleton', HIDDEN_TOO)).not.toHaveLength(0);
    expect(screen.queryByText(COPY.noSeats)).toBeNull();
  });

  it('says it resumes when its read is held offline', async () => {
    await openPage();
    act(() => {
      onlineManager.setOnline(false);
      queryClient.removeQueries({ queryKey: proposalKeys.fillIn(CREW.id, 'padel') });
    });
    await pressFillIn();

    expect(await screen.findByText(offlineMessage('resumes'))).toBeTruthy();
    expect(screen.queryByText(COPY.noSeats)).toBeNull();
  });

  it('says why the read failed, and reads again on the retry', async () => {
    let refused = true;
    await openPageServing(() =>
      refused ? errorResponse(503, 'block_state_unavailable') : json(fillIn([seatToFill()])),
    );
    await pressFillIn();

    // A 503 is retried before it is said, so the note waits for the retries to run out.
    expect(await screen.findByRole('alert', {}, { timeout: 30 * SECOND })).toBeTruthy();
    expect(screen.queryByText(COPY.noSeats)).toBeNull();
    refused = false;
    fireEvent.press(screen.getByRole('button', { name: PROPOSALS_COPY.readAgain }));
    expect(await screen.findByTestId(/^seat-to-fill-/)).toBeTruthy();
  });

  it('keeps its rows when You’re in’s read is refused', async () => {
    const row = seatToFill();
    transport.on('GET', LIVE_YESES_PATH, () => errorResponse(429, 'rate_limited'));
    await openFillIn(() => [row]);

    expect(await screen.findByTestId(`seat-to-fill-${row.booking_id}`)).toBeTruthy();
    expect(screen.queryByRole('alert')).toBeNull();
  });

  // #881: the bar floats over the page's foot, so the page ends at its reach and the gutter.
  it('scrolls a long Fill in to its last row fully clear of the bar, by the page’s gutter', async () => {
    const rows = Array.from({ length: 8 }, () => seatToFill());
    await openFillIn(() => rows);

    const last = rows[rows.length - 1] as Wire['SeatToFillSchema'];
    const page = pageOf(await screen.findByTestId(`seat-to-fill-${last.booking_id}`));

    expect(page?.props.testID).toBe('group-page-body');
    expect(clearanceAbove(page as NonNullable<typeof page>)).toBe(theme.size.gutter);
  });
});

describe('pulling Fill in', () => {
  // The page's own scroller — the Groups list under it has a pull of its own (#529).
  const pageBody = () => within(screen.getByTestId('group-page-body'));
  const control = () => pageBody().UNSAFE_getByType(RefreshControl);
  const pull = () => fireEvent(control(), 'refresh');

  it('reads everything again — a seat offered meanwhile, a yes said on another phone', async () => {
    let rows: Wire['SeatToFillSchema'][] = [];
    await openFillIn(() => rows);
    expect(await screen.findByText(COPY.noSeats)).toBeTruthy();

    rows = [seatToFill()];
    stubLiveYeses(transport, [liveYes({ pool_id: CREW.id })]);
    await act(async () => {
      pull();
    });

    expect(await screen.findByTestId(`seat-to-fill-${rows[0]?.booking_id ?? ''}`)).toBeTruthy();
    // And the tabs' badges with it: none on Fill in, where the new seat is on screen, and You’re
    // in's new yes.
    expect(screen.getByRole('button', { name: 'Fill in', selected: true })).toBeTruthy();
    expect(await screen.findByRole('button', { name: 'You’re in, 1 new game' })).toBeTruthy();
    await waitFor(() => expect(control().props.refreshing).toBe(false));
  });

  it('takes off a row gone meanwhile', async () => {
    let rows = [seatToFill()];
    await openFillIn(() => rows);
    expect(await screen.findByTestId(/^seat-to-fill-/)).toBeTruthy();

    // Somebody else took the seat.
    rows = [];
    await act(async () => {
      pull();
    });

    expect(await screen.findByText(COPY.noSeats)).toBeTruthy();
    expect(screen.queryByTestId(/^seat-to-fill-/)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// A Seats to fill row
// ---------------------------------------------------------------------------

describe('a Seats to fill row (A3.1, mock 12)', () => {
  it('takes the seat: ten seconds, the booking’s seat, It’s a game! with the booking’s faces, and the row leaves', async () => {
    const row = seatToFill();
    let taken = false;
    transport.on('POST', seatsPath(row.booking_id), () => {
      taken = true;
      return json<Wire['YesAnswerResponse']>({
        proposal_id: row.booking_id,
        open_seats: 0,
        booked: { booking_id: row.booking_id, game_id: GAME_ID },
        your_payment: null,
      });
    });
    transport.on('GET', bookingPath(row.booking_id), () =>
      json(bookingDetails({ booking_id: row.booking_id, game_id: GAME_ID, pool_id: CREW.id })),
    );
    await openFillIn(() => (taken ? [] : [row]));

    fireEvent.press(
      await screen.findByRole('button', { name: 'Pay 27 zł, held until the cut-off' }),
    );

    expect(screen.getByText('Booking in 10 s')).toBeTruthy();
    expect(screen.getByRole('button', { name: FILL_COPY.undo.booking })).toBeTruthy();
    expect(transport.requestsTo('POST', seatsPath(row.booking_id))).toHaveLength(0);
    act(() => jest.advanceTimersByTime(10 * SECOND));

    await waitFor(() =>
      expect(transport.requestsTo('POST', seatsPath(row.booking_id))).toHaveLength(1),
    );
    // A row holds no sides: the faces are the booking's, read once the seat is taken.
    const [, partner] = bookedSides().yours;
    expect(
      await screen.findByRole('header', {
        name: `It’s a game! You and ${partner?.nickname ?? ''} against ines.d and bartek.l`,
      }),
    ).toBeTruthy();
    await waitFor(() => expect(screen.queryByTestId(`seat-to-fill-${row.booking_id}`)).toBeNull());
  });

  it('says the seat is gone, in the sheet, when another join won the race, and the row leaves', async () => {
    const row = seatToFill();
    let taken = false;
    transport.on('POST', seatsPath(row.booking_id), () => {
      taken = true;
      return errorResponse(409, 'seat_just_taken');
    });
    await openFillIn(() => (taken ? [] : [row]));

    fireEvent.press(
      await screen.findByRole('button', { name: 'Pay 27 zł, held until the cut-off' }),
    );
    act(() => jest.advanceTimersByTime(10 * SECOND));

    // A rescue whose seat went is said in the sheet the player must close, as on the deck.
    expect(await screen.findByText('This game isn’t available')).toBeTruthy();
    expect(screen.getByText('Someone just took this seat, so nothing was charged.')).toBeTruthy();
    expect(toasts()).not.toContainEqual(['Someone just took it.', 'bad']);
    expect(screen.queryByTestId('its-a-game')).toBeNull();
    await waitFor(() => expect(screen.queryByTestId(`seat-to-fill-${row.booking_id}`)).toBeNull());
  });

  it('says offered until the start once the cut-off has passed — and Pay is paid now (Q113)', async () => {
    await openFillIn(() => [
      seatToFill({ fills_by_the_cut_off: false, deadline: '2026-10-03T14:00:00Z' }),
    ]);

    expect(await screen.findByText(COPY.offeredUntilTheStart)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Pay 27 zł, paid now' })).toBeTruthy();
  });

  it('opens the rescue’s details from its upper block — the game seen from outside', async () => {
    const row = seatToFill();
    await openFillIn(() => [row]);

    fireEvent.press(
      await screen.findByRole('button', {
        name: 'Padel · Saturday 16:00, Ogrody 33, Court 6, fills by Fri 16:00, 1 seat open',
      }),
    );

    await waitFor(() =>
      expect(screen).toHavePathname(`/play/group/${CREW.id}/rescue/${row.booking_id}`),
    );
  });

  // #753 (Q68, applying since Q128): a square marks the reader's own friend, and only theirs.
  it('marks the reader’s own friends friend on their squares, and nobody else', async () => {
    const kuba = KUBA({ friend: true });
    const row = seatToFill({
      players: [KAROL(), ANIA(), kuba].map((tile) => ({
        player_id: tile.player_id,
        is_you: false,
        nickname: tile.nickname,
        photo_id: null,
        photo_url: null,
        level: tile.level,
        paid: true,
        friend: tile.friend,
      })),
    });
    await openFillIn(() => [row]);

    const rescue = await screen.findByTestId(`seat-to-fill-${row.booking_id}`);
    expect(within(rescue).getByTestId(`fill-in-friend-${kuba.player_id}`)).toBeTruthy();
    expect(within(rescue).getAllByText('friend')).toHaveLength(1);
    expect(within(rescue).getByLabelText('kuba.w, friend')).toBeTruthy();
    expect(within(rescue).getByLabelText('karol.t')).toBeTruthy();
  });

  it('opens a player’s record from a held poster', async () => {
    const karol = KAROL();
    transport.on('GET', `/api/v1/players/${karol.player_id}/record`, () =>
      json<Wire['PlayerRecordResponse']>({
        is_self: false,
        relation: 'NONE',
        can_add_friend: true,
        nickname: 'karol.t',
        photos: [],
        area_code: 'A+050612+0019938',
        social_tags: [],
        sports: [{ sport: 'PADEL', level: 2.75, band: 'Established' }],
        reliability: servedReliability({ player_score: 88, band: 'HIGH', is_new: false }),
        variety: { distinct_opponents: 3, times_on_court: 3 },
      }),
    );
    await openFillIn(() => [seatToFill()]);

    fireEvent(await screen.findByTestId(`fill-in-poster-${karol.player_id}`), 'longPress');

    expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
  });
});
