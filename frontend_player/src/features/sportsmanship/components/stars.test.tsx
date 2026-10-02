/**
 * **The card, walked the way a player walks it**: the real route tree, the real shell, and only
 * `fetch` faked.
 *
 * The ticket's acceptance criteria are assertions in this file and opinions nowhere else — the
 * card is drawn only for the courts the server names, everybody else on that court is on it
 * (partner included), any of them may be left blank, submitting with everybody blank closes it
 * too, an answered card is gone and cannot be answered again, and the card carries the line
 * saying a low answer will not stop you being matched. Two of them are checked here **as
 * absences**: the window — no card before the day after and none after seven days — is the
 * server's list and nothing on this side re-derives it, and ignoring a card costs nothing, so
 * there is nothing anywhere that counts what a player has not answered.
 *
 * **Every walk opens a game**, because the card is drawn at the end of the **result screen**
 * rather than above the games list on Now. That is the one structural thing this suite says
 * about where the card lives, and it says it twice: every test reaches the card through a row,
 * and one asserts that the Home tab does not so much as **ask** for the list any more.
 *
 * It asserts against the **copy deck** rather than against strings, because the wording is the
 * deck's to change and the rules are not.
 */

import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';
import { router } from 'expo-router';
import { onlineManager } from '@tanstack/react-query';

import { AppError, offlineMessage } from '@/shared/errors';
import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  GAMES_PATH,
  GATE_USER,
  SPORTSMANSHIP_PATH,
  launchSignedIn,
  stubGames,
  stubGate,
  stubSportsmanship,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import type { StarSubject } from '../domain/card';

import {
  CLEAR_HINT,
  LEAVE_ANYBODY_BLANK,
  STARS_HEADING,
  matchingLine,
  starName,
  starsErrorMessage,
  submitLabel,
  submitName,
} from './starsPresentation';

const GAME = '8f14e45f-ceea-467a-9dd1-4bd9c39d4a58';
const SINGLES_GAME = '1a2b3c4d-0000-4000-8000-000000000009';
const ANSWER_PATH = `${SPORTSMANSHIP_PATH}/${GAME}`;

const ME = GATE_USER.id;
const PARTNER = 'aaaaaaaa-0000-4000-8000-000000000001';
const OPPONENT = 'bbbbbbbb-0000-4000-8000-000000000002';
const THEIR_PARTNER = 'cccccccc-0000-4000-8000-000000000003';

const READ_AT = '2026-09-05T09:00:00Z';

/** A settled doubles padel game: me and my partner on A, two opponents on B. */
const DOUBLES: Wire['GameSchema'] = {
  game_id: GAME,
  challenge_id: 'dddddddd-0000-4000-8000-000000000004',
  sport: 'PADEL',
  kind: 'COUNTED',
  standing: 'CONFIRMED',
  planned_at: '2026-09-01T09:00:00Z',
  played_at: '2026-09-02T20:00:00Z',
  score: { sets: [{ a: 6, b: 4 }] },
  outcome: 'WIN',
  seats: [
    { side: 'A', player_id: ME, name: 'ada' },
    { side: 'A', player_id: PARTNER, name: 'kasia_w' },
    { side: 'B', player_id: OPPONENT, name: 'tomek.p' },
    { side: 'B', player_id: THEIR_PARTNER, name: 'marekb' },
  ],
  proposals: [],
  no_shows: [],
};

/** A settled singles squash game, for the second card and the singles sentence. */
const SINGLES: Wire['GameSchema'] = {
  ...DOUBLES,
  game_id: SINGLES_GAME,
  sport: 'SQUASH',
  seats: [
    { side: 'A', player_id: ME, name: 'ada' },
    { side: 'B', player_id: OPPONENT, name: 'tomek.p' },
  ],
};

/** The card the server draws for that court — everybody else, in the line-up's own order. */
const DOUBLES_CARD: Wire['OpenCardSchema'] = {
  game_id: GAME,
  players: [PARTNER, OPPONENT, THEIR_PARTNER],
};

const SINGLES_CARD: Wire['OpenCardSchema'] = {
  game_id: SINGLES_GAME,
  players: [OPPONENT],
};

const KASIA: StarSubject = { playerId: PARTNER, name: { kind: 'player', name: 'kasia_w' } };
const TOMEK: StarSubject = { playerId: OPPONENT, name: { kind: 'player', name: 'tomek.p' } };
const MAREK: StarSubject = {
  playerId: THEIR_PARTNER,
  name: { kind: 'player', name: 'marekb' },
};

const EVERYBODY = [KASIA, TOMEK, MAREK];

/** One rating, because the entry gate sends an unrated player to onboarding rather than Now. */
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
});

afterEach(async () => {
  // One test takes the connection away, and `onlineManager` is a singleton.
  onlineManager.setOnline(true);
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/**
 * Land in the app with these evenings and these cards waiting, and **open one game** — the
 * card is drawn at the end of the result screen, so getting to it is a tap on a row rather
 * than an arrival.
 *
 * `opening` defaults to the first game, and is passed only where the point is that this
 * screen draws *its own* card and not somebody else's.
 *
 * **The push is direct, because there is no longer a door.** The games list came off the Now
 * tab with the rest of that placeholder's furniture, so nothing a player can tap reaches this
 * route today — which is what the Now assertion below is about, and why every other test here
 * arrives by pushing.
 */
async function land(
  games: readonly Wire['GameSchema'][],
  cards: readonly Wire['OpenCardSchema'][],
  opening: Wire['GameSchema'] | undefined = games[0],
) {
  stubGames(transport, games, READ_AT);
  stubSportsmanship(transport, cards);
  await launchSignedIn();

  if (opening === undefined) return;

  act(() => {
    router.push({ pathname: '/games/[gameId]', params: { gameId: opening.game_id } });
  });
  await waitFor(() => expect(screen).toHavePathname(`/games/${opening.game_id}`));
}

/** Press one star on one person's row. */
function give(stars: number, subject: StarSubject) {
  fireEvent.press(screen.getByLabelText(starName(stars, subject)));
}

const answers = () => transport.requestsTo('POST', ANSWER_PATH).map((request) => request.body);

/** Every ask for the open-card list. Its **absence** is what the Home tab is asserted on. */
const cardReads = () => transport.requestsTo('GET', SPORTSMANSHIP_PATH);

describe('the card at the end of the result screen', () => {
  it('asks about everybody else on the court, partner included', async () => {
    await land([DOUBLES], [DOUBLES_CARD]);

    await screen.findByText(STARS_HEADING);

    // Three people, and the partner is one of them: *the person who saw you play closest was
    // on your own side of the net.*
    expect(screen.getByLabelText(starName(3, KASIA))).toBeTruthy();
    expect(screen.getByLabelText(starName(3, TOMEK))).toBeTruthy();
    expect(screen.getByLabelText(starName(3, MAREK))).toBeTruthy();
  });

  it('never asks about you, because you rate everybody else and nobody else', async () => {
    await land([DOUBLES], [DOUBLES_CARD]);
    await screen.findByText(STARS_HEADING);

    expect(screen.queryByLabelText(/for ada$/)).toBeNull();
  });

  it('offers five whole stars and no zero', async () => {
    await land([SINGLES], [SINGLES_CARD]);
    await screen.findByText(STARS_HEADING);

    [1, 2, 3, 4, 5].forEach((value) => {
      expect(screen.getByLabelText(starName(value, TOMEK))).toBeTruthy();
    });
    expect(screen.queryByLabelText(/^0 stars/)).toBeNull();
  });

  it('says a low answer will not stop you being matched', async () => {
    await land([SINGLES], [SINGLES_CARD]);

    // Pass and Block already exist and both mean something specific — a control that silently
    // did two things is the one this sentence exists to prevent.
    expect(await screen.findByText(matchingLine([TOMEK]))).toBeTruthy();
  });

  it('says anybody may be left blank, and that the press is final, before the press', async () => {
    await land([SINGLES], [SINGLES_CARD]);

    expect(await screen.findByText(LEAVE_ANYBODY_BLANK)).toBeTruthy();
  });

  /**
   * The window is the server's: a game not yet a day old, one whose week has run out and one
   * already answered are all simply not on the list. This client draws what it was handed, so
   * a settled game with no card open draws none — and that is the whole of how *not before the
   * day after* and *gone after seven days* are honoured here.
   */
  it('draws no card for a settled game the server did not name', async () => {
    await land([DOUBLES], []);

    // The read is what is waited on rather than a sentence: the point is that the list was
    // asked and answered with nothing, not that some other element happened to render first.
    await waitFor(() => expect(cardReads()).toHaveLength(1));
    expect(screen.queryByText(STARS_HEADING)).toBeNull();
  });

  /**
   * The list read answers about **every** court still waiting, and this screen is about one.
   * Drawing another evening's card here would put the wrong people under the wrong score,
   * which is the one way the join can be wrong and still render something.
   */
  it('draws this evening’s card and never another one’s', async () => {
    await land([DOUBLES, SINGLES], [SINGLES_CARD, DOUBLES_CARD], SINGLES);
    await screen.findByText(STARS_HEADING);

    const drawn = screen
      .getAllByLabelText(/^Send /)
      .map((one) => String(one.props.accessibilityLabel));

    expect(drawn).toEqual([submitName(submitLabel(0), 'Squash', [TOMEK])]);
  });

  /**
   * **Now no longer carries it**, which is the cost of moving the card to the evening it is
   * about: the rail draws the games and nothing above them, and a player who never re-opens a
   * settled game never sees it. Asserted rather than left to a docstring, because a card
   * quietly reappearing above the rail is exactly the regression this move makes easy.
   */
  it('is nowhere on the Home tab, which no longer surfaces it at all', async () => {
    stubGames(transport, [DOUBLES], READ_AT);
    stubSportsmanship(transport, [DOUBLES_CARD]);
    await launchSignedIn();

    // Now is the rail — a heading with a count and a card per game — and the card asking about
    // an evening is not among the things it draws.
    await screen.findByText(/^Your games · \d+$/);
    expect(screen.queryByText(STARS_HEADING)).toBeNull();
    // **Not even asked for.** The heading being absent would also be true of a read that
    // happened and returned nothing; what this asserts is that the tab has stopped carrying
    // the question at all, which is the half a stray composition would put back.
    expect(cardReads()).toHaveLength(0);
  });
});

describe('answering it', () => {
  it('sends the stars given and leaves everybody else out', async () => {
    await land([DOUBLES], [DOUBLES_CARD]);
    await screen.findByText(STARS_HEADING);

    give(5, KASIA);
    give(3, MAREK);

    transport.on('POST', ANSWER_PATH, () => noContent());
    fireEvent.press(screen.getByLabelText(submitName(submitLabel(2), 'Padel', EVERYBODY)));

    // tomek.p is not in the body at all — a blank is spelled by absence and nothing else.
    await waitFor(() =>
      expect(answers()).toEqual([
        {
          ratings: [
            { player_id: PARTNER, stars: 5 },
            { player_id: THEIR_PARTNER, stars: 3 },
          ],
        },
      ]),
    );
  });

  /**
   * *An explicit "I am not rating anyone" is an answer.* So the control names that act rather
   * than saying *Send* over a body with nothing in it, and it closes the card like any other.
   */
  it('closes the card with an empty answer when nobody was given any', async () => {
    await land([SINGLES], [SINGLES_CARD]);
    await screen.findByText(STARS_HEADING);

    transport.on('POST', `${SPORTSMANSHIP_PATH}/${SINGLES_GAME}`, () => noContent());
    fireEvent.press(screen.getByLabelText(submitName(submitLabel(0), 'Squash', [TOMEK])));

    await waitFor(() =>
      expect(
        transport
          .requestsTo('POST', `${SPORTSMANSHIP_PATH}/${SINGLES_GAME}`)
          .map((one) => one.body),
      ).toEqual([{ ratings: [] }]),
    );
  });

  it('clears a row when the star that already stands is pressed again', async () => {
    await land([SINGLES], [SINGLES_CARD]);
    await screen.findByText(STARS_HEADING);

    give(4, TOMEK);
    expect(screen.getByLabelText(starName(4, TOMEK)).props.accessibilityHint).toBe(CLEAR_HINT);

    give(4, TOMEK);

    // Back to blank, which is what the control says it is about to make: nobody rated.
    expect(screen.getByLabelText(submitName(submitLabel(0), 'Squash', [TOMEK]))).toBeTruthy();
  });

  it('is gone once it is answered, and cannot be answered again', async () => {
    await land([DOUBLES], [DOUBLES_CARD]);
    await screen.findByText(STARS_HEADING);

    give(4, TOMEK);
    transport.on('POST', ANSWER_PATH, () => noContent());
    // The card closed for ever when it was answered, so the re-read no longer carries it.
    transport.on('GET', SPORTSMANSHIP_PATH, () => json<Wire['OpenCardsResponse']>({ cards: [] }));

    fireEvent.press(screen.getByLabelText(submitName(submitLabel(1), 'Padel', EVERYBODY)));

    await waitFor(() => expect(screen.queryByText(STARS_HEADING)).toBeNull());
    // The evening itself is untouched — the screen the card was drawn on is still the screen
    // this player is on. A card is a question **about** a game and never the game, so closing
    // one takes nothing away and moves nobody.
    expect(screen).toHavePathname(`/games/${GAME}`);
  });

  it('says the card is closed when it was already answered, and does not pretend otherwise', async () => {
    await land([DOUBLES], [DOUBLES_CARD]);
    await screen.findByText(STARS_HEADING);

    transport.on('POST', ANSWER_PATH, () => errorResponse(409, 'you_have_already_rated_this_game'));
    fireEvent.press(screen.getByLabelText(submitName(submitLabel(0), 'Padel', EVERYBODY)));

    const refusal = new AppError('conflict', 'business-conflict', 'test failure', {
      code: 'you_have_already_rated_this_game',
    });

    expect(await screen.findByText(starsErrorMessage(refusal))).toBeTruthy();
  });

  it('keeps the card and the draft when the send is refused', async () => {
    await land([DOUBLES], [DOUBLES_CARD]);
    await screen.findByText(STARS_HEADING);

    give(2, KASIA);
    transport.on('POST', ANSWER_PATH, () => errorResponse(403, 'this_game_is_not_yours_to_rate'));
    fireEvent.press(screen.getByLabelText(submitName(submitLabel(1), 'Padel', EVERYBODY)));

    // A retry belongs to the act that failed, and it cannot be if what was typed is gone.
    await waitFor(() =>
      expect(screen.getByLabelText(submitName(submitLabel(1), 'Padel', EVERYBODY))).toBeTruthy(),
    );
  });

  /**
   * **The one press that must not be able to happen twice.** There is no `Idempotency-Key`
   * here and there must not be — one answer per card is a rule that does not expire and a key
   * does — so the closed button is the whole of what stands between a paused send and a second
   * one. Queued twice, the first would close the card and the second would come back
   * `you_have_already_rated_this_game`, telling the player whose answer landed that they had
   * already answered.
   */
  it('closes the control while the send is paused, so nothing is queued twice', async () => {
    await land([SINGLES], [SINGLES_CARD]);
    await screen.findByText(STARS_HEADING);

    give(4, TOMEK);
    const path = `${SPORTSMANSHIP_PATH}/${SINGLES_GAME}`;
    transport.on('POST', path, () => noContent());

    act(() => onlineManager.setOnline(false));
    fireEvent.press(screen.getByLabelText(submitName(submitLabel(1), 'Squash', [TOMEK])));

    // It pauses rather than failing — the seven days run from the game and not from the tap —
    // and the sentence beside the closed control is the one that promises it resumes.
    expect(await screen.findByText(offlineMessage('resumes'))).toBeTruthy();

    const button = screen.getByLabelText(submitName(submitLabel(1), 'Squash', [TOMEK]));
    expect(button.props.accessibilityState.disabled).toBe(true);

    fireEvent.press(button);
    act(() => onlineManager.setOnline(true));

    // **One request, not two.** Asserting nothing was sent while offline would have passed
    // whether or not the button was closed — a paused mutation sends nothing either way — so
    // the connection comes back and the count is taken on the other side of it.
    await waitFor(() => expect(transport.requestsTo('POST', path)).toHaveLength(1));
  });
});

describe('what ignoring it costs', () => {
  /**
   * Nothing, anywhere. There is no strand for rating, no penalty and nothing recorded about a
   * card that expired — so there is no count of what is outstanding, no badge and nothing that
   * asks twice. The read is one `GET` and the only write is the one a press makes.
   */
  it('never writes anything a player did not press', async () => {
    await land([DOUBLES, SINGLES], [DOUBLES_CARD, SINGLES_CARD]);
    await screen.findByText(STARS_HEADING);

    give(5, KASIA);

    expect(transport.requests.filter((one) => one.method === 'POST')).toEqual([]);
    expect(transport.requestsTo('GET', SPORTSMANSHIP_PATH)).toHaveLength(1);
  });

  it('counts nothing at the player and thanks nobody', async () => {
    await land([DOUBLES], [DOUBLES_CARD]);
    await screen.findByText(STARS_HEADING);

    expect(screen.queryByText(/of 3/)).toBeNull();
    expect(screen.queryByText(/outstanding/i)).toBeNull();
  });
});

describe('the join against the games list', () => {
  it('draws nothing for a card whose game this build could not read', async () => {
    // The games mapper refuses a game whose sport or court it cannot draw, whole — so the card
    // over it has nobody to name and is dropped rather than drawn with ids in it.
    transport.on('GET', GAMES_PATH, () =>
      json<Wire['GameListResponse']>({
        read_at: READ_AT,
        games: [{ ...DOUBLES, sport: 'PICKLEBALL' as Wire['GameSchema']['sport'] }],
      }),
    );
    stubSportsmanship(transport, [DOUBLES_CARD]);
    await launchSignedIn();

    await screen.findByText(/^Your games · \d+$/);
    expect(screen.queryByText(STARS_HEADING)).toBeNull();
  });
});
