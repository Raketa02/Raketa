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
 * **The deck is read at `DECK_READ_AT`**, Wednesday 30 September 2026 at 10:00 in Warsaw: the
 * suite pins the fake clock there once the tree is up, so the countdown and the court's day are
 * read against a known instant. A navigation runs the pending timers and moves the clock a few
 * seconds on, so a countdown is asserted to its hour and never to its minute.
 */

import { onlineManager } from '@tanstack/react-query';
import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { RECORD_TITLE } from '@/features/player_record/types';
import { PROPOSALS_COPY } from '@/features/proposals/types';
import { offlineMessage } from '@/shared/errors';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { useToastQueue } from '@/shared/store/toast.store';
import { theme } from '@/shared/ui';
import {
  ANIA,
  deckCard,
  deckPath,
  DECK_READ_AT,
  EWA,
  groupDeck,
  hoursAfterRead,
  KAROL,
  KUBA,
  noPath,
  stubGroupDeck,
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
  stubProfileOptions,
  stubProfileSurface,
  stubShare,
} from '@/test-support/onboardingRouter';
import { fakeClipboard, fakeHaptics, fakeShare, type FakeHaptics } from '@/test-support/platform';
import { dragTo, release, swipe } from '@/test-support/swipe';
import {
  errorResponse,
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { useGameIntent } from '../store/gameIntent.store';

const COPY = PROPOSALS_COPY;
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
  return { player_id: `e0000000-0000-4000-8000-00000000000${n}`, name };
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
        { player_id: GATE_USER.id, name: 'Ada Lovelace' },
        person(2, 'Member 2'),
        person(3, 'Member 3'),
        person(4, 'Member 4'),
      ],
    },
  ],
  member_faces: [],
  administrator_name: null,
  is_administrator: false,
};

/** Karol's record, as `GET /players/{id}/record` answers when a tile opens it. */
function karolsRecord(): Wire['PlayerRecordResponse'] {
  return {
    is_self: false,
    name: 'Karol Tomaszewski',
    nickname: 'karol_t',
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
    reliability: {
      player_score: 88,
      strands: [{ strand: 'SHOWS_UP', good: 3, opportunities: 3, pct: 100 }],
    },
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

describe('the switch', () => {
  it('draws Competitive · N and For fun · N, off the read', async () => {
    await openGames(
      groupDeck({
        segments: [
          { kind: 'COMPETITIVE', count: 5 },
          { kind: 'FOR_FUN', count: 1 },
        ],
      }),
    );

    expect(
      await screen.findByRole('button', { name: 'Competitive, 5 games', selected: true }),
    ).toBeTruthy();
    expect(screen.getByText('Competitive · 5')).toBeTruthy();
    expect(screen.getByText('For fun · 1')).toBeTruthy();
  });

  it('reads the other kind when pressed, and keeps it for Friends', async () => {
    const funCard = deckCard({
      kind: 'FOR_FUN',
      sides: { yours: [youTile(), KUBA()], theirs: [ANIA(), EWA()] },
    });
    await openGames((kind) =>
      groupDeck({
        kind: kind ?? 'COMPETITIVE',
        segments: [
          { kind: 'COMPETITIVE', count: 0 },
          { kind: 'FOR_FUN', count: 1 },
        ],
        cards: kind === 'FOR_FUN' ? [funCard] : [],
      }),
    );

    fireEvent.press(await screen.findByRole('button', { name: 'For fun, 1 game' }));

    expect(await screen.findByTestId(`game-card-${funCard.proposal_id}`)).toBeTruthy();
    expect(deckRequests().some((request) => request.path.includes('kind=FOR_FUN'))).toBe(true);
    expect(useGameIntent.getState().intent).toBe('forFun');
  });

  it('shows only the segment a one-kind intent wants, whatever the switch last stood on', async () => {
    const funCard = deckCard({ kind: 'FOR_FUN' });
    await openGames((kind) =>
      groupDeck({
        segments: [{ kind: 'FOR_FUN', count: 1 }],
        cards: kind === 'FOR_FUN' ? [funCard] : [],
      }),
    );

    expect(await screen.findByTestId(`game-card-${funCard.proposal_id}`)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'For fun, 1 game', selected: true })).toBeTruthy();
    expect(screen.queryByText(/^Competitive ·/)).toBeNull();
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
  it('keeps the starting card when nothing is dealt, and Nothing picked gains a disabled Post a game', async () => {
    await openGames();

    expect(await screen.findByText('Nothing picked right now')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Post a game', disabled: true })).toBeTruthy();
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

  it('counts the cards somebody is In on, on the Games tab', async () => {
    await openGames(groupDeck({ cards: [deckCard()], games_badge: 4 }));

    expect(await screen.findByRole('button', { name: 'Games, 4 with somebody In' })).toBeTruthy();
  });

  it('says why a read failed, and reads again on the retry', async () => {
    let refused = false;
    stubMyGroups(transport, [CREW]);
    transport.on('GET', `/api/v1/groups/${CREW.id}`, () => json(PAGE));
    transport.on('GET', deckPath(CREW.id), () => {
      if (refused) return json(groupDeck({ cards: [deckCard()] }));
      refused = true;
      return errorResponse(429, 'rate_limited');
    });
    await launchSignedIn();
    fireEvent.press(await screen.findByLabelText('Play'));
    fireEvent.press(await screen.findByRole('button', { name: /^Kazimierz crew,/ }));

    fireEvent.press(await screen.findByRole('button', { name: COPY.readAgain }));

    expect(await screen.findByLabelText(COPY.details)).toBeTruthy();
  });
});

describe('the card', () => {
  it('draws a pick — the ribbon, the tiles, the vs line, the forecast, the grid and a free vote', async () => {
    const card = deckCard();
    await openGames(groupDeck({ cards: [card] }));

    expect(await screen.findByRole('header', { name: 'Picked for you' })).toBeTruthy();
    // Your side on top while nobody is In, you first: YOU + ZOFIA VS ANIA + EWA.
    expect(screen.getByText('You + Zofia vs Ania + Ewa', HIDDEN_TOO)).toBeTruthy();
    expect(screen.getByLabelText('Zofia Bielecka, level 2,69')).toBeTruthy();
    expect(screen.getByLabelText('You, level 2,71')).toBeTruthy();
    expect(
      screen.getByLabelText('Balance forecast 87%, very even: You + Zofia against Ania + Ewa'),
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

    expect(await screen.findByLabelText('Karol Tomaszewski, level 2,75, In')).toBeTruthy();
    expect(screen.getAllByText(COPY.in, HIDDEN_TOO)).toHaveLength(3);
    // The side with more people In is the top row, and In reads before you: *Ania + You*.
    expect(screen.getByText('Karol + Zofia vs Ania + You', HIDDEN_TOO)).toBeTruthy();
    expect(screen.queryByText(/asked|no answer yet|^friend$/i, HIDDEN_TOO)).toBeNull();
  });

  it('says you complete it, and a Book it now court carries its price on the stamp', async () => {
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
    expect(screen.getByText('I’m in · 32 zł', HIDDEN_TOO)).toBeTruthy();
    expect(screen.getByText('Not this time', HIDDEN_TOO)).toBeTruthy();
    release(tile(KAROL().player_id));
  });

  it('prices no stamp at an On request club, where the charge waits for the club', async () => {
    await openGames(
      groupDeck({
        cards: [
          deckCard({ court: 'BOOK_IT_NOW', club_confirms: true, open_seats_after_your_yes: 0 }),
        ],
      }),
    );

    await screen.findByLabelText(COPY.details);
    expect(screen.getByText('I’m in', HIDDEN_TOO)).toBeTruthy();
    expect(screen.queryByText(/I’m in · /, HIDDEN_TOO)).toBeNull();
  });

  it('prices no stamp on a free vote', async () => {
    await openGames(groupDeck({ cards: [deckCard()] }));

    await screen.findByLabelText(COPY.details);
    expect(screen.queryByText(/I’m in · /, HIDDEN_TOO)).toBeNull();
  });

  it('draws a challenge by name, and the group’s once the poster withdrew', async () => {
    const byKuba = deckCard({
      type: 'CHALLENGE',
      challenger: { player_id: KUBA().player_id, name: 'Kuba Wiśniewski' },
      in_count: 1,
      sides: { yours: [youTile(), EWA()], theirs: [KUBA({ is_in: true }), ANIA()] },
    });
    const byTheGroup = deckCard({ type: 'CHALLENGE', challenger: null });
    await openGames(groupDeck({ cards: [byKuba, byTheGroup] }));

    expect(
      await screen.findByRole('header', { name: 'Kuba Wiśniewski challenged you' }),
    ).toBeTruthy();
    expect(screen.getByText('The group challenged you', HIDDEN_TOO)).toBeTruthy();
  });

  it('draws a rescue’s ribbon, its Booked court and a price on the stamp', async () => {
    await openGames(groupDeck({ cards: [deckCard({ type: 'SEAT_OPEN' })] }));

    expect(await screen.findByRole('header', { name: 'Seat open · court booked' })).toBeTruthy();
    expect(screen.getByLabelText('Booked, 32 zł, Saturday 16:00 · Bonarka Arena')).toBeTruthy();
    expect(screen.getByText('I’m in · 32 zł', HIDDEN_TOO)).toBeTruthy();
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

    // The card behind is drawn first — the stage paints deepest first — so each is found by its
    // words rather than by its place.
    expect(await screen.findAllByTestId('game-countdown', HIDDEN_TOO)).toHaveLength(2);
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

    expect(await screen.findByLabelText('Kuba Wiśniewski, level 2,80')).toBeTruthy();
    expect(screen.queryByText(/ vs /, HIDDEN_TOO)).toBeNull();
  });

  it('opens a player’s record from their tile', async () => {
    transport.on('GET', `/api/v1/players/${KAROL().player_id}/record`, () => json(karolsRecord()));
    await openGames(
      groupDeck({
        cards: [deckCard({ sides: { yours: [youTile(), KAROL()], theirs: [ANIA(), EWA()] } })],
      }),
    );

    fireEvent.press(await screen.findByLabelText('Karol Tomaszewski, level 2,75'));

    expect(await screen.findByText(RECORD_TITLE)).toBeTruthy();
    expect(transport.requestsTo('GET', `/api/v1/players/${KAROL().player_id}/record`)).toHaveLength(
      1,
    );
  });

  /** Q90: the cards behind fade as well as shrink, and they are real cards, never placeholders. */
  it('draws the next two cards behind the top one, and no more', async () => {
    const cards = [deckCard(), deckCard(), deckCard(), deckCard()];
    await openGames(groupDeck({ cards }));

    await screen.findByTestId(`game-card-${cards[0]!.proposal_id}`);
    expect(screen.getByTestId(`game-card-${cards[1]!.proposal_id}`, HIDDEN_TOO)).toBeTruthy();
    expect(screen.getByTestId(`game-card-${cards[2]!.proposal_id}`, HIDDEN_TOO)).toBeTruthy();
    expect(screen.queryByTestId(`game-card-${cards[3]!.proposal_id}`, HIDDEN_TOO)).toBeNull();
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
    expect(await screen.findByLabelText('Zofia Bielecka, level 2,69')).toBeTruthy();
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

  it('puts the card back and says why when a yes needs a saved way to pay', async () => {
    const first = deckCard({ sides: { yours: [youTile(), KAROL()], theirs: [ANIA(), EWA()] } });
    transport.on('POST', yesPath(first.proposal_id), () =>
      errorResponse(409, 'payment_method_required'),
    );
    await openGames(groupDeck({ cards: [first] }));
    await screen.findByTestId(`game-card-${first.proposal_id}`);

    fireEvent.press(screen.getByRole('button', { name: COPY.yes }));
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));

    await waitFor(() => expect(toasts()).toEqual([[COPY.refused.payment_method_required, 'bad']]));
    expect(await screen.findByTestId(`game-card-${first.proposal_id}`)).toBeTruthy();
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

  it('says the live-yes cap with its count and sport', async () => {
    const first = deckCard();
    transport.on('POST', yesPath(first.proposal_id), () =>
      json(
        {
          code: 'live_yeses_exhausted',
          message: 'cap',
          trace_id: 'trace-test',
          details: { cap: 10, sport: 'PADEL' },
        },
        409,
      ),
    );
    await openGames(groupDeck({ cards: [first] }));
    await screen.findByTestId(`game-card-${first.proposal_id}`);

    fireEvent.press(screen.getByRole('button', { name: COPY.yes }));
    act(() => jest.advanceTimersByTime(PAST_THE_FLIGHT));

    await waitFor(() =>
      expect(toasts()).toEqual([['You already have 10 live yeses in padel.', 'bad']]),
    );
  });
});

describe('the game’s details', () => {
  const card = () =>
    deckCard({
      in_count: 1,
      sides: { yours: [youTile(), KAROL({ is_in: true })], theirs: [ANIA(), EWA()] },
    });

  async function openDetails(shown = card()) {
    let dealt = [shown];
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

  it('opens from the i: the status, who is In, the club, the book-by, the overlap and what a yes means', async () => {
    await openDetails();

    expect(await screen.findByText('Filling · 1 of 4 in')).toBeTruthy();
    expect(screen.getByLabelText('Karol Tomaszewski, level 2,75, In')).toBeTruthy();
    expect(screen.getByLabelText('Where, Bonarka Arena')).toBeTruthy();
    expect(screen.getByLabelText('Day, Saturday, 3 Oct')).toBeTruthy();
    expect(screen.getByLabelText('Time, 16:00, until 17:00')).toBeTruthy();
    expect(
      screen.getByLabelText('Your share, 32 zł, if it fills · book by Fri 10:00'),
    ).toBeTruthy();
    expect(screen.getByTestId('overlap-grid')).toBeTruthy();
    expect(screen.getByText(COPY.game.whatAYesMeans)).toBeTruthy();
    expect(screen.getByText('Karol Tomaszewski, Ania Kowalska, Ewa Majewska')).toBeTruthy();
  });

  it('opens from a press on the card too', async () => {
    const shown = card();
    await openGames(groupDeck({ cards: [shown] }));

    fireEvent.press(await screen.findByTestId(`game-card-${shown.proposal_id}`));

    await waitFor(() =>
      expect(screen).toHavePathname(`/play/group/${CREW.id}/game/${shown.proposal_id}`),
    );
  });

  it('says yes in place, then offers Withdraw, which puts the answers back', async () => {
    const shown = await openDetails();

    fireEvent.press(await screen.findByRole('button', { name: COPY.yes }));

    expect(await screen.findByRole('button', { name: COPY.game.withdraw })).toBeTruthy();
    expect(screen.getByText('Filling · 2 of 4 in')).toBeTruthy();
    expect(transport.requestsTo('POST', yesPath(shown.proposal_id))).toHaveLength(1);

    fireEvent.press(screen.getByRole('button', { name: COPY.game.withdraw }));

    expect(await screen.findByRole('button', { name: COPY.yes })).toBeTruthy();
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
