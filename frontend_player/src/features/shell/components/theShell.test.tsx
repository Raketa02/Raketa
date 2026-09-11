/**
 * The shell, walked the way a player walks it: through the real route tree, with the real
 * bar, and only `fetch` faked.
 *
 * **The one rule here that cannot be seen is the one this suite exists for.** A shell built
 * out of `<Tabs>` passes every visible assertion below and still fails *back goes where I
 * came from* — the tab bar looks right, every screen is reachable, nothing throws, and a
 * player who left the deck and came back lands on the deck. So the assertions are about the
 * **stack**: what is underneath, and whether there is anything underneath at all.
 */

import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { authKeys } from '@/features/auth/types';
import { onboardingKeys } from '@/features/onboarding/types';
import { FIND_A_GAME_TITLE, modeControlLabel, usePlaySession } from '@/features/play/types';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  CHALLENGES_PATH,
  GATE_USER,
  launchSignedIn,
  stubChallenges,
  stubConversation,
  stubConversations,
  stubEntries,
  stubGate,
  stubProfileOptions,
  stubInterest,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import { installTransport, json, type Transport, type Wire } from '@/test-support/transport';
import { declarationOptionLabel } from '@/shared/vocabulary/playIntentPresentation';

import { enterPlay } from './shellNavigation';
import { CHATS_COPY, NOW_COPY, PLACEHOLDER_COPY } from './shellCopy';

/** One rating and a committed profile: the gate's fourth answer is *the app*. */
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

let transport: Transport;

/**
 * *The player is on Find a game*, asserted on the **header** rather than on the words.
 *
 * The screen's title and Play's segment now say the same thing — the segment is a view
 * switch and the view it switches to is this screen — so the string alone matches twice.
 * The header is the one of the two that means *this is where you are*.
 */
const onFindAGame = () => screen.findByRole('header', { name: FIND_A_GAME_TITLE });

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [RATING], hasPlayerProfile: true });
  // ⚡Play is a screen now, and it reads three routes. Stubbed here rather than in the two
  // tests that press the tab, because an unstubbed route throws at the socket and the
  // failure would name `fetch` rather than the screen.
  stubProfileSurface(transport);
  stubInterest(transport);
  stubProfileOptions(transport);
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

/** A player standing on the tab the entry gate lands them on. */
async function launchIntoTheApp() {
  await launchSignedIn();
  expect(await screen.findByText(NOW_COPY.empty.line)).toBeTruthy();
}

/** Press one of the five columns by the name the bar gives it. */
function pressTab(label: string) {
  fireEvent.press(screen.getByLabelText(label));
}

describe('what a player lands on', () => {
  it('opens on Now, with the bar under it', async () => {
    await launchIntoTheApp();

    expect(screen).toHavePathname('/');
    expect(screen.getAllByRole('tab').map((tab) => tab.props.accessibilityLabel)).toEqual([
      'Now',
      'Around',
      'Play',
      'Chats',
      'You',
    ]);
  });

  it('lights the tab the player is on, and only that one', async () => {
    await launchIntoTheApp();

    const selected = () =>
      screen
        .getAllByRole('tab')
        .filter((tab) => tab.props.accessibilityState?.selected === true)
        .map((tab) => tab.props.accessibilityLabel);

    expect(selected()).toEqual(['Now']);

    pressTab('Chats');
    await waitFor(() => expect(selected()).toEqual(['Chats']));
  });
});

describe('the placeholders', () => {
  it.each([
    ['Around', PLACEHOLDER_COPY.around],
    ['You', PLACEHOLDER_COPY.you],
  ])('says what belongs on %s rather than apologising', async (label, copy) => {
    await launchIntoTheApp();

    pressTab(label);

    expect(await screen.findByText(copy.line)).toBeTruthy();
  });

  it('never tells the player nothing is happening', async () => {
    // Now is where a send lands, so a placeholder asserting emptiness would be lying one tap
    // after a challenge went out. What the lines *say* is `shellCopy.test.ts`'s; this is the
    // rendered half — the tab a launch actually opens on, with the sentence on it.
    await launchIntoTheApp();

    expect(screen.queryByText(/nothing is happening/i)).toBeNull();
  });

  it('keeps the way out of a session on You, where it belongs', async () => {
    // The account panel outlived the screen it used to be: sign-out is the only way back
    // to the beginning, and the tab whose citation is *your profile* is where it goes.
    await launchIntoTheApp();

    pressTab('You');

    expect(await screen.findByText(PLACEHOLDER_COPY.you.line)).toBeTruthy();
    expect(await screen.findByText(`${GATE_USER.nickname} · ${GATE_USER.email}`)).toBeTruthy();
    expect(screen.getByLabelText('Sign out')).toBeTruthy();
  });

  it('lets a player out of the session from inside the shell', async () => {
    // The one flow the shell moved: sign-out used to be the screen a player landed on, and
    // is now three screens inside a stack the guard has to unwind from.
    transport.on('POST', '/api/v1/auth/logout', () => json({ message: 'Logged out' }));
    await launchIntoTheApp();

    pressTab('You');
    fireEvent.press(await screen.findByLabelText('Sign out'));

    await waitFor(() => expect(screen).toHavePathname('/sign-in'));
  });
});

describe('⚡Play', () => {
  it('always opens Find a game, from whichever tab the player was on', async () => {
    await launchIntoTheApp();

    pressTab('Around');
    await waitFor(() => expect(screen).toHavePathname('/around'));

    pressTab('Play');

    expect(await onFindAGame()).toBeTruthy();
    expect(screen).toHavePathname('/play');
  });

  it('stays lit for the screen it opened', async () => {
    await launchIntoTheApp();

    pressTab('Play');

    await waitFor(() => expect(screen).toHavePathname('/play'));
    const play = screen.getAllByRole('tab')[2];
    expect(play?.props.accessibilityState?.selected).toBe(true);
  });

  it('leaves Now underneath, so back leaves Play entirely', async () => {
    await launchIntoTheApp();

    pressTab('Play');
    await waitFor(() => expect(screen).toHavePathname('/play'));

    // The platform's own back, which is what the rule is about: Find a game does not refuse
    // to be the last screen, it has Now underneath it.
    act(() => router.back());

    expect(await screen.findByText(NOW_COPY.empty.line)).toBeTruthy();
    expect(screen).toHavePathname('/');
  });

  it('is entered the same way from inside the tab as from the bar', async () => {
    // The reset's second caller. #268's *Find a game* segment re-enters the tab from inside
    // it, and re-entering has to mean the arrangement arriving means — otherwise a player on
    // the deck who taps it goes *back* rather than to the start.
    await launchIntoTheApp();
    pressTab('Chats');
    await waitFor(() => expect(screen).toHavePathname('/chats'));

    act(() => enterPlay());

    expect(await onFindAGame()).toBeTruthy();
    expect(screen).toHavePathname('/play');
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/'));
  });

  it('re-enters rather than going back when it is pressed from inside Play', async () => {
    await launchIntoTheApp();

    pressTab('Play');
    await waitFor(() => expect(screen).toHavePathname('/play'));

    pressTab('Play');

    await waitFor(() => expect(screen).toHavePathname('/play'));
    // And the stack has not grown a second Find a game to walk back through.
    expect(router.canGoBack()).toBe(true);
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(router.canGoBack()).toBe(false);
  });
});

describe('a Play session ends exactly when the shell lays a stack down', () => {
  /** A player mid-build: a week they have edited, and two people on the court. */
  function halfwayThroughBuildingOne() {
    const session = usePlaySession.getState();
    session.enter([{ day: 2, part: 'evening' }]);
    session.toggleWeekCell({ day: 6, part: 'morning' });
    session.seat('search-1', 'player-a');
    session.seat('search-1', 'player-b');
  }

  it('clears the working copy and the line-up when the player leaves for another tab', async () => {
    // The definition, walked rather than called: nothing in Play tidies up after itself, and
    // the only thing that clears a session is arriving somewhere.
    await launchIntoTheApp();
    pressTab('Play');
    await waitFor(() => expect(screen).toHavePathname('/play'));
    halfwayThroughBuildingOne();

    pressTab('Chats');

    await waitFor(() => expect(screen).toHavePathname('/chats'));
    expect(usePlaySession.getState().week).toBeUndefined();
    expect(usePlaySession.getState().lineup).toBeUndefined();
  });

  it('clears it on the way back in too, so ⚡ opens on a week seeded from the profile', async () => {
    // AC-2 lands a returning player on Find a game. A line-up that survived would sit
    // invisible behind a screen whose week no longer matches the search it was built on.
    //
    // **Read on a player who actually left**, which is what *returning* means. This walked
    // out and back through one press of Play on Find a game until 2026-09-10 — and that
    // press is not a return, it is a player who never went anywhere (see below).
    await launchIntoTheApp();
    pressTab('Play');
    await waitFor(() => expect(screen).toHavePathname('/play'));
    halfwayThroughBuildingOne();
    pressTab('Chats');
    await waitFor(() => expect(screen).toHavePathname('/chats'));
    halfwayThroughBuildingOne();

    pressTab('Play');

    await waitFor(() => expect(screen).toHavePathname('/play'));
    expect(usePlaySession.getState().lineup).toBeUndefined();
  });

  /**
   * **A tab you are already at the start of is not a place to be sent to.**
   *
   * Every press of the bar laid the stack down again, so a player tapping Play on Find a game
   * got the screen rebuilt underneath them: the session ended, the working week went back to
   * the profile's, and whatever they had ticked was gone — a reload with no cause, on the
   * gesture people press twice when a screen is slow.
   *
   * The rule the reset is for is *pressing a tab goes to that tab's start*, and a player
   * already standing on it is already there. Nothing about leaving changes: the press still
   * resets from anywhere else in Play, which is the test below this one.
   */
  it('does nothing at all when the tab pressed is the one already on screen', async () => {
    await launchIntoTheApp();
    pressTab('Play');
    await waitFor(() => expect(screen).toHavePathname('/play'));
    halfwayThroughBuildingOne();

    pressTab('Play');

    await waitFor(() => expect(screen).toHavePathname('/play'));
    // The session the player is in the middle of is still the session they are in.
    expect(usePlaySession.getState().week).toEqual([
      { day: 2, part: 'evening' },
      { day: 6, part: 'morning' },
    ]);
    expect(usePlaySession.getState().lineup?.seats).toEqual(['player-a', 'player-b']);
  });

  it('still lays the stack down again from anywhere else inside the tab', async () => {
    await launchIntoTheApp();
    pressTab('Play');
    await waitFor(() => expect(screen).toHavePathname('/play'));
    halfwayThroughBuildingOne();
    act(() => router.push('/play/deck'));
    await waitFor(() => expect(screen).toHavePathname('/play/deck'));

    pressTab('Play');

    await waitFor(() => expect(screen).toHavePathname('/play'));
    expect(usePlaySession.getState().lineup).toBeUndefined();
  });
});

describe('the shell keeps no per-tab history', () => {
  it('leaves nothing behind a flanking tab', async () => {
    await launchIntoTheApp();

    pressTab('Around');

    await waitFor(() => expect(screen).toHavePathname('/around'));
    // Not `[Now, Around]`: switching tabs replaces, so there is no cross-tab back to walk.
    expect(router.canGoBack()).toBe(false);
  });

  it('throws away Play depth when the player leaves, and does not restore it', async () => {
    await launchIntoTheApp();

    pressTab('Play');
    await waitFor(() => expect(screen).toHavePathname('/play'));

    pressTab('Chats');
    await waitFor(() => expect(screen).toHavePathname('/chats'));
    // Play's two screens went with it. This is the assertion `<Tabs>` fails silently.
    expect(router.canGoBack()).toBe(false);

    pressTab('Play');

    await waitFor(() => expect(screen).toHavePathname('/play'));
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/'));
  });
});

/**
 * **The shell outlives the entry gate re-reading the player, and a shell built from nothing opens
 * on Now.** Two facts, and the first press after a cold start on a device was where they were both
 * found false at once: bootstrap **seeds** the player into the cache, so the gate's own read of
 * them never fetched at mount; thirty seconds later that seed is stale, and the first screen to
 * mount `useCurrentUser()` refetches it — which the gate took for *a read this mount is in the
 * middle of replacing* and answered `pending`, rendering nothing and tearing the authenticated
 * tree down for the length of the round trip. The tree came back with a fresh stack, and a fresh
 * stack opens on the **first route name it holds**, which was `play/index` — so every first press
 * landed on Find a game with ⚡Play lit, whichever column had been pressed.
 *
 * `launchSignedIn` never seeded the player, which is why every suite here stayed green while a
 * device did that on every launch. The first test puts the cache the way bootstrap leaves it.
 */
describe('the shell survives the gate re-reading the player', () => {
  /** The cache as `restoreSessionStep` leaves it: the validated player, fresh, unfetched here. */
  function seedThePlayer() {
    queryClient.setQueryData(authKeys.currentUser(), {
      id: GATE_USER.id,
      email: GATE_USER.email,
      nickname: GATE_USER.nickname,
      hasPlayerProfile: true,
    });
  }

  it('stays on the tab the player pressed while a screen refetches the seeded player', async () => {
    seedThePlayer();
    await launchIntoTheApp();
    // The seed was honoured: the gate answered from it and asked the server nothing.
    expect(transport.requestsTo('GET', '/api/v1/users/me')).toHaveLength(0);

    // The seed goes stale — the app's `staleTime` is thirty seconds — and the next screen to
    // read the player will send for a fresh copy. That refetch is a background one: the gate
    // already has its answer, and it is not what this mount set out to replace.
    // Advanced outside `act`: inside it, this harness runs every pending timer — Query's
    // five-minute collection among them — rather than the thirty seconds asked for.
    jest.advanceTimersByTime(31_000);
    act(() => {});

    pressTab('Chats');

    await waitFor(() => expect(transport.requestsTo('GET', '/api/v1/users/me')).toHaveLength(1));
    await waitFor(() =>
      expect(queryClient.getQueryState(authKeys.currentUser())?.fetchStatus).toBe('idle'),
    );
    // Let anything the gate might have torn down come back before looking.
    jest.advanceTimersByTime(50);
    act(() => {});

    expect(screen).toHavePathname('/chats');
    expect(await screen.findByRole('header', { name: CHATS_COPY.title })).toBeTruthy();
    expect(screen.queryByRole('header', { name: FIND_A_GAME_TITLE })).toBeNull();
    expect(screen.getAllByRole('tab')).toHaveLength(5);
  });

  it('opens on Now, never on the first route it happens to list, when rebuilt from nothing', async () => {
    // The gate genuinely losing its answer is the one way the tree is rebuilt, and the stack it
    // comes back with holds no history — so what it opens on is the initial route, which has to
    // be the tab the gate lands on rather than whichever screen the shell listed first for its
    // transition. Reset rather than invalidated: an invalidated read still holds its answer.
    //
    // The re-read is **held open**, for the reason the gate's own suite holds its own: a
    // navigator torn down forgets its state one tick later, and on a device the round trip is
    // longer than that tick. Answered at once, the stack would come back rehydrated onto Chats
    // and prove nothing about a stack that holds no history at all.
    await launchIntoTheApp();
    pressTab('Chats');
    await waitFor(() => expect(screen).toHavePathname('/chats'));

    let answerRatings = () => {};
    const held = new Promise<void>((resolve) => {
      answerRatings = resolve;
    });
    transport.on('GET', '/api/v1/ratings', async () => {
      await held;
      return json<Wire['RatingsResponse']>({ ratings: [RATING] });
    });

    act(() => {
      void queryClient.resetQueries({ queryKey: onboardingKeys.ratings() });
    });

    // Query tells its observers on a timer of its own, and the gate answers on the render that
    // follows: nothing, not a route tree — the bar is gone with everything under the gate.
    jest.advanceTimersByTime(10);
    act(() => {});
    expect(screen.queryAllByRole('tab')).toHaveLength(0);
    // One tick later the navigator that was under it has forgotten its state, as it would
    // have on a device long before the answer came back.
    jest.advanceTimersByTime(10);
    act(() => {});

    answerRatings();

    expect(await screen.findByText(NOW_COPY.empty.line)).toBeTruthy();
    expect(screen).toHavePathname('/');
    expect(screen.queryByRole('header', { name: FIND_A_GAME_TITLE })).toBeNull();
    expect(screen.getAllByRole('tab')).toHaveLength(5);
  });
});

/**
 * **Two tabs, and the one rule that spans them** — asserted here because the shell is the one
 * feature allowed to read across that boundary, and neither of the two features it names may
 * import the other.
 *
 * *You* now lists what a player has declared per sport and writes it
 * ([#296](https://github.com/Raketa02/Raketa/issues/296)). It must not move the mode Play
 * opens in: the two values have to be able to disagree, which is what ADR-0094's drift
 * backstop is written for, and a declaration edited on another tab quietly re-seeding the
 * segment would leave it nothing to catch.
 */
describe('what a declaration changed on You does to Play', () => {
  const PADEL_INTENT = '/api/v1/play-intents/PADEL';

  /**
   * Which half of the mode segment is on, whichever it is.
   *
   * The assertion is *unchanged* rather than *competitive*, and it has to be: `playPreferences`
   * is scoped to the **process**, so the mode a suite finds is whatever an earlier test in the
   * same file seeded — and the rule under test is about the value not moving, not about which
   * value it is.
   */
  const selectedMode = () =>
    (['COMPETITIVE', 'FOR_FUN'] as const).find(
      (mode) =>
        screen.getByLabelText(modeControlLabel(mode)).props.accessibilityState?.selected === true,
    );

  it('leaves the mode the segment is on exactly where it was', async () => {
    await launchIntoTheApp();

    pressTab('Play');
    await screen.findByLabelText(modeControlLabel('COMPETITIVE'));
    const before = selectedMode();
    expect(before).toBeDefined();

    // Declare the **other** answer, so a segment re-seeded from the declaration would move.
    const other = before === 'COMPETITIVE' ? 'FOR_FUN' : 'COMPETITIVE';
    transport.on('PUT', PADEL_INTENT, () =>
      json<Wire['PlayIntentDeclarationResponse']>({ sport: 'PADEL', intent: other }),
    );

    pressTab('You');
    fireEvent.press(await screen.findByText('Padel'));
    fireEvent.press(await screen.findByLabelText(declarationOptionLabel(other, 'Padel')));
    await waitFor(() => expect(transport.requestsTo('PUT', PADEL_INTENT)).toHaveLength(1));

    pressTab('Play');
    await screen.findByLabelText(modeControlLabel('COMPETITIVE'));
    expect(selectedMode()).toBe(before);
  });
});

/**
 * **The bar stands down inside a conversation, and nowhere else under Chats.** The composer
 * replaces it there so the keyboard and the stream get the whole screen
 * ([#400](https://github.com/Raketa02/Raketa/issues/400)) — and it is *not rendered* rather than
 * hidden, because the bar is a flex sibling of the navigator and a hidden one would still take its
 * height and the bottom inset. The two neighbours are asserted beside it because a `/chats/*`
 * match is the mistake this shape invites: the inbox the room is pushed over and the challenge
 * screen beside it both keep their bar.
 */
describe('the bar stands down inside a conversation', () => {
  const TOMEK = 'bbbbbbbb-0000-4000-8000-000000000002';
  const ROOM = 'eeeeeeee-0000-4000-8000-000000000005';
  const CHALLENGE = 'aaaaaaaa-0000-4000-8000-000000000001';
  const READ_AT = '2026-09-08T12:00:00Z';

  const MEMBERS: Wire['ConversationMemberSchema'][] = [
    { player_id: GATE_USER.id, nickname: 'me_' },
    { player_id: TOMEK, nickname: 'tomek.p' },
  ];

  /** One squash challenge addressed to you, with its detail — enough for the screen to draw. */
  const CHALLENGE_ROW: Wire['ChallengeSchema'] = {
    challenge_id: CHALLENGE,
    sport: 'SQUASH',
    organiser_id: TOMEK,
    standing: 'AWAITING_ANSWERS',
    opened_at: '2026-09-08T08:00:00Z',
    seats: [
      { side: 'A', player_id: TOMEK, answer: 'ACCEPTED', nickname: 'tomek.p' },
      {
        side: 'B',
        player_id: GATE_USER.id,
        answer: null,
        answer_by: '2026-09-09T08:00:00Z',
        nickname: 'me_',
      },
    ],
  };

  const tabs = () => screen.queryAllByRole('tab');

  /** By the start of the name: with a challenge waiting, the column's label carries the count. */
  async function openChats() {
    await launchIntoTheApp();
    fireEvent.press(screen.getByLabelText(/^Chats/));
    await waitFor(() => expect(screen).toHavePathname('/chats'));
  }

  it('draws no bar in the room, and draws it again on the way back out', async () => {
    stubConversations(transport, [
      {
        conversation_id: ROOM,
        challenge_id: CHALLENGE,
        game_id: null,
        sport: 'PADEL',
        members: MEMBERS,
        last_entry: null,
      },
    ]);
    stubConversation(transport, {
      read_at: READ_AT,
      conversation_id: ROOM,
      challenge_id: CHALLENGE,
      game_id: null,
      sport: 'PADEL',
      members: MEMBERS,
      entries: [],
    });
    stubEntries(transport, ROOM);
    await openChats();
    expect(tabs()).toHaveLength(5);

    fireEvent.press(await screen.findByLabelText(/^tomek\.p/));

    await waitFor(() => expect(screen).toHavePathname(`/chats/conversation/${ROOM}`));
    expect(tabs()).toHaveLength(0);

    act(() => router.back());

    await waitFor(() => expect(screen).toHavePathname('/chats'));
    expect(tabs()).toHaveLength(5);
  });

  it('keeps the bar on the challenge screen, which is under the same tab', async () => {
    stubChallenges(transport, [CHALLENGE_ROW], READ_AT);
    transport.on('GET', `${CHALLENGES_PATH}/${CHALLENGE}`, () =>
      json<Wire['ChallengeDetailResponse']>({ read_at: READ_AT, ...CHALLENGE_ROW }),
    );
    await openChats();

    fireEvent.press(await screen.findByLabelText(/^tomek\.p, Squash/));

    await waitFor(() => expect(screen).toHavePathname(`/chats/challenge/${CHALLENGE}`));
    expect(tabs()).toHaveLength(5);
    expect(tabs().map((tab) => tab.props.accessibilityState?.selected)).toEqual([
      false,
      false,
      false,
      true,
      false,
    ]);
  });
});
