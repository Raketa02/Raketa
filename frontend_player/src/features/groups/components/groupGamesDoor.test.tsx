/**
 * **The kind of game you don't play is a door** — a group's Games switch draws both kinds always,
 * the one the intent doesn't want dimmed with no number, and its press opens a panel in place that
 * changes the intent for the page's sport ([#740](https://github.com/Raketa02/Raketa/issues/740),
 * ADR-0201 §2; the screens A1, A2.1; the words §28).
 *
 * The real route tree, with the socket faked at the platform edge as a small server: it holds the
 * player's intent per sport, answers `PUT /play-intents/{sport}` by changing that sport's alone,
 * and deals the deck off it — the segments the intent shows, each counting its cards, and the
 * cards of the kind asked for only where the intent shows it. So the switch a test reads after an
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

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { TIMEOUT_MS } from '@/shared/lib/http';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { theme } from '@/shared/ui';
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

/** A live side of the switch, by its spoken name. */
const live = (name: string, selected?: boolean) =>
  screen.findByRole('button', { name, ...(selected === undefined ? {} : { selected }) });

/** The door, by its spoken name. */
const door = (kind: 'For fun' | 'Competitive') =>
  screen.findByRole('button', { name: `${kind}, not a kind you play` });

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

describe('the switch draws both kinds always', () => {
  it('draws Ania’s kind live with its number, and For fun dimmed with none', async () => {
    await openGames('COMPETITIVE');

    expect(await live('Competitive, 7 games', true)).toBeTruthy();
    expect(screen.getByText('Competitive · 7')).toBeTruthy();
    expect(await door('For fun')).toBeTruthy();
    expect(screen.getByText('For fun')).toBeTruthy();
    expect(screen.queryByText(/^For fun ·/)).toBeNull();
    expect(StyleSheet.flatten(screen.getByText('For fun').props.style as ViewStyle).opacity).toBe(
      theme.size.segDoorOpacity,
    );
  });

  it('draws Kuba’s mirror: Competitive dimmed, For fun · 3 live', async () => {
    await openGames('FOR_FUN');

    expect(await live('For fun, 3 games', true)).toBeTruthy();
    expect(screen.getByText('For fun · 3')).toBeTruthy();
    expect(await door('Competitive')).toBeTruthy();
    expect(screen.queryByText(/^Competitive ·/)).toBeNull();
  });

  it('leaves Zofia’s Either suits me as it was: both live, no door', async () => {
    await openGames('NO_PREFERENCE');

    expect(await live('Competitive, 7 games', true)).toBeTruthy();
    expect(screen.getByText('For fun · 3')).toBeTruthy();
    expect(screen.queryByLabelText(/not a kind you play/)).toBeNull();
  });

  it('still asks the first-time question, with no switch, for an undeclared sport', async () => {
    await openGames(undefined);

    expect(await screen.findByText('Your usual game at Padel')).toBeTruthy();
    expect(screen.queryByLabelText(/not a kind you play/)).toBeNull();
    expect(screen.queryByText(/^Competitive ·/)).toBeNull();
    expect(screen.queryByText(/^For fun ·/)).toBeNull();
  });
});

describe('the deck never opens on the dimmed kind', () => {
  it('opens on Ania’s competitive cards when the phone last stood on For fun elsewhere', async () => {
    useGameIntent.setState({ intent: 'forFun' });
    await openGames('COMPETITIVE');

    expect(await screen.findByTestId(`game-card-${FIRST.COMPETITIVE.proposal_id}`)).toBeTruthy();
    expect(
      screen.getByRole('button', { name: 'Competitive, 7 games', selected: true }),
    ).toBeTruthy();
    expect(screen.queryByTestId(`game-card-${FIRST.FOR_FUN.proposal_id}`, HIDDEN_TOO)).toBeNull();
  });

  it('does not move the remembered position when the door is tapped', async () => {
    useGameIntent.setState({ intent: 'forFun' });
    await openGames('COMPETITIVE');

    fireEvent.press(await door('For fun'));
    expect(await screen.findByTestId('kind-door')).toBeTruthy();
    expect(useGameIntent.getState().intent).toBe('forFun');

    fireEvent.press(screen.getByRole('button', { name: 'Keep competitive' }));
    expect(useGameIntent.getState().intent).toBe('forFun');
    expect(
      screen.getByRole('button', { name: 'Competitive, 7 games', selected: true }),
    ).toBeTruthy();
  });
});

describe('the panel', () => {
  it('opens in place over the deck, on the group page, with Ania’s words and count', async () => {
    await openGames('COMPETITIVE');
    await screen.findByTestId(`game-card-${FIRST.COMPETITIVE.proposal_id}`);

    fireEvent.press(await door('For fun'));

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

    // An overlay inside the deck's area: no new route, the switch still drawn, and the cards
    // still laid out under it rather than squeezed by it.
    expect(screen).toHavePathname(PAGE_PATH);
    expect(
      screen.getByTestId(`game-card-${FIRST.COMPETITIVE.proposal_id}`, HIDDEN_TOO),
    ).toBeTruthy();
    expect(
      screen.getByRole('button', { name: 'Competitive, 7 games', selected: true }),
    ).toBeTruthy();
  });

  it('is Kuba’s mirror for a for-fun player', async () => {
    await openGames('FOR_FUN');

    fireEvent.press(await door('Competitive'));

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

    fireEvent.press(await door('For fun'));

    expect(
      await screen.findByText('Keep your 1 competitive card and get for-fun ones too.'),
    ).toBeTruthy();
    expect(screen.getByText('Your 1 competitive card goes. Games you’re In on stay.')).toBeTruthy();
  });

  it('drops the number with nothing dealt, over the group’s starting card', async () => {
    dealing.COMPETITIVE = 0;
    await openGames('COMPETITIVE');
    expect(await screen.findByText('Nothing picked right now')).toBeTruthy();

    fireEvent.press(await door('For fun'));

    expect(await screen.findByText('Get for-fun games as well as competitive ones.')).toBeTruthy();
    expect(
      screen.getByText('Raketa stops dealing you competitive games. Games you’re In on stay.'),
    ).toBeTruthy();
    expect(screen.getByText('Nothing picked right now', HIDDEN_TOO)).toBeTruthy();
  });

  it('closes on Keep competitive and sends nothing', async () => {
    await openGames('COMPETITIVE');

    fireEvent.press(await door('For fun'));
    fireEvent.press(await screen.findByRole('button', { name: 'Keep competitive' }));

    expect(panel()).toBeNull();
    expect(declarations('PADEL')).toHaveLength(0);
    expect(screen.getByTestId(`game-card-${FIRST.COMPETITIVE.proposal_id}`)).toBeTruthy();
  });

  it('closes on the live kind’s press, and on Android’s back, sending nothing', async () => {
    await openGames('COMPETITIVE');

    fireEvent.press(await door('For fun'));
    await screen.findByTestId('kind-door');
    fireEvent.press(screen.getByRole('button', { name: 'Competitive, 7 games' }));
    expect(panel()).toBeNull();

    fireEvent.press(await door('For fun'));
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

    fireEvent.press(await door('For fun'));
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

    fireEvent.press(await door('For fun'));
    fireEvent.press(answer('Either suits me'));

    expect(await live('For fun, 3 games', true)).toBeTruthy();
    expect(await screen.findByTestId(`game-card-${FIRST.FOR_FUN.proposal_id}`)).toBeTruthy();
    expect(screen.getByText('Competitive · 7')).toBeTruthy();
    expect(screen.queryByLabelText(/not a kind you play/)).toBeNull();
    expect(panel()).toBeNull();
    expect(declarations('PADEL').map((request) => request.body)).toEqual([
      { intent: 'NO_PREFERENCE', surface: 'DECK' },
    ]);
    expect(useGameIntent.getState().intent).toBe('forFun');
  });

  it('the kind tapped declares it alone, and the kind Ania played becomes the door', async () => {
    await openGames('COMPETITIVE');

    fireEvent.press(await door('For fun'));
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

    fireEvent.press(await door('Competitive'));
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

    fireEvent.press(await door('For fun'));
    fireEvent.press(answer('Either suits me'));
    expect(await live('For fun, 3 games', true)).toBeTruthy();

    await pickSport('Padel', 'Tennis');

    expect(await live('For fun, 2 games', true)).toBeTruthy();
    expect(await door('Competitive')).toBeTruthy();
    expect(declarations('TENNIS')).toHaveLength(0);
    expect(intents.TENNIS).toBe('FOR_FUN');
  });

  it('holds the switch while it is on its way, then lands on the kind tapped', async () => {
    await openGames('COMPETITIVE');
    const release = holdTheDeclaration();

    fireEvent.press(await door('For fun'));
    fireEvent.press(answer('For fun'));
    await waitFor(() => expect(declarations('PADEL')).toHaveLength(1));

    // The live kind's press, which would close the panel at rest, moves nothing meanwhile.
    fireEvent.press(screen.getByRole('button', { name: 'Competitive, 7 games' }));
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

    fireEvent.press(await door('For fun'));
    fireEvent.press(answer('Either suits me'));
    await waitFor(() => expect(declarations('PADEL')).toHaveLength(1));
    await pickSport('Padel', 'Tennis');
    expect(await live('For fun, 2 games', true)).toBeTruthy();

    await act(async () => release());
    await pickSport('Tennis', 'Padel');

    // Padel was read again for the answer, and the switch stands on the kind tapped.
    expect(await live('For fun, 3 games', true)).toBeTruthy();
    expect(screen.getByText('Competitive · 7')).toBeTruthy();
    expect(useGameIntent.getState().intent).toBe('forFun');
  });

  it('says why a refused answer failed, in the panel, and changes nothing', async () => {
    await openGames('COMPETITIVE');
    transport.on('PUT', intentPath('PADEL'), () => errorResponse(500, 'internal_error'));

    fireEvent.press(await door('For fun'));
    fireEvent.press(answer('For fun'));

    expect(await within(screen.getByTestId('kind-door')).findByRole('alert')).toBeTruthy();
    expect(
      screen.getByRole('button', { name: 'Competitive, 7 games', selected: true }),
    ).toBeTruthy();
    expect(intents.PADEL).toBe('COMPETITIVE');
  });
});

describe('finding, after the door’s answer', () => {
  it('says it is finding the kind tapped while the group is dealt, then deals its cards', async () => {
    await openGames('COMPETITIVE');
    const release = holdTheDeal();

    fireEvent.press(await door('For fun'));
    fireEvent.press(answer('Either suits me'));

    expect(await findingSays('Finding for-fun games for you…')).toBeTruthy();
    expect(panel()).toBeNull();
    // Over the deck's area: the cards it covers are still laid out under it.
    expect(
      screen.getByTestId(`game-card-${FIRST.COMPETITIVE.proposal_id}`, HIDDEN_TOO),
    ).toBeTruthy();

    await act(async () => release());

    expect(await live('For fun, 3 games', true)).toBeTruthy();
    expect(await screen.findByTestId(`game-card-${FIRST.FOR_FUN.proposal_id}`)).toBeTruthy();
    expect(screen.queryByText('Finding for-fun games for you…')).toBeNull();
  });

  it('sends the answer, then the deal, then reads the deck — once', async () => {
    await openGames('COMPETITIVE');
    fireEvent.press(await door('For fun'));
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

    fireEvent.press(await door('For fun'));
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

    fireEvent.press(await door('For fun'));
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

    fireEvent.press(await door('For fun'));
    fireEvent.press(answer('For fun'));

    // Finding ends, and the switch stays on the deck the phone has rather than one no read can reach.
    await waitFor(() => expect(screen.queryByText(/^Finding/)).toBeNull());
    expect(
      screen.getByRole('button', { name: 'Competitive, 7 games', selected: true }),
    ).toBeTruthy();
    expect(screen.getByTestId(`game-card-${FIRST.COMPETITIVE.proposal_id}`)).toBeTruthy();
    expect(screen.queryByRole('alert')).toBeNull();
    expect(useGameIntent.getState().intent).toBe('competitive');
  });

  it('ends on Nothing picked right now and Post a game when the deal deals nothing', async () => {
    dealing.FOR_FUN = 0;
    await openGames('COMPETITIVE');

    fireEvent.press(await door('For fun'));
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

      fireEvent.press(await door('For fun'));
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

    await act(async () => release());

    expect(await live('For fun, 3 games', true)).toBeTruthy();
    expect(await screen.findByTestId(`game-card-${FIRST.FOR_FUN.proposal_id}`)).toBeTruthy();
    expect(await door('Competitive')).toBeTruthy();
  });

  it('names no kind after Either suits me, and lands where the switch stood', async () => {
    await openGames(undefined);
    const release = holdTheDeal();

    fireEvent.press(
      await screen.findByRole('button', { name: 'Either suits me, your usual at Padel' }),
    );

    expect(await findingSays('Finding games for you…')).toBeTruthy();

    await act(async () => release());

    expect(await live('Competitive, 7 games', true)).toBeTruthy();
    expect(screen.getByText('For fun · 3')).toBeTruthy();
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
