/**
 * The shell, walked the way a player walks it: through the real route tree, with the real
 * bar, and only `fetch` faked.
 *
 * **The one rule here that cannot be seen is the one this suite exists for.** A shell built
 * out of `<Tabs>` passes every visible assertion below and still fails *back goes where I
 * came from* — the tab bar looks right, every screen is reachable, nothing throws, and a
 * player who left a screen and came back lands on it. So the assertions are about the
 * **stack**: what is underneath, and whether there is anything underneath at all.
 *
 * **The bar is Home · ⚡Play · You, for good** ([#576](https://github.com/Raketa02/Raketa/issues/576)):
 * the old loop's Players and Chats columns, and the flag that brought them back, are gone.
 */

import { router } from 'expo-router';
import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { authKeys, NICKNAME_ROW_TITLE } from '@/features/auth/types';
import { OPEN_THE_CHAT } from '@/features/conversations/types';
import {
  AREA_LINE,
  INTRO_TITLE,
  PHOTOS_TITLE,
  TAGS_TITLE,
  WHAT_KIND_OF_GAME_TITLE,
  WHERE_YOU_PLAY_TITLE,
  WHO_YOU_PLAY_WITH_TITLE,
  YOUR_WEEK_TITLE,
  introLine,
  kindOfGameLine,
  photosLine,
  tagsLine,
  weekLine,
  whoYouPlayWithLine,
} from '@/features/player_profile/types';
import {
  HOW_OTHERS_SEE_YOU_LINE,
  HOW_OTHERS_SEE_YOU_TITLE,
  OWN_RECORD_TITLE,
  PLAYER_RELIABILITY_TITLE,
  SKILL_PASSPORT_TITLE,
  passportLine,
  reliabilityLine,
  scoreRingLabel,
} from '@/features/player_record/types';
import { HOME_GAME_COPY } from '@/features/proposals/types';
import { doorRowLabel } from '@/shared/ui';
import {
  BOOKED_ROOM,
  BOOKING,
  bookedRoom,
  bookedRoomRow,
  bookingDetails,
  homeGame,
  stubBooking,
  stubHomeGames,
} from '@/test-support/home';
import { scrollerOf } from '@/test-support/pinned';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { forgetPhonePreferences } from '@/shared/lib/preferences';
import { queryClient } from '@/shared/lib/query-client';
import {
  GATE_USER,
  launchSignedIn,
  OWN_RECORD_SERVED,
  PROFILE_OPTIONS_SERVED,
  PROFILE_SURFACE_SERVED,
  stubConversation,
  stubConversations,
  stubEntries,
  stubGate,
  stubOwnRecord,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import { installTransport, json, type Transport, type Wire } from '@/test-support/transport';

import { HOME_COPY, PLAY_COPY } from './shellCopy';
import { YOU_COPY } from './youCopy';

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

/** *The player is on Play*: its *Groups* segment, which is what the tab opens on. */
const onPlay = () => screen.findByRole('button', { name: PLAY_COPY.segment.groups });

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [RATING], hasPlayerProfile: true });
  // You reads the profile, its options and your own record on arrival — the rows' lines, the
  // header card's face and score, and the reliability row's line.
  stubProfileSurface(transport);
  stubProfileOptions(transport);
  stubOwnRecord(transport);
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
  // Play's segment and the games opened are kept on the phone per account.
  await forgetPhonePreferences();
});

/** A player standing on the tab the entry gate lands them on. */
async function launchIntoTheApp() {
  await launchSignedIn();
  expect(await screen.findByText(HOME_COPY.empty.line)).toBeTruthy();
}

/** Press one of the three columns by the name the bar gives it. */
function pressTab(label: string) {
  fireEvent.press(screen.getByLabelText(label));
}

const columns = () => screen.getAllByRole('tab').map((tab) => tab.props.accessibilityLabel);

describe('what a player lands on', () => {
  it('opens on Home, with the bar under it — three columns, and no switch for more', async () => {
    await launchIntoTheApp();

    expect(screen).toHavePathname('/');
    expect(columns()).toEqual(['Home', 'Play', 'You']);
  });

  it('lights the tab the player is on, and only that one', async () => {
    await launchIntoTheApp();

    const selected = () =>
      screen
        .getAllByRole('tab')
        .filter((tab) => tab.props.accessibilityState?.selected === true)
        .map((tab) => tab.props.accessibilityLabel);

    expect(selected()).toEqual(['Home']);

    pressTab('You');
    await waitFor(() => expect(selected()).toEqual(['You']));

    pressTab('Play');
    await waitFor(() => expect(selected()).toEqual(['Play']));
  });

  /**
   * **The old loop asks the server nothing** — the bar used to hold its challenges, games and
   * plans for the session, and a flags host's datafile was fetched the moment the app opened.
   */
  it('reads none of the old loop’s lists, and no datafile', async () => {
    await launchIntoTheApp();
    pressTab('You');
    await waitFor(() => expect(screen).toHavePathname('/you'));
    pressTab('Play');
    await onPlay();

    const asked = transport.requests.map((request) => request.path);
    for (const old of [
      '/api/v1/challenges',
      '/api/v1/plans',
      '/api/v1/games',
      '/api/v1/interest',
    ]) {
      expect(asked).not.toContain(old);
    }
    expect(asked.filter((path) => path.includes('featurevisor'))).toEqual([]);
  });
});

/**
 * **Home's badge counts the booked games that need you** — a seat open, a result to enter or
 * confirm, a no-show against you, a payment to confirm
 * ([the mechanics §3](../../../../../docs/specs/games-and-fill-in/the-mechanics.md#3-where-everything-lives)).
 * The count is the server's `needing_you` on Home's own read, which the shell holds on every
 * screen, so it is there before the player has looked at Home, and it is spoken in the column's
 * own name. Which games are counted is the server's; what is walked here is that the count reaches
 * the bar, and that nothing else is added to it.
 */
describe('Home’s badge', () => {
  it('counts the booked games that need you, on Home, wherever the player is', async () => {
    stubHomeGames(transport, [homeGame({ status: 'NEEDS_RESULT', needs_you: true })], {
      needing_you: 2,
    });
    await launchSignedIn();

    expect(await screen.findByLabelText('Home, 2 games waiting on you')).toBeTruthy();

    pressTab('You');
    await waitFor(() => expect(screen).toHavePathname('/you'));
    expect(screen.getByLabelText('Home, 2 games waiting on you')).toBeTruthy();

    pressTab('Play');
    await onPlay();
    expect(screen.getByLabelText('Home, 2 games waiting on you')).toBeTruthy();
  });

  it('draws nothing when no game needs you', async () => {
    stubHomeGames(transport, [homeGame()], { needing_you: 0 });
    await launchSignedIn();

    await screen.findByTestId(`home-game-${BOOKING}`);
    expect(screen.getByLabelText('Home')).toBeTruthy();
    expect(screen.queryByLabelText(/^Home, /)).toBeNull();
  });
});

/**
 * **The You tab is a screen, and the last placeholder went with it**
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)).
 * What each row's screen does is its feature's suite's; what the shell owes the tab is the
 * composition — the header card, the three groups with every row in its group, each row
 * spoken as *title, live line* off the read that carries it, the way out at the foot, and the
 * one overlay two of its parts open.
 */
describe('You', () => {
  /** The stubbed profile's one declaration, as the row says it. */
  const DECLARED_LINE = kindOfGameLine([{ sport: 'padel', intent: 'FOR_FUN' }]);
  /** The stubbed record's points and band, as the row says it — `75 · High` (#660). */
  const RELIABILITY_LINE = reliabilityLine({
    playerScore: OWN_RECORD_SERVED.reliability.player_score,
    band: OWN_RECORD_SERVED.reliability.band,
    isNew: OWN_RECORD_SERVED.reliability.is_new,
  });

  /** The tab, with its reads in — the last row's line is the last read to land. */
  async function openYou() {
    await launchIntoTheApp();
    pressTab('You');
    await screen.findByRole('header', { name: YOU_COPY.title });
    await screen.findByLabelText(
      doorRowLabel(
        YOUR_WEEK_TITLE,
        weekLine([
          { day: 2, hour: 19 },
          { day: 6, hour: 9 },
        ]),
      ),
    );
  }

  it('titles the tab as the bar does, and names the three groups over three cards', async () => {
    await openYou();

    // #529: the title stands alone — no *Player profile* over it.
    expect(screen.queryByText('Player profile')).toBeNull();
    for (const group of Object.values(YOU_COPY.groups)) {
      expect(screen.getByText(group)).toBeTruthy();
    }
  });

  it('draws every row in its group, each spoken as its title and its live line', async () => {
    await openYou();

    // Playing — the two facts a player cannot touch, and the declaration.
    expect(
      screen.getByLabelText(
        doorRowLabel(SKILL_PASSPORT_TITLE, passportLine([{ sport: 'padel', level: 2.71 }])),
      ),
    ).toBeTruthy();
    expect(
      await screen.findByLabelText(doorRowLabel(PLAYER_RELIABILITY_TITLE, RELIABILITY_LINE)),
    ).toBeTruthy();
    expect(
      screen.getByLabelText(doorRowLabel(WHAT_KIND_OF_GAME_TITLE, DECLARED_LINE)),
    ).toBeTruthy();
    // Finding players — the three declarations, each off the profile read; the one that gates
    // the matcher says the preference, and never the gender.
    expect(
      screen.getByLabelText(
        doorRowLabel(
          YOUR_WEEK_TITLE,
          weekLine([
            { day: 2, hour: 19 },
            { day: 6, hour: 9 },
          ]),
        ),
      ),
    ).toBeTruthy();
    expect(screen.getByLabelText(doorRowLabel(WHERE_YOU_PLAY_TITLE, AREA_LINE))).toBeTruthy();
    expect(
      screen.getByLabelText(doorRowLabel(WHO_YOU_PLAY_WITH_TITLE, whoYouPlayWithLine('any'))),
    ).toBeTruthy();
    // On your card — the door to the sheet, the three social facts off the read, and the name.
    expect(
      screen.getByLabelText(doorRowLabel(HOW_OTHERS_SEE_YOU_TITLE, HOW_OTHERS_SEE_YOU_LINE)),
    ).toBeTruthy();
    expect(
      screen.getByLabelText(
        doorRowLabel(
          PHOTOS_TITLE,
          photosLine([{ photoId: 'photo-held-1', review: 'allowed' }, { photoId: 'photo-held-2' }]),
        ),
      ),
    ).toBeTruthy();
    expect(
      screen.getByLabelText(
        doorRowLabel(
          TAGS_TITLE,
          tagsLine(
            ['STAYS_FOR_A_DRINK', 'PLAYS_TO_WIN', 'WARMS_UP_PROPERLY', 'HERE_TO_IMPROVE'],
            PROFILE_OPTIONS_SERVED.social_tag_selection.maximum_tags,
          ),
        ),
      ),
    ).toBeTruthy();
    expect(
      screen.getByLabelText(doorRowLabel(INTRO_TITLE, introLine(PROFILE_SURFACE_SERVED.intro))),
    ).toBeTruthy();
    expect(
      screen.getByLabelText(doorRowLabel(NICKNAME_ROW_TITLE, GATE_USER.nickname ?? '')),
    ).toBeTruthy();
  });

  /**
   * **Two rows left with the questions that set them** ([#582](https://github.com/Raketa02/Raketa/issues/582)):
   * *How far to look* and *Game suggestions* were read only by the old loop's ranking, so a
   * player who changed either changed nothing they would ever see. *Finding players* is the
   * week, the area and who they play with — every one of them read when a game is proposed.
   */
  it('lists neither How far to look nor Game suggestions under Finding players', async () => {
    await openYou();

    expect(screen.queryByText('How far to look')).toBeNull();
    expect(screen.queryByText('Game suggestions')).toBeNull();

    const drawn = screen.getAllByText(/./);
    const at = (text: string) => drawn.indexOf(screen.getByText(text));
    const finding = [
      YOU_COPY.groups.findingPlayers,
      YOUR_WEEK_TITLE,
      WHERE_YOU_PLAY_TITLE,
      WHO_YOU_PLAY_WITH_TITLE,
      YOU_COPY.groups.onYourCard,
    ].map(at);
    expect(finding).toEqual([...finding].sort((a, b) => a - b));
  });

  /**
   * The rows are the features' and the groups are the shell's: *which row sits in which
   * group* is the one thing this file decides, so it is asserted as an order rather than as
   * eleven presences.
   */
  it('lays the groups down in the order the three questions are asked', async () => {
    await openYou();

    const drawn = screen.getAllByText(/./);
    const at = (text: string) => drawn.indexOf(screen.getByText(text));
    expect(at(YOU_COPY.groups.playing)).toBeLessThan(at(SKILL_PASSPORT_TITLE));
    expect(at(SKILL_PASSPORT_TITLE)).toBeLessThan(at(YOU_COPY.groups.findingPlayers));
    expect(at(YOU_COPY.groups.findingPlayers)).toBeLessThan(at(YOUR_WEEK_TITLE));
    expect(at(YOUR_WEEK_TITLE)).toBeLessThan(at(YOU_COPY.groups.onYourCard));
    expect(at(YOU_COPY.groups.onYourCard)).toBeLessThan(at(NICKNAME_ROW_TITLE));
    expect(at(NICKNAME_ROW_TITLE)).toBeLessThan(at('Sign out'));
  });

  it('draws the header card from the three reads, and the score in its ring', async () => {
    await openYou();

    expect(
      await screen.findByLabelText(scoreRingLabel(OWN_RECORD_SERVED.reliability.player_score)),
    ).toBeTruthy();
    // The nickname, with no handle line under it and never with an @ (ADR-0199 §1) — drawn by
    // the card and by the *Nickname* row's line — and the intro in the drawing's marks.
    expect(screen.getAllByText(GATE_USER.nickname ?? '')).toHaveLength(2);
    expect(screen.queryByText(`@${GATE_USER.nickname ?? ''}`)).toBeNull();
    // Twice on the tab: the card quotes the record's line, and the *Intro* row quotes the
    // profile read's — the same line, off two reads (#471).
    expect(screen.getAllByText(`“${OWN_RECORD_SERVED.intro ?? ''}”`)).toHaveLength(2);
  });

  it('opens your own record, retitled, from the header card and from the row', async () => {
    await openYou();

    fireEvent.press(
      screen.getByLabelText(doorRowLabel(HOW_OTHERS_SEE_YOU_TITLE, HOW_OTHERS_SEE_YOU_LINE)),
    );

    // The sheet is up under the server's own title for a record that is yours, and the read
    // behind it is the ungated `/me` route.
    expect(await screen.findByRole('header', { name: OWN_RECORD_TITLE })).toBeTruthy();
    expect(transport.requestsTo('GET', '/api/v1/players/me/record').length).toBeGreaterThan(0);
    fireEvent.press(screen.getByLabelText(`Close ${OWN_RECORD_TITLE.toLowerCase()}`));
    await waitFor(() =>
      expect(screen.queryByRole('header', { name: OWN_RECORD_TITLE })).toBeNull(),
    );

    // The header card is one press whose name is the identity; its hint names the door.
    fireEvent.press(screen.getByHintText(`Opens ${OWN_RECORD_TITLE.toLowerCase()}`));
    expect(await screen.findByRole('header', { name: OWN_RECORD_TITLE })).toBeTruthy();
  });

  it('never tells the player nothing is happening', async () => {
    // Home is where a game lands, so a placeholder asserting emptiness would be lying one tap
    // after one was booked. What the lines *say* is `shellCopy.test.ts`'s; this is the rendered
    // half — the tab a launch actually opens on, with the sentence on it.
    await launchIntoTheApp();

    expect(screen.queryByText(/nothing is happening/i)).toBeNull();
  });

  it('keeps the way out of a session on You, pinned at the foot', async () => {
    // The account panel outlived the screen it used to be: sign-out is the only way back
    // to the beginning, and the tab about the player is where it goes.
    await openYou();

    // #529: pinned under the page, so it is in one place however many rows are over it.
    expect(scrollerOf(screen.getByText(NICKNAME_ROW_TITLE))).toBeDefined();
    expect(scrollerOf(screen.getByLabelText('Sign out'))).toBeUndefined();
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
  it('always opens Play’s root, from whichever tab the player was on', async () => {
    await launchIntoTheApp();

    pressTab('You');
    await waitFor(() => expect(screen).toHavePathname('/you'));

    pressTab('Play');

    expect(await onPlay()).toBeTruthy();
    expect(screen).toHavePathname('/play');
  });

  it('stays lit for the screen it opened', async () => {
    await launchIntoTheApp();

    pressTab('Play');

    await waitFor(() => expect(screen).toHavePathname('/play'));
    expect(screen.getByRole('tab', { name: 'Play', selected: true })).toBeTruthy();
  });

  it('leaves Home underneath, so back leaves Play entirely', async () => {
    await launchIntoTheApp();

    pressTab('Play');
    await waitFor(() => expect(screen).toHavePathname('/play'));

    // The platform's own back, which is what the rule is about: Play does not refuse to be the
    // last screen, it has Home underneath it.
    act(() => router.back());

    expect(await screen.findByText(HOME_COPY.empty.line)).toBeTruthy();
    expect(screen).toHavePathname('/');
  });

  it('does nothing at all when the tab pressed is the one already on screen', async () => {
    await launchIntoTheApp();

    pressTab('Play');
    await waitFor(() => expect(screen).toHavePathname('/play'));

    pressTab('Play');

    await waitFor(() => expect(screen).toHavePathname('/play'));
    // And the stack has not grown a second Play to walk back through.
    expect(router.canGoBack()).toBe(true);
    act(() => router.back());
    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(router.canGoBack()).toBe(false);
  });
});

describe('the shell keeps no per-tab history', () => {
  it('leaves nothing behind a flanking tab', async () => {
    await launchIntoTheApp();

    pressTab('You');

    await waitFor(() => expect(screen).toHavePathname('/you'));
    // Not `[Home, You]`: switching tabs replaces, so there is no cross-tab back to walk.
    expect(router.canGoBack()).toBe(false);
  });

  it('throws away Play depth when the player leaves, and does not restore it', async () => {
    await launchIntoTheApp();

    pressTab('Play');
    await waitFor(() => expect(screen).toHavePathname('/play'));

    pressTab('You');
    await waitFor(() => expect(screen).toHavePathname('/you'));
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
 * on Home.** Two facts, and the first press after a cold start on a device was where they were both
 * found false at once: bootstrap **seeds** the player into the cache, so the gate's own read of
 * them never fetched at mount; thirty seconds later that seed is stale, and the first screen to
 * mount `useCurrentUser()` refetches it — which the gate took for *a read this mount is in the
 * middle of replacing* and answered `pending`, rendering nothing and tearing the authenticated
 * tree down for the length of the round trip. The tree came back with a fresh stack, and a fresh
 * stack opens on the **first route name it holds**, which was `play/index` — so every first press
 * landed on Play with ⚡Play lit, whichever column had been pressed.
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
      nickname: GATE_USER.nickname ?? undefined,
      hasPlayerProfile: true,
      profiles: { actsAsPlayer: true, administers: [], pendingInvitations: [], handovers: [] },
    });
  }

  it('stays on the tab the player pressed while a screen refetches the seeded player', async () => {
    seedThePlayer();
    await launchIntoTheApp();
    // The seed was honoured: the gate answered from it and asked the server nothing.
    expect(transport.requestsTo('GET', '/api/v1/users/me')).toHaveLength(0);

    // The seed goes stale — on a device, thirty seconds on, the app's `staleTime` — and the next
    // screen to read the player will send for a fresh copy. That refetch is a background one: the
    // gate already has its answer, and it is not what this mount set out to replace.
    //
    // Marked stale rather than waited out: the seed is written before `renderRouter` installs its
    // fake timers, so its timestamp is on the previous test's clock, and how far that clock ran
    // decided whether thirty-one seconds were enough. They were only while the gate's two retired
    // reads (#730) spent half a minute of fake time on every launch. Nothing is refetched here —
    // the gate observes the read, and only a screen mounting one more observer sends for it.
    act(() => {
      void queryClient.invalidateQueries({
        queryKey: authKeys.currentUser(),
        refetchType: 'none',
      });
    });

    pressTab('You');

    await waitFor(() => expect(transport.requestsTo('GET', '/api/v1/users/me')).toHaveLength(1));
    await waitFor(() =>
      expect(queryClient.getQueryState(authKeys.currentUser())?.fetchStatus).toBe('idle'),
    );
    // Let anything the gate might have torn down come back before looking.
    jest.advanceTimersByTime(50);
    act(() => {});

    expect(screen).toHavePathname('/you');
    expect(await screen.findByRole('header', { name: YOU_COPY.title })).toBeTruthy();
    expect(screen.queryByRole('button', { name: PLAY_COPY.segment.groups })).toBeNull();
    expect(screen.getAllByRole('tab')).toHaveLength(3);
  });

  it('opens on Home, never on the first route it happens to list, when rebuilt from nothing', async () => {
    // The gate genuinely losing its answer is the one way the tree is rebuilt, and the stack it
    // comes back with holds no history — so what it opens on is the initial route, which has to
    // be the tab the gate lands on rather than whichever screen the shell listed first for its
    // transition. Reset rather than invalidated: an invalidated read still holds its answer.
    //
    // The re-read is **held open**, for the reason the gate's own suite holds its own: a
    // navigator torn down forgets its state one tick later, and on a device the round trip is
    // longer than that tick. Answered at once, the stack would come back rehydrated onto You
    // and prove nothing about a stack that holds no history at all.
    await launchIntoTheApp();
    pressTab('You');
    await waitFor(() => expect(screen).toHavePathname('/you'));

    // The gate's one read is the player (#730): the ratings and the run route nowhere now.
    let answerMe = () => {};
    const held = new Promise<void>((resolve) => {
      answerMe = resolve;
    });
    transport.on('GET', '/api/v1/users/me', async () => {
      await held;
      return json<Wire['MeResponse']>({ ...GATE_USER, has_player_profile: true });
    });

    act(() => {
      void queryClient.resetQueries({ queryKey: authKeys.currentUser() });
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

    answerMe();

    expect(await screen.findByText(HOME_COPY.empty.line)).toBeTruthy();
    expect(screen).toHavePathname('/');
    expect(screen.queryByRole('button', { name: PLAY_COPY.segment.groups })).toBeNull();
    expect(screen.getAllByRole('tab')).toHaveLength(3);
  });
});

/**
 * **The bar stands down inside a booked game's chat, and nowhere else.** The composer replaces it
 * there so the keyboard and the stream get the whole screen
 * ([#400](https://github.com/Raketa02/Raketa/issues/400)) — and it is *not rendered* rather than
 * hidden, because the bar is a flex sibling of the navigator and a hidden one would still take its
 * height and the bottom inset. The details the room is pushed over keep their bar, which is what a
 * prefix match under `/booking/…` would get wrong.
 */
describe('the bar stands down inside a booked game’s chat', () => {
  const tabs = () => screen.queryAllByRole('tab');

  it('draws no bar in the room, and draws it again on the way back to the details', async () => {
    stubHomeGames(transport, [homeGame()]);
    stubBooking(transport, bookingDetails());
    stubConversations(transport, [bookedRoomRow()]);
    stubConversation(transport, bookedRoom());
    stubEntries(transport, BOOKED_ROOM);
    await launchSignedIn();

    fireEvent.press(await screen.findByRole('button', { name: HOME_GAME_COPY.openGame }));
    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
    expect(tabs()).toHaveLength(3);
    expect(screen.getByRole('tab', { name: 'Home', selected: true })).toBeTruthy();

    fireEvent.press(await screen.findByRole('button', { name: OPEN_THE_CHAT }));

    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}/chat`));
    expect(tabs()).toHaveLength(0);

    act(() => router.back());

    await waitFor(() => expect(screen).toHavePathname(`/booking/${BOOKING}`));
    expect(tabs()).toHaveLength(3);
  });
});
