/**
 * **A group's You’re in tab, walked** — the reader's own live yeses in this group and sport, its
 * badge, its empty states, *+ Post a game* floating over it, and a yes withdrawn from its row
 * ([#847](https://github.com/Raketa02/Raketa/issues/847), PRD #844; the screens A1, A3, A3.2; split
 * mocks 2 and 3; the mechanics §10).
 *
 * The real route tree from Play › Groups, with `fetch` and the platform edges faked. The rows are
 * read at `DECK_READ_AT` — Wednesday 30 September 2026, 10:00 in Warsaw — so a Saturday game is
 * *Saturday*. Fill in, the tab beside it, is `groupFillIn.test.tsx`'s.
 */

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { onlineManager } from '@tanstack/react-query';
import { router } from 'expo-router';
import { RefreshControl } from 'react-native';

import { RECORD_TITLE } from '@/features/player_record/types';
import { FILL_IN_COPY, PROPOSALS_COPY, proposalKeys } from '@/features/proposals/types';
import { offlineMessage } from '@/shared/errors';
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
  stubFillIn,
  stubGroupDeck,
  stubProposal,
  yesPath,
  youTile,
} from '@/test-support/groupDeck';
import {
  GATE_USER,
  HOME_PATH,
  LIVE_YESES_PATH,
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
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { GROUPS_COPY } from './groupsCopy';

const COPY = FILL_IN_COPY;

/** A skeleton is hidden from a listener, so it is found with the hidden elements too. */
const HIDDEN_TOO = { includeHiddenElements: true } as const;
const START = GROUPS_COPY.youreIn;
const SECOND = 1_000;

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
  administrator_nickname: null,
  is_administrator: false,
};

const GROUP_PATH = `/play/group/${CREW.id}`;

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

/** The crew's page on Games, as it opens; Fill in reading these rows unless the suite serves it. */
async function openPage(rows: () => readonly Wire['SeatToFillSchema'][] = () => []) {
  stubMyGroups(transport, [CREW]);
  transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(PAGE));
  stubGroupDeck(transport, CREW.id, groupDeck());
  stubFillIn(transport, CREW.id, () => fillIn(rows()));
  await launchSignedIn();
  jest.setSystemTime(DECK_READ_AT);
  fireEvent.press(await screen.findByLabelText('Play'));
  fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));
  await waitFor(() => expect(screen).toHavePathname(GROUP_PATH));
}

const tab = (name: RegExp, selected?: boolean) =>
  screen.findByRole('button', { name, ...(selected === undefined ? {} : { selected }) });

const YOURE_IN = /^You’re in/;
const FILL_IN = /^Fill in/;

async function openTab(name: RegExp) {
  fireEvent.press(await tab(name));
  expect(await tab(name, true)).toBeTruthy();
}

async function openYoureIn(rows?: () => readonly Wire['SeatToFillSchema'][]) {
  await openPage(rows);
  await openTab(YOURE_IN);
}

/** A yes of the reader's on a game still filling in the crew — and its game, read in detail. */
function yesInTheCrew(
  details: Partial<Wire['ProposalDetailsResponse']> = {},
  extra: Partial<Wire['LiveYesSchema']> = {},
) {
  const yes = liveYes({ pool_id: CREW.id, ...extra });
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

/** The floating *+ Post a game* — the Games card's own door is a button of the same name. */
const fab = () => screen.queryByTestId('post-a-game-fab');

// ---------------------------------------------------------------------------
// The tab
// ---------------------------------------------------------------------------

describe('the You’re in tab (split mock 2)', () => {
  it('draws only this group’s yeses in this sport, soonest first, with no heading', async () => {
    const soonest = yesInTheCrew();
    const later = yesInTheCrew({}, { starts_at: '2026-10-04T13:00:00Z' });
    const rescue = seatToFill();
    stubLiveYeses(transport, [soonest, later, liveYes({ pool_id: ELSEWHERE })]);
    await openYoureIn(() => [rescue]);

    const mine = await screen.findByTestId(`youre-in-${soonest.proposal_id}`);
    expect(within(mine).getByText('Padel · Saturday 15:00')).toBeTruthy();
    expect(within(mine).getByText('book by Thu 10:00')).toBeTruthy();
    // You, In — and three seats still open on the game, once its details are read; then Withdraw.
    expect(await within(mine).findByTestId(`fill-in-poster-${GATE_USER.id}`)).toBeTruthy();
    expect(within(mine).getAllByTestId('fill-in-open-seat')).toHaveLength(3);
    expect(within(mine).getByRole('button', { name: COPY.withdraw })).toBeTruthy();
    // The list's order, which is the server's: soonest first. Never another group's yes.
    expect(screen.getAllByTestId(/^youre-in-/).map((row) => row.props.testID)).toEqual([
      `youre-in-${soonest.proposal_id}`,
      `youre-in-${later.proposal_id}`,
    ]);
    // The tab's name says what it holds: no heading, and the rescues are Fill in's.
    expect(screen.queryByRole('header', { name: /You’re In|Seats to fill/i })).toBeNull();
    expect(screen.queryByTestId(`seat-to-fill-${rescue.booking_id}`)).toBeNull();
  });

  // New until the tab is visited (#849) — `groupBadges.test.tsx` walks the rest.
  it('counts its rows on its tab from the moment the page opens, and says the count aloud', async () => {
    stubLiveYeses(transport, [yesInTheCrew(), yesInTheCrew(), liveYes({ pool_id: ELSEWHERE })]);
    await openPage(() => [seatToFill()]);

    // On Games: the read started with the page, not with the tab.
    expect(await screen.findByRole('button', { name: 'You’re in, 2 new games' })).toBeTruthy();
    expect(transport.requestsTo('GET', LIVE_YESES_PATH)).toHaveLength(1);
    // Games' and Fill in's badges are their own, as before.
    expect(screen.getByRole('button', { name: 'Fill in, 1 new seat to fill' })).toBeTruthy();
  });

  it('never holds up the page or a tab switch while its read is on its way', async () => {
    transport.on('GET', LIVE_YESES_PATH, neverResponds());
    const row = seatToFill();
    await openPage(() => [row]);

    expect(await screen.findByText(GROUPS_COPY.games.nothingPicked)).toBeTruthy();
    await openTab(FILL_IN);
    expect(await screen.findByTestId(`seat-to-fill-${row.booking_id}`)).toBeTruthy();
    // And no count is claimed for a list not read yet.
    expect(screen.getByRole('button', { name: GROUPS_COPY.group.tabs.youreIn })).toBeTruthy();
  });

  // #875: its rows shimmer, where a spinner stood.
  it('shimmers its rows while its read is on its way', async () => {
    transport.on('GET', LIVE_YESES_PATH, neverResponds());
    await openYoureIn();

    expect(await screen.findAllByTestId('board-skeleton', HIDDEN_TOO)).not.toHaveLength(0);
    expect(screen.queryByText(START.others)).toBeNull();
  });

  it('says it resumes when its read is held offline', async () => {
    await openPage();
    act(() => {
      onlineManager.setOnline(false);
      queryClient.removeQueries({ queryKey: proposalKeys.liveYeses() });
    });
    await openTab(YOURE_IN);

    expect(await screen.findByText(offlineMessage('resumes'))).toBeTruthy();
    expect(screen.queryByText(START.others)).toBeNull();
  });

  // Fill in keeping its rows meanwhile is `groupFillIn.test.tsx`'s.
  it('says why its read was refused, and reads again on the retry', async () => {
    let refused = true;
    const yes = yesInTheCrew();
    transport.on('GET', LIVE_YESES_PATH, () =>
      refused
        ? errorResponse(503, 'block_state_unavailable')
        : json<Wire['LiveYesesResponse']>({ yeses: [yes] }),
    );
    await openYoureIn();

    // A 503 is retried before it is said, so the note waits for the retries to run out.
    expect(await screen.findByRole('alert', {}, { timeout: 30 * SECOND })).toBeTruthy();
    expect(screen.queryByText(START.others)).toBeNull();
    refused = false;
    fireEvent.press(screen.getByRole('button', { name: PROPOSALS_COPY.readAgain }));
    expect(await screen.findByTestId(`youre-in-${yes.proposal_id}`)).toBeTruthy();
  });

  it('keeps its rows when Fill in’s read is refused', async () => {
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
    await openTab(YOURE_IN);

    expect(await screen.findByTestId(`youre-in-${yes.proposal_id}`)).toBeTruthy();
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('keeps the tab while a game’s details and Info are pushed over the page', async () => {
    const yes = yesInTheCrew();
    stubLiveYeses(transport, [yes]);
    await openYoureIn();

    fireEvent.press(
      await screen.findByRole('button', {
        name: 'Padel · Saturday 15:00, Bonarka Arena, book by Thu 10:00',
      }),
    );
    await waitFor(() => expect(screen).toHavePathname(`${GROUP_PATH}/game/${yes.proposal_id}`));
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname(GROUP_PATH));
    expect(await tab(YOURE_IN, true)).toBeTruthy();

    fireEvent.press(await screen.findByHintText(GROUPS_COPY.group.openInfo));
    await waitFor(() => expect(screen).toHavePathname(`${GROUP_PATH}/info`));
    fireEvent.press(await screen.findByRole('button', { name: GROUPS_COPY.info.back }));
    await waitFor(() => expect(screen).toHavePathname(GROUP_PATH));
    expect(await tab(YOURE_IN, true)).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// Empty
// ---------------------------------------------------------------------------

describe('You’re in with nothing on it', () => {
  it('is the group’s starting card when Fill in has nothing either', async () => {
    await openYoureIn();

    expect(await screen.findByText(START.others)).toBeTruthy();
    expect(screen.queryByText(COPY.noYeses)).toBeNull();
  });

  it('is one line when Fill in has a seat to fill — never the starting card', async () => {
    await openYoureIn(() => [seatToFill()]);

    expect(await screen.findByText(COPY.noYeses)).toBeTruthy();
    expect(screen.queryByText(START.others)).toBeNull();
  });

  it('is one line when Fill in could not say — the starting card needs both reads', async () => {
    stubMyGroups(transport, [CREW]);
    transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(PAGE));
    stubGroupDeck(transport, CREW.id, groupDeck());
    transport.on('GET', fillInPath(CREW.id), () => errorResponse(429, 'rate_limited'));
    await launchSignedIn();
    jest.setSystemTime(DECK_READ_AT);
    fireEvent.press(await screen.findByLabelText('Play'));
    fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));
    await openTab(YOURE_IN);

    expect(await screen.findByText(COPY.noYeses)).toBeTruthy();
    expect(screen.queryByText(START.others)).toBeNull();
  });

  it('never draws the starting card as a first frame — it waits for Fill in’s read', async () => {
    const waiting: (() => void)[] = [];
    stubMyGroups(transport, [CREW]);
    transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(PAGE));
    stubGroupDeck(transport, CREW.id, groupDeck());
    transport.on(
      'GET',
      fillInPath(CREW.id),
      () =>
        new Promise<Response>((resolve) => {
          waiting.push(() => resolve(json(fillIn([]))));
        }),
    );
    await launchSignedIn();
    jest.setSystemTime(DECK_READ_AT);
    fireEvent.press(await screen.findByLabelText('Play'));
    fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));
    await openTab(YOURE_IN);
    await waitFor(() => expect(transport.requestsTo('GET', LIVE_YESES_PATH)).toHaveLength(1));

    expect(await screen.findAllByTestId('board-skeleton', HIDDEN_TOO)).not.toHaveLength(0);
    expect(screen.queryByText(START.others)).toBeNull();
    expect(screen.queryByText(COPY.noYeses)).toBeNull();

    // A read the navigation timed out is asked again; answer every one, and run the backoff.
    await act(async () => {
      for (const answer of waiting.splice(0)) answer();
      jest.advanceTimersByTime(2 * SECOND);
    });
    await act(async () => {
      for (const answer of waiting.splice(0)) answer();
    });
    expect(await screen.findByText(START.others)).toBeTruthy();
  });

  it('is just you while nobody else has joined, with the link’s doors', async () => {
    stubMyGroups(transport, [CREW]);
    transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json({ ...PAGE, member_count: 1 }));
    stubGroupDeck(transport, CREW.id, groupDeck());
    await launchSignedIn();
    jest.setSystemTime(DECK_READ_AT);
    fireEvent.press(await screen.findByLabelText('Play'));
    fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));
    await openTab(YOURE_IN);

    expect(await screen.findByText(START.alone)).toBeTruthy();
    expect(screen.getByRole('button', { name: GROUPS_COPY.link.share })).toBeTruthy();
    expect(screen.getByRole('button', { name: GROUPS_COPY.link.copy })).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// + Post a game
// ---------------------------------------------------------------------------

describe('+ Post a game (the screens A3, split override 1)', () => {
  it('floats on You’re in and only there', async () => {
    await openPage();
    // Games draws its own door on Nothing picked right now, never the floating one.
    expect(await screen.findByText(GROUPS_COPY.games.nothingPicked)).toBeTruthy();
    expect(fab()).toBeNull();

    await openTab(FILL_IN);
    expect(await screen.findByText(COPY.noSeats)).toBeTruthy();
    expect(fab()).toBeNull();

    await openTab(YOURE_IN);
    expect(await screen.findByText(START.others)).toBeTruthy();
    const floating = fab();
    expect(floating).not.toBeNull();
    expect(
      within(floating as NonNullable<typeof floating>).getByRole('button', {
        name: START.postAGame,
        disabled: false,
      }),
    ).toBeTruthy();

    await openTab(/^Friends/);
    expect(fab()).toBeNull();
  });

  it('floats over the rows too, and opens Post a game', async () => {
    stubLiveYeses(transport, [yesInTheCrew()]);
    await openYoureIn();

    const floating = await screen.findByTestId('post-a-game-fab');
    fireEvent.press(within(floating).getByRole('button', { name: START.postAGame }));

    await waitFor(() => expect(screen).toHavePathname(`${GROUP_PATH}/post`));
  });
});

// ---------------------------------------------------------------------------
// The pull, and the route
// ---------------------------------------------------------------------------

describe('pulling You’re in', () => {
  const pageBody = () => within(screen.getByTestId('group-page-body'));
  const control = () => pageBody().UNSAFE_getByType(RefreshControl);
  const pull = () => fireEvent(control(), 'refresh');

  it('reads everything again — a yes said on another phone, and a seat offered meanwhile', async () => {
    let rows: Wire['SeatToFillSchema'][] = [];
    await openYoureIn(() => rows);
    expect(await screen.findByText(START.others)).toBeTruthy();

    const yes = yesInTheCrew();
    stubLiveYeses(transport, [yes]);
    rows = [seatToFill()];
    await act(async () => {
      pull();
    });

    expect(await screen.findByTestId(`youre-in-${yes.proposal_id}`)).toBeTruthy();
    // None on You’re in, where the new yes is on screen; Fill in's new seat on its own tab.
    expect(screen.getByRole('button', { name: 'You’re in', selected: true })).toBeTruthy();
    expect(await screen.findByRole('button', { name: 'Fill in, 1 new seat to fill' })).toBeTruthy();
    await waitFor(() => expect(control().props.refreshing).toBe(false));
  });

  it('reads the group with it — the starting card counts who joined meanwhile', async () => {
    let page: Wire['GroupResponse'] = { ...PAGE, member_count: 1 };
    await openYoureIn();
    transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(page));
    await act(async () => {
      pull();
    });
    expect(await screen.findByText(START.alone)).toBeTruthy();

    page = { ...PAGE, member_count: 2 };
    await act(async () => {
      pull();
    });

    expect(await screen.findByText(START.others)).toBeTruthy();
  });
});

describe('a route naming the tab', () => {
  it('opens the page on You’re in', async () => {
    stubMyGroups(transport, [CREW]);
    transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(PAGE));
    stubGroupDeck(transport, CREW.id, groupDeck());
    await launchSignedIn(`${GROUP_PATH}?tab=youreIn`);

    expect(await tab(YOURE_IN, true)).toBeTruthy();
    expect(await screen.findByText(START.others)).toBeTruthy();
  });

  it('drops a tab this build does not know, and opens on Games', async () => {
    stubMyGroups(transport, [CREW]);
    transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(PAGE));
    stubGroupDeck(transport, CREW.id, groupDeck());
    await launchSignedIn(`${GROUP_PATH}?tab=seatsToFill`);

    expect(await tab(/^Games/, true)).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// A You're in row
// ---------------------------------------------------------------------------

describe('a You’re in row (A3.2, mock 13)', () => {
  it('withdraws the last yes in place — the tab stays, on the starting card', async () => {
    const yes = yesInTheCrew();
    stubLiveYeses(transport, [yes]);
    transport.on('DELETE', yesPath(yes.proposal_id), () => {
      stubLiveYeses(transport, []);
      return noContent();
    });
    await openYoureIn();

    fireEvent.press(await screen.findByRole('button', { name: COPY.withdraw }));

    await waitFor(() =>
      expect(transport.requestsTo('DELETE', yesPath(yes.proposal_id))).toHaveLength(1),
    );
    await waitFor(() => expect(screen.queryByTestId(`youre-in-${yes.proposal_id}`)).toBeNull());
    expect(await screen.findByText(START.others)).toBeTruthy();
    expect(screen).toHavePathname(GROUP_PATH);
    expect(await tab(YOURE_IN, true)).toBeTruthy();
  });

  it('withdraws the last yes to the one line while Fill in has a seat', async () => {
    const yes = yesInTheCrew();
    stubLiveYeses(transport, [yes]);
    transport.on('DELETE', yesPath(yes.proposal_id), () => {
      stubLiveYeses(transport, []);
      return noContent();
    });
    await openYoureIn(() => [seatToFill()]);

    fireEvent.press(await screen.findByRole('button', { name: COPY.withdraw }));

    expect(await screen.findByText(COPY.noYeses)).toBeTruthy();
    expect(screen).toHavePathname(GROUP_PATH);
  });

  /**
   * **A full game gone back to filling is on Home too** (#629; Q106), and *Withdraw* here takes it
   * off — so the withdrawal reads Home again, which the shell holds all session.
   */
  it('reads Home again once the yes is withdrawn — a game filling again leaves it', async () => {
    const yes = yesInTheCrew();
    stubLiveYeses(transport, [yes]);
    transport.on('DELETE', yesPath(yes.proposal_id), () => noContent());
    await openYoureIn();

    const withdraw = await screen.findByRole('button', { name: COPY.withdraw });
    await waitFor(() => expect(transport.requestsTo('GET', HOME_PATH).length).toBeGreaterThan(0));
    const before = transport.requestsTo('GET', HOME_PATH).length;
    fireEvent.press(withdraw);

    await waitFor(() =>
      expect(transport.requestsTo('GET', HOME_PATH).length).toBeGreaterThan(before),
    );
  });

  it('hides Withdraw while the full game waits for one payment — Leave is on its details', async () => {
    const yes = yesInTheCrew({ status: 'WAITING_FOR_A_PAYMENT', actions: ['LEAVE'], in_count: 4 });
    stubLiveYeses(transport, [yes]);
    await openYoureIn();

    expect(await screen.findByText('book by Thu 10:00')).toBeTruthy();
    expect(screen.queryByText(/waiting for the club|answers by/)).toBeNull();
    await waitFor(() =>
      expect(transport.requestsTo('GET', proposalPath(yes.proposal_id)).length).toBeGreaterThan(0),
    );
    expect(screen.queryByRole('button', { name: COPY.withdraw })).toBeNull();
  });

  it('offers no Withdraw until its game’s details say it may — a withdrawal while a payment is awaited is a departure', async () => {
    const yes = liveYes({ pool_id: CREW.id });
    stubLiveYeses(transport, [yes]);
    transport.on('GET', proposalPath(yes.proposal_id), () => errorResponse(429, 'rate_limited'));
    await openYoureIn();

    expect(await screen.findByText('book by Thu 10:00')).toBeTruthy();
    await waitFor(() =>
      expect(transport.requestsTo('GET', proposalPath(yes.proposal_id)).length).toBeGreaterThan(0),
    );
    expect(screen.queryByRole('button', { name: COPY.withdraw })).toBeNull();
  });

  it('opens a player’s record from a held poster', async () => {
    const karol = KAROL({ is_in: true });
    const yes = yesInTheCrew({
      in_count: 2,
      sides: { yours: [youTile({ is_in: true }), karol], theirs: [] },
    });
    stubLiveYeses(transport, [yes]);
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
    await openYoureIn();

    fireEvent(await screen.findByTestId(`fill-in-poster-${karol.player_id}`), 'longPress');

    expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
  });

  it('opens the game’s details from its upper block', async () => {
    const yes = yesInTheCrew();
    stubLiveYeses(transport, [yes]);
    await openYoureIn();

    fireEvent.press(
      await screen.findByRole('button', {
        name: 'Padel · Saturday 15:00, Bonarka Arena, book by Thu 10:00',
      }),
    );

    await waitFor(() => expect(screen).toHavePathname(`${GROUP_PATH}/game/${yes.proposal_id}`));
    expect(await screen.findByText('Filling · 1 of 4 in')).toBeTruthy();
  });
});
