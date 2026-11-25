/**
 * **The kind of game you don't play is a door** — a group's Games tab's menu draws both kinds always,
 * the one the intent doesn't want dimmed with no number, and picking it shuts the menu and opens a
 * panel in place that changes the intent for the page's sport (the menu since #862; the switch's
 * before) ([#740](https://github.com/Raketa02/Raketa/issues/740),
 * ADR-0201 §2; the screens A1, A2.1; the words §28).
 *
 * The real route tree, with the socket faked at the platform edge as a small server: it holds the
 * player's intent per sport, answers `PUT /play-intents/{sport}` by changing that sport's alone,
 * and deals the deck off it — the segments the intent shows, each counting its cards, and the
 * cards of the kind asked for only where the intent shows it. So the menu a test reads after an
 * answer is the one the server's new intent draws.
 *
 * **A kind the intent has just gained has no cards until the group is dealt** — the server's
 * `built`, which `POST /pools/{id}/deal` fills, as the card-builder would. So a deck read before the
 * deal would say *Nothing picked right now*, and the finding that covers the wait (#741) is what a
 * test sees instead.
 *
 * **The cast is the PRD's.** Ania is Competitive in padel (`Competitive · 7`), Kuba is For fun
 * (`For fun · 3`), and Zofia's *Either suits me* draws both live. The reader is whichever of them
 * the suite declares; their tennis is For fun, to prove a padel answer leaves it alone.
 *
 * **Finding** (#741, ADR-0201 §4, the screens A2.1 state 5): after an answer on the door's panel or
 * the first-time question, the group is dealt and then its deck read, the tab saying *Finding…*
 * meanwhile — in that order, and with a failed deal falling through to the read.
 */

import { act, fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { StyleSheet, type ViewStyle } from 'react-native';

import { PROPOSALS_COPY } from '@/features/proposals/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { TIMEOUT_MS } from '@/shared/lib/http';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { REVEAL_CEILING, theme } from '@/shared/ui';
import {
  dealPath,
  deckCard,
  deckPath,
  fillInPath,
  DECK_READ_AT,
  groupDeck,
  KUBA,
  stubFillIn,
  youTile,
} from '@/test-support/groupDeck';
import {
  menuLine,
  menuSays,
  menuTab,
  openTabMenu,
  pickKind,
  shutTabMenu,
} from '@/test-support/tabMenu';
import { bottomOf, PLAYERS_BAR } from '@/test-support/tabBarReach';
import {
  pressHardwareBack,
  stopWatchingHardwareBack,
  watchHardwareBack,
} from '@/test-support/hardwareBack';
import {
  GATE_USER,
  launchSignedIn,
  stubGate,
  stubMyGroups,
  stubPaymentMethod,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  networkFailure,
  neverResponds,
  noContent,
  type RecordedRequest,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { useGameIntent } from '../store/gameIntent.store';

const HIDDEN_TOO = { includeHiddenElements: true } as const;

const COPY = PROPOSALS_COPY;

type Kind = Wire['SearchMode'];
type Intent = Wire['PlayIntentDeclarationResponse']['intent'];

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

/** *Padel po pracy* — padel and tennis, so a padel answer has a sport to leave alone. */
const GROUP: Wire['MyGroupSchema'] = {
  id: 'a0000000-0000-4000-8000-000000000007',
  kind: 'PLAYER',
  name: 'Padel po pracy',
  monogram: { letters: 'Pp', colour: 2 },
  sports: ['PADEL', 'TENNIS'],
  member_count: 20,
  home_club: { id: 'c0000000-0000-4000-8000-000000000001', name: 'Centrum Ruchu' },
};

function person(n: number, name: string): Wire['GroupPersonSchema'] {
  return { player_id: `e0000000-0000-4000-8000-00000000000${n}`, nickname: name };
}

/** Enough rated in each sport for a court, so a deck dealing nothing says *Nothing picked*. */
const PAGE: Wire['GroupResponse'] = {
  ...GROUP,
  link: 'https://raketa.app/join/P4PRACY2',
  join_policy: 'ANYONE',
  is_owner: false,
  rated_by_sport: [
    {
      sport: 'PADEL',
      rated_count: 8,
      first_rated: [
        { player_id: GATE_USER.id, nickname: 'ada' },
        person(2, 'Member 2'),
        person(3, 'Member 3'),
        person(4, 'Member 4'),
      ],
    },
    {
      sport: 'TENNIS',
      rated_count: 4,
      first_rated: [{ player_id: GATE_USER.id, nickname: 'ada' }, person(2, 'Member 2')],
    },
  ],
  member_faces: [],
  administrator_nickname: null,
  is_administrator: false,
};

/** The PUT routes the server answers — one per sport, so a wrong sport is a request on record. */
const intentPath = (sport: Wire['Sport']) => `/api/v1/play-intents/${sport}`;

let transport: Transport;
/** The server's intents, per sport — what `PUT /play-intents/{sport}` writes and the deck reads. */
let intents: Partial<Record<Wire['Sport'], Intent>>;
/** How many padel cards of each kind the server deals the reader in this group. */
let dealing: Record<Kind, number>;
/** The padel kinds the group has been dealt in for the reader — what the deal fills. */
let built: Set<Kind>;
/** A padel kind whose deck reads never answer, or are refused — none unless a test says so. */
let unread: { readonly kind: Kind; readonly how: 'held' | 'refused' } | undefined;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, {
    ratings: [rating('PADEL', 2.71), rating('TENNIS', 3.1)],
    hasPlayerProfile: true,
  });
  stubProfileOptions(transport);
  stubProfileSurface(transport);
  stubPaymentMethod(transport, { brand: 'visa', last_four: '4312', wallet: null });
  useGameIntent.setState({ intent: 'competitive' });
  useToastQueue.setState({ queue: [] });
  intents = { TENNIS: 'FOR_FUN' };
  dealing = { COMPETITIVE: 7, FOR_FUN: 3 };
  unread = undefined;
  watchHardwareBack();
});

afterEach(async () => {
  stopWatchingHardwareBack();
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** The kinds an intent shows — both for *Either suits me*, none while undeclared. */
function shows(intent: Intent | undefined): readonly Kind[] {
  if (intent === undefined) return [];
  return intent === 'NO_PREFERENCE' ? ['COMPETITIVE', 'FOR_FUN'] : [intent];
}

/** One padel card of each kind, by its place among that kind's cards — the deck draws the first. */
function padelCard(kind: Kind, n: number): Wire['DeckCardSchema'] {
  return deckCard({
    proposal_id: `c0000000-0000-4000-8000-${kind === 'COMPETITIVE' ? '1' : '2'}${String(n).padStart(11, '0')}`,
    kind,
    sides: { yours: [youTile(), KUBA()], theirs: [] },
  });
}

const FIRST: Record<Kind, Wire['DeckCardSchema']> = {
  COMPETITIVE: padelCard('COMPETITIVE', 1),
  FOR_FUN: padelCard('FOR_FUN', 1),
};

/** Which sport and kind a deck request asked for. */
function askedOf(request: RecordedRequest): { sport: Wire['Sport']; kind: Kind } {
  const sport = /[?&]sport=([A-Z]+)/.exec(request.path)?.[1] as Wire['Sport'];
  const kind = /[?&]kind=([A-Z_]+)/.exec(request.path)?.[1] as Kind;
  return { sport, kind };
}

/** The deck as the server deals it now — see the module note. */
function dealt(sport: Wire['Sport'], kind: Kind): Wire['GroupDeckResponse'] {
  const kinds = shows(intents[sport]);
  const count = (of: Kind) => {
    if (sport !== 'PADEL') return 2;
    return built.has(of) ? dealing[of] : 0;
  };
  const cards =
    sport === 'PADEL' && kinds.includes(kind)
      ? Array.from({ length: count(kind) }, (_, at) => padelCard(kind, at + 1))
      : [];
  return groupDeck({
    pool_id: GROUP.id,
    sport,
    kind,
    segments: kinds.map((of) => ({ kind: of, count: count(of) })),
    cards,
  });
}

/** Land on the group's page, Games on padel, the reader declared as `padel` says. */
async function openGames(padel: Intent | undefined) {
  if (padel !== undefined) intents.PADEL = padel;
  built = new Set(shows(intents.PADEL));
  stubMyGroups(transport, [GROUP]);
  transport.on('GET', `/api/v1/groups/${GROUP.id}`, () => json(PAGE));
  transport.on('GET', deckPath(GROUP.id), (request) => {
    const { sport, kind } = askedOf(request);
    if (sport === 'PADEL' && unread?.kind === kind) {
      return unread.how === 'held'
        ? new Promise<Response>(() => undefined)
        : errorResponse(429, 'rate_limited');
    }
    return json(dealt(sport, kind));
  });
  stubFillIn(transport, GROUP.id);
  transport.on('POST', dealPath(GROUP.id), () => deal());
  for (const sport of ['PADEL', 'TENNIS'] as const) {
    transport.on('PUT', intentPath(sport), (request) => {
      const { intent } = request.body as { intent: Intent };
      intents[sport] = intent;
      return json<Wire['PlayIntentDeclarationResponse']>({ sport, intent });
    });
  }
  await launchSignedIn();
  jest.setSystemTime(DECK_READ_AT);
  fireEvent.press(await screen.findByLabelText('Play'));
  await waitFor(() => expect(screen).toHavePathname('/play'));
  fireEvent.press(await screen.findByRole('button', { name: /^Padel po pracy,/ }));
  await waitFor(() => expect(screen).toHavePathname(`/play/group/${GROUP.id}`));
}

const PAGE_PATH = `/play/group/${GROUP.id}`;

/**
 * Once nothing is on its way — no answer, no finding — so the Games tab's menu opens again (#862):
 * an answer and its finding hold it still. A line said to be selected waits for the tab to say its
 * kind, which it does once the deck has landed there.
 */
async function settled(selectedKind?: string) {
  if (selectedKind !== undefined) {
    await screen.findByRole('button', { name: `Games, ${selectedKind}`, selected: true });
  }
  await waitFor(() => expect(screen.queryByText(/^Finding/)).toBeNull());
  // The mutations' own state reaches the page on Query's next notify tick.
  act(() => jest.advanceTimersByTime(0));
}

/** A live line of the Games tab's menu, by its spoken name — read, and the menu shut again. */
async function live(name: string, selected?: boolean) {
  await settled(selected === true ? name.split(',')[0] : undefined);
  return menuSays('Games', name, selected);
}

/** The door, by its spoken name — a line of the Games tab's menu, read and put away. */
async function door(kind: 'For fun' | 'Competitive') {
  await settled();
  return menuSays('Games', `${kind}, not a kind you play`, false);
}

/** **The door, opened from the menu** (#862): the menu shuts, and the panel opens over the deck. */
const openTheDoor = (kind: 'For fun' | 'Competitive') => pickKind('Games', kind);

/** Every door the Games tab's menu draws now — the menu opened to look, and shut again. */
async function doorsInTheMenu(): Promise<string[]> {
  const open = await openTabMenu('Games');
  const doors = within(open)
    .getAllByRole('button')
    .map((line) => line.props.accessibilityLabel as string)
    .filter((name) => name.endsWith('not a kind you play'));
  await shutTabMenu('Games');
  return doors;
}

/** Games' chevron, wherever it is drawn — a mark, never spoken. */
const chevron = () => screen.queryByTestId('segment-chevron-games', HIDDEN_TOO);

/**
 * A press on the selected Games tab that opens nothing — the menu stays shut, to a finger and a
 * listener alike (one folding away from the door's pick is still drawn, out of reach).
 */
async function tabOpensNothing() {
  fireEvent.press(await menuTab('Games'));
  expect(screen.queryByTestId('tab-menu')).toBeNull();
  expect(await menuTab('Games', false)).toBeTruthy();
}

const declarations = (sport: Wire['Sport']) => transport.requestsTo('PUT', intentPath(sport));

/** A button's fill as drawn, nothing pressed. */
function fill(button: { readonly props: { readonly style?: unknown } }): unknown {
  const style = button.props.style;
  const drawn = typeof style === 'function' ? style({ pressed: false }) : style;
  return StyleSheet.flatten(drawn as ViewStyle).backgroundColor;
}

/** The card-builder's run: every kind the padel intent shows now holds its cards. */
function deal(): Response {
  for (const kind of shows(intents.PADEL)) built.add(kind);
  return noContent();
}

/** Hold the deal until the suite lets it go — the wait finding covers. */
function holdTheDeal(): () => void {
  let release: () => void = () => undefined;
  const dealtNow = new Promise<void>((resolve) => {
    release = resolve;
  });
  transport.on('POST', dealPath(GROUP.id), async () => {
    await dealtNow;
    return deal();
  });
  return () => release();
}

/** The answer, the deal and the deck's reads since `from`, in the order they reached the socket. */
function trafficSince(from: number): string[] {
  const routes = [
    `PUT ${intentPath('PADEL')}`,
    `POST ${dealPath(GROUP.id)}`,
    `GET ${deckPath(GROUP.id)}`,
  ];
  return transport.requests
    .slice(from)
    .map((request) => `${request.method} ${request.path.split('?')[0]}`)
    .filter((route) => routes.includes(route));
}

const findingSays = (line: string) => screen.findByText(line);

/** Hold the padel declaration's answer until the suite lets it go. */
function holdTheDeclaration(): () => void {
  let release: () => void = () => undefined;
  const answered = new Promise<void>((resolve) => {
    release = resolve;
  });
  transport.on('PUT', intentPath('PADEL'), async (request) => {
    await answered;
    const { intent } = request.body as { intent: Intent };
    intents.PADEL = intent;
    return json<Wire['PlayIntentDeclarationResponse']>({ sport: 'PADEL', intent });
  });
  return () => release();
}

/** Open the sport bar and pick one. */
async function pickSport(from: string, to: string) {
  fireEvent.press(await screen.findByRole('button', { name: `Sport: ${from}` }));
  act(() => jest.advanceTimersByTime(theme.motion.unfold));
  fireEvent.press(within(screen.getByTestId('sport-bar')).getByRole('button', { name: to }));
}

const panel = () => screen.queryByTestId('kind-door');

/** The panel's answers, by the first-time question's spoken names. */
const answer = (intent: 'Either suits me' | 'For fun' | 'Competitive') =>
  within(screen.getByTestId('kind-door')).getByRole('button', {
    name: `${intent}, your usual at Padel`,
  });

describe('the Games tab’s menu draws both kinds always (#862)', () => {
  it('draws Ania’s kind live with its number, and For fun dimmed with none', async () => {
    await openGames('COMPETITIVE');

    const open = await openTabMenu('Games');
    const competitive = await menuLine('Competitive', true);
    expect(competitive.props.accessibilityLabel).toBe('Competitive, 7 games');
    expect(within(competitive).getByText('7', HIDDEN_TOO)).toBeTruthy();
    // The door: the kind's words alone, dimmed, no number, no tick — and never disabled.
    const forFun = await menuLine('For fun');
    expect(forFun.props.accessibilityLabel).toBe('For fun, not a kind you play');
    expect(forFun.props.accessibilityState).toEqual({ selected: false });
    expect(within(forFun).queryByText(/[0-9]/, HIDDEN_TOO)).toBeNull();
    expect(within(forFun).queryByTestId('tab-menu-tick', HIDDEN_TOO)).toBeNull();
    expect(
      StyleSheet.flatten(within(forFun).getByText('For fun').props.style as ViewStyle).opacity,
    ).toBe(theme.size.segDoorOpacity);
    expect(within(open).getAllByRole('button')).toHaveLength(2);
  });

  it('draws Kuba’s mirror: Competitive dimmed, For fun · 3 live', async () => {
    await openGames('FOR_FUN');

    expect(await live('For fun, 3 games', true)).toBeTruthy();
    expect(await door('Competitive')).toBeTruthy();
    expect((await menuTab('Games')).props.accessibilityLabel).toBe('Games, For fun');
  });

  it('leaves Zofia’s Either suits me as it was: both live, no door', async () => {
    await openGames('NO_PREFERENCE');

    expect(await live('Competitive, 7 games', true)).toBeTruthy();
    expect(await live('For fun, 3 games', false)).toBeTruthy();
    expect(await doorsInTheMenu()).toEqual([]);
  });

  it('still asks the first-time question, with no chevron, for an undeclared sport', async () => {
    await openGames(undefined);

    expect(await screen.findByText('Your usual game at Padel')).toBeTruthy();
    expect(chevron()).toBeNull();
    expect(screen.queryByLabelText(/not a kind you play/, HIDDEN_TOO)).toBeNull();
  });
});

describe('the deck never opens on the dimmed kind', () => {
  it('opens on Ania’s competitive cards when the phone last stood on For fun elsewhere', async () => {
    useGameIntent.setState({ intent: 'forFun' });
    await openGames('COMPETITIVE');

    expect(await screen.findByTestId(`game-card-${FIRST.COMPETITIVE.proposal_id}`)).toBeTruthy();
    expect(await live('Competitive, 7 games', true)).toBeTruthy();
    expect(screen.queryByTestId(`game-card-${FIRST.FOR_FUN.proposal_id}`, HIDDEN_TOO)).toBeNull();
  });

  // The code review's catch (#862): the menu is drawn off the read of the kind the phone last stood
  // on, which says the intent shows only Competitive, while the deck reads Competitive itself — and a
  // door drawn there is a door that opens, over the deck's skeleton (#875) or its failure.
  it.each([
    ['on its way', 'held', () => screen.findAllByTestId('deck-skeleton', HIDDEN_TOO)],
    ['refused', 'refused', () => screen.findByRole('button', { name: COPY.readAgain })],
  ] as const)(
    'opens the door from the menu while the deck’s own read is %s',
    async (_state, how, deckSays) => {
      useGameIntent.setState({ intent: 'forFun' });
      unread = { kind: 'COMPETITIVE', how };
      await openGames('COMPETITIVE');
      // While the deck's own read is out the page shimmers, and the tab bar comes in at the ceiling
      // (#875): the menu is reached from there.
      act(() => jest.advanceTimersByTime(REVEAL_CEILING));
      expect(await deckSays()).toBeTruthy();
      expect(await door('For fun')).toBeTruthy();

      await openTheDoor('For fun');

      expect(
        await screen.findByText(
          'You play padel competitively, so Raketa only puts you in competitive games.',
        ),
      ).toBeTruthy();
      expect(
        screen.getByText('Keep your 7 competitive cards and get for-fun ones too.'),
      ).toBeTruthy();
      // The area runs under the floating bar to the phone's foot (#881); what covers it ends at the
      // bar's reach, so the door's last button scrolls clear of the bar — the code review's catch.
      const layer = screen.getByTestId('games-deck-over');
      expect(within(layer).getByTestId('kind-door')).toBeTruthy();
      expect(bottomOf(layer)).toBe(PLAYERS_BAR);
      expect(useGameIntent.getState().intent).toBe('forFun');
      fireEvent.press(screen.getByRole('button', { name: 'Keep competitive' }));
      expect(panel()).toBeNull();
      expect(await deckSays()).toBeTruthy();
    },
  );

  it('does not move the remembered position when the door is tapped', async () => {
    useGameIntent.setState({ intent: 'forFun' });
    await openGames('COMPETITIVE');

    await openTheDoor('For fun');
    expect(await screen.findByTestId('kind-door')).toBeTruthy();
    expect(useGameIntent.getState().intent).toBe('forFun');

    fireEvent.press(screen.getByRole('button', { name: 'Keep competitive' }));
    expect(useGameIntent.getState().intent).toBe('forFun');
    expect(await live('Competitive, 7 games', true)).toBeTruthy();
  });
});

describe('the panel', () => {
  it('opens in place over the deck, on the group page, with Ania’s words and count', async () => {
    await openGames('COMPETITIVE');
    await screen.findByTestId(`game-card-${FIRST.COMPETITIVE.proposal_id}`);

    await openTheDoor('For fun');

    expect(
      await screen.findByText(
        'You play padel competitively, so Raketa only puts you in competitive games.',
      ),
    ).toBeTruthy();
    expect(screen.getByText('Want for-fun games too?')).toBeTruthy();
    expect(
      screen.getByText('Keep your 7 competitive cards and get for-fun ones too.'),
    ).toBeTruthy();
    expect(screen.getByText('Your 7 competitive cards go. Games you’re In on stay.')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Keep competitive' })).toBeTruthy();
    // Either suits me first, the kind tapped second, the way out last.
    expect(
      within(screen.getByTestId('kind-door'))
        .getAllByRole('button')
        .map((button) => button.props.accessibilityLabel as string),
    ).toEqual([
      'Either suits me, your usual at Padel',
      'For fun, your usual at Padel',
      'Keep competitive',
    ]);
    // …and highlighted: Either suits me on the primary fill, the other two on the card's own.
    expect(fill(answer('Either suits me'))).toBe(theme.color.coralInk);
    expect(fill(answer('For fun'))).toBe(theme.color.onDarkFill);

    // An overlay inside the deck's area: no new route, the menu shut before it opened, the tab and
    // its chevron still drawn, and the cards still laid out under it rather than squeezed by it.
    expect(screen).toHavePathname(PAGE_PATH);
    expect(screen.queryByTestId('tab-menu')).toBeNull();
    expect((await menuTab('Games')).props.accessibilityLabel).toBe('Games, Competitive');
    expect(chevron()).toBeTruthy();
    expect(
      screen.getByTestId(`game-card-${FIRST.COMPETITIVE.proposal_id}`, HIDDEN_TOO),
    ).toBeTruthy();
  });

  it('is Kuba’s mirror for a for-fun player', async () => {
    await openGames('FOR_FUN');

    await openTheDoor('Competitive');

    expect(
      await screen.findByText('You play padel for fun, so Raketa only puts you in for-fun games.'),
    ).toBeTruthy();
    expect(screen.getByText('Want competitive games too?')).toBeTruthy();
    expect(
      screen.getByText('Keep your 3 for-fun cards and get competitive ones too.'),
    ).toBeTruthy();
    expect(screen.getByText('Your 3 for-fun cards go. Games you’re In on stay.')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Keep for fun' })).toBeTruthy();
  });

  it('says card, not cards, for one', async () => {
    dealing.COMPETITIVE = 1;
    await openGames('COMPETITIVE');

    await openTheDoor('For fun');

    expect(
      await screen.findByText('Keep your 1 competitive card and get for-fun ones too.'),
    ).toBeTruthy();
    expect(screen.getByText('Your 1 competitive card goes. Games you’re In on stay.')).toBeTruthy();
  });

  it('drops the number with nothing dealt, over the group’s starting card', async () => {
    dealing.COMPETITIVE = 0;
    await openGames('COMPETITIVE');
    expect(await screen.findByText('Nothing picked right now')).toBeTruthy();

    await openTheDoor('For fun');

    expect(await screen.findByText('Get for-fun games as well as competitive ones.')).toBeTruthy();
    expect(
      screen.getByText('Raketa stops dealing you competitive games. Games you’re In on stay.'),
    ).toBeTruthy();
    expect(screen.getByText('Nothing picked right now', HIDDEN_TOO)).toBeTruthy();
  });

  it('closes on Keep competitive and sends nothing', async () => {
    await openGames('COMPETITIVE');

    await openTheDoor('For fun');
    fireEvent.press(await screen.findByRole('button', { name: 'Keep competitive' }));

    expect(panel()).toBeNull();
    expect(declarations('PADEL')).toHaveLength(0);
    expect(screen.getByTestId(`game-card-${FIRST.COMPETITIVE.proposal_id}`)).toBeTruthy();
  });

  // Left open by the grilling, decided by #862 as the switch had it: the tab still opens its menu
  // over the panel, and the live kind picked there closes the panel — the kind it already is.
  it('closes on the live kind picked in the menu, and on Android’s back, sending nothing', async () => {
    await openGames('COMPETITIVE');

    await openTheDoor('For fun');
    await screen.findByTestId('kind-door');
    await pickKind('Games', 'Competitive');
    expect(panel()).toBeNull();
    expect(screen.queryByTestId('tab-menu')).toBeNull();
    expect(useGameIntent.getState().intent).toBe('competitive');

    await openTheDoor('For fun');
    await screen.findByTestId('kind-door');
    let claimed = false;
    act(() => {
      claimed = pressHardwareBack();
    });
    expect(claimed).toBe(true);
    expect(panel()).toBeNull();
    expect(screen).toHavePathname(PAGE_PATH);

    expect(declarations('PADEL')).toHaveLength(0);
  });

  it('closes on a change of sport, and is not there on coming back', async () => {
    await openGames('COMPETITIVE');

    await openTheDoor('For fun');
    await screen.findByTestId('kind-door');
    await pickSport('Padel', 'Tennis');
    expect(await live('For fun, 2 games', true)).toBeTruthy();
    expect(panel()).toBeNull();

    await pickSport('Tennis', 'Padel');
    expect(await live('Competitive, 7 games', true)).toBeTruthy();
    expect(panel()).toBeNull();
  });
});

describe('an answer', () => {
  it('Either suits me declares it for padel on the deck, and lands on For fun with both live', async () => {
    await openGames('COMPETITIVE');

    await openTheDoor('For fun');
    fireEvent.press(answer('Either suits me'));

    expect(await live('For fun, 3 games', true)).toBeTruthy();
    expect(await screen.findByTestId(`game-card-${FIRST.FOR_FUN.proposal_id}`)).toBeTruthy();
    expect(await live('Competitive, 7 games', false)).toBeTruthy();
    expect(await doorsInTheMenu()).toEqual([]);
    expect(panel()).toBeNull();
    expect(declarations('PADEL').map((request) => request.body)).toEqual([
      { intent: 'NO_PREFERENCE', surface: 'DECK' },
    ]);
    expect(useGameIntent.getState().intent).toBe('forFun');
  });

  it('the kind tapped declares it alone, and the kind Ania played becomes the door', async () => {
    await openGames('COMPETITIVE');

    await openTheDoor('For fun');
    fireEvent.press(answer('For fun'));

    expect(await live('For fun, 3 games', true)).toBeTruthy();
    expect(await door('Competitive')).toBeTruthy();
    expect(await screen.findByTestId(`game-card-${FIRST.FOR_FUN.proposal_id}`)).toBeTruthy();
    expect(declarations('PADEL').map((request) => request.body)).toEqual([
      { intent: 'FOR_FUN', surface: 'DECK' },
    ]);
  });

  it('lands Kuba on Competitive when he takes it', async () => {
    useGameIntent.setState({ intent: 'forFun' });
    await openGames('FOR_FUN');

    await openTheDoor('Competitive');
    fireEvent.press(answer('Competitive'));

    expect(await live('Competitive, 7 games', true)).toBeTruthy();
    expect(await door('For fun')).toBeTruthy();
    expect(declarations('PADEL').map((request) => request.body)).toEqual([
      { intent: 'COMPETITIVE', surface: 'DECK' },
    ]);
    expect(useGameIntent.getState().intent).toBe('competitive');
  });

  it('changes padel only: tennis keeps its For fun', async () => {
    await openGames('COMPETITIVE');

    await openTheDoor('For fun');
    fireEvent.press(answer('Either suits me'));
    expect(await live('For fun, 3 games', true)).toBeTruthy();

    await pickSport('Padel', 'Tennis');

    expect(await live('For fun, 2 games', true)).toBeTruthy();
    expect(await door('Competitive')).toBeTruthy();
    expect(declarations('TENNIS')).toHaveLength(0);
    expect(intents.TENNIS).toBe('FOR_FUN');
  });

  it('holds the menu while it is on its way — the chevron drawn, inert — then lands on the kind tapped', async () => {
    await openGames('COMPETITIVE');
    const release = holdTheDeclaration();

    await openTheDoor('For fun');
    fireEvent.press(answer('For fun'));
    await waitFor(() => expect(declarations('PADEL')).toHaveLength(1));
    act(() => jest.advanceTimersByTime(0));

    // The chevron stays so the bar doesn't jump, and a press on the tab opens nothing meanwhile.
    expect(chevron()).toBeTruthy();
    await tabOpensNothing();
    expect(screen.getByTestId('kind-door')).toBeTruthy();
    expect(useGameIntent.getState().intent).toBe('competitive');

    await act(async () => release());

    expect(await live('For fun, 3 games', true)).toBeTruthy();
    expect(panel()).toBeNull();
    expect(useGameIntent.getState().intent).toBe('forFun');
  });

  it('still lands when the page goes to another sport before it does', async () => {
    await openGames('COMPETITIVE');
    const release = holdTheDeclaration();

    await openTheDoor('For fun');
    fireEvent.press(answer('Either suits me'));
    await waitFor(() => expect(declarations('PADEL')).toHaveLength(1));
    await pickSport('Padel', 'Tennis');
    expect(await live('For fun, 2 games', true)).toBeTruthy();

    await act(async () => release());
    await pickSport('Tennis', 'Padel');

    // Padel was read again for the answer, and the deck stands on the kind tapped.
    expect(await live('For fun, 3 games', true)).toBeTruthy();
    expect(await live('Competitive, 7 games', false)).toBeTruthy();
    expect(useGameIntent.getState().intent).toBe('forFun');
  });

  it('says why a refused answer failed, in the panel, and changes nothing', async () => {
    await openGames('COMPETITIVE');
    transport.on('PUT', intentPath('PADEL'), () => errorResponse(500, 'internal_error'));

    await openTheDoor('For fun');
    fireEvent.press(answer('For fun'));

    expect(await within(screen.getByTestId('kind-door')).findByRole('alert')).toBeTruthy();
    expect(await live('Competitive, 7 games', true)).toBeTruthy();
    expect(intents.PADEL).toBe('COMPETITIVE');
  });
});

describe('finding, after the door’s answer', () => {
  it('says it is finding the kind tapped while the group is dealt, then deals its cards', async () => {
    await openGames('COMPETITIVE');
    const release = holdTheDeal();

    await openTheDoor('For fun');
    fireEvent.press(answer('Either suits me'));

    expect(await findingSays('Finding for-fun games for you…')).toBeTruthy();
    expect(panel()).toBeNull();
    // Over the deck's area: the cards it covers are still laid out under it.
    expect(
      screen.getByTestId(`game-card-${FIRST.COMPETITIVE.proposal_id}`, HIDDEN_TOO),
    ).toBeTruthy();
    // The chevron stays drawn while the games are found, and a press on the tab opens nothing.
    act(() => jest.advanceTimersByTime(0));
    expect(chevron()).toBeTruthy();
    await tabOpensNothing();

    await act(async () => release());

    expect(await live('For fun, 3 games', true)).toBeTruthy();
    expect(await screen.findByTestId(`game-card-${FIRST.FOR_FUN.proposal_id}`)).toBeTruthy();
    expect(screen.queryByText('Finding for-fun games for you…')).toBeNull();
    // Landed by finding, the kind is drawn directly: no stack went out, and none comes in (#863).
    const stack = StyleSheet.flatten(
      screen.getByTestId('games-deck-stack').props.style as ViewStyle,
    );
    expect([stack.opacity, stack.transform]).toEqual([1, [{ translateY: 0 }]]);
  });

  it('sends the answer, then the deal, then reads the deck — once', async () => {
    await openGames('COMPETITIVE');
    await openTheDoor('For fun');
    const from = transport.requests.length;

    fireEvent.press(answer('For fun'));

    expect(await live('For fun, 3 games', true)).toBeTruthy();
    expect(trafficSince(from)).toEqual([
      `PUT ${intentPath('PADEL')}`,
      `POST ${dealPath(GROUP.id)}`,
      `GET ${deckPath(GROUP.id)}`,
    ]);
    expect(transport.requestsTo('GET', deckPath(GROUP.id)).at(-1)?.path).toContain('kind=FOR_FUN');
    // The page's Fill in is read again with it: who a seat is offered to reads the intent too.
    expect(
      transport.requests
        .slice(from)
        .filter((request) => request.path.split('?')[0] === fillInPath(GROUP.id)),
    ).toHaveLength(1);
  });

  it('still lands on the kind asked for when the player leaves Games before it has', async () => {
    await openGames('COMPETITIVE');
    const release = holdTheDeal();

    await openTheDoor('For fun');
    fireEvent.press(answer('Either suits me'));
    expect(await findingSays('Finding for-fun games for you…')).toBeTruthy();
    fireEvent.press(await screen.findByRole('button', { name: /^Fill in/ }));
    await act(async () => release());
    await waitFor(() => expect(useGameIntent.getState().intent).toBe('forFun'));

    fireEvent.press(await screen.findByRole('button', { name: /^Games/ }));

    expect(await live('For fun, 3 games', true)).toBeTruthy();
    expect(await screen.findByTestId(`game-card-${FIRST.FOR_FUN.proposal_id}`)).toBeTruthy();
  });

  it('gives a deal that never answers up at the request’s timeout, and reads the deck', async () => {
    await openGames('COMPETITIVE');
    transport.on('POST', dealPath(GROUP.id), neverResponds());

    await openTheDoor('For fun');
    fireEvent.press(answer('For fun'));
    expect(await findingSays('Finding for-fun games for you…')).toBeTruthy();

    act(() => jest.advanceTimersByTime(TIMEOUT_MS.request + 1));

    expect(await live('For fun, 0 games', true)).toBeTruthy();
    expect(await screen.findByText('Nothing picked right now')).toBeTruthy();
    expect(screen.queryByText(/^Finding/)).toBeNull();
  });

  it('keeps the deck as it stands when the connection is gone for the read too', async () => {
    await openGames('COMPETITIVE');
    await screen.findByTestId(`game-card-${FIRST.COMPETITIVE.proposal_id}`);
    transport.on('POST', dealPath(GROUP.id), networkFailure());
    transport.on('GET', deckPath(GROUP.id), networkFailure());

    await openTheDoor('For fun');
    fireEvent.press(answer('For fun'));

    // Finding ends, and the deck stays on the kind the phone has rather than one no read can reach.
    await waitFor(() => expect(screen.queryByText(/^Finding/)).toBeNull());
    expect(await live('Competitive, 7 games', true)).toBeTruthy();
    expect(screen.getByTestId(`game-card-${FIRST.COMPETITIVE.proposal_id}`)).toBeTruthy();
    expect(screen.queryByRole('alert')).toBeNull();
    expect(useGameIntent.getState().intent).toBe('competitive');
  });

  it('ends on Nothing picked right now and Post a game when the deal deals nothing', async () => {
    dealing.FOR_FUN = 0;
    await openGames('COMPETITIVE');

    await openTheDoor('For fun');
    fireEvent.press(answer('For fun'));

    expect(await live('For fun, 0 games', true)).toBeTruthy();
    expect(await screen.findByText('Nothing picked right now')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Post a game' })).toBeTruthy();
    expect(screen.queryByText(/^Finding/)).toBeNull();
  });

  it.each([
    ['the network', networkFailure()],
    ['pool_not_found', () => errorResponse(404, 'pool_not_found')],
    ['a server error', () => errorResponse(500, 'internal_error')],
  ])(
    'shows the deck as it stands when the deal fails on %s — said nowhere, tried once',
    async (_failure, responder) => {
      await openGames('COMPETITIVE');
      transport.on('POST', dealPath(GROUP.id), responder);

      await openTheDoor('For fun');
      fireEvent.press(answer('For fun'));

      // Nothing was dealt, so the new kind has nothing yet — the deck's own empty card says so.
      expect(await live('For fun, 0 games', true)).toBeTruthy();
      expect(await screen.findByText('Nothing picked right now')).toBeTruthy();
      expect(screen.queryByText(/^Finding/)).toBeNull();
      expect(screen.queryByRole('alert')).toBeNull();
      expect(useToastQueue.getState().queue).toEqual([]);
      expect(transport.requestsTo('POST', dealPath(GROUP.id))).toHaveLength(1);
      expect(transport.requestsTo('GET', deckPath(GROUP.id)).at(-1)?.path).toContain(
        'kind=FOR_FUN',
      );
    },
  );
});

describe('finding, after the first-time question', () => {
  it('names the kind answered while the group is dealt, then deals its cards', async () => {
    await openGames(undefined);
    const release = holdTheDeal();

    fireEvent.press(await screen.findByRole('button', { name: 'For fun, your usual at Padel' }));

    expect(await findingSays('Finding for-fun games for you…')).toBeTruthy();
    expect(screen.queryByText('Your usual game at Padel')).toBeNull();
    // No chevron yet: it first appears with the deck the answer lands on.
    expect(chevron()).toBeNull();

    await act(async () => release());

    expect(await live('For fun, 3 games', true)).toBeTruthy();
    expect(await screen.findByTestId(`game-card-${FIRST.FOR_FUN.proposal_id}`)).toBeTruthy();
    expect(await door('Competitive')).toBeTruthy();
  });

  it('names no kind after Either suits me, and lands where the deck stood', async () => {
    await openGames(undefined);
    const release = holdTheDeal();

    fireEvent.press(
      await screen.findByRole('button', { name: 'Either suits me, your usual at Padel' }),
    );

    expect(await findingSays('Finding games for you…')).toBeTruthy();

    await act(async () => release());

    expect(await live('Competitive, 7 games', true)).toBeTruthy();
    expect(await live('For fun, 3 games', false)).toBeTruthy();
    expect(await screen.findByTestId(`game-card-${FIRST.COMPETITIVE.proposal_id}`)).toBeTruthy();
  });

  it('sends the answer, then the deal, then reads the deck', async () => {
    await openGames(undefined);
    const ask = await screen.findByRole('button', { name: 'Competitive, your usual at Padel' });
    const from = transport.requests.length;

    fireEvent.press(ask);

    expect(await live('Competitive, 7 games', true)).toBeTruthy();
    expect(trafficSince(from)).toEqual([
      `PUT ${intentPath('PADEL')}`,
      `POST ${dealPath(GROUP.id)}`,
      `GET ${deckPath(GROUP.id)}`,
    ]);
  });

  it('shows the deck as it stands when the deal fails', async () => {
    await openGames(undefined);
    transport.on('POST', dealPath(GROUP.id), networkFailure());

    fireEvent.press(
      await screen.findByRole('button', { name: 'Competitive, your usual at Padel' }),
    );

    expect(await live('Competitive, 0 games', true)).toBeTruthy();
    expect(await screen.findByText('Nothing picked right now')).toBeTruthy();
    expect(screen.queryByRole('alert')).toBeNull();
  });
});
