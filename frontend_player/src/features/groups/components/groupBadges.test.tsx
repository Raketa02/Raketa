/**
 * **A group page's badges count what the player hasn't seen, and the phone remembers what they
 * have** — Fill in's and You’re in's ([#849](https://github.com/Rakieta02/Rakieta/issues/849)), and
 * Games' across both kinds ([#850](https://github.com/Rakieta02/Rakieta/issues/850);
 * [ADR-0208](../../../../../docs/adr/0208-the-phone-remembers-which-rows-of-a-group-pages-tabs-a-player-has-seen.md);
 * PRD #844; split override 2).
 *
 * A tab's rows are seen while it is on screen — the page in view, nothing pushed over it and no
 * record's sheet up — and the tab on screen draws no badge. On Games that is the deck of the kind
 * the switch is on, every card of it, so the other kind's stay new until the switch moves there. A
 * row is known by its id, so one that only changed stays seen, and only a new one brings the badge
 * back.
 *
 * The real route tree from Play › Groups, with `fetch` and the platform edges faked. *A relaunch* is
 * the process ending and a new one starting: the Query cache and the session go, and what the phone
 * keeps — the keychain and its preferences — stays. **A badge the phone's memory clears is asserted
 * against one it doesn't**: after a relaunch the page is served one row it saw and one it didn't, so
 * *1 new* says both that the memory was read and that it held.
 */

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { router } from 'expo-router';
import { RefreshControl } from 'react-native';

import { RECORD_TITLE } from '@/features/player_record/types';
import { proposalKeys } from '@/features/proposals/types';
import { clearStoredTokens, endSession, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import {
  ANIA,
  DECK_READ_AT,
  EWA,
  KAROL,
  KUBA,
  bothKinds,
  deckCard,
  fillIn,
  liveYes,
  overlapCells,
  proposalDetails,
  proposalPath,
  seatsPath,
  seatToFill,
  stubFillIn,
  stubGroupDeck,
  stubProposal,
  yesPath,
  youTile,
} from '@/test-support/groupDeck';
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
  stubMyGroups,
  stubPaymentMethod,
  stubPayments,
  stubProfileOptions,
  stubProfileSurface,
  stubShare,
} from '@/test-support/onboardingRouter';
import { fakeClipboard, fakeHaptics, fakePayments, fakeShare } from '@/test-support/platform';
import { bookingDetails } from '@/test-support/home';
import { servedReliability } from '@/test-support/playerRecord';
import { landTheSwap, menuSays, menuTab, pickKind } from '@/test-support/tabMenu';
import {
  installTransport,
  json,
  neverResponds,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { useGameIntent } from '../store/gameIntent.store';

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

const GROUP_PATH = `/play/group/${CREW.id}`;

/** Somebody else signing in on the same phone. */
const BORIS = '99999999-8888-4777-8666-555555555555';

let transport: Transport;
/** What the crew's Fill in serves at each read. */
let rescues: Wire['SeatToFillSchema'][];
/** What the live yeses serve at each read. */
let yeses: Wire['LiveYesSchema'][];
/** What the crew's deck deals at each read, per kind — every read with both kinds' ids (#846). */
let dealt: Parameters<typeof bothKinds>[0];

/**
 * The crew's page, its deck, its Fill in and the live yeses, each read off the suite's state as it is
 * asked.
 */
function serve() {
  stubMyGroups(transport, [CREW]);
  transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(PAGE));
  stubGroupDeck(transport, CREW.id, (kind) => bothKinds(dealt)(kind));
  stubFillIn(transport, CREW.id, () => fillIn(rescues));
  transport.on('GET', LIVE_YESES_PATH, () => json<Wire['LiveYesesResponse']>({ yeses }));
}

beforeEach(() => {
  transport = installTransport();
  rescues = [];
  yeses = [];
  dealt = {};
  // The deck's switch, which a new process opens on Competitive.
  useGameIntent.setState({ intent: 'competitive' });
  stubGate(transport, { ratings: [RATING], hasPlayerProfile: true });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  stubShare(fakeShare());
  stubClipboard(fakeClipboard());
  stubHaptics(fakeHaptics());
  stubPayments(fakePayments());
  stubPaymentMethod(transport, { brand: 'visa', last_four: '4312', wallet: null });
  useToastQueue.setState({ queue: [] });
  serve();
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

/** Into the app, and onto the crew's page — on Games, as it always opens. */
async function launchOnThePage() {
  await launchSignedIn();
  jest.setSystemTime(DECK_READ_AT);
  fireEvent.press(await screen.findByLabelText('Play'));
  fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));
  await waitFor(() => expect(screen).toHavePathname(GROUP_PATH));
}

/** The process ends and a new one starts — on the crew's page again, its switch on Competitive. */
async function relaunch() {
  screen.unmount();
  queryClient.clear();
  resetSessionStatus();
  useGameIntent.setState({ intent: 'competitive' });
  await launchOnThePage();
}

const FILL_IN = /^Fill in/;
const YOURE_IN = /^You’re in/;
const GAMES = /^Games/;

/** The tab, by the whole of its spoken name — `Fill in` alone is the tab with no badge. */
const tabNamed = (name: string, selected?: boolean) =>
  screen.findByRole('button', { name, ...(selected === undefined ? {} : { selected }) });

async function visit(tab: RegExp) {
  fireEvent.press(await screen.findByRole('button', { name: tab }));
  expect(await screen.findByRole('button', { name: tab, selected: true })).toBeTruthy();
}

/**
 * A row drawn on the page while something covers it — a screen pushed over it, or a sheet — so
 * hidden from a listener: what proves the row reached the tab before the player could see it.
 */
const drawnUnder = (testId: string) => screen.findByTestId(testId, { includeHiddenElements: true });

/** The count a tab draws over its corner — hidden from a listener, who hears it in the tab's name. */
const drawnCount = (tab: Parameters<typeof within>[0]) =>
  within(tab).queryByText(/^[0-9]+$/, { includeHiddenElements: true });

/** A yes of the reader's in the crew — and its game, read in detail for the row's squares. */
function yesHere(extra: Partial<Wire['LiveYesSchema']> = {}): Wire['LiveYesSchema'] {
  const yes = liveYes({ pool_id: CREW.id, ...extra });
  const card = deckCard({
    proposal_id: yes.proposal_id,
    starts_at: yes.starts_at,
    share_grosze: yes.share_grosze,
    deadline: yes.book_by,
    in_count: 1,
    sides: { yours: [youTile({ is_in: true })], theirs: [] },
  });
  stubProposal(transport, yes.proposal_id, proposalDetails(card));
  return yes;
}

/** A player's record, served for the sheet a held poster or a pressed tile opens. */
function stubRecord(player: Wire['DeckTileSchema']) {
  transport.on('GET', `/api/v1/players/${player.player_id}/record`, () =>
    json<Wire['PlayerRecordResponse']>({
      is_self: false,
      relation: 'NONE',
      can_add_friend: true,
      nickname: player.nickname ?? 'karol.t',
      photos: [],
      area_code: 'A+050612+0019938',
      social_tags: [],
      sports: [{ sport: 'PADEL', level: 2.75, band: 'Established' }],
      reliability: servedReliability({ player_score: 88, band: 'HIGH', is_new: false }),
      variety: { distinct_opponents: 3, times_on_court: 3 },
    }),
  );
}

/** A re-read of a tab's read while the player is elsewhere — what an answer in the group sets off. */
async function reread(queryKey: readonly unknown[]) {
  await act(async () => {
    await queryClient.invalidateQueries({ queryKey });
  });
}

const rereadFillIn = () => reread(proposalKeys.fillIn(CREW.id, 'padel'));
const rereadYeses = () => reread(proposalKeys.liveYeses());

// ---------------------------------------------------------------------------
// Fill in
// ---------------------------------------------------------------------------

describe('Fill in’s badge — the rescues you haven’t seen', () => {
  it('counts on the tab not shown, says it is new, and draws nothing on the tab shown', async () => {
    rescues = [seatToFill(), seatToFill()];
    await launchOnThePage();

    // The first run: nothing has been seen, so today's count, until the tab is visited.
    const counted = await tabNamed('Fill in, 2 new seats to fill', false);
    expect(drawnCount(counted)?.props.children).toBe(2);

    await visit(FILL_IN);

    const shown = await tabNamed('Fill in', true);
    expect(drawnCount(shown)).toBeNull();
  });

  it('is cleared by a visit', async () => {
    rescues = [seatToFill()];
    await launchOnThePage();
    expect(await tabNamed('Fill in, 1 new seat to fill')).toBeTruthy();

    await visit(FILL_IN);
    await visit(GAMES);

    const left = await tabNamed('Fill in', false);
    expect(drawnCount(left)).toBeNull();
  });

  it('comes back for a new rescue, never for one that only changed', async () => {
    const first = seatToFill();
    rescues = [first];
    await launchOnThePage();
    await visit(FILL_IN);
    await visit(GAMES);
    expect(await tabNamed('Fill in', false)).toBeTruthy();

    // The seen one's cut-off has passed — offered until the start now — and a second is offered.
    rescues = [
      { ...first, fills_by_the_cut_off: false, deadline: '2026-10-03T14:00:00Z' },
      seatToFill(),
    ];
    await rereadFillIn();

    expect(await tabNamed('Fill in, 1 new seat to fill', false)).toBeTruthy();
  });

  it('sees at once what a pull brings while the tab is on screen', async () => {
    rescues = [seatToFill()];
    await launchOnThePage();
    await visit(FILL_IN);

    const second = seatToFill();
    rescues = [...rescues, second];
    const control = within(screen.getByTestId('group-page-body')).UNSAFE_getByType(RefreshControl);
    await act(async () => {
      fireEvent(control, 'refresh');
    });
    expect(await screen.findByTestId(`seat-to-fill-${second.booking_id}`)).toBeTruthy();
    expect(await tabNamed('Fill in', true)).toBeTruthy();

    await visit(GAMES);

    expect(await tabNamed('Fill in', false)).toBeTruthy();
  });

  it('does not see a rescue that arrives while its details cover the page', async () => {
    const first = seatToFill();
    rescues = [first];
    transport.on('GET', bookingPath(first.booking_id), neverResponds());
    await launchOnThePage();
    await visit(FILL_IN);
    fireEvent.press(
      await screen.findByRole('button', {
        name: 'Padel · Saturday 16:00, Ogrody 33, Court 6, fills by Fri 16:00, 1 seat open',
      }),
    );
    await waitFor(() => expect(screen).toHavePathname(`${GROUP_PATH}/rescue/${first.booking_id}`));

    // A second rescue reaches the page, and is drawn on it, under the details.
    const second = seatToFill();
    rescues = [first, second];
    await rereadFillIn();
    expect(await drawnUnder(`seat-to-fill-${second.booking_id}`)).toBeTruthy();

    // Android kills the app before the details are closed: the second was never on screen.
    await relaunch();

    expect(await tabNamed('Fill in, 1 new seat to fill', false)).toBeTruthy();
  });

  it('does not see a rescue that arrives while It’s a game! is up over the tab', async () => {
    const taken = seatToFill();
    const next = seatToFill();
    let joined = false;
    transport.on('POST', seatsPath(taken.booking_id), () => {
      joined = true;
      return json<Wire['YesAnswerResponse']>({
        proposal_id: taken.booking_id,
        open_seats: 0,
        booked: { booking_id: taken.booking_id, game_id: 'a1000000-0000-4000-8000-000000000007' },
        your_payment: null,
      });
    });
    transport.on('GET', bookingPath(taken.booking_id), () =>
      json(bookingDetails({ booking_id: taken.booking_id, pool_id: CREW.id })),
    );
    rescues = [taken];
    await launchOnThePage();
    await visit(FILL_IN);

    // The seat taken, the group re-read after it — and the re-read brings a rescue nobody has seen.
    fireEvent.press(
      await screen.findByRole('button', { name: 'Pay 27 zł, held until the cut-off' }),
    );
    rescues = [next];
    act(() => jest.advanceTimersByTime(10_000));
    await waitFor(() => expect(joined).toBe(true));
    expect(await screen.findByTestId('its-a-game')).toBeTruthy();
    expect(await drawnUnder(`seat-to-fill-${next.booking_id}`)).toBeTruthy();
    await relaunch();

    expect(await tabNamed('Fill in, 1 new seat to fill', false)).toBeTruthy();
  });

  it('does not see a rescue that arrives while a player’s record is open over the tab', async () => {
    const karol = KAROL();
    stubRecord(karol);
    const first = seatToFill();
    rescues = [first];
    await launchOnThePage();
    await visit(FILL_IN);
    fireEvent(await screen.findByTestId(`fill-in-poster-${karol.player_id}`), 'longPress');
    expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();

    const second = seatToFill();
    rescues = [first, second];
    await rereadFillIn();
    expect(await drawnUnder(`seat-to-fill-${second.booking_id}`)).toBeTruthy();
    // The tab on screen draws no badge, even for a row it has not had on screen yet.
    const shown = await tabNamed('Fill in', true);
    expect(drawnCount(shown)).toBeNull();
    await relaunch();

    expect(await tabNamed('Fill in, 1 new seat to fill', false)).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// You’re in
// ---------------------------------------------------------------------------

describe('You’re in’s badge — the yeses you haven’t seen', () => {
  it('counts on the tab not shown, says it is new, and draws nothing on the tab shown', async () => {
    yeses = [yesHere(), yesHere(), liveYes({ pool_id: 'a0000000-0000-4000-8000-000000000099' })];
    await launchOnThePage();

    // Only this group's yeses in this sport, and the first run's whole count.
    const counted = await tabNamed('You’re in, 2 new games', false);
    expect(drawnCount(counted)?.props.children).toBe(2);

    await visit(YOURE_IN);

    const shown = await tabNamed('You’re in', true);
    expect(drawnCount(shown)).toBeNull();
  });

  it('is cleared by a visit', async () => {
    yeses = [yesHere()];
    await launchOnThePage();
    expect(await tabNamed('You’re in, 1 new game')).toBeTruthy();

    await visit(YOURE_IN);
    await visit(GAMES);

    const left = await tabNamed('You’re in', false);
    expect(drawnCount(left)).toBeNull();
  });

  it('comes back for a new yes, never for one that only changed', async () => {
    const first = yesHere();
    yeses = [first];
    await launchOnThePage();
    await visit(YOURE_IN);
    await visit(FILL_IN);
    expect(await tabNamed('You’re in', false)).toBeTruthy();

    // The seen one's book-by moved, and a yes said on another phone arrives.
    yeses = [{ ...first, book_by: '2026-10-03T09:00:00Z' }, yesHere()];
    await rereadYeses();

    expect(await tabNamed('You’re in, 1 new game', false)).toBeTruthy();
  });

  it('sees at once what a pull brings while the tab is on screen', async () => {
    await launchOnThePage();
    await visit(YOURE_IN);

    const yes = yesHere();
    yeses = [yes];
    const control = within(screen.getByTestId('group-page-body')).UNSAFE_getByType(RefreshControl);
    await act(async () => {
      fireEvent(control, 'refresh');
    });
    expect(await screen.findByTestId(`youre-in-${yes.proposal_id}`)).toBeTruthy();

    await visit(GAMES);

    expect(await tabNamed('You’re in', false)).toBeTruthy();
  });

  it('does not see a yes that arrives while a game’s details cover the page — until they close', async () => {
    const first = yesHere();
    yeses = [first];
    await launchOnThePage();
    await visit(YOURE_IN);
    fireEvent.press(
      await screen.findByRole('button', {
        name: 'Padel · Saturday 15:00, Bonarka Arena, book by Thu 10:00',
      }),
    );
    await waitFor(() => expect(screen).toHavePathname(`${GROUP_PATH}/game/${first.proposal_id}`));

    const second = yesHere();
    yeses = [first, second];
    await rereadYeses();
    expect(await drawnUnder(`youre-in-${second.proposal_id}`)).toBeTruthy();

    // Back on the page, the second is on screen, and seen.
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname(GROUP_PATH));
    expect(await screen.findByTestId(`youre-in-${second.proposal_id}`)).toBeTruthy();
    await visit(GAMES);

    expect(await tabNamed('You’re in', false)).toBeTruthy();
  });

  it('keeps a yes that arrived under a game’s details new, when the app is killed there', async () => {
    const first = yesHere();
    yeses = [first];
    await launchOnThePage();
    await visit(YOURE_IN);
    fireEvent.press(
      await screen.findByRole('button', {
        name: 'Padel · Saturday 15:00, Bonarka Arena, book by Thu 10:00',
      }),
    );
    await waitFor(() => expect(screen).toHavePathname(`${GROUP_PATH}/game/${first.proposal_id}`));

    const second = yesHere();
    yeses = [first, second];
    await rereadYeses();
    expect(await drawnUnder(`youre-in-${second.proposal_id}`)).toBeTruthy();
    await relaunch();

    expect(await tabNamed('You’re in, 1 new game', false)).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// The phone's memory
// ---------------------------------------------------------------------------

describe('what the phone remembers, and for whom (ADR-0208)', () => {
  it('keeps both tabs’ seen rows across a relaunch — only what arrived since is new', async () => {
    const rescue = seatToFill();
    const yes = yesHere();
    rescues = [rescue];
    yeses = [yes];
    await launchOnThePage();
    await visit(FILL_IN);
    await visit(YOURE_IN);
    await visit(GAMES);
    expect(await tabNamed('Fill in', false)).toBeTruthy();
    expect(await tabNamed('You’re in', false)).toBeTruthy();

    rescues = [rescue, seatToFill()];
    yeses = [yes, yesHere()];
    await relaunch();

    expect(await tabNamed('Fill in, 1 new seat to fill', false)).toBeTruthy();
    expect(await tabNamed('You’re in, 1 new game', false)).toBeTruthy();
  });

  it('forgets them when the player signs out', async () => {
    rescues = [seatToFill()];
    await launchOnThePage();
    await visit(FILL_IN);
    await visit(GAMES);
    expect(await tabNamed('Fill in', false)).toBeTruthy();

    screen.unmount();
    await endSession('requested');
    queryClient.clear();
    resetSessionStatus();
    await launchOnThePage();

    expect(await tabNamed('Fill in, 1 new seat to fill', false)).toBeTruthy();
  });

  it('forgets them when the server ends the session too', async () => {
    yeses = [yesHere()];
    await launchOnThePage();
    await visit(YOURE_IN);
    await visit(GAMES);
    expect(await tabNamed('You’re in', false)).toBeTruthy();

    screen.unmount();
    await endSession('session-invalidated');
    queryClient.clear();
    resetSessionStatus();
    await launchOnThePage();

    expect(await tabNamed('You’re in, 1 new game', false)).toBeTruthy();
  });

  it('keeps Games’ seen cards across a relaunch — only a card dealt since is new', async () => {
    const fun = forFunIn();
    dealt = { forFun: [fun] };
    await launchOnThePage();
    await switchToForFun(fun);
    await visit(FILL_IN);
    expect(await tabNamed('Games', false)).toBeTruthy();

    dealt = { forFun: [fun, forFunIn()] };
    await relaunch();
    await visit(FILL_IN);

    expect(await tabNamed(GAMES_NEW, false)).toBeTruthy();
  });

  it('forgets Games’ seen cards when the player signs out', async () => {
    const fun = forFunIn();
    dealt = { forFun: [fun] };
    await launchOnThePage();
    await switchToForFun(fun);
    await visit(FILL_IN);
    expect(await tabNamed('Games', false)).toBeTruthy();

    screen.unmount();
    await endSession('requested');
    queryClient.clear();
    resetSessionStatus();
    useGameIntent.setState({ intent: 'competitive' });
    await launchOnThePage();
    await visit(FILL_IN);

    expect(await tabNamed(GAMES_NEW, false)).toBeTruthy();
  });

  it('starts somebody else on this phone with nothing seen', async () => {
    rescues = [seatToFill()];
    await launchOnThePage();
    await visit(FILL_IN);
    await visit(GAMES);
    expect(await tabNamed('Fill in', false)).toBeTruthy();

    screen.unmount();
    queryClient.clear();
    resetSessionStatus();
    stubGate(transport, { ratings: [RATING], hasPlayerProfile: true, id: BORIS });
    serve();
    await launchOnThePage();

    expect(await tabNamed('Fill in, 1 new seat to fill', false)).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// Games
// ---------------------------------------------------------------------------

/** A card Kuba has said yes to — somebody In with you. */
function kubaIn(extra: Partial<Wire['DeckCardSchema']> = {}): Wire['DeckCardSchema'] {
  return deckCard({
    in_count: 1,
    sides: { yours: [youTile(), KUBA({ is_in: true })], theirs: [ANIA(), EWA()] },
    ...extra,
  });
}

/** The same on For fun, which sends a vibe and no forecast (#830). */
const forFunIn = (extra: Partial<Wire['DeckCardSchema']> = {}) =>
  kubaIn({ kind: 'FOR_FUN', forecast: null, vibe: { pct: 82 }, ...extra });

const rereadDecks = () => reread(proposalKeys.group(CREW.id));

/** The deck on Competitive, as the page opens — its read drawn, and the tab saying its kind. */
const onCompetitive = () => menuTab('Games');

/**
 * The deck moved to For fun in the Games tab's menu (#862), and the card drawn there — its stack
 * landed, so it answers and opens (#863).
 */
async function switchToForFun(card: Wire['DeckCardSchema']) {
  await pickKind('Games', 'For fun');
  expect(await screen.findByTestId(`game-card-${card.proposal_id}`)).toBeTruthy();
  landTheSwap();
}

const GAMES_NEW = 'Games, 1 new with somebody In';

describe('Games’ badge — the cards with somebody In you haven’t seen, across both kinds (#850)', () => {
  it('counts the other kind’s card, says it is new, and draws nothing on the tab shown', async () => {
    dealt = { forFun: [forFunIn()] };
    await launchOnThePage();

    // On Games, on Competitive: the tab shown draws no badge, even for the other kind's card.
    expect(await onCompetitive()).toBeTruthy();
    act(() => jest.advanceTimersByTime(0));
    expect(drawnCount(await tabNamed('Games, Competitive', true))).toBeNull();

    await visit(FILL_IN);

    const counted = await tabNamed(GAMES_NEW, false);
    expect(drawnCount(counted)?.props.children).toBe(1);
  });

  it('marks the whole deck of the kind on screen, not only the card on top', async () => {
    dealt = { competitive: [kubaIn(), kubaIn()], forFun: [forFunIn()] };
    await launchOnThePage();
    expect(await onCompetitive()).toBeTruthy();

    await visit(FILL_IN);

    // Both Competitive cards were seen as the page opened; the For-fun one was not.
    expect(await tabNamed(GAMES_NEW, false)).toBeTruthy();
  });

  it('is not cleared by a visit on the other kind — Marta’s walk', async () => {
    // Her switch is on Competitive, and Kuba says yes on a For-fun card: Games 1.
    dealt = { forFun: [forFunIn()] };
    await launchOnThePage();
    await visit(FILL_IN);
    expect(await tabNamed(GAMES_NEW, false)).toBeTruthy();

    // She opens Games on Competitive and leaves: still Games 1.
    await visit(GAMES);
    expect(await onCompetitive()).toBeTruthy();
    await visit(FILL_IN);

    expect(await tabNamed(GAMES_NEW, false)).toBeTruthy();
  });

  // #862: the menu names both kinds and counts them, and that is no look at either deck.
  it('sees nothing when the Games tab’s menu is opened — the other kind’s card stays new', async () => {
    dealt = { forFun: [forFunIn()] };
    await launchOnThePage();
    expect(await onCompetitive()).toBeTruthy();

    // She opens the menu over Competitive, reads For fun's count, and picks the kind she is on.
    expect(await menuSays('Games', 'For fun, 1 game', false)).toBeTruthy();
    await pickKind('Games', 'Competitive');
    await visit(FILL_IN);

    expect(await tabNamed(GAMES_NEW, false)).toBeTruthy();
  });

  it('is cleared by switching to the kind', async () => {
    const fun = forFunIn();
    dealt = { forFun: [fun] };
    await launchOnThePage();
    await visit(FILL_IN);
    expect(await tabNamed(GAMES_NEW, false)).toBeTruthy();

    // She opens Games, switches to For fun and leaves: the badge is gone.
    await visit(GAMES);
    await switchToForFun(fun);
    await visit(FILL_IN);

    expect(drawnCount(await tabNamed('Games', false))).toBeNull();
  });

  it('keeps a card that only changed seen, and comes back for a new one', async () => {
    const fun = forFunIn();
    dealt = { forFun: [fun] };
    await launchOnThePage();
    await switchToForFun(fun);
    await visit(FILL_IN);
    expect(await tabNamed('Games', false)).toBeTruthy();

    // The seen card gains Ania's yes and a new version; a new card with somebody In is dealt on
    // Competitive, which the switch is not on.
    dealt = {
      competitive: [kubaIn()],
      forFun: [{ ...fun, in_count: 2, version_count: 2 }],
    };
    await rereadDecks();

    expect(await tabNamed(GAMES_NEW, false)).toBeTruthy();
  });

  // The code review's catch: one list for both kinds was cut back to whatever kind's read was drawn,
  // and the other kind's read held from an earlier visit can be older than the card she has seen.
  it('keeps a card seen when the switch moves to a kind whose read is older than it', async () => {
    const fun = deckCard({ kind: 'FOR_FUN', forecast: null, vibe: { pct: 82 } });
    dealt = { forFun: [fun] };
    await launchOnThePage();
    // A look at For fun, nobody In anywhere — its read stays in the cache.
    await switchToForFun(fun);
    await pickKind('Games', 'Competitive');
    expect((await onCompetitive()).props.accessibilityLabel).toBe('Games, Competitive');

    // Kuba says yes on a Competitive card, which a re-read brings while she is looking at it.
    const seenHere = kubaIn();
    dealt = { competitive: [seenHere], forFun: [fun] };
    await rereadDecks();
    expect(await screen.findByTestId(`game-card-${seenHere.proposal_id}`)).toBeTruthy();

    // On For fun again, its read from before the yes is drawn first, then read again.
    await switchToForFun(fun);
    await visit(FILL_IN);

    expect(drawnCount(await tabNamed('Games', false))).toBeNull();
  });

  // The code review's catch: a notice's kind reaches the switch a frame after the deck is drawn, and
  // a deck the page had read for the kind the switch stood on would be marked though never seen.
  it('leaves the kind the switch stood on unseen when a notice opens the page over its read', async () => {
    const fun = deckCard({ kind: 'FOR_FUN', forecast: null, vibe: { pct: 82 } });
    dealt = { forFun: [fun] };
    await launchOnThePage();
    await visit(FILL_IN);

    // While she is on Fill in, Kuba says yes on a Competitive card: the tab bar's read has it.
    dealt = { competitive: [kubaIn()], forFun: [fun] };
    await rereadDecks();
    expect(await tabNamed(GAMES_NEW, false)).toBeTruthy();

    // Back to the list. The cache keeps what the page read — the suite's navigation runs every
    // pending timer, its collection among them, so it is put back as five minutes would leave it.
    const kept = queryClient
      .getQueryCache()
      .findAll()
      .map((query) => [query.queryKey, query.state.data] as const);
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/play'));
    for (const [queryKey, data] of kept) {
      if (data !== undefined) queryClient.setQueryData(queryKey, data);
    }

    // A notice's tap opens the deck at the For-fun card.
    act(() =>
      router.push({
        pathname: '/play/group/[groupId]',
        params: { groupId: CREW.id, sport: 'padel', kind: 'forFun', card: fun.proposal_id },
      }),
    );
    expect(await screen.findByTestId(`game-card-${fun.proposal_id}`)).toBeTruthy();
    await visit(FILL_IN);

    expect(await tabNamed(GAMES_NEW, false)).toBeTruthy();
  });

  // The code review's catch: a card this build cannot draw — its game on a day it does not know —
  // is counted all the same, and a visit to its kind is what clears it.
  it('clears a card this build cannot draw with a visit to its kind', async () => {
    const drawn = forFunIn();
    const undrawable = forFunIn({
      overlap: { grade: 'HIGH', cells: overlapCells(), game: { day: 0, range: 'EVENING' } },
    });
    dealt = { forFun: [drawn, undrawable] };
    await launchOnThePage();
    await visit(FILL_IN);
    expect(await tabNamed('Games, 2 new with somebody In', false)).toBeTruthy();

    await visit(GAMES);
    await switchToForFun(drawn);
    expect(screen.queryByTestId(`game-card-${undrawable.proposal_id}`)).toBeNull();
    await visit(FILL_IN);

    expect(drawnCount(await tabNamed('Games', false))).toBeNull();
  });

  it('does not see a card dealt while a game’s details cover the page', async () => {
    const first = forFunIn();
    dealt = { forFun: [first] };
    transport.on('GET', proposalPath(first.proposal_id), neverResponds());
    await launchOnThePage();
    await switchToForFun(first);
    fireEvent.press(screen.getByRole('button', { name: 'Game details' }));
    await waitFor(() => expect(screen).toHavePathname(`${GROUP_PATH}/game/${first.proposal_id}`));

    // A second For-fun card reaches the deck, and is drawn on it, under the details.
    const second = forFunIn();
    dealt = { forFun: [first, second] };
    await rereadDecks();
    expect(await drawnUnder(`game-card-${second.proposal_id}`)).toBeTruthy();

    // Android kills the app there; the page opens on Competitive again, as a new process does.
    await relaunch();
    await visit(FILL_IN);

    expect(await tabNamed(GAMES_NEW, false)).toBeTruthy();
  });

  it('does not see a card dealt while a player’s record is open over the deck', async () => {
    const ania = ANIA();
    stubRecord(ania);
    const first = forFunIn();
    dealt = { forFun: [first] };
    await launchOnThePage();
    await switchToForFun(first);
    fireEvent.press(await screen.findByLabelText(/^ania\.k, /));
    expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();

    const second = forFunIn();
    dealt = { forFun: [first, second] };
    await rereadDecks();
    expect(await drawnUnder(`game-card-${second.proposal_id}`)).toBeTruthy();
    await relaunch();
    await visit(FILL_IN);

    expect(await tabNamed(GAMES_NEW, false)).toBeTruthy();
  });

  it('does not see a card dealt while It’s a game! is up over the deck', async () => {
    const last = forFunIn();
    const bookingId = 'a1000000-0000-4000-8000-000000000008';
    transport.on('POST', yesPath(last.proposal_id), () =>
      json<Wire['YesAnswerResponse']>({
        proposal_id: last.proposal_id,
        open_seats: 0,
        booked: { booking_id: bookingId, game_id: 'a1000000-0000-4000-8000-000000000009' },
        your_payment: null,
      }),
    );
    transport.on('GET', bookingPath(bookingId), () =>
      json(bookingDetails({ booking_id: bookingId, pool_id: CREW.id })),
    );
    dealt = { forFun: [last] };
    await launchOnThePage();
    await switchToForFun(last);

    // Her free vote is the one that fills it — and the deck re-read after it deals a card nobody
    // has seen.
    const next = forFunIn();
    dealt = { forFun: [next] };
    fireEvent.press(screen.getByRole('button', { name: 'I’m in' }));
    expect(await screen.findByTestId('its-a-game')).toBeTruthy();
    expect(await drawnUnder(`game-card-${next.proposal_id}`)).toBeTruthy();
    await relaunch();
    await visit(FILL_IN);

    expect(await tabNamed(GAMES_NEW, false)).toBeTruthy();
  });

  it('leaves a notice’s card’s kind seen, like any visit', async () => {
    const fun = forFunIn();
    dealt = { competitive: [kubaIn()], forFun: [fun] };
    await launchSignedIn();
    jest.setSystemTime(DECK_READ_AT);
    fireEvent.press(await screen.findByLabelText('Play'));

    // A notice's tap opens the deck at the For-fun card, the switch moved to its kind (#559).
    act(() =>
      router.push({
        pathname: '/play/group/[groupId]',
        params: { groupId: CREW.id, sport: 'padel', kind: 'forFun', card: fun.proposal_id },
      }),
    );
    expect(await screen.findByTestId(`game-card-${fun.proposal_id}`)).toBeTruthy();
    await visit(FILL_IN);

    // The For-fun cards were seen; the Competitive one was never on screen.
    expect(await tabNamed(GAMES_NEW, false)).toBeTruthy();
  });

  it('never reads the server’s count', async () => {
    stubGroupDeck(transport, CREW.id, (kind) => ({
      ...bothKinds({ forFun: [forFunIn()] })(kind),
      // Kept on the wire for older installed apps, and saying something else here.
      games_badge: 4,
    }));
    // `stubGroupDeck` serves an empty Fill in too; the suite's own is put back.
    stubFillIn(transport, CREW.id, () => fillIn(rescues));
    await launchOnThePage();

    await visit(FILL_IN);

    expect(await tabNamed(GAMES_NEW, false)).toBeTruthy();
  });
});
