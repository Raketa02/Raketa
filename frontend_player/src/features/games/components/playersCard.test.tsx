/**
 * **The players card on the game screen's plan lead, walked the way a player walks it**: the
 * real route tree, the real shell, and only `fetch` faked.
 *
 * [#415](https://github.com/Raketa02/Raketa/issues/415)'s acceptance criteria for the card are
 * assertions in this file and opinions nowhere else — the rows in reading order with you first,
 * the whole handle with `(you)` after yours, the level row as a fixture reads it, no level row
 * under an unrated seat, no chip on anybody, a **tap** opening the record sheet for that player,
 * and the footer sentence. The forecast block above it is `forecastBlock.test.tsx`'s.
 */

import { fireEvent, screen, waitFor, within } from 'expo-router/testing-library';
import { Image, Text } from 'react-native';

import { OWN_RECORD_TITLE, RECORD_TITLE, recordCloseLabel } from '@/features/player_record/types';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { Card } from '@/shared/ui';
import {
  GATE_USER,
  launchSignedIn,
  stubConversation,
  stubConversations,
  stubEntries,
  stubGames,
  stubGate,
  stubPairing,
  stubPlans,
} from '@/test-support/onboardingRouter';
import { installTransport, json, type Transport, type Wire } from '@/test-support/transport';

import {
  PLAYERS,
  PLAYERS_FOOTER,
  playerRowName,
  recordLabel,
  seatLevelLine,
} from './gamePresentation';

const ME = GATE_USER.id;
const TOMEK = 'bbbbbbbb-0000-4000-8000-000000000002';
const KASIA = 'cccccccc-0000-4000-8000-000000000003';
const MAREK = 'dddddddd-0000-4000-8000-000000000004';

const GAME = 'aaaaaaaa-0000-4000-8000-000000000009';
const CHALLENGE = 'ffffffff-0000-4000-8000-000000000006';
const ROOM = 'eeeeeeee-0000-4000-8000-000000000005';

const READ_AT = '2026-09-12T09:00:00Z';
const PLANNED_AT = '2026-09-08T09:00:00Z';

/** A signed link, as the room mints one — the only address a photograph has. */
const TOMEK_PHOTO = 'https://photos.example.test/tomek.jpg?sig=abc';

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

const FOUR: Wire['ConversationMemberSchema'][] = [
  { player_id: ME, name: 'me_' },
  { player_id: TOMEK, name: 'tomek.p', photo_id: 'p1', photo_url: TOMEK_PHOTO },
  { player_id: KASIA, name: 'kasia.w' },
  { player_id: MAREK, name: 'marek b' },
];

/** Seated in the challenge's order — the other side first, and you last on yours. */
const DOUBLES_SEATS: Wire['GameSchema']['seats'] = [
  { side: 'B', player_id: TOMEK, name: 'tomek.p' },
  { side: 'B', player_id: MAREK, name: 'marek b' },
  { side: 'A', player_id: KASIA, name: 'kasia.w' },
  { side: 'A', player_id: ME, name: 'me_' },
];

function game(over: Partial<Wire['GameSchema']> = {}): Wire['GameSchema'] {
  return {
    game_id: GAME,
    challenge_id: CHALLENGE,
    sport: 'PADEL',
    kind: 'COUNTED',
    standing: 'AWAITING_ENTRY',
    planned_at: PLANNED_AT,
    entry_closes_at: '2026-09-20T09:00:00Z',
    seats: DOUBLES_SEATS,
    proposals: [],
    ...over,
  };
}

/** Mock 8's own rows: four Levels, each with a band, a range and a certainty. */
const ROWS: Wire['GamePairingSeatSchema'][] = [
  {
    player_id: TOMEK,
    level: 2.8,
    band: 'Established',
    range: { low: 2.72, high: 2.88 },
    confidence: 88,
  },
  {
    player_id: MAREK,
    level: 2.64,
    band: 'Developing',
    range: { low: 2.48, high: 2.8 },
    confidence: 71,
  },
  {
    player_id: KASIA,
    level: 2.69,
    band: 'Developing',
    range: { low: 2.58, high: 2.8 },
    confidence: 80,
  },
  {
    player_id: ME,
    level: 2.71,
    band: 'Established',
    range: { low: 2.55, high: 2.87 },
    confidence: 74,
  },
];

function pairing(over: Partial<Wire['GamePairingResponse']> = {}): Wire['GamePairingResponse'] {
  return {
    read_at: READ_AT,
    forecast: { pct: 90, sigma_group: 0.4, provisional: false, assumption: null },
    split: { your_side: 2.7, their_side: 2.71, gap: -0.01 },
    at_stake: { win_delta: 0.08, loss_delta: -0.08 },
    seats: ROWS,
    ...over,
  };
}

function record(over: Partial<Wire['PlayerRecordResponse']> = {}): Wire['PlayerRecordResponse'] {
  return {
    is_self: false,
    name: 'tomek.p',
    nickname: 'tomek_p',
    area_code: 'A+050612+0019938',
    social_tags: [],
    sports: [{ sport: 'PADEL', level: 2.8, band: 'Established' }],
    skill: {
      sport: 'PADEL',
      level: 2.8,
      band: 'Established',
      confidence: 88,
      counted_games: 21,
      likely_range: { low: 2.72, high: 2.88 },
      last_five: ['WIN', 'WIN', 'LOSS'],
    },
    reliability: { player_score: 93, strands: [] },
    variety: { distinct_opponents: 14, times_on_court: 20 },
    ...over,
  };
}

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [PADEL_RATING], hasPlayerProfile: true });
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

function stubTheWorld({
  games = [game()],
  court = pairing(),
}: {
  readonly games?: readonly Wire['GameSchema'][];
  readonly court?: Parameters<typeof stubPairing>[2];
} = {}) {
  stubGames(transport, games, READ_AT);
  stubPlans(transport, []);
  stubConversations(transport, [
    {
      conversation_id: ROOM,
      challenge_id: CHALLENGE,
      game_id: GAME,
      sport: 'PADEL',
      members: FOUR,
      people: FOUR,
      last_entry: null,
    },
  ]);
  stubConversation(transport, {
    read_at: READ_AT,
    conversation_id: ROOM,
    challenge_id: CHALLENGE,
    game_id: GAME,
    sport: 'PADEL',
    members: FOUR,
    people: FOUR,
    entries: [],
  });
  stubEntries(transport, ROOM);
  stubPairing(transport, GAME, court);
}

async function openTheGame(over: Parameters<typeof stubTheWorld>[0] = {}) {
  stubTheWorld(over);

  await launchSignedIn(`/games/${GAME}`);
  await waitFor(() => expect(screen).toHavePathname(`/games/${GAME}`));
  // By role: the bar's second column says *Players* too, and it is a tab and not a heading.
  await screen.findByRole('header', { name: PLAYERS });
}

/** The card, found by its own eyebrow. */
function theCard() {
  const card = screen
    .UNSAFE_getAllByType(Card)
    .find((one) => within(one).queryByText(PLAYERS) !== null);
  if (card === undefined) throw new Error('no players card on the screen');
  return card;
}

/** Every string the card draws, in tree order. */
const drawnIn = () =>
  within(theCard())
    .UNSAFE_getAllByType(Text)
    .map((text) => text.props.children)
    .filter((child): child is string => typeof child === 'string');

const me = { name: 'me_', yours: true };
const tomek = { name: 'tomek.p', yours: false };
const kasia = { name: 'kasia.w', yours: false };
const marek = { name: 'marek b', yours: false };

describe('the rows', () => {
  /**
   * **Your side first — you, then your partner — then the other side**, whatever order the
   * challenge seated the court in. The court here is seated the other way round on purpose.
   */
  it('draws you first, then your partner, then the other side', async () => {
    await openTheGame();

    const drawn = drawnIn();
    const at = (person: Parameters<typeof playerRowName>[0]) =>
      drawn.indexOf(playerRowName(person));

    expect(at(me)).toBeGreaterThan(-1);
    expect(at(me)).toBeLessThan(at(kasia));
    expect(at(kasia)).toBeLessThan(at(tomek));
    expect(at(tomek)).toBeLessThan(at(marek));
  });

  /** The whole handle, and `(you)` after yours — never a familiar form, never *You* alone. */
  it('names every row by the whole handle and marks yours', async () => {
    await openTheGame();

    expect(screen.getByText('me_ (you)')).toBeTruthy();
    expect(screen.getByText('tomek.p')).toBeTruthy();
    expect(screen.getByText('marek b')).toBeTruthy();
  });

  /** The level row, as mock 8's first row reads once §6.4's words are put back. */
  it('prints the level row under each handle from the pairing', async () => {
    await openTheGame();

    expect(
      await screen.findByText('2,71 · Established · likely 2,55 – 2,87 · 74% sure'),
    ).toBeTruthy();
    expect(screen.getByText('2,80 · Established · likely 2,72 – 2,88 · 88% sure')).toBeTruthy();
    expect(
      screen.getByText(
        seatLevelLine({
          playerId: MAREK,
          level: 2.64,
          band: 'Developing',
          range: { low: 2.48, high: 2.8 },
          confidence: 71,
        }),
      ),
    ).toBeTruthy();
  });

  /** Somebody unrated is not in `seats`, and their row is a handle with nothing under it. */
  it('draws a handle and no level row for a seat the pairing has no row for', async () => {
    await openTheGame({ court: pairing({ seats: ROWS.filter((row) => row.player_id !== MAREK) }) });

    expect(await screen.findAllByText(/% sure$/)).toHaveLength(3);
    expect(screen.getByText('marek b')).toBeTruthy();
    expect(screen.queryByText(/2,64/)).toBeNull();
  });

  /** Mock 4's *proposed it* / *in* are not built: no chip, no tag, on anybody. */
  it('draws no chip on anybody', async () => {
    await openTheGame();

    expect(drawnIn()).not.toEqual(
      expect.arrayContaining([expect.stringMatching(/proposed|^in$/i)]),
    );
  });

  /** The same faces join as the card above: a photograph where the room has one, a poster otherwise. */
  it('draws a face where the room has a photograph', async () => {
    await openTheGame();

    const faces = within(theCard())
      .UNSAFE_getAllByType(Image)
      .map((image) => image.props.source);

    expect(faces).toEqual([{ uri: TOMEK_PHOTO }]);
  });

  /** The card stands without the pairing: the seats are the game's, and the Levels are extra. */
  it('draws every handle with no level row when the route refuses by name', async () => {
    await openTheGame({ court: { refused: 409, code: 'pairing_is_history' } });

    expect(screen.getByText('me_ (you)')).toBeTruthy();
    expect(screen.getByText('tomek.p')).toBeTruthy();
    expect(screen.queryByText(/% sure$/)).toBeNull();
  });
});

describe('the tap', () => {
  /**
   * **Tap, not hold** (#285): the whole row is a button named for the record it opens, and the
   * sheet that opens is that player's — the read is `GET /players/{id}/record`, admitted because
   * you share a game with them, and no backend work stands behind the tap.
   */
  it('opens the record sheet for the player whose row was tapped', async () => {
    await openTheGame();
    transport.on('GET', `/api/v1/players/${TOMEK}/record?sport=PADEL`, () => json(record()));

    // No `@` on any row: the handle is the record's and the You tab's, and nobody else's.
    expect(screen.queryByText(/@/)).toBeNull();

    fireEvent.press(screen.getByRole('button', { name: recordLabel(tomek) }));

    expect(await screen.findByLabelText(recordCloseLabel(false))).toBeTruthy();
    expect(screen.getByText(RECORD_TITLE)).toBeTruthy();
    await waitFor(() =>
      expect(
        transport.requestsTo('GET', `/api/v1/players/${TOMEK}/record?sport=PADEL`),
      ).toHaveLength(1),
    );
    // The name, and the `@nickname` under it — the record is one of the two places it is drawn
    // (ADR-0171 §4).
    expect(await screen.findByText('@tomek_p')).toBeTruthy();
  });

  /** Your own row opens your own record, retitled, through the route that serves it. */
  it('opens your own record from your own row', async () => {
    await openTheGame();
    transport.on('GET', '/api/v1/players/me/record?sport=PADEL', () =>
      json(record({ is_self: true, name: 'me_' })),
    );

    fireEvent.press(screen.getByRole('button', { name: recordLabel(me) }));

    expect(await screen.findByText(OWN_RECORD_TITLE)).toBeTruthy();
    await waitFor(() =>
      expect(transport.requestsTo('GET', '/api/v1/players/me/record?sport=PADEL')).toHaveLength(1),
    );
  });

  it('closes the sheet, and the card is still there', async () => {
    await openTheGame();
    transport.on('GET', `/api/v1/players/${TOMEK}/record?sport=PADEL`, () => json(record()));

    fireEvent.press(screen.getByRole('button', { name: recordLabel(tomek) }));
    fireEvent.press(await screen.findByLabelText(recordCloseLabel(false)));

    await waitFor(() => expect(screen.queryByText(RECORD_TITLE)).toBeNull());
    expect(screen.getByRole('header', { name: PLAYERS })).toBeTruthy();
  });
});

describe('the footer', () => {
  /** The sentence is true: it says *tap*, and the record it promises is the one the tap opens. */
  it('says tap, and what the record holds', async () => {
    await openTheGame();

    expect(screen.getByText(PLAYERS_FOOTER)).toBeTruthy();
    expect(screen.queryByText(/press and hold/i)).toBeNull();
    expect(screen.queryByText(/reviews/i)).toBeNull();
  });
});
