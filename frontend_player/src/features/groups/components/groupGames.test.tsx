/**
 * **A group's Games tab, walked** — the switch, the one-time question, the stage and its answers,
 * every card type and tag the read can deal, the states around the deck, and the game's details
 * the card opens ([#553](https://github.com/Raketa02/Raketa/issues/553); the screens A2, A4.2).
 *
 * The real route tree, with the socket and the haptic motor faked at the platform edge. Swipes are
 * driven at the stage's responder by `test-support/swipe.ts`, in the order the responder system
 * calls it, and a card's flight is landed by advancing the clock past it — never polled
 * (`router-harness` memory: a JS-driven animation fires every fake millisecond).
 *
 * **Every player here has a card on file** (`stubPaymentMethod`), so a yes is a yes: a first yes
 * with nothing saved, the ten seconds of *Undo* and *It's a game!* are `proposals/components/
 * theFill.test.tsx`'s.
 *
 * **The deck is read at `DECK_READ_AT`**, Wednesday 30 September 2026 at 10:00 in Warsaw: the
 * suite pins the fake clock there once the tree is up, so the countdown and the court's day are
 * read against a known instant. A navigation runs the pending timers and moves the clock a few
 * seconds on, so a countdown is asserted to its hour and never to its minute.
 */

import { onlineManager } from '@tanstack/react-query';
import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import {
  AccessibilityInfo,
  RefreshControl,
  StyleSheet,
  type TextStyle,
  type ViewStyle,
} from 'react-native';

import { onboardingKeys } from '@/features/onboarding/types';
import { PAYMENTS_COPY } from '@/features/payments/types';
import { RECORD_TITLE } from '@/features/player_record/types';
import { PROPOSALS_COPY, proposalKeys } from '@/features/proposals/types';
import { offlineMessage } from '@/shared/errors';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { REVEAL_CEILING, theme } from '@/shared/ui';
import { BALANCE_FORECAST, LOSE_TILE, WIN_TILE } from '@/shared/vocabulary/forecastPresentation';
import {
  ANIA,
  deckCard,
  deckPath,
  kindAsked,
  DETAILS_CARD,
  DETAILS_SCREEN,
  DECK_READ_AT,
  EWA,
  groupDeck,
  hoursAfterRead,
  KAROL,
  KUBA,
  noPath,
  proposalDetails,
  proposalPath,
  rescueCard,
  stubGroupDeck,
  stubProposal,
  withYourYes,
  yesPath,
  youTile,
  ZOFIA,
} from '@/test-support/groupDeck';
import {
  GATE_USER,
  launchSignedIn,
  resetClipboard,
  resetHaptics,
  resetShare,
  stubClipboard,
  stubGate,
  stubHaptics,
  stubMyGroups,
  stubPaymentMethod,
  stubProfileOptions,
  stubProfileSurface,
  stubShare,
} from '@/test-support/onboardingRouter';
import { fakeClipboard, fakeHaptics, fakeShare, type FakeHaptics } from '@/test-support/platform';
import { inOrder, partOf } from '@/test-support/readingOrder';
import {
  menuLine,
  menuSays,
  menuTab,
  openTabMenu,
  pickKind,
  shutTabMenu,
} from '@/test-support/tabMenu';
import { clearanceAbove, pageOf, PLAYERS_BAR } from '@/test-support/tabBarReach';
import { dragTo, release, swipe } from '@/test-support/swipe';
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

import { useGameIntent } from '../store/gameIntent.store';

import { GROUPS_COPY } from './groupsCopy';

const COPY = PROPOSALS_COPY;

/** The payment setup's sheet, as a yes with nothing saved opens it (#555). */
const PAYMENTS_SETUP_TITLE = PAYMENTS_COPY.setupSheet.title;
const { commit } = theme.size.deckSwipe;

/** Past the card's flight, so the stage has told the deck it has gone. */
const PAST_THE_FLIGHT = 400;

const HIDDEN_TOO = { includeHiddenElements: true } as const;

function rating(sport: Wire['Sport'], mu: number): Wire['RatingResponse'] {
  return {
    sport,
    mu,
    sigma: 0.62,
    confidence: 28,
    range: { low: mu - 0.6, high: mu + 0.6 },
    band: { name: 'Established', lower: 2.7, upper: 3.8 },
    status: 'initial_estimate',
    engine_version: 'racketskill-v3',
    updated_at: '2026-08-14T09:00:00Z',
  };
}

const CREW: Wire['MyGroupSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000005',
  kind: 'PLAYER',
  name: 'Kazimierz crew',
  monogram: { letters: 'Kc', colour: 1 },
  sports: ['PADEL'],
  member_count: 6,
  home_club: { id: 'c0000000-0000-4000-8000-000000000001', name: 'Centrum Ruchu' },
};

function person(n: number, name: string): Wire['GroupPersonSchema'] {
  return { player_id: `e0000000-0000-4000-8000-00000000000${n}`, nickname: name };
}

/** Five of the crew rated in padel — enough for a court, so an empty deck says *Nothing picked*. */
const PAGE: Wire['GroupResponse'] = {
  ...CREW,
  link: 'https://raketa.app/join/K7PQ2MXA',
  join_policy: 'ANYONE',
  is_owner: false,
  rated_by_sport: [
    {
      sport: 'PADEL',
      rated_count: 5,
      first_rated: [
        { player_id: GATE_USER.id, nickname: 'ada' },
        person(2, 'Member 2'),
        person(3, 'Member 3'),
        person(4, 'Member 4'),
      ],
    },
  ],
  member_faces: [],
  administrator_nickname: null,
  is_administrator: false,
};

/** Karol's record, as `GET /players/{id}/record` answers when a tile opens it. */
function karolsRecord(): Wire['PlayerRecordResponse'] {
  return {
    is_self: false,
    relation: 'NONE',
    can_add_friend: true,
    nickname: 'karol.t',
    photos: [],
    area_code: 'A+050612+0019938',
    social_tags: [],
    sports: [{ sport: 'PADEL', level: 2.75, band: 'Established' }],
    skill: {
      sport: 'PADEL',
      level: 2.75,
      band: 'Established',
      confidence: 40,
      counted_games: 3,
      likely_range: { low: 2.5, high: 2.9 },
      last_five: ['WIN', 'LOSS', 'WIN'],
    },
    reliability: servedReliability({
      player_score: 88,
      band: 'HIGH',
      is_new: false,
      turned_up: 3,
      turned_up_of: 3,
    }),
    variety: { distinct_opponents: 3, times_on_court: 3 },
  };
}

let transport: Transport;
let haptics: FakeHaptics;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [rating('PADEL', 2.71)], hasPlayerProfile: true });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  stubShare(fakeShare());
  stubClipboard(fakeClipboard());
  haptics = fakeHaptics();
  stubHaptics(haptics);
  stubPaymentMethod(transport, { brand: 'visa', last_four: '4312', wallet: null });
  useGameIntent.setState({ intent: 'competitive' });
  useToastQueue.setState({ queue: [] });
});

afterEach(async () => {
  transport.restore();
  resetShare();
  resetClipboard();
  resetHaptics();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** Land on the crew's page, its Games tab reading this deck. */
async function openGames(deck: Parameters<typeof stubGroupDeck>[2] = groupDeck()) {
  stubMyGroups(transport, [CREW]);
  transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(PAGE));
  stubGroupDeck(transport, CREW.id, deck);
  await launchSignedIn();
  jest.setSystemTime(DECK_READ_AT);
  fireEvent.press(await screen.findByLabelText('Play'));
  await waitFor(() => expect(screen).toHavePathname('/play'));
  fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));
  await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));
}

/** The tile of the person with this id — the top card's, the stage's handle for a swipe. */
const tile = (playerId: string) => screen.getByTestId(`game-tile-${playerId}`);

const toasts = () => useToastQueue.getState().queue.map((toast) => [toast.message, toast.tone]);

const deckRequests = () => transport.requestsTo('GET', deckPath(CREW.id));

/**
 * **The Games tab's menu** (#862, PRD #859; the screens A1; tab menu mocks 1 and 3, illustrations):
 * the row of *Competitive · N / For fun · N* over the deck is gone, and the kind is picked from a
 * menu hanging from the selected Games tab. Its door — the kind the intent doesn't want — is
 * `groupGamesDoor.test.tsx`'s, and what the menu sees is `groupBadges.test.tsx`'s.
 */
const BOTH_KINDS: Wire['GroupDeckResponse']['segments'] = [
  { kind: 'COMPETITIVE', count: 5 },
  { kind: 'FOR_FUN', count: 1 },
];

/** Zofia's deck — *Either suits me*, both kinds live, a card of each. */
function eitherDeck() {
  const competitive = deckCard();
  const forFun = deckCard({
    kind: 'FOR_FUN',
    forecast: null,
    sides: { yours: [youTile(), KUBA()], theirs: [ANIA(), EWA()] },
  });
  const deal = (kind: Wire['SearchMode'] | undefined) =>
    groupDeck({
      kind: kind ?? 'COMPETITIVE',
      segments: BOTH_KINDS,
      cards: kind === 'FOR_FUN' ? [forFun] : [competitive],
    });
  return { competitive, forFun, deal };
}

/**
 * The deck's reads from now on: `kind`'s answered so — never, with a refusal, or with this deck —
 * and the other kind's as `others` deals it.
 */
function serveKind(
  kind: Wire['SearchMode'],
  served: 'held' | 'refused' | Wire['GroupDeckResponse'],
  others: (kind: Wire['SearchMode'] | undefined) => Wire['GroupDeckResponse'],
) {
  transport.on('GET', deckPath(CREW.id), (request) => {
    const asked = kindAsked(request);
    if (asked !== kind) return json(others(asked));
    if (served === 'held') return new Promise<Response>(() => undefined);
    if (served === 'refused') return errorResponse(429, 'rate_limited');
    return json(served);
  });
}

/** Games' chevron, wherever it is drawn — a mark, never spoken. */
const chevron = () => screen.queryByTestId('segment-chevron-games', HIDDEN_TOO);
/** The menu, as a finger and a listener reach it — not while it folds away. */
const menu = () => screen.queryByTestId('tab-menu');
/** The selected Games tab drawing no menu: its name alone, with nothing expanded. */
const gamesAlone = () => screen.findByRole('button', { name: 'Games', selected: true });

/**
 * The deck-card block standing in the stack's place while a kind picked from the menu is read (#876)
 * — the group page's own block, where today's spinner stood — or `null` where none stands.
 */
function blockInTheStack() {
  const stage = screen.queryByTestId('games-deck-stage', HIDDEN_TOO);
  return stage === null ? null : within(stage).queryByTestId('deck-skeleton', HIDDEN_TOO);
}

/** The buttons' row the block leaves bare under it, where the deck draws no buttons. */
function bareButtonsRow() {
  const block = blockInTheStack();
  return block === null ? null : within(block).queryByTestId('deck-skeleton-buttons', HIDDEN_TOO);
}

describe('the Games tab’s menu — where its chevron is drawn (#862)', () => {
  it('draws no row over the deck, and a chevron on the selected tab — spoken with the kind', async () => {
    await openGames(groupDeck({ segments: BOTH_KINDS, cards: [deckCard()] }));

    const games = await menuTab('Games');
    expect(games.props.accessibilityLabel).toBe('Games, Competitive');
    expect(games.props.accessibilityState).toEqual({ selected: true, expanded: false });
    expect(chevron()).toBeTruthy();
    // Nothing on the page names a kind while the menu is shut: no row, no count.
    expect(screen.queryByRole('button', { name: /^(Competitive|For fun),/ })).toBeNull();
    expect(screen.queryByText(/^(Competitive|For fun) · /)).toBeNull();
  });

  it('puts the weekly cap directly under the tabs, then the deck', async () => {
    const card = deckCard();
    await openGames(
      groupDeck({
        segments: BOTH_KINDS,
        cards: [card],
        capped_weeks: [{ starts_on: '2026-09-28', booked: 2 }],
      }),
    );
    const cap = 'Your 2 games this week are booked — showing next week';
    expect(await screen.findByText(cap)).toBeTruthy();

    // The tab bar, the cap line, then the deck and its buttons: no row between them.
    expect(inOrder(screen.toJSON(), ['button:Friends', cap, 'button:Not this time'])).toEqual([
      'button:Friends',
      cap,
      'button:Not this time',
    ]);
  });

  it('draws none on the tabs that are not selected, and Games is its name alone there', async () => {
    await openGames(groupDeck({ segments: BOTH_KINDS, cards: [deckCard()] }));
    expect(await menuTab('Games')).toBeTruthy();

    fireEvent.press(screen.getByRole('button', { name: /^Fill in/ }));

    expect(await screen.findByRole('button', { name: /^Fill in/, selected: true })).toBeTruthy();
    expect(chevron()).toBeNull();
    const games = screen.getByRole('button', { name: 'Games', selected: false });
    expect(games.props.accessibilityState).toEqual({ selected: false });
  });

  it('draws none while the first read is on its way — and a press on the tab opens nothing', async () => {
    stubMyGroups(transport, [CREW]);
    transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(PAGE));
    stubGroupDeck(transport, CREW.id);
    transport.on('GET', deckPath(CREW.id), neverResponds());
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('Play'));
    fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));

    // The deck's block, where a spinner stood (#875): the read timed out by the navigation and
    // asked again, so the page is revealed and the tab keeps its block.
    expect(await screen.findAllByTestId('deck-skeleton', HIDDEN_TOO)).not.toHaveLength(0);
    expect(chevron()).toBeNull();
    fireEvent.press(await gamesAlone());
    expect(screen.queryByTestId('tab-menu', HIDDEN_TOO)).toBeNull();
  });

  it('draws none after the first read failed', async () => {
    stubMyGroups(transport, [CREW]);
    transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(PAGE));
    stubGroupDeck(transport, CREW.id);
    transport.on('GET', deckPath(CREW.id), () => errorResponse(429, 'rate_limited'));
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('Play'));
    fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));

    expect(await screen.findByRole('button', { name: COPY.readAgain })).toBeTruthy();
    expect(chevron()).toBeNull();
    expect(await gamesAlone()).toBeTruthy();
  });

  it('draws none while the first-time question is up', async () => {
    await openGames(groupDeck({ segments: [], cards: [] }));

    expect(await screen.findByText('Your usual game at Padel')).toBeTruthy();
    expect(chevron()).toBeNull();
    fireEvent.press(await gamesAlone());
    expect(screen.queryByTestId('tab-menu', HIDDEN_TOO)).toBeNull();
  });
});

describe('the Games tab’s menu — its lines (#862)', () => {
  it('hangs Competitive then For fun, each with today’s count, the deck’s kind ticked', async () => {
    await openGames(groupDeck({ segments: BOTH_KINDS, cards: [deckCard()] }));
    // Counted once the chevron is drawn — that is, once the deck's own read has come back.
    expect(await menuTab('Games')).toBeTruthy();
    const asked = deckRequests().length;

    const open = await openTabMenu('Games');

    expect(await menuTab('Games', true)).toBeTruthy();
    expect(
      within(open)
        .getAllByRole('button')
        .map((line) => [line.props.accessibilityLabel, line.props.accessibilityState]),
    ).toEqual([
      ['Competitive, 5 games', { selected: true }],
      ['For fun, 1 game', { selected: false }],
    ]);
    const competitive = await menuLine('Competitive');
    expect(within(competitive).getByTestId('tab-menu-tick', HIDDEN_TOO)).toBeTruthy();
    // The count in muted mono, after the words.
    const count = within(competitive).getByText('5', HIDDEN_TOO);
    expect(StyleSheet.flatten(count.props.style as TextStyle)).toMatchObject({
      color: theme.color.muted,
      fontFamily: theme.num.tiny.fontFamily,
    });
    expect(within(await menuLine('For fun')).getByText('1', HIDDEN_TOO)).toBeTruthy();
    // Opening it asked for nothing.
    expect(deckRequests()).toHaveLength(asked);
  });

  it('shuts on a second press on the tab, with nothing changed', async () => {
    await openGames(groupDeck({ segments: BOTH_KINDS, cards: [deckCard()] }));
    await openTabMenu('Games');

    await shutTabMenu('Games');

    expect(menu()).toBeNull();
    expect(await menuTab('Games')).toBeTruthy();
    expect(useGameIntent.getState().intent).toBe('competitive');
  });

  it('shuts on a press on the deck under it, which answers no card', async () => {
    const card = deckCard();
    await openGames(groupDeck({ segments: BOTH_KINDS, cards: [card] }));
    await screen.findByTestId(`game-card-${card.proposal_id}`);
    await openTabMenu('Games');

    // Under the menu the deck takes no touch: its buttons do nothing.
    fireEvent.press(screen.getByRole('button', { name: 'Not this time' }));
    expect(menu()).toBeTruthy();
    fireEvent.press(screen.getByTestId('tab-menu-catcher-below'));

    expect(menu()).toBeNull();
    expect(screen.getByTestId(`game-card-${card.proposal_id}`)).toBeTruthy();
    expect(transport.requestsTo('POST', noPath(card.proposal_id))).toHaveLength(0);
  });
});

describe('the Games tab’s menu — picking a kind (#862)', () => {
  it('swaps the deck to the other kind in place when it was read, and stays on Games', async () => {
    const { competitive, forFun, deal } = eitherDeck();
    await openGames(deal);
    await screen.findByTestId(`game-card-${competitive.proposal_id}`);
    await pickKind('Games', 'For fun');
    expect(await screen.findByTestId(`game-card-${forFun.proposal_id}`)).toBeTruthy();
    expect(useGameIntent.getState().intent).toBe('forFun');

    // Competitive was read a moment ago: it comes in once For fun's stack has gone out, with no
    // skeleton between them (the swap itself is the next describe's, #863, #876).
    await pickKind('Games', 'Competitive');

    expect(menu()).toBeNull();
    expect(await screen.findByTestId(`game-card-${competitive.proposal_id}`)).toBeTruthy();
    expect(blockInTheStack()).toBeNull();
    expect(screen).toHavePathname(`/play/group/${CREW.id}`);
    expect(await menuTab('Games')).toBeTruthy();
    expect((await menuTab('Games')).props.accessibilityLabel).toBe('Games, Competitive');
  });

  it('reads a kind not read yet under the deck-card skeleton, the tabs, the chevron and the menu still up', async () => {
    const { competitive, forFun, deal } = eitherDeck();
    await openGames(deal);
    await screen.findByTestId(`game-card-${competitive.proposal_id}`);
    serveKind('FOR_FUN', 'held', deal);

    await pickKind('Games', 'For fun');

    await waitFor(() => expect(blockInTheStack()).not.toBeNull());
    expect(screen.queryByLabelText(COPY.reading)).toBeNull();
    expect(screen.queryByTestId(`game-card-${competitive.proposal_id}`)).toBeNull();
    // The menu stays, drawn off Competitive's read, which carries the same counts.
    expect((await menuTab('Games')).props.accessibilityLabel).toBe('Games, For fun');
    expect(chevron()).toBeTruthy();
    expect(await menuSays('Games', 'For fun, 1 game', true)).toBeTruthy();

    // And picking back mid-read draws Competitive's cards at once.
    await pickKind('Games', 'Competitive');
    expect(screen.getByTestId(`game-card-${competitive.proposal_id}`)).toBeTruthy();
    expect(screen.queryByTestId(`game-card-${forFun.proposal_id}`)).toBeNull();
    expect(blockInTheStack()).toBeNull();
  });

  it('says why a kind’s read failed, with its retry, and the menu still works', async () => {
    const { competitive, forFun, deal } = eitherDeck();
    await openGames(deal);
    await screen.findByTestId(`game-card-${competitive.proposal_id}`);
    serveKind('FOR_FUN', 'refused', deal);

    await pickKind('Games', 'For fun');

    expect(await screen.findByRole('button', { name: COPY.readAgain })).toBeTruthy();
    expect(chevron()).toBeTruthy();
    expect(await menuSays('Games', 'Competitive, 5 games', false)).toBeTruthy();

    // The retry reads it again…
    serveKind('FOR_FUN', deal('FOR_FUN'), deal);
    fireEvent.press(screen.getByRole('button', { name: COPY.readAgain }));
    expect(await screen.findByTestId(`game-card-${forFun.proposal_id}`)).toBeTruthy();
    // …and the menu goes back as it came.
    await pickKind('Games', 'Competitive');
    expect(await screen.findByTestId(`game-card-${competitive.proposal_id}`)).toBeTruthy();
  });

  it('just shuts on the kind it stands on — nothing read again', async () => {
    await openGames(groupDeck({ segments: BOTH_KINDS, cards: [deckCard()] }));
    await openTabMenu('Games');
    const asked = deckRequests().length;

    fireEvent.press(await menuLine('Competitive'));

    expect(menu()).toBeNull();
    expect(useGameIntent.getState().intent).toBe('competitive');
    expect(deckRequests()).toHaveLength(asked);
  });

  it('keeps the kind picked while the app is open', async () => {
    const { forFun, deal } = eitherDeck();
    await openGames(deal);

    await pickKind('Games', 'For fun');

    expect(await screen.findByTestId(`game-card-${forFun.proposal_id}`)).toBeTruthy();
    expect(deckRequests().some((request) => request.path.includes('kind=FOR_FUN'))).toBe(true);
    expect(useGameIntent.getState().intent).toBe('forFun');
  });

  // The other kind is a door with no number (#740) — `groupGamesDoor.test.tsx` walks it.
  it('opens on the kind a one-kind intent wants, whatever the menu last stood on', async () => {
    const funCard = deckCard({ kind: 'FOR_FUN' });
    await openGames((kind) =>
      groupDeck({
        segments: [{ kind: 'FOR_FUN', count: 1 }],
        cards: kind === 'FOR_FUN' ? [funCard] : [],
      }),
    );

    expect(await screen.findByTestId(`game-card-${funCard.proposal_id}`)).toBeTruthy();
    expect((await menuTab('Games')).props.accessibilityLabel).toBe('Games, For fun');
    expect(await menuSays('Games', 'For fun, 1 game', true)).toBeTruthy();
    expect(await menuSays('Games', 'Competitive, not a kind you play', false)).toBeTruthy();
  });

  it('moves to a notice’s card’s kind directly, and shuts a menu left open', async () => {
    const { competitive, forFun, deal } = eitherDeck();
    await openGames(deal);
    await screen.findByTestId(`game-card-${competitive.proposal_id}`);
    await openTabMenu('Games');

    act(() =>
      router.push({
        pathname: '/play/group/[groupId]',
        params: { groupId: CREW.id, sport: 'padel', kind: 'forFun', card: forFun.proposal_id },
      }),
    );

    expect(await screen.findByTestId(`game-card-${forFun.proposal_id}`)).toBeTruthy();
    expect(menu()).toBeNull();
    expect((await menuTab('Games')).props.accessibilityLabel).toBe('Games, For fun');
    expect(useGameIntent.getState().intent).toBe('forFun');
  });
});

/**
 * **Picking the other kind swaps the deck in place** (#863, PRD #859; the tab menu log §5.1–§5.2):
 * the stack goes out, down and fading, and the other kind's rises into its place — the cards only,
 * the buttons staying where both kinds have them. **Asserted at the end of each beat, never
 * mid-motion**, and each beat is its own advance: the second is set going by the first one's end,
 * and state set inside an advance is drawn only when it is over (`player-reanimated-tests`).
 */
describe('the Games deck swapped in place (#863)', () => {
  const { out: OUT, in: IN, rise: RISE } = theme.motion.kindSwap;
  const AT_REST = { opacity: 1, down: 0 };

  /** A view's style, its layers merged — what the stage's own suite reads its cards by. */
  function styleOf(view: { readonly props: { readonly style: unknown } }): ViewStyle {
    const styles = [view.props.style].flat(3) as (ViewStyle | undefined)[];
    return Object.assign({}, ...styles.filter((entry) => entry !== undefined)) as ViewStyle;
  }

  /** How the deck's stack stands in its layer: how faded, and how far down. */
  function stackStands(): { readonly opacity: number; readonly down: number } {
    const style = styleOf(screen.getByTestId('games-deck-stack', HIDDEN_TOO));
    const transform = (style.transform ?? []) as readonly Record<string, unknown>[];
    const down = transform.find((entry) => 'translateY' in entry)?.['translateY'];
    return { opacity: Number(style.opacity ?? 1), down: Number(down ?? 0) };
  }

  /** How seen the buttons are — `undefined` where none are drawn. */
  function buttonsSeen(): number | undefined {
    const layer = screen.queryByTestId('games-deck-buttons', HIDDEN_TOO);
    return layer === null ? undefined : Number(styleOf(layer).opacity ?? 1);
  }

  /** The stack going out, to its end. */
  const goneOut = () => act(() => jest.advanceTimersByTime(OUT));
  /** The other kind's stack coming in, to its end: it has landed. */
  const cameIn = () => act(() => jest.advanceTimersByTime(IN));

  const passButton = () => screen.queryByRole('button', { name: 'Not this time' });

  /** Zofia's competitive card, then Kuba's for-fun one: a tile of each to swipe by. */
  const ZOFIAS = ZOFIA().player_id;
  const KUBAS = KUBA().player_id;

  /**
   * `kind`'s read held from now on, until the suite lands it — so the swap's skeleton is certain to
   * stand when the stack has gone out — and the other kind's as `others` deals it.
   */
  function holdRead(
    kind: Wire['SearchMode'],
    others: (asked: Wire['SearchMode'] | undefined) => Wire['GroupDeckResponse'],
  ): (read: Wire['GroupDeckResponse']) => Promise<void> {
    let answer: ((read: Response) => void) | undefined;
    transport.on('GET', deckPath(CREW.id), (request) =>
      kindAsked(request) === kind
        ? new Promise<Response>((resolve) => {
            answer = resolve;
          })
        : json(others(kindAsked(request))),
    );
    return async (read) => {
      await act(async () => {
        answer?.(json(read));
      });
    };
  }

  /** The deck's answers from now on, a yes on either card taken. */
  function takeYeses(...cards: readonly Wire['DeckCardSchema'][]) {
    for (const card of cards) {
      transport.on('POST', yesPath(card.proposal_id), () =>
        json({ proposal_id: card.proposal_id, open_seats: 2 }),
      );
      transport.on('POST', noPath(card.proposal_id), () => noContent());
    }
  }

  it('sends the stack out, then brings the other kind’s in — its top card answering once it has landed', async () => {
    const { competitive, forFun, deal } = eitherDeck();
    takeYeses(competitive, forFun);
    await openGames(deal);
    await screen.findByTestId(`game-card-${competitive.proposal_id}`);

    await pickKind('Games', 'For fun');

    // Going out, it is still Competitive's stack on screen — and it answers nothing (a request
    // sets out a tick after the answer, so the walk's end says so).
    expect(screen.getByTestId(`game-card-${competitive.proposal_id}`)).toBeTruthy();
    swipe(tile(ZOFIAS), commit + 40);

    // Gone out: down `rise` and faded — and the For-fun stack comes up from there.
    goneOut();
    expect(stackStands()).toEqual({ opacity: 0, down: RISE });
    expect(await screen.findByTestId(`game-card-${forFun.proposal_id}`)).toBeTruthy();
    expect(screen.queryByTestId(`game-card-${competitive.proposal_id}`, HIDDEN_TOO)).toBeNull();
    // Still coming in, it answers nothing either.
    swipe(tile(KUBAS), commit + 40);
    cameIn();

    expect(stackStands()).toEqual(AT_REST);
    expect(blockInTheStack()).toBeNull();
    expect(swipe(tile(KUBAS), commit + 40)).toBe(true);
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));
    await waitFor(() =>
      expect(transport.requestsTo('POST', yesPath(forFun.proposal_id))).toHaveLength(1),
    );
    expect(transport.requestsTo('POST', yesPath(competitive.proposal_id))).toHaveLength(0);
  });

  /**
   * The code review's catch: the flight (240 ms) outlasts the stack going out (200), and a card
   * answered just before the pick left the other kind's read — the one drawn by then.
   */
  it('lets a card still in flight fly out with its own stack, and leave its own kind’s read', async () => {
    const { competitive, forFun, deal } = eitherDeck();
    takeYeses(competitive, forFun);
    await openGames(deal);
    await screen.findByTestId(`game-card-${competitive.proposal_id}`);

    expect(swipe(tile(ZOFIAS), commit + 40)).toBe(true);
    await pickKind('Games', 'For fun');
    goneOut();

    // The beat is over, and the card is still flying: Competitive is drawn until it has flown.
    expect(screen.getByTestId(`game-card-${competitive.proposal_id}`, HIDDEN_TOO)).toBeTruthy();
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT - OUT));

    const competitiveRead = queryClient.getQueryData<{
      readonly cards: readonly { proposalId: string }[];
    }>(proposalKeys.deck(CREW.id, 'padel', 'competitive'));
    expect(competitiveRead?.cards.map((card) => card.proposalId)).toEqual([]);
    expect(await screen.findByTestId(`game-card-${forFun.proposal_id}`)).toBeTruthy();
    cameIn();
    expect(stackStands()).toEqual(AT_REST);
  });

  it('keeps the buttons when both kinds deal cards, answering nothing until the stack has landed', async () => {
    const { competitive, forFun, deal } = eitherDeck();
    takeYeses(competitive, forFun);
    await openGames(deal);
    await screen.findByTestId(`game-card-${competitive.proposal_id}`);

    await pickKind('Games', 'For fun');

    fireEvent.press(passButton()!);
    expect(buttonsSeen()).toBe(1);
    goneOut();
    await screen.findByTestId(`game-card-${forFun.proposal_id}`);
    expect(buttonsSeen()).toBe(1);
    fireEvent.press(passButton()!);
    cameIn();
    expect(buttonsSeen()).toBe(1);
    expect(transport.requestsTo('POST', noPath(competitive.proposal_id))).toHaveLength(0);
    expect(transport.requestsTo('POST', noPath(forFun.proposal_id))).toHaveLength(0);

    // Landed, they answer the card that came in.
    fireEvent.press(passButton()!);
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));
    await waitFor(() =>
      expect(transport.requestsTo('POST', noPath(forFun.proposal_id))).toHaveLength(1),
    );
  });

  it('brings the starting card in when the other kind deals nothing, and the buttons go', async () => {
    const card = deckCard();
    await openGames((kind) =>
      groupDeck({
        kind: kind ?? 'COMPETITIVE',
        segments: [
          { kind: 'COMPETITIVE', count: 1 },
          { kind: 'FOR_FUN', count: 0 },
        ],
        cards: kind === 'FOR_FUN' ? [] : [card],
      }),
    );
    await screen.findByTestId(`game-card-${card.proposal_id}`);

    await pickKind('Games', 'For fun');
    // Going out, the stack and its buttons are still Competitive's.
    expect(screen.getByTestId(`game-card-${card.proposal_id}`)).toBeTruthy();
    expect(buttonsSeen()).toBe(1);
    goneOut();

    expect(await screen.findByText('Nothing picked right now')).toBeTruthy();
    expect(buttonsSeen()).toBeUndefined();
    cameIn();
    expect(stackStands()).toEqual(AT_REST);
    expect(passButton()).toBeNull();
  });

  it('brings the buttons back in, from the starting card to a kind with cards', async () => {
    const card = deckCard({
      kind: 'FOR_FUN',
      forecast: null,
      sides: { yours: [youTile(), KUBA()], theirs: [ANIA(), EWA()] },
    });
    takeYeses(card);
    const deal = (kind: Wire['SearchMode'] | undefined) =>
      groupDeck({
        kind: kind ?? 'COMPETITIVE',
        segments: [
          { kind: 'COMPETITIVE', count: 0 },
          { kind: 'FOR_FUN', count: 1 },
        ],
        cards: kind === 'FOR_FUN' ? [card] : [],
      });
    await openGames(deal);
    // Either suits her, so Competitive is live with nothing in it.
    expect(await screen.findByText('Nothing picked right now')).toBeTruthy();
    expect(passButton()).toBeNull();
    const land = holdRead('FOR_FUN', deal);

    await pickKind('Games', 'For fun');
    // Going out, it is the starting card that goes.
    expect(screen.getByText('Nothing picked right now')).toBeTruthy();
    goneOut();
    // The starting card had none, so none stand under the block: it leaves their row bare, as the
    // group page's own block does, and they come in with the cards.
    expect(blockInTheStack()).not.toBeNull();
    expect(bareButtonsRow()).not.toBeNull();
    expect(buttonsSeen()).toBeUndefined();
    await land(deal('FOR_FUN'));
    await screen.findByTestId(`game-card-${card.proposal_id}`);
    cameIn();

    expect(blockInTheStack()).toBeNull();
    expect(buttonsSeen()).toBe(1);
    expect(swipe(tile(KUBAS), commit + 40)).toBe(true);
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));
    await waitFor(() =>
      expect(transport.requestsTo('POST', yesPath(card.proposal_id))).toHaveLength(1),
    );
  });

  /**
   * **The uncached path** (#876, the loading shimmer log §10, Q26): the group page's deck-card block
   * stands where today's spinner stood, and the stack's rise replaces the shimmer's cross-fade —
   * asserted at the end of each beat.
   */
  it('stands the deck-card skeleton in the stack’s place while a kind not read yet is read, then brings it in', async () => {
    const { competitive, forFun, deal } = eitherDeck();
    takeYeses(forFun);
    await openGames(deal);
    await screen.findByTestId(`game-card-${competitive.proposal_id}`);
    const land = holdRead('FOR_FUN', deal);

    await pickKind('Games', 'For fun');
    goneOut();

    expect(blockInTheStack()).not.toBeNull();
    expect(screen.queryByLabelText(COPY.reading)).toBeNull();
    expect(stackStands()).toEqual({ opacity: 0, down: RISE });
    expect(screen.queryByTestId(`game-card-${competitive.proposal_id}`, HIDDEN_TOO)).toBeNull();
    // Both kinds deal cards: the buttons stay under it, answering nothing — no bare row of its own.
    expect(buttonsSeen()).toBe(1);
    expect(bareButtonsRow()).toBeNull();

    await land(deal('FOR_FUN'));
    expect(await screen.findByTestId(`game-card-${forFun.proposal_id}`)).toBeTruthy();
    expect(blockInTheStack()).toBeNull();
    cameIn();

    expect(stackStands()).toEqual(AT_REST);
    expect(swipe(tile(KUBAS), commit + 40)).toBe(true);
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));
    await waitFor(() =>
      expect(transport.requestsTo('POST', yesPath(forFun.proposal_id))).toHaveLength(1),
    );
  });

  it('goes out to today’s failure when that read is refused, and a retry draws the deck directly', async () => {
    const { competitive, forFun, deal } = eitherDeck();
    await openGames(deal);
    await screen.findByTestId(`game-card-${competitive.proposal_id}`);
    serveKind('FOR_FUN', 'refused', deal);

    await pickKind('Games', 'For fun');
    // The stack goes out first, whatever the read will say.
    expect(screen.getByTestId(`game-card-${competitive.proposal_id}`)).toBeTruthy();
    goneOut();

    expect(await screen.findByRole('button', { name: COPY.readAgain })).toBeTruthy();
    expect(passButton()).toBeNull();
    expect(screen.queryByTestId('games-deck-stack')).toBeNull();

    serveKind('FOR_FUN', deal('FOR_FUN'), deal);
    fireEvent.press(screen.getByRole('button', { name: COPY.readAgain }));
    expect(await screen.findByTestId(`game-card-${forFun.proposal_id}`)).toBeTruthy();
    expect(stackStands()).toEqual(AT_REST);
  });

  /**
   * A skeleton stands only while a read is in flight (the loading shimmer log §4): one held for a
   * connection says it resumes, where the swap's spinner used to turn for ever (#875's review).
   */
  it('says a kind picked offline waits for a connection, in the stack’s place, and brings it in once back', async () => {
    const { competitive, forFun, deal } = eitherDeck();
    await openGames(deal);
    await screen.findByTestId(`game-card-${competitive.proposal_id}`);

    act(() => onlineManager.setOnline(false));
    try {
      await pickKind('Games', 'For fun');
      goneOut();

      const stage = within(screen.getByTestId('games-deck-stage', HIDDEN_TOO));
      expect(await stage.findByText(offlineMessage('resumes'))).toBeTruthy();
      expect(blockInTheStack()).toBeNull();
      expect(stackStands()).toEqual({ opacity: 0, down: RISE });
    } finally {
      act(() => onlineManager.setOnline(true));
    }

    expect(await screen.findByTestId(`game-card-${forFun.proposal_id}`)).toBeTruthy();
    expect(screen.queryByText(offlineMessage('resumes'))).toBeNull();
    cameIn();
    expect(stackStands()).toEqual(AT_REST);
  });

  // The code review's catch: an answer held offline already says it above the deck.
  it('says it once when an answer is held offline too — on the line above the deck', async () => {
    const { competitive, deal } = eitherDeck();
    takeYeses(competitive);
    await openGames(deal);
    await screen.findByTestId(`game-card-${competitive.proposal_id}`);

    act(() => onlineManager.setOnline(false));
    try {
      fireEvent.press(screen.getByRole('button', { name: COPY.yes }));
      act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));
      expect(await screen.findByText(offlineMessage('resumes'))).toBeTruthy();

      await pickKind('Games', 'For fun');
      goneOut();

      expect(stackStands()).toEqual({ opacity: 0, down: RISE });
      expect(screen.getAllByText(offlineMessage('resumes'))).toHaveLength(1);
      expect(blockInTheStack()).toBeNull();
    } finally {
      act(() => onlineManager.setOnline(true));
    }
  });

  // The code review's catch: a Games tab out of sight draws no skeleton (#875), the swap's neither.
  it('draws no block while another tab is on, and stands it again back on Games', async () => {
    const { competitive, deal } = eitherDeck();
    await openGames(deal);
    await screen.findByTestId(`game-card-${competitive.proposal_id}`);
    holdRead('FOR_FUN', deal);

    await pickKind('Games', 'For fun');
    goneOut();
    expect(blockInTheStack()).not.toBeNull();

    fireEvent.press(screen.getByRole('button', { name: /^Fill in/ }));
    expect(await screen.findByRole('button', { name: /^Fill in/, selected: true })).toBeTruthy();
    expect(blockInTheStack()).toBeNull();

    fireEvent.press(screen.getByRole('button', { name: 'Games', selected: false }));
    await waitFor(() => expect(blockInTheStack()).not.toBeNull());
  });

  it('draws a notice’s kind directly — no stack goes out, none comes in', async () => {
    const { competitive, forFun, deal } = eitherDeck();
    await openGames(deal);
    await screen.findByTestId(`game-card-${competitive.proposal_id}`);
    // For fun read once, so the notice's kind is drawn from the cache on its first frame.
    await pickKind('Games', 'For fun');
    goneOut();
    await screen.findByTestId(`game-card-${forFun.proposal_id}`);
    cameIn();
    await pickKind('Games', 'Competitive');
    goneOut();
    await screen.findByTestId(`game-card-${competitive.proposal_id}`);
    cameIn();

    act(() =>
      router.push({
        pathname: '/play/group/[groupId]',
        params: { groupId: CREW.id, sport: 'padel', kind: 'forFun', card: forFun.proposal_id },
      }),
    );

    expect(await screen.findByTestId(`game-card-${forFun.proposal_id}`)).toBeTruthy();
    expect(stackStands()).toEqual(AT_REST);
    expect(screen.queryByTestId(`game-card-${competitive.proposal_id}`, HIDDEN_TOO)).toBeNull();
  });

  describe('under reduced motion', () => {
    // Answered back as the phone usually answers, never restored: `spyOn` on the preset's own mock
    // hands back that mock, and restoring it strips its answer for every suite after this one.
    beforeEach(() => {
      jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(true);
    });
    afterEach(() => {
      jest.spyOn(AccessibilityInfo, 'isReduceMotionEnabled').mockResolvedValue(false);
    });

    it('crossfades: the stack fades out where it stands, and the other kind’s fades in there', async () => {
      const { competitive, forFun, deal } = eitherDeck();
      takeYeses(forFun);
      await openGames(deal);
      await screen.findByTestId(`game-card-${competitive.proposal_id}`);

      await pickKind('Games', 'For fun');
      goneOut();

      expect(stackStands()).toEqual({ opacity: 0, down: 0 });
      expect(await screen.findByTestId(`game-card-${forFun.proposal_id}`)).toBeTruthy();
      cameIn();

      expect(stackStands()).toEqual(AT_REST);
      expect(swipe(tile(KUBAS), commit + 40)).toBe(true);
      act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));
      await waitFor(() =>
        expect(transport.requestsTo('POST', yesPath(forFun.proposal_id))).toHaveLength(1),
      );
    });
  });
});

describe('a player with no intent for the sport', () => {
  it('is asked once, inline, and the deck is read again once they answer', async () => {
    let declared = false;
    const card = deckCard();
    transport.on('PUT', '/api/v1/play-intents/PADEL', () => {
      declared = true;
      return json({ sport: 'PADEL', intent: 'NO_PREFERENCE' });
    });
    await openGames(() =>
      declared ? groupDeck({ cards: [card] }) : groupDeck({ segments: [], cards: [] }),
    );

    expect(await screen.findByText('Your usual game at Padel')).toBeTruthy();
    expect(screen.queryByText(/^Competitive ·/)).toBeNull();

    fireEvent.press(screen.getByRole('button', { name: 'Either suits me, your usual at Padel' }));

    expect(await screen.findByTestId(`game-card-${card.proposal_id}`)).toBeTruthy();
    expect(transport.requestsTo('PUT', '/api/v1/play-intents/PADEL')[0]?.body).toEqual({
      intent: 'NO_PREFERENCE',
      surface: 'DECK',
    });
  });
});

describe('the states around the deck', () => {
  it('keeps the starting card when nothing is dealt, and Nothing picked gains Post a game (#558)', async () => {
    await openGames();

    expect(await screen.findByText('Nothing picked right now')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Post a game', disabled: false })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Share the link' })).toBeTruthy();
  });

  it('says the week is full above the deck', async () => {
    await openGames(
      groupDeck({ cards: [deckCard()], capped_weeks: [{ starts_on: '2026-09-28', booked: 2 }] }),
    );

    expect(
      await screen.findByText('Your 2 games this week are booked — showing next week'),
    ).toBeTruthy();
  });

  // The Games tab's badge — what is new with somebody In, across both kinds — is walked in
  // `groupBadges.test.tsx` (#850): the tab on screen draws none.

  it('says why a read failed, and reads again on the retry', async () => {
    // Refused until the player asks again: the page reads the deck ahead while the group is read,
    // and the tab's own read meets the refusal too.
    let refusing = true;
    stubMyGroups(transport, [CREW]);
    transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(PAGE));
    transport.on('GET', deckPath(CREW.id), () =>
      refusing ? errorResponse(429, 'rate_limited') : json(groupDeck({ cards: [deckCard()] })),
    );
    await launchSignedIn();
    // The deck's own clock, as `openGames` pins it: on the real one the card's book-by — two days
    // after the read — has passed since 2 October 2026, and the retried deck draws nothing.
    jest.setSystemTime(DECK_READ_AT);
    fireEvent.press(await screen.findByLabelText('Play'));
    fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));

    const retry = await screen.findByRole('button', { name: COPY.readAgain });
    refusing = false;
    fireEvent.press(retry);

    expect(await screen.findByLabelText(COPY.details)).toBeTruthy();
  });
});

/**
 * **The deck stands above the bar** (#881, ADR-0210 §3): the bar floats over the page's foot, so the
 * stage takes what the page leaves down to the buttons and the buttons stand 15 above the bar's
 * reach — the gutter they stood at above the bar before it floated. So does the block that stands
 * where the deck will, ending where the buttons will.
 */
describe('the deck above the bar (#881)', () => {
  it('stands its ✕ · i · ✓ 15 above the bar, the last thing on the page', async () => {
    const card = deckCard();
    await openGames(groupDeck({ cards: [card] }));
    await screen.findByTestId(`game-card-${card.proposal_id}`);

    const page = pageOf(screen.getByTestId('games-deck-buttons', HIDDEN_TOO));

    expect(page?.props.testID).toBe('games-deck-body');
    expect(clearanceAbove(page as NonNullable<typeof page>)).toBe(theme.space.lg);
  });

  it('ends the first read’s block where the buttons will stand', async () => {
    stubMyGroups(transport, [CREW]);
    transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(PAGE));
    transport.on('GET', deckPath(CREW.id), neverResponds());
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('Play'));
    fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));

    const [block] = await screen.findAllByTestId('deck-skeleton', HIDDEN_TOO);
    const end = StyleSheet.flatten((block as NonNullable<typeof block>).props.style).paddingBottom;

    expect(end).toBe(PLAYERS_BAR + theme.space.lg);
  });
});

/**
 * **The page shimmers until it is built, then reveals together** (#875; PRD #867; the loading
 * shimmer log §10) — the header and the tab bar, which wait for the group and the sport, then Games'
 * deck. Reads are held on their way by the fake server (`transport.hold`, deaf to the client's abort,
 * so the navigation's timeout never fires them) and landed when the walk says. That navigation runs
 * every pending timer, the 2.5 s ceiling's included once set, so a walk that holds the header reads
 * the rule as it holds from the top: the deck is never revealed before the header. The rule's own
 * table and its ceiling's timer are `groupPage.test.ts`'s and `Reveal.test.tsx`'s.
 */
describe('the page while its first reads are out (#875)', () => {
  const GROUP_PATH = `/api/v1/groups/${CREW.id}`;
  const RATINGS_PATH = '/api/v1/ratings';
  const padelRating = rating('PADEL', 2.71);
  /** Past Query's first retry's backoff (`queryClient.ts`'s `retryDelay`). */
  const RETRY = 2_000;
  /** A part's skeleton, standing in its `Reveal` until the fade has taken it — `null` once gone. */
  const skeletonOf = (part: 'group-tabs-reveal' | 'group-games-reveal') => {
    const reveal = screen.queryByTestId(part, HIDDEN_TOO);
    return reveal === null ? null : within(reveal).queryByTestId('reveal-skeleton', HIDDEN_TOO);
  };
  const headerShimmers = () => screen.queryByTestId('group-header-skeleton', HIDDEN_TOO) !== null;
  /** The header, by what it opens — the list's card under the page is named by the group too. */
  const header = () => screen.queryByHintText(GROUPS_COPY.group.openInfo);
  const pill = () => screen.queryByRole('button', { name: 'Sport: Padel' });
  const tabBar = () => screen.queryByRole('button', { name: /^Fill in/ });
  const deck = () => screen.queryByRole('button', { name: 'Not this time' });
  const pastTheFade = () => act(() => jest.advanceTimersByTime(theme.motion.fade + 16));

  /** Play, then the crew's card pressed with these reads held on their way. */
  async function openHolding(paths: readonly string[]) {
    stubMyGroups(transport, [CREW]);
    transport.on('GET', GROUP_PATH, () => json(PAGE));
    stubGroupDeck(transport, CREW.id, groupDeck({ cards: [deckCard()] }));
    await launchSignedIn();
    jest.setSystemTime(DECK_READ_AT);
    fireEvent.press(await screen.findByLabelText('Play'));
    await waitFor(() => expect(screen).toHavePathname('/play'));
    const held = paths.map((path) => transport.hold('GET', path));
    fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));
    return held;
  }

  afterEach(() => onlineManager.setOnline(true));

  it('stands a circle and a name bar by the real way back, the tab bar’s shape and one deck-card block', async () => {
    await openHolding([GROUP_PATH, deckPath(CREW.id)]);

    expect(headerShimmers()).toBe(true);
    expect(header()).toBeNull();
    expect(pill()).toBeNull();
    expect(skeletonOf('group-tabs-reveal')).not.toBeNull();
    expect(tabBar()).toBeNull();
    const block = skeletonOf('group-games-reveal');
    expect(block).not.toBeNull();
    expect(within(block!).getByTestId('deck-skeleton', HIDDEN_TOO)).toBeTruthy();
    expect(deck()).toBeNull();

    // The way back is the real one, and answers while the page shimmers.
    fireEvent.press(screen.getByRole('button', { name: GROUPS_COPY.group.back }));
    await waitFor(() => expect(screen).toHavePathname('/play'));
  });

  it('reveals the header, the tabs and the deck together — never the deck first, though it lands first', async () => {
    const [group, cards] = await openHolding([GROUP_PATH, deckPath(CREW.id)]);
    // The deck sets out beside the group's read, so it can land first.
    expect(transport.requestsTo('GET', deckPath(CREW.id)).length).toBeGreaterThan(0);

    await act(async () => cards!.land());
    expect(headerShimmers()).toBe(true);
    expect(skeletonOf('group-games-reveal')).not.toBeNull();
    expect(deck()).toBeNull();

    await act(async () => group!.land());

    expect(await screen.findByHintText(GROUPS_COPY.group.openInfo)).toBeTruthy();
    expect(headerShimmers()).toBe(false);
    expect(pill()).not.toBeNull();
    expect(tabBar()).not.toBeNull();
    expect(deck()).not.toBeNull();
    pastTheFade();
    expect(skeletonOf('group-tabs-reveal')).toBeNull();
    expect(skeletonOf('group-games-reveal')).toBeNull();
  });

  it('from the ceiling, brings the header and the tabs in while the deck keeps its block', async () => {
    const [cards] = await openHolding([deckPath(CREW.id)]);
    act(() => jest.advanceTimersByTime(REVEAL_CEILING));

    expect(header()).not.toBeNull();
    expect(pill()).not.toBeNull();
    expect(tabBar()).not.toBeNull();
    expect(skeletonOf('group-games-reveal')).not.toBeNull();
    expect(deck()).toBeNull();

    await act(async () => cards!.land());

    expect(await screen.findByRole('button', { name: 'Not this time' })).toBeTruthy();
    pastTheFade();
    expect(skeletonOf('group-games-reveal')).toBeNull();
  });

  /**
   * The ratings were read at launch; asked again here — reset under Home's own observer — they are
   * held on their way while the page opens, so the group lands before the sport is known.
   */
  async function openWithTheSportOut(ratings: () => Response | Promise<Response>) {
    stubMyGroups(transport, [CREW]);
    transport.on('GET', GROUP_PATH, () => json(PAGE));
    stubGroupDeck(transport, CREW.id, groupDeck({ cards: [deckCard()] }));
    await launchSignedIn();
    jest.setSystemTime(DECK_READ_AT);
    fireEvent.press(await screen.findByLabelText('Play'));
    await waitFor(() => expect(screen).toHavePathname('/play'));
    transport.on('GET', RATINGS_PATH, ratings);
    const held = transport.hold('GET', RATINGS_PATH);
    await act(async () => {
      void queryClient.resetQueries({ queryKey: onboardingKeys.ratings() });
    });
    fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));
    // The group is in: its tab bar is drawn, unseen under the bar's skeleton.
    await waitFor(() => expect(screen.queryAllByText('Fill in', HIDDEN_TOO)).not.toHaveLength(0));
    return held;
  }

  it('keeps the deck’s block in its place while the sport is read after the group', async () => {
    const ratings = await openWithTheSportOut(() => json({ ratings: [padelRating] }));
    // The group is in, the sport is not: the header waits, and the body is still Games' block.
    expect(headerShimmers()).toBe(true);
    const block = skeletonOf('group-games-reveal');
    expect(block).not.toBeNull();
    expect(within(block!).getByTestId('deck-skeleton', HIDDEN_TOO)).toBeTruthy();
    expect(screen.queryByTestId('group-page-body', HIDDEN_TOO)).toBeNull();

    await act(async () => ratings.land());

    expect(await screen.findByRole('button', { name: 'Not this time' })).toBeTruthy();
    expect(header()).not.toBeNull();
  });

  it('keeps shimmering while the ratings are asked again after one failure', async () => {
    let asked = 0;
    const ratings = await openWithTheSportOut(() => {
      asked += 1;
      return asked === 1 ? errorResponse(503, 'unavailable') : json({ ratings: [padelRating] });
    });

    await act(async () => ratings.land());
    // The refusal lands, short of the retry's backoff.
    await act(() => jest.advanceTimersByTimeAsync(RETRY / 4));
    expect(asked).toBe(1);
    // Refused once and to be asked again: no sport yet, so no header and no tab bar over a blank body.
    expect(headerShimmers()).toBe(true);
    expect(skeletonOf('group-tabs-reveal')).not.toBeNull();
    expect(tabBar()).toBeNull();

    await act(() => jest.advanceTimersByTimeAsync(RETRY));

    expect(asked).toBe(2);
    expect(await screen.findByRole('button', { name: 'Not this time' })).toBeTruthy();
    expect(header()).not.toBeNull();
  });

  it('says the group’s read is held for a connection — never a blank page — and builds it once back', async () => {
    stubMyGroups(transport, [CREW]);
    transport.on('GET', GROUP_PATH, () => json(PAGE));
    stubGroupDeck(transport, CREW.id, groupDeck({ cards: [deckCard()] }));
    await launchSignedIn();
    jest.setSystemTime(DECK_READ_AT);
    fireEvent.press(await screen.findByLabelText('Play'));
    await waitFor(() => expect(screen).toHavePathname('/play'));
    act(() => onlineManager.setOnline(false));
    fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));

    expect(await screen.findByText(offlineMessage('resumes'))).toBeTruthy();
    expect(headerShimmers()).toBe(false);
    expect(screen.getByRole('button', { name: GROUPS_COPY.group.back })).toBeTruthy();
    expect(tabBar()).toBeNull();

    act(() => onlineManager.setOnline(true));

    expect(await screen.findByHintText(GROUPS_COPY.group.openInfo)).toBeTruthy();
    expect(await screen.findByRole('button', { name: 'Not this time' })).toBeTruthy();
    expect(screen.queryByText(offlineMessage('resumes'))).toBeNull();
  });

  it('says the deck’s first read is held for a connection, where a spinner turned for ever', async () => {
    // Refused once as the phone goes offline: Query asks again, and the retry waits for a connection.
    transport.on('GET', deckPath(CREW.id), () => errorResponse(503, 'unavailable'));
    stubMyGroups(transport, [CREW]);
    transport.on('GET', GROUP_PATH, () => json(PAGE));
    await launchSignedIn();
    jest.setSystemTime(DECK_READ_AT);
    fireEvent.press(await screen.findByLabelText('Play'));
    await waitFor(() => expect(screen).toHavePathname('/play'));
    const held = transport.hold('GET', deckPath(CREW.id));
    fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));
    await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));

    act(() => onlineManager.setOnline(false));
    await act(async () => held.land());
    await act(() => jest.advanceTimersByTimeAsync(RETRY));

    expect(await screen.findByText(offlineMessage('resumes'))).toBeTruthy();
    expect(header()).not.toBeNull();
    expect(tabBar()).not.toBeNull();
    expect(screen.queryAllByTestId('deck-skeleton', HIDDEN_TOO)).toHaveLength(0);

    stubGroupDeck(transport, CREW.id, groupDeck({ cards: [deckCard()] }));
    act(() => onlineManager.setOnline(true));

    expect(await screen.findByRole('button', { name: 'Not this time' })).toBeTruthy();
    expect(screen.queryByText(offlineMessage('resumes'))).toBeNull();
  });
});

describe('pulling Games', () => {
  // The deck's own scroller — the Groups list under the page has a pull of its own (#529).
  const body = () => within(screen.getByTestId('games-deck-body'));
  const control = () => body().UNSAFE_getByType(RefreshControl);
  const pull = () => fireEvent(control(), 'refresh');

  it('reads the deck again: a game dealt meanwhile is on it, one gone is off it', async () => {
    const taken = deckCard();
    const posted = deckCard();
    let dealt = [taken];
    await openGames(() => groupDeck({ cards: dealt }));
    expect(await screen.findByTestId(`game-card-${taken.proposal_id}`)).toBeTruthy();

    // The first game filled on other phones, and somebody posted another.
    dealt = [posted];
    await act(async () => {
      pull();
    });

    expect(await screen.findByTestId(`game-card-${posted.proposal_id}`)).toBeTruthy();
    expect(screen.queryByTestId(`game-card-${taken.proposal_id}`)).toBeNull();
    await waitFor(() => expect(control().props.refreshing).toBe(false));
  });

  it('pulls on the starting card too, and the game dealt meanwhile takes its place', async () => {
    const posted = deckCard();
    let dealt: Wire['DeckCardSchema'][] = [];
    await openGames(() => groupDeck({ cards: dealt }));
    expect(await screen.findByText('Nothing picked right now')).toBeTruthy();

    dealt = [posted];
    await act(async () => {
      pull();
    });

    expect(await screen.findByTestId(`game-card-${posted.proposal_id}`)).toBeTruthy();
    expect(screen.queryByText('Nothing picked right now')).toBeNull();
  });

  it('pulls on a read that failed, as the retry does', async () => {
    // Refused until the player asks again: the page reads the deck ahead while the group is read,
    // and the tab's own read meets the refusal too.
    let refusing = true;
    stubMyGroups(transport, [CREW]);
    transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(PAGE));
    transport.on('GET', deckPath(CREW.id), () =>
      refusing ? errorResponse(429, 'rate_limited') : json(groupDeck({ cards: [deckCard()] })),
    );
    await launchSignedIn();
    jest.setSystemTime(DECK_READ_AT);
    fireEvent.press(await screen.findByLabelText('Play'));
    fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));
    expect(await screen.findByRole('button', { name: COPY.readAgain })).toBeTruthy();
    refusing = false;

    await act(async () => {
      pull();
    });

    expect(await screen.findByLabelText(COPY.details)).toBeTruthy();
  });

  it('reads the group with it — the starting card counts who is in it now', async () => {
    await openGames();
    expect(await screen.findByText('Nothing picked right now')).toBeTruthy();

    // The four others who play padel left on their phones.
    transport.on('GET', `/api/v1/groups/${CREW.id}`, () =>
      json<Wire['GroupResponse']>({
        ...PAGE,
        rated_by_sport: [
          {
            sport: 'PADEL',
            rated_count: 1,
            first_rated: [{ player_id: GATE_USER.id, nickname: 'ada' }],
          },
        ],
      }),
    );
    await act(async () => {
      pull();
    });

    expect(await screen.findByText('Just you so far')).toBeTruthy();
  });
});

describe('the card', () => {
  it('draws a pick — the ribbon, the tiles, the vs line, the forecast, the grid and a free vote', async () => {
    const card = deckCard();
    await openGames(groupDeck({ cards: [card] }));

    expect(await screen.findByRole('header', { name: 'Picked for you' })).toBeTruthy();
    // Your side on top while nobody is In, you first: YOU + ZOFIA VS ANIA + EWA — each
    // nickname cut at its first dot, a box's drawing (ADR-0157).
    expect(screen.getByText('You + zofia vs ania + ewa', HIDDEN_TOO)).toBeTruthy();
    // The tiles say each nickname whole, never with an @ (ADR-0199 §1): ania.k is ania.k.
    expect(screen.getByLabelText('ania.k, level 2,68')).toBeTruthy();
    expect(screen.getAllByText('ania.k', HIDDEN_TOO).length).toBeGreaterThan(0);
    expect(screen.getByLabelText('zofia.b, level 2,69')).toBeTruthy();
    expect(screen.getByLabelText('You, level 2,71')).toBeTruthy();
    expect(screen.queryByText(/@/, HIDDEN_TOO)).toBeNull();
    expect(
      screen.getByLabelText('Balance forecast 87%, very even: You + zofia against ania + ewa'),
    ).toBeTruthy();
    expect(screen.getByText('Slim overlap', HIDDEN_TOO)).toBeTruthy();
    expect(
      screen.getByLabelText(
        'Slim overlap. everybody free on Saturday afternoon. all but one on Friday evening. the game is Saturday afternoon',
      ),
    ).toBeTruthy();
    expect(
      screen.getByLabelText('Court available, 32 zł, Saturday 16:00 · Bonarka Arena'),
    ).toBeTruthy();
    // A book-by two days off draws no countdown.
    expect(screen.queryByTestId('game-countdown')).toBeNull();
  });

  it('leads a For-fun card with its Social vibe, and draws no forecast even if one is sent (#838)', async () => {
    const card = deckCard({
      kind: 'FOR_FUN',
      // Sent by mistake: the server stopped sending it on For fun (#830), and the card ignores it.
      forecast: { pct: 87, provisional: false },
      vibe: { pct: 82 },
    });
    await openGames((kind) =>
      groupDeck({
        segments: [{ kind: 'FOR_FUN', count: 1 }],
        cards: kind === 'FOR_FUN' ? [card] : [],
      }),
    );

    expect(await screen.findByLabelText('Social vibe, 82 percent, Great vibe')).toBeTruthy();
    expect(screen.getByText('82%', HIDDEN_TOO)).toBeTruthy();
    expect(screen.queryByLabelText(/^Balance forecast/)).toBeNull();
    expect(screen.queryByText('87%', HIDDEN_TOO)).toBeNull();
    // With no forecast to say the sides, the vs line says them — partner and opponents.
    expect(screen.getByLabelText('You and zofia.b against ania.k and ewa.m')).toBeTruthy();
    // Everything else is the card it was: the ribbon, the tiles, the vs line, the grid, the court.
    expect(screen.getByRole('header', { name: 'Picked for you' })).toBeTruthy();
    expect(screen.getByLabelText('ania.k, level 2,68')).toBeTruthy();
    expect(screen.getByText('You + zofia vs ania + ewa', HIDDEN_TOO)).toBeTruthy();
    expect(screen.getByText('Slim overlap', HIDDEN_TOO)).toBeTruthy();
    expect(
      screen.getByLabelText('Court available, 32 zł, Saturday 16:00 · Bonarka Arena'),
    ).toBeTruthy();
  });

  it('keeps a competitive card’s forecast, and draws it no Social vibe (#838)', async () => {
    await openGames(groupDeck({ cards: [deckCard({ vibe: { pct: 82 } })] }));

    expect(
      await screen.findByLabelText(
        'Balance forecast 87%, very even: You + zofia against ania + ewa',
      ),
    ).toBeTruthy();
    expect(screen.queryByLabelText(/^Social vibe/)).toBeNull();
    expect(screen.queryByText('Social vibe', HIDDEN_TOO)).toBeNull();
    expect(screen.queryByText('82%', HIDDEN_TOO)).toBeNull();
    // The forecast's name says the sides, so the vs line stays a drawing: said once, not twice.
    expect(screen.queryByLabelText('You and zofia.b against ania.k and ewa.m')).toBeNull();
  });

  it('tags the people In, and nobody else', async () => {
    await openGames(
      groupDeck({
        cards: [
          deckCard({
            in_count: 3,
            open_seats_after_your_yes: 0,
            court: 'BOOK_IT_NOW',
            sides: {
              yours: [youTile(), ANIA({ is_in: true })],
              theirs: [KAROL({ is_in: true }), ZOFIA({ is_in: true })],
            },
          }),
        ],
      }),
    );

    expect(await screen.findByLabelText('karol.t, level 2,75, In')).toBeTruthy();
    expect(screen.getAllByText(COPY.in, HIDDEN_TOO)).toHaveLength(3);
    // The side with more people In is the top row, and In reads before you: *Ania + You*.
    expect(screen.getByText('karol + zofia vs ania + You', HIDDEN_TOO)).toBeTruthy();
    expect(screen.queryByText(/asked|no answer yet/i, HIDDEN_TOO)).toBeNull();
    // Nobody here is the reader's friend, so no tile says FRIEND.
    expect(screen.queryByText(COPY.friend, HIDDEN_TOO)).toBeNull();
  });

  // #753 turned this round (Q68, applying since Q128): the reader's own friends carry FRIEND.
  it('tags the reader’s own friends FRIEND, In or not, and nobody else', async () => {
    await openGames(
      groupDeck({
        cards: [
          deckCard({
            in_count: 1,
            sides: {
              yours: [youTile(), ANIA({ friend: true })],
              theirs: [KAROL({ is_in: true, friend: true }), ZOFIA()],
            },
          }),
        ],
      }),
    );

    expect(await screen.findByLabelText('ania.k, level 2,68, friend')).toBeTruthy();
    expect(screen.getByLabelText('karol.t, level 2,75, In, friend')).toBeTruthy();
    expect(screen.getByLabelText('zofia.b, level 2,69')).toBeTruthy();
    expect(screen.getAllByText(COPY.friend, HIDDEN_TOO)).toHaveLength(2);
    const ania = screen.getByTestId(`game-tile-${ANIA().player_id}`);
    expect(within(ania).getByText(COPY.friend, HIDDEN_TOO)).toBeTruthy();
    const zofia = screen.getByTestId(`game-tile-${ZOFIA().player_id}`);
    expect(within(zofia).queryByText(COPY.friend, HIDDEN_TOO)).toBeNull();
  });

  it('says you complete it, and a Book it now stamp says Pay with its share — the ball stays I’m in', async () => {
    const card = deckCard({
      in_count: 3,
      open_seats_after_your_yes: 0,
      court: 'BOOK_IT_NOW',
      sides: {
        yours: [youTile(), ANIA({ is_in: true })],
        theirs: [KAROL({ is_in: true }), ZOFIA({ is_in: true })],
      },
    });
    await openGames(groupDeck({ cards: [card] }));

    expect(await screen.findByLabelText('You, you complete it')).toBeTruthy();
    expect(screen.getByText(COPY.youCompleteIt, HIDDEN_TOO)).toBeTruthy();
    expect(
      screen.getByLabelText('Book it now, 32 zł, Saturday 16:00 · Bonarka Arena'),
    ).toBeTruthy();

    dragTo(tile(KAROL().player_id), commit / 2);
    expect(screen.getByText('Pay · 32 zł', HIDDEN_TOO)).toBeTruthy();
    expect(screen.getByText('Not this time', HIDDEN_TOO)).toBeTruthy();
    release(tile(KAROL().player_id));
    // The stamp under the thumb says Pay; the ball is named I'm in on every card (Q124).
    expect(screen.getByRole('button', { name: COPY.yes })).toBeTruthy();
  });

  it('prices a free vote’s stamp too, as I’m in — the word, not the price, tells it from a payment', async () => {
    await openGames(groupDeck({ cards: [deckCard()] }));

    await screen.findByLabelText(COPY.details);
    expect(screen.getByText('I’m in · 32 zł', HIDDEN_TOO)).toBeTruthy();
    expect(screen.queryByText(/^Pay · /, HIDDEN_TOO)).toBeNull();
  });

  it('draws a challenge by name, and the group’s once the poster withdrew', async () => {
    const byKuba = deckCard({
      type: 'CHALLENGE',
      challenger: { player_id: KUBA().player_id, nickname: 'kuba.w' },
      in_count: 1,
      sides: { yours: [youTile(), EWA()], theirs: [KUBA({ is_in: true }), ANIA()] },
    });
    const byTheGroup = deckCard({ type: 'CHALLENGE', challenger: null });
    await openGames(groupDeck({ cards: [byKuba, byTheGroup] }));

    expect(await screen.findByRole('header', { name: 'kuba.w challenged you' })).toBeTruthy();
    // Behind, and drawn a frame after the top card.
    expect(await screen.findByText('The group challenged you', HIDDEN_TOO)).toBeTruthy();
  });

  it('draws a rescue’s ribbon, its Booked court and Pay with its share on the stamp', async () => {
    await openGames(groupDeck({ cards: [rescueCard({ deadline: hoursAfterRead(48) })] }));

    expect(await screen.findByRole('header', { name: 'Seat open · court booked' })).toBeTruthy();
    expect(
      screen.getByLabelText('Booked, 27 zł, Saturday 16:00 · Ogrody 33 · Court 6'),
    ).toBeTruthy();
    expect(screen.getByText('Pay · 27 zł', HIDDEN_TOO)).toBeTruthy();
  });

  it('counts down under a day, and in minutes under an hour', async () => {
    await openGames(
      groupDeck({
        cards: [
          deckCard({ deadline: hoursAfterRead(21.5) }),
          deckCard({ deadline: hoursAfterRead(0.9) }),
        ],
      }),
    );

    // The card behind is drawn a frame after the top one, and the stage paints deepest first — so
    // each is found by its words rather than by its place.
    await waitFor(() =>
      expect(screen.getAllByTestId('game-countdown', HIDDEN_TOO)).toHaveLength(2),
    );
    expect(screen.getByText(/^21 h \d\d$/, HIDDEN_TOO)).toBeTruthy();
    expect(screen.getByText(/^\d\d? min$/, HIDDEN_TOO)).toBeTruthy();
  });

  /** The deck's clock runs while a card counts down, and a card at its deadline leaves unsaid. */
  it('keeps counting, and lets a card go silently at its deadline', async () => {
    const soon = deckCard({ deadline: hoursAfterRead(0.9) });
    const later = deckCard({ deadline: hoursAfterRead(48) });
    await openGames(groupDeck({ cards: [soon, later] }));
    const before = (await screen.findByText(/^\d\d? min$/, HIDDEN_TOO)).props.children as string;

    act(() => jest.advanceTimersByTime(5 * 60_000));
    const after = screen.getByText(/^\d\d? min$/, HIDDEN_TOO).props.children as string;
    expect(parseInt(after, 10)).toBeLessThan(parseInt(before, 10));

    act(() => jest.advanceTimersByTime(60 * 60_000));
    await waitFor(() =>
      expect(screen.queryByTestId(`game-card-${soon.proposal_id}`, HIDDEN_TOO)).toBeNull(),
    );
    expect(screen.getByTestId(`game-card-${later.proposal_id}`)).toBeTruthy();
    expect(toasts()).toEqual([]);
    expect(transport.requestsTo('POST', yesPath(soon.proposal_id))).toHaveLength(0);
  });

  it('says a card late enough has no free cancellation, and names tomorrow', async () => {
    await openGames(
      groupDeck({
        cards: [deckCard({ no_free_cancellation: true, starts_at: '2026-10-01T17:00:00Z' })],
      }),
    );

    expect(
      await screen.findByLabelText(
        'Court available, 32 zł, Tomorrow 19:00 · Bonarka Arena, no free cancellation',
      ),
    ).toBeTruthy();
  });

  it('says how many are In on the whole game when it was dealt in versions', async () => {
    await openGames(
      groupDeck({
        cards: [
          deckCard({
            version_count: 2,
            in_count: 4,
            sides: { yours: [youTile(), ZOFIA({ is_in: true })], theirs: [ANIA(), EWA()] },
          }),
        ],
      }),
    );

    expect(await screen.findByText('4 people are In on this game', HIDDEN_TOO)).toBeTruthy();
  });

  it('draws singles as two tiles and no vs line', async () => {
    stubGate(transport, { ratings: [rating('TENNIS', 3.1)], hasPlayerProfile: true });
    const singles = {
      ...PAGE,
      rated_by_sport: [{ sport: 'TENNIS' as const, rated_count: 2, first_rated: [] }],
    };
    stubMyGroups(transport, [CREW]);
    transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(singles));
    stubGroupDeck(
      transport,
      CREW.id,
      groupDeck({
        sport: 'TENNIS',
        cards: [deckCard({ sides: { yours: [youTile()], theirs: [KUBA()] } })],
      }),
    );
    await launchSignedIn();
    jest.setSystemTime(DECK_READ_AT);
    fireEvent.press(await screen.findByLabelText('Play'));
    fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));

    expect(await screen.findByLabelText('kuba.w, level 2,80')).toBeTruthy();
    expect(screen.queryByText(/ vs /, HIDDEN_TOO)).toBeNull();
  });

  it('opens a player’s record from their tile', async () => {
    transport.on('GET', `/api/v1/players/${KAROL().player_id}/record`, () => json(karolsRecord()));
    await openGames(
      groupDeck({
        cards: [deckCard({ sides: { yours: [youTile(), KAROL()], theirs: [ANIA(), EWA()] } })],
      }),
    );

    fireEvent.press(await screen.findByLabelText('karol.t, level 2,75'));

    expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
    expect(transport.requestsTo('GET', `/api/v1/players/${KAROL().player_id}/record`)).toHaveLength(
      1,
    );
  });

  /**
   * **Her record says ania.k large, with nothing under it** (ADR-0199 §1): the nickname is the
   * identity, so the `@nickname` line that once sat under a name is gone, and nothing anywhere
   * writes an @.
   */
  it('opens ania.k’s record from her tile, her nickname large and no handle line under it', async () => {
    transport.on('GET', `/api/v1/players/${ANIA().player_id}/record`, () =>
      json<Wire['PlayerRecordResponse']>({ ...karolsRecord(), nickname: 'ania.k' }),
    );
    await openGames(
      groupDeck({
        cards: [deckCard({ sides: { yours: [youTile(), KAROL()], theirs: [ANIA(), EWA()] } })],
      }),
    );

    fireEvent.press(await screen.findByLabelText('ania.k, level 2,68'));

    expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
    const header = await screen.findByLabelText(/^ania\.k\. /);
    expect(within(header).getByText('ania.k')).toBeTruthy();
    expect(screen.queryByText(/@/, HIDDEN_TOO)).toBeNull();
  });

  it('says Indoor or Outdoor on a card the server promises a kind for, and nothing where it promises neither (#677)', async () => {
    const indoor = deckCard({ indoor: true });
    await openGames(groupDeck({ cards: [indoor] }));

    expect(
      await screen.findByLabelText(
        'Court available, 32 zł, Saturday 16:00 · Bonarka Arena · Indoor',
      ),
    ).toBeTruthy();
  });

  it('draws the cards in the order the server dealt them, the owed card first (#677)', async () => {
    // The server puts a card owed to the reader first (#673); the phone draws the order it is served.
    const owed = deckCard({ open_seats_after_your_yes: 1 });
    const other = deckCard();
    await openGames(groupDeck({ cards: [owed, other] }));

    await screen.findByTestId(`game-card-${owed.proposal_id}`);
    expect(screen.queryByTestId(`game-card-${other.proposal_id}`)).toBeNull();
    expect(await screen.findByTestId(`game-card-${other.proposal_id}`, HIDDEN_TOO)).toBeTruthy();
  });

  /** Q90: the cards behind fade as well as shrink, and they are real cards, never placeholders. */
  it('draws the next two cards behind the top one, holds one more unseen, and no more', async () => {
    const cards = [deckCard(), deckCard(), deckCard(), deckCard(), deckCard()];
    await openGames(groupDeck({ cards }));

    await screen.findByTestId(`game-card-${cards[0]!.proposal_id}`);
    expect(
      await screen.findByTestId(`game-card-${cards[1]!.proposal_id}`, HIDDEN_TOO),
    ).toBeTruthy();
    expect(screen.getByTestId(`game-card-${cards[2]!.proposal_id}`, HIDDEN_TOO)).toBeTruthy();
    // The one after them, drawn and unseen once the top card has arrived, so a card leaving brings
    // forward cards already drawn (`DeckStage`).
    expect(
      await screen.findByTestId(`game-card-${cards[3]!.proposal_id}`, HIDDEN_TOO),
    ).toBeTruthy();
    expect(screen.queryByTestId(`game-card-${cards[4]!.proposal_id}`, HIDDEN_TOO)).toBeNull();
  });
});

describe('answering', () => {
  function served(cards: readonly Wire['DeckCardSchema'][]) {
    let dealt = [...cards];
    const answered = (id: string) => {
      dealt = dealt.filter((card) => card.proposal_id !== id);
    };
    for (const card of cards) {
      transport.on('POST', yesPath(card.proposal_id), () => {
        answered(card.proposal_id);
        return json({ proposal_id: card.proposal_id, open_seats: 2 });
      });
      transport.on('POST', noPath(card.proposal_id), () => {
        answered(card.proposal_id);
        return noContent();
      });
    }
    return () => groupDeck({ cards: dealt });
  }

  it('says yes on a swipe right, and the next card comes up', async () => {
    const first = deckCard({ sides: { yours: [youTile(), KAROL()], theirs: [ANIA(), EWA()] } });
    const second = deckCard({ sides: { yours: [youTile(), ZOFIA()], theirs: [KUBA(), EWA()] } });
    await openGames(served([first, second]));
    await screen.findByTestId(`game-card-${first.proposal_id}`);

    expect(swipe(tile(KAROL().player_id), commit + 40)).toBe(true);
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));

    await waitFor(() =>
      expect(transport.requestsTo('POST', yesPath(first.proposal_id))).toHaveLength(1),
    );
    expect(await screen.findByLabelText('zofia.b, level 2,69')).toBeTruthy();
    expect(screen.queryByTestId(`game-card-${first.proposal_id}`, HIDDEN_TOO)).toBeNull();
    expect(haptics.felt).toEqual(['light']);
  });

  it('says no on a swipe left', async () => {
    const first = deckCard({ sides: { yours: [youTile(), KAROL()], theirs: [ANIA(), EWA()] } });
    await openGames(served([first]));
    await screen.findByTestId(`game-card-${first.proposal_id}`);

    swipe(tile(KAROL().player_id), -(commit + 40));
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));

    await waitFor(() =>
      expect(transport.requestsTo('POST', noPath(first.proposal_id))).toHaveLength(1),
    );
    expect(await screen.findByText('Nothing picked right now')).toBeTruthy();
  });

  it('sends nothing when the drag is released short of the threshold', async () => {
    const first = deckCard({ sides: { yours: [youTile(), KAROL()], theirs: [ANIA(), EWA()] } });
    await openGames(served([first]));
    await screen.findByTestId(`game-card-${first.proposal_id}`);

    swipe(tile(KAROL().player_id), commit - 1);
    await act(async () => {});

    expect(transport.requestsTo('POST', yesPath(first.proposal_id))).toHaveLength(0);
    expect(transport.requestsTo('POST', noPath(first.proposal_id))).toHaveLength(0);
  });

  it('answers with the ball and the ✕', async () => {
    const first = deckCard();
    const second = deckCard();
    await openGames(served([first, second]));
    await screen.findByTestId(`game-card-${first.proposal_id}`);

    fireEvent.press(screen.getByRole('button', { name: COPY.yes }));
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));
    await waitFor(() =>
      expect(transport.requestsTo('POST', yesPath(first.proposal_id))).toHaveLength(1),
    );

    await waitFor(() =>
      expect(screen.queryByTestId(`game-card-${first.proposal_id}`, HIDDEN_TOO)).toBeNull(),
    );
    fireEvent.press(screen.getByRole('button', { name: COPY.no }));
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));

    await waitFor(() =>
      expect(transport.requestsTo('POST', noPath(second.proposal_id))).toHaveLength(1),
    );
  });

  it('puts the card back and opens the payment setup when the server says a yes needs a saved way to pay', async () => {
    const first = deckCard({ sides: { yours: [youTile(), KAROL()], theirs: [ANIA(), EWA()] } });
    transport.on('POST', yesPath(first.proposal_id), () =>
      errorResponse(409, 'payment_method_required'),
    );
    await openGames(groupDeck({ cards: [first] }));
    await screen.findByTestId(`game-card-${first.proposal_id}`);

    fireEvent.press(screen.getByRole('button', { name: COPY.yes }));
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));

    expect(await screen.findByText(PAYMENTS_SETUP_TITLE)).toBeTruthy();
    expect(toasts()).toEqual([]);
    expect(await screen.findByTestId(`game-card-${first.proposal_id}`, HIDDEN_TOO)).toBeTruthy();
  });

  it('lets the card go, and says so, when the game just filled', async () => {
    const first = deckCard();
    let full = false;
    transport.on('POST', yesPath(first.proposal_id), () => {
      full = true;
      return errorResponse(409, 'proposal_is_full');
    });
    await openGames(() => groupDeck({ cards: full ? [] : [first] }));
    await screen.findByTestId(`game-card-${first.proposal_id}`);

    fireEvent.press(screen.getByRole('button', { name: COPY.yes }));
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));

    await waitFor(() => expect(toasts()).toEqual([[COPY.refused.proposal_is_full, 'bad']]));
    expect(await screen.findByText('Nothing picked right now')).toBeTruthy();
  });
});

// Another player's yes reaches this deck on its next read (the mechanics §6.4, §8.2): the card it
// rose to comes up next, and the card the player is reading is never swapped from under them.
describe('the deck read again while it is answered', () => {
  const READING = () =>
    deckCard({ sides: { yours: [youTile(), KAROL()], theirs: [ANIA(), EWA()] } });
  const pull = () =>
    fireEvent(
      within(screen.getByTestId('games-deck-body')).UNSAFE_getByType(RefreshControl),
      'refresh',
    );

  /**
   * The deck's route, as a slow server answers it once `slow` is on: each read is computed when it
   * arrives (`atRequest`) or when it is let go, and waits in `out` until a test lets it go.
   */
  function slowDeck(dealt: () => Wire['DeckCardSchema'][]) {
    const state = { slow: false, atRequest: false, out: [] as (() => void)[] };
    transport.on('GET', deckPath(CREW.id), () => {
      if (!state.slow) return json(groupDeck({ cards: dealt() }));
      const computed = state.atRequest ? groupDeck({ cards: dealt() }) : undefined;
      return new Promise<Response>((resolve) => {
        state.out.push(() => resolve(json(computed ?? groupDeck({ cards: dealt() }))));
      });
    });
    return state;
  }

  async function letGo(state: { out: (() => void)[] }) {
    const out = state.out.splice(0);
    await act(async () => {
      for (const release of out) release();
    });
  }

  it('keeps the card being read on top, its tiles fresh, and deals the game that rose behind it', async () => {
    const reading = READING();
    const rising = deckCard({ sides: { yours: [youTile(), ZOFIA()], theirs: [KUBA(), EWA()] } });
    let dealt = [reading, rising];
    await openGames(() => groupDeck({ cards: dealt }));
    expect(await screen.findByLabelText('karol.t, level 2,75')).toBeTruthy();

    // On their phones: Zofia and Kuba said yes to the second game, which now ranks first, and Karol
    // to the one on screen.
    dealt = [
      {
        ...rising,
        in_count: 2,
        open_seats_after_your_yes: 1,
        sides: {
          yours: [youTile(), ZOFIA({ is_in: true })],
          theirs: [KUBA({ is_in: true }), EWA()],
        },
      },
      {
        ...reading,
        in_count: 1,
        sides: { yours: [youTile(), KAROL({ is_in: true })], theirs: [ANIA(), EWA()] },
      },
    ];
    await act(async () => {
      pull();
    });

    // The card under the thumb is the one it was, with Karol In on it; the risen game is behind it.
    expect(await screen.findByLabelText('karol.t, level 2,75, In')).toBeTruthy();
    expect(screen.queryByLabelText(/^zofia.b/)).toBeNull();
    expect(await screen.findByLabelText('zofia.b, level 2,69, In', HIDDEN_TOO)).toBeTruthy();

    // Answered, it goes, and the risen game comes up next.
    transport.on('POST', noPath(reading.proposal_id), () => noContent());
    fireEvent.press(screen.getByRole('button', { name: COPY.no }));
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));

    expect(await screen.findByLabelText('zofia.b, level 2,69, In')).toBeTruthy();
  });

  it('lets a slow read land while the player answers on, so a yes said meanwhile reaches the deck', async () => {
    const first = READING();
    const second = deckCard({ sides: { yours: [youTile(), KUBA()], theirs: [ANIA(), EWA()] } });
    const third = deckCard({ sides: { yours: [youTile(), ZOFIA()], theirs: [KUBA(), EWA()] } });
    let dealt = [first, second, third];
    await openGames(() => groupDeck({ cards: dealt }));
    await screen.findByLabelText('karol.t, level 2,75');
    const server = slowDeck(() => dealt);
    for (const card of [first, second]) {
      transport.on('POST', noPath(card.proposal_id), () => {
        dealt = dealt.filter((dealtCard) => dealtCard.proposal_id !== card.proposal_id);
        return noContent();
      });
    }
    server.slow = true;

    // The first answer settles, and the deck is read again — slowly.
    fireEvent.press(screen.getByRole('button', { name: COPY.no }));
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));
    await waitFor(() => expect(server.out).toHaveLength(1));
    // The player answers the next card before that read is back.
    expect(await screen.findByLabelText(/^kuba.w, level/)).toBeTruthy();
    fireEvent.press(screen.getByRole('button', { name: COPY.no }));
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));
    await waitFor(() =>
      expect(transport.requestsTo('POST', noPath(second.proposal_id))).toHaveLength(1),
    );
    await act(async () => {});
    // The second answer's re-read waits for the read already out, rather than throwing it away.
    expect(server.out).toHaveLength(1);

    // Meanwhile Zofia said yes to the third game on her phone.
    dealt = [
      {
        ...third,
        in_count: 1,
        sides: { yours: [youTile(), ZOFIA({ is_in: true })], theirs: [KUBA(), EWA()] },
      },
    ];
    // The read that was out comes back: it is drawn, not thrown away for the second answer's.
    await letGo(server);

    expect(await screen.findByLabelText('zofia.b, level 2,69, In')).toBeTruthy();
    // One more read follows it, for the answer that settled while it was out — and only one.
    await waitFor(() => expect(server.out).toHaveLength(1));
    server.slow = false;
    await letGo(server);
  });

  it('never deals back a card answered while a read that predates the answer was out', async () => {
    const first = READING();
    const second = deckCard({ sides: { yours: [youTile(), KUBA()], theirs: [ANIA(), EWA()] } });
    let dealt = [first, second];
    await openGames(() => groupDeck({ cards: dealt }));
    await screen.findByLabelText('karol.t, level 2,75');
    const server = slowDeck(() => dealt);
    transport.on('POST', noPath(first.proposal_id), () => {
      dealt = [second];
      return noContent();
    });
    server.slow = true;
    server.atRequest = true;

    // A read goes out with both cards in it, and the first is answered before it is back.
    await act(async () => {
      pull();
    });
    await waitFor(() => expect(server.out).toHaveLength(1));
    fireEvent.press(screen.getByRole('button', { name: COPY.no }));
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));
    await waitFor(() =>
      expect(transport.requestsTo('POST', noPath(first.proposal_id))).toHaveLength(1),
    );
    server.slow = false;
    await letGo(server);

    expect(await screen.findByLabelText(/^kuba.w, level/)).toBeTruthy();
    expect(screen.queryByTestId(`game-card-${first.proposal_id}`, HIDDEN_TOO)).toBeNull();
  });
});

describe('the game’s details', () => {
  const card = () =>
    deckCard({
      in_count: 1,
      sides: { yours: [youTile(), KAROL({ is_in: true })], theirs: [ANIA(), EWA()] },
    });

  async function openDetails(shown = card(), read: Partial<Wire['ProposalDetailsResponse']> = {}) {
    let dealt = [shown];
    const deciding = proposalDetails(shown, read);
    stubProposal(transport, shown.proposal_id, () =>
      dealt.length === 0 ? withYourYes(deciding) : deciding,
    );
    transport.on('POST', yesPath(shown.proposal_id), () => {
      dealt = [];
      return json({ proposal_id: shown.proposal_id, open_seats: 2 });
    });
    transport.on('DELETE', yesPath(shown.proposal_id), () => {
      dealt = [shown];
      return noContent();
    });
    transport.on('POST', noPath(shown.proposal_id), () => {
      dealt = [];
      return noContent();
    });
    await openGames(() => groupDeck({ cards: dealt }));
    fireEvent.press(await screen.findByRole('button', { name: COPY.details }));
    await waitFor(() =>
      expect(screen).toHavePathname(`/play/group/${CREW.id}/game/${shown.proposal_id}`),
    );
    return shown;
  }

  it('opens from the i: the status, who is In, the club, the book-by and the share', async () => {
    const shown = await openDetails();

    expect(await screen.findByText('Filling · 1 of 4 in')).toBeTruthy();
    expect(transport.requestsTo('GET', proposalPath(shown.proposal_id)).length).toBeGreaterThan(0);
    expect(screen.getByLabelText('karol.t, level 2,75, In')).toBeTruthy();
    expect(screen.getByLabelText('Where, Bonarka Arena, 3,1 km')).toBeTruthy();
    expect(screen.getByLabelText('Day, Saturday, 3 Oct')).toBeTruthy();
    expect(screen.getByLabelText('Time, 16:00, until 17:00')).toBeTruthy();
    expect(
      screen.getByLabelText('Your share, 32 zł, if it fills · book by Fri 10:00'),
    ).toBeTruthy();
    expect(screen.getByText('karol.t, ania.k, ewa.m')).toBeTruthy();
  });

  it('draws no paragraph about what a yes costs: the share and its line say it', async () => {
    await openDetails();

    await screen.findByText('Filling · 1 of 4 in');
    expect(screen.queryByText(/costs nothing/)).toBeNull();
  });

  it('draws the overlap once a second player is In', async () => {
    await openDetails(
      deckCard({
        in_count: 2,
        sides: { yours: [youTile(), KAROL({ is_in: true })], theirs: [ANIA(), EWA()] },
      }),
    );

    await screen.findByText('Filling · 2 of 4 in');
    expect(screen.getByTestId('overlap-grid')).toBeTruthy();
  });

  // #836, the For-fun mocks 3–6: the top card is read first, the answers sit under the facts they
  // answer, and Who is free follows the card.
  it('reads the top card, then the game card with the answers in its foot, then Who is free', async () => {
    await openDetails(
      deckCard({
        in_count: 2,
        sides: { yours: [youTile(), KAROL({ is_in: true })], theirs: [ANIA(), EWA()] },
      }),
    );

    await screen.findByText('Filling · 2 of 4 in');
    const whoIsFree = `image:${String(screen.getByTestId('overlap-grid').props.accessibilityLabel)}`;
    const order = [
      `header:${BALANCE_FORECAST}`,
      'header:Filling · 2 of 4 in',
      COPY.game.where,
      `button:${COPY.no}`,
      `button:${COPY.yes}`,
      whoIsFree,
    ];
    expect(inOrder(partOf(screen.toJSON(), DETAILS_SCREEN), order)).toEqual(order);
  });

  it('draws the answer pair in the game card’s foot, and Who is free outside it', async () => {
    await openDetails(
      deckCard({
        in_count: 2,
        sides: { yours: [youTile(), KAROL({ is_in: true })], theirs: [ANIA(), EWA()] },
      }),
    );

    const card = await screen.findByTestId(DETAILS_CARD);
    expect(within(card).getByText('Filling · 2 of 4 in')).toBeTruthy();
    expect(
      within(card).getByLabelText('Your share, 32 zł, if it fills · book by Fri 10:00'),
    ).toBeTruthy();
    expect(within(card).getByRole('button', { name: COPY.no })).toBeTruthy();
    expect(within(card).getByRole('button', { name: COPY.yes })).toBeTruthy();
    expect(within(card).queryByTestId('overlap-grid')).toBeNull();
    expect(within(card).queryByText(BALANCE_FORECAST)).toBeNull();
  });

  // #839: what is at stake is the details' — the deck card behind keeps its forecast row, and no
  // stake is drawn there.
  it('draws what is at stake on the details, and never on the deck card', async () => {
    const shown = await openDetails(card(), { at_stake: { win_delta: 0.08, loss_delta: -0.07 } });

    const details = await screen.findByTestId(DETAILS_SCREEN);
    expect(within(details).getByText(WIN_TILE)).toBeTruthy();
    expect(within(details).getByText(LOSE_TILE)).toBeTruthy();

    const onTheDeck = screen.getByTestId(`game-card-${shown.proposal_id}`, HIDDEN_TOO);
    expect(within(onTheDeck).getByTestId('game-forecast', HIDDEN_TOO)).toBeTruthy();
    expect(within(onTheDeck).queryByText(WIN_TILE, HIDDEN_TOO)).toBeNull();
    expect(within(onTheDeck).queryByText(LOSE_TILE, HIDDEN_TOO)).toBeNull();
  });

  it('says in the card’s foot that an answer given offline is held', async () => {
    await openDetails();
    const card = await screen.findByTestId(DETAILS_CARD);

    act(() => onlineManager.setOnline(false));
    try {
      fireEvent.press(within(card).getByRole('button', { name: COPY.yes }));

      expect(await within(card).findByText(offlineMessage('resumes'))).toBeTruthy();
    } finally {
      act(() => onlineManager.setOnline(true));
    }
  });

  it('keeps the header: the faces, the others named, and the sport — the count is the tag’s alone', async () => {
    await openDetails();

    await screen.findByText('Filling · 1 of 4 in');
    expect(screen.getByRole('header', { name: /^karol\.t, ania\.k, ewa\.m/ })).toBeTruthy();
    expect(screen.getByText('Padel')).toBeTruthy();
    expect(screen.queryByText(/^Padel · \d of \d in$/)).toBeNull();
    expect(screen.getAllByText(/\d of \d in/)).toHaveLength(1);
  });

  it('says Padel · For fun under a For-fun game’s header', async () => {
    const card = deckCard({ kind: 'FOR_FUN', forecast: null, vibe: { pct: 82 } });
    stubProposal(transport, card.proposal_id, proposalDetails(card));
    await openGames((kind) =>
      groupDeck({
        segments: [{ kind: 'FOR_FUN', count: 1 }],
        cards: kind === 'FOR_FUN' ? [card] : [],
      }),
    );
    fireEvent.press(await screen.findByRole('button', { name: COPY.details }));

    expect(await screen.findByText('Padel · For fun')).toBeTruthy();
    expect(screen.getByRole('header', { name: /^zofia\.b, ania\.k, ewa\.m/ })).toBeTruthy();
    expect(
      within(screen.getByTestId(DETAILS_CARD)).getByRole('button', { name: COPY.yes }),
    ).toBeTruthy();
  });

  it('hides the overlap, and titles the header Only you, when the reader is alone In', async () => {
    await openDetails(deckCard({ in_count: 1, sides: { yours: [youTile()], theirs: [] } }));

    expect(await screen.findByText('Only you')).toBeTruthy();
    expect(screen.queryByTestId('overlap-grid')).toBeNull();
  });

  it('keeps the state out of the header’s subtitle, which says the sport alone', async () => {
    await openDetails();

    await screen.findByText('Filling · 1 of 4 in');
    expect(screen.queryByText(/· ?filling$/i)).toBeNull();
    expect(screen.getAllByText(/^Padel/).length).toBeGreaterThan(0);
  });

  it('opens from a press on the card too', async () => {
    const shown = card();
    stubProposal(transport, shown.proposal_id, proposalDetails(shown));
    await openGames(groupDeck({ cards: [shown] }));

    fireEvent.press(await screen.findByTestId(`game-card-${shown.proposal_id}`));

    await waitFor(() =>
      expect(screen).toHavePathname(`/play/group/${CREW.id}/game/${shown.proposal_id}`),
    );
  });

  it('says yes in place, then offers Withdraw in the card’s foot, which puts the answers back', async () => {
    const shown = await openDetails();

    fireEvent.press(await screen.findByRole('button', { name: COPY.yes }));

    const card = () => screen.getByTestId(DETAILS_CARD);
    expect(await within(card()).findByRole('button', { name: COPY.game.withdraw })).toBeTruthy();
    expect(screen.getByText('Filling · 2 of 4 in')).toBeTruthy();
    expect(transport.requestsTo('POST', yesPath(shown.proposal_id))).toHaveLength(1);

    fireEvent.press(screen.getByRole('button', { name: COPY.game.withdraw }));

    expect(await within(card()).findByRole('button', { name: COPY.yes })).toBeTruthy();
    expect(transport.requestsTo('DELETE', yesPath(shown.proposal_id))).toHaveLength(1);
  });

  it('says no and goes back to a deck without the card', async () => {
    const shown = await openDetails();

    fireEvent.press(await screen.findByRole('button', { name: COPY.no }));

    await waitFor(() => expect(screen).toHavePathname(`/play/group/${CREW.id}`));
    expect(transport.requestsTo('POST', noPath(shown.proposal_id))).toHaveLength(1);
    expect(await screen.findByText('Nothing picked right now')).toBeTruthy();
  });

  it('says a game it cannot find is no longer dealt', async () => {
    transport.on('GET', proposalPath('c0000000-0000-4000-8000-00000000ffff'), () =>
      errorResponse(404, 'proposal_not_found'),
    );
    await openGames(groupDeck());
    act(() =>
      router.push({
        pathname: '/play/group/[groupId]/game/[proposalId]',
        params: {
          groupId: CREW.id,
          proposalId: 'c0000000-0000-4000-8000-00000000ffff',
          sport: 'padel',
          kind: 'competitive',
        },
      }),
    );

    expect(await screen.findByText(COPY.game.gone)).toBeTruthy();
  });
});

describe('offline', () => {
  it('holds the answer, keeps the card gone, and says the answer resumes', async () => {
    const first = deckCard();
    await openGames(groupDeck({ cards: [first] }));
    await screen.findByTestId(`game-card-${first.proposal_id}`);

    act(() => onlineManager.setOnline(false));
    try {
      fireEvent.press(screen.getByRole('button', { name: COPY.yes }));
      act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));

      expect(await screen.findByText(offlineMessage('resumes'))).toBeTruthy();
      expect(transport.requestsTo('POST', yesPath(first.proposal_id))).toHaveLength(0);
    } finally {
      act(() => onlineManager.setOnline(true));
    }
  });
});
