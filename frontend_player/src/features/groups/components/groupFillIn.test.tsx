/**
 * **A group's Fill in tab, walked** — *Seats to fill* and *You're In* on the group page, the tab's
 * badge, a rescue taken from its row and a yes withdrawn from its own
 * ([#557](https://github.com/Raketa02/Raketa/issues/557); the screens A1, A3; mocks 11–14; the
 * mechanics §10).
 *
 * The real route tree from Play › Groups, with `fetch`, the payment provider's phone half and the
 * platform edges faked. **The ten seconds are walked by advancing the fake clock past them, never by
 * polling** (`theFill.test.tsx`'s rule). The rows are read at `DECK_READ_AT` — Wednesday 30 September
 * 2026, 10:00 in Warsaw — so a Saturday game is *Saturday*.
 */

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';

import { RECORD_TITLE } from '@/features/player_record/types';
import { FILL_COPY, FILL_IN_COPY, PROPOSALS_COPY } from '@/features/proposals/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import {
  DECK_READ_AT,
  KAROL,
  deckCard,
  fillIn,
  fillInPath,
  groupDeck,
  liveYes,
  proposalDetails,
  proposalPath,
  seatToFill,
  seatsPath,
  stubFillIn,
  stubGroupDeck,
  stubProposal,
  yesPath,
  youTile,
} from '@/test-support/groupDeck';
import { bookedSides, bookingDetails } from '@/test-support/home';
import {
  GATE_USER,
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
import {
  errorResponse,
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { GROUPS_COPY } from './groupsCopy';

const COPY = FILL_IN_COPY;
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
  link: 'https://raketa.app/join/K7PQ2MXA',
  join_policy: 'ANYONE',
  is_owner: false,
  rated_by_sport: [{ sport: 'PADEL', rated_count: 10, first_rated: [] }],
  member_faces: [],
  administrator_name: null,
  is_administrator: false,
};

/** A yes the reader said in another group — never this tab's. */
const ELSEWHERE = 'a0000000-0000-4000-8000-000000000099';

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

async function openFillIn(rows?: () => readonly Wire['SeatToFillSchema'][]) {
  await openPage(rows);
  fireEvent.press(await screen.findByRole('button', { name: /^Fill in/ }));
}

/** A yes of the reader's on a game still filling in the crew — and its game, read in detail. */
function yesInTheCrew(details: Partial<Wire['ProposalDetailsResponse']> = {}) {
  const yes = liveYes({ pool_id: CREW.id });
  const card = deckCard({
    proposal_id: yes.proposal_id,
    starts_at: yes.starts_at,
    share_grosze: yes.share_grosze,
    deadline: yes.book_by,
    in_count: 1,
    sides: { yours: [youTile({ is_in: true })], theirs: [] },
  });
  stubProposal(transport, yes.proposal_id, proposalDetails(card, details));
  return yes;
}

const toasts = () => useToastQueue.getState().queue.map((toast) => [toast.message, toast.tone]);

// ---------------------------------------------------------------------------
// The tab
// ---------------------------------------------------------------------------

describe('the Fill in tab (mock 11)', () => {
  it('counts the seats to fill on its tab, from whichever tab the page is on', async () => {
    await openPage(() => [seatToFill()]);

    expect(await screen.findByRole('button', { name: 'Fill in, 1 seat to fill' })).toBeTruthy();
  });

  it('draws Seats to fill, then You’re In — this group’s yeses in this sport only', async () => {
    const row = seatToFill();
    const yes = yesInTheCrew();
    stubLiveYeses(transport, [yes, liveYes({ pool_id: ELSEWHERE })]);
    await openFillIn(() => [row]);

    expect(await screen.findByRole('header', { name: 'Seats to fill · 1' })).toBeTruthy();
    const rescue = screen.getByTestId(`seat-to-fill-${row.booking_id}`);
    expect(within(rescue).getByText('Padel · Saturday 16:00')).toBeTruthy();
    expect(within(rescue).getByText('fills by Fri 16:00')).toBeTruthy();
    expect(within(rescue).getAllByTestId(/^fill-in-poster-/)).toHaveLength(3);
    expect(within(rescue).getByText(COPY.openSeat)).toBeTruthy();
    expect(within(rescue).getByRole('button', { name: 'I’m in, pays 27 zł now' })).toBeTruthy();

    expect(await screen.findByRole('header', { name: 'You’re In · 1' })).toBeTruthy();
    const mine = screen.getByTestId(`youre-in-${yes.proposal_id}`);
    expect(within(mine).getByText('Padel · Saturday 15:00')).toBeTruthy();
    expect(within(mine).getByText('book by Thu 10:00')).toBeTruthy();
    // You, In — and three seats still open on the game, once its details are read; then Withdraw.
    expect(await within(mine).findByTestId(`fill-in-poster-${GATE_USER.id}`)).toBeTruthy();
    expect(within(mine).getAllByTestId('fill-in-open-seat')).toHaveLength(3);
    expect(within(mine).getByRole('button', { name: COPY.withdraw })).toBeTruthy();
    expect(screen.queryAllByTestId(/^youre-in-/)).toHaveLength(1);
  });

  it('draws only the sections with rows', async () => {
    await openFillIn(() => [seatToFill()]);

    expect(await screen.findByRole('header', { name: 'Seats to fill · 1' })).toBeTruthy();
    expect(screen.queryByText(/You’re In/)).toBeNull();
  });

  it('is the group’s starting card with nothing in either, and Post a game floats, open (#558)', async () => {
    await openFillIn();

    expect(await screen.findByText(GROUPS_COPY.fillIn.others)).toBeTruthy();
    expect(
      screen.getByRole('button', { name: GROUPS_COPY.fillIn.postAGame, disabled: false }),
    ).toBeTruthy();
  });

  it('keeps You’re In when Seats to fill could not be read, and says why in its place', async () => {
    const yes = yesInTheCrew();
    stubLiveYeses(transport, [yes]);
    stubMyGroups(transport, [CREW]);
    transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(PAGE));
    stubGroupDeck(transport, CREW.id, groupDeck());
    transport.on('GET', fillInPath(CREW.id), () => errorResponse(429, 'rate_limited'));
    await launchSignedIn();
    jest.setSystemTime(DECK_READ_AT);
    fireEvent.press(await screen.findByLabelText('Play'));
    fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));
    fireEvent.press(await screen.findByRole('button', { name: /^Fill in/ }));

    expect(await screen.findByRole('header', { name: 'You’re In · 1' })).toBeTruthy();
    expect(await screen.findByRole('alert', {}, { timeout: 30 * SECOND })).toBeTruthy();
    expect(screen.queryByText(GROUPS_COPY.fillIn.others)).toBeNull();
  });

  it('says why the read failed, and reads again on the retry', async () => {
    let refused = true;
    stubMyGroups(transport, [CREW]);
    transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(PAGE));
    stubGroupDeck(transport, CREW.id, groupDeck());
    transport.on('GET', fillInPath(CREW.id), () =>
      refused ? errorResponse(503, 'block_state_unavailable') : json(fillIn([seatToFill()])),
    );
    await launchSignedIn();
    jest.setSystemTime(DECK_READ_AT);
    fireEvent.press(await screen.findByLabelText('Play'));
    fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));
    fireEvent.press(await screen.findByRole('button', { name: /^Fill in/ }));

    // A 503 is retried before it is said, so the note waits for the retries to run out.
    expect(await screen.findByRole('alert', {}, { timeout: 30 * SECOND })).toBeTruthy();
    refused = false;
    fireEvent.press(screen.getByRole('button', { name: PROPOSALS_COPY.readAgain }));
    expect(await screen.findByRole('header', { name: 'Seats to fill · 1' })).toBeTruthy();
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
        waiting_for_the_club: false,
        your_payment: null,
      });
    });
    transport.on('GET', bookingPath(row.booking_id), () =>
      json(bookingDetails({ booking_id: row.booking_id, game_id: GAME_ID, pool_id: CREW.id })),
    );
    await openFillIn(() => (taken ? [] : [row]));

    fireEvent.press(await screen.findByRole('button', { name: 'I’m in, pays 27 zł now' }));

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
        name: `It’s a game! You and ${partner?.name ?? ''} against Inés Díaz and Bartek Lis`,
      }),
    ).toBeTruthy();
    await waitFor(() => expect(screen.queryByTestId(`seat-to-fill-${row.booking_id}`)).toBeNull());
  });

  it('says Someone just took it when another join won the race, and the row leaves', async () => {
    const row = seatToFill();
    let taken = false;
    transport.on('POST', seatsPath(row.booking_id), () => {
      taken = true;
      return errorResponse(409, 'seat_just_taken');
    });
    await openFillIn(() => (taken ? [] : [row]));

    fireEvent.press(await screen.findByRole('button', { name: 'I’m in, pays 27 zł now' }));
    act(() => jest.advanceTimersByTime(10 * SECOND));

    await waitFor(() => expect(toasts()).toContainEqual(['Someone just took it.', 'bad']));
    expect(screen.queryByTestId('its-a-game')).toBeNull();
    await waitFor(() => expect(screen.queryByTestId(`seat-to-fill-${row.booking_id}`)).toBeNull());
  });

  it('says offered until the start once the cut-off has passed', async () => {
    await openFillIn(() => [
      seatToFill({ fills_by_the_cut_off: false, deadline: '2026-10-03T14:00:00Z' }),
    ]);

    expect(await screen.findByText(COPY.offeredUntilTheStart)).toBeTruthy();
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

  it('opens a player’s record from a held poster', async () => {
    const karol = KAROL();
    transport.on('GET', `/api/v1/players/${karol.player_id}/record`, () =>
      json<Wire['PlayerRecordResponse']>({
        is_self: false,
        name: 'Karol Tomaszewski',
        nickname: 'karol_t',
        area_code: 'A+050612+0019938',
        social_tags: [],
        sports: [{ sport: 'PADEL', level: 2.75, band: 'Established' }],
        reliability: { player_score: 88, strands: [] },
        variety: { distinct_opponents: 3, times_on_court: 3 },
      }),
    );
    await openFillIn(() => [seatToFill()]);

    fireEvent(await screen.findByTestId(`fill-in-poster-${karol.player_id}`), 'longPress');

    expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// A You're In row
// ---------------------------------------------------------------------------

describe('a You’re In row (A3.2, mock 13)', () => {
  it('withdraws the yes, free and silent, and the row leaves with it', async () => {
    const yes = yesInTheCrew();
    stubLiveYeses(transport, [yes]);
    transport.on('DELETE', yesPath(yes.proposal_id), () => {
      stubLiveYeses(transport, []);
      return noContent();
    });
    await openFillIn();

    fireEvent.press(await screen.findByRole('button', { name: COPY.withdraw }));

    await waitFor(() =>
      expect(transport.requestsTo('DELETE', yesPath(yes.proposal_id))).toHaveLength(1),
    );
    await waitFor(() => expect(screen.queryByTestId(`youre-in-${yes.proposal_id}`)).toBeNull());
    expect(await screen.findByText(GROUPS_COPY.fillIn.others)).toBeTruthy();
  });

  it('says waiting for the club while an On request club decides, and hides Withdraw', async () => {
    const yes = yesInTheCrew({ status: 'WAITING_FOR_THE_CLUB', actions: ['LEAVE'], in_count: 4 });
    stubLiveYeses(transport, [yes]);
    await openFillIn();

    expect(await screen.findByText(COPY.waitingForTheClub)).toBeTruthy();
    await waitFor(() =>
      expect(transport.requestsTo('GET', proposalPath(yes.proposal_id)).length).toBeGreaterThan(0),
    );
    expect(screen.queryByRole('button', { name: COPY.withdraw })).toBeNull();
  });

  it('offers no Withdraw until its game’s details say it may — a withdrawal while the club decides is a departure', async () => {
    const yes = liveYes({ pool_id: CREW.id });
    stubLiveYeses(transport, [yes]);
    transport.on('GET', proposalPath(yes.proposal_id), () => errorResponse(429, 'rate_limited'));
    await openFillIn();

    expect(await screen.findByText('book by Thu 10:00')).toBeTruthy();
    await waitFor(() =>
      expect(transport.requestsTo('GET', proposalPath(yes.proposal_id)).length).toBeGreaterThan(0),
    );
    expect(screen.queryByRole('button', { name: COPY.withdraw })).toBeNull();
  });

  it('opens the game’s details from its upper block', async () => {
    const yes = yesInTheCrew();
    stubLiveYeses(transport, [yes]);
    await openFillIn();

    fireEvent.press(
      await screen.findByRole('button', {
        name: 'Padel · Saturday 15:00, Bonarka Arena, book by Thu 10:00',
      }),
    );

    await waitFor(() =>
      expect(screen).toHavePathname(`/play/group/${CREW.id}/game/${yes.proposal_id}`),
    );
    expect(await screen.findByText('Filling · 1 of 4 in')).toBeTruthy();
  });
});
