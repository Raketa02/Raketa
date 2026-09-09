/**
 * The Social tags step, driven through the real route tree with only `fetch` faked.
 *
 * The same harness the rest of onboarding uses: the router, the http client, the mapper,
 * the query, the store and the screen all run. What is faked is the socket, so the
 * vocabulary under test is one the *server* served rather than one the screen invented —
 * which is the property this step exists to have.
 *
 * Every assertion is about what a player can see, what they can operate, or what an
 * assistive technology is told.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';
import { TextInput } from 'react-native';

import { refreshTokens } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  launchSignedIn,
  stubGate as stubGateWith,
  stubProfileOptions as stubOptionsWith,
  PROFILE_OPTIONS_SERVED,
  PROFILE_OPTIONS_PATH,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { useProfileDraft } from '../store/profileDraft.store';

/** One rating: the first part is behind this player, and the second one is not. */
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

/**
 * Every label, in the order the fixture serves them.
 *
 * Written out rather than derived from the presentation table: a test that asked the code
 * for the words would agree with any words at all, including none.
 */
const EVERY_TAG_IN_ORDER = [
  'Stays for a drink',
  'Straight home after',
  'Talks through the match',
  'Settles up on the spot',
  'Books the next one',
  'Shares a lift',
  'Plays to win',
  'Laughs off mistakes',
  'Encourages a partner',
  'Generous on line calls',
  'Quiet and focused',
  'Warms up properly',
  'Here to improve',
  'Here to compete',
  'Here for the exercise',
  'Here to meet players',
  'Here for a regular game',
  'Here to get back into it',
  'Open to meet someone',
];

/** Six presses that fill the served ceiling exactly. */
const SIX = EVERY_TAG_IN_ORDER.slice(0, 6);

let transport: Transport;

/** Every chip, in render order — the continue control and the back chevron excluded. */
function chipLabels(): string[] {
  return screen
    .getAllByRole('button')
    .map((node) => String(node.props.accessibilityLabel))
    .filter((label) => EVERY_TAG_IN_ORDER.includes(label));
}

function selectedLabels(): string[] {
  return screen
    .getAllByRole('button')
    .filter((node) => node.props.accessibilityState?.selected === true)
    .map((node) => String(node.props.accessibilityLabel));
}

function press(label: string) {
  fireEvent.press(screen.getByLabelText(label));
}

/** A launch by a player the gate owes the second part to, landing on its first step. */
async function reachTheTagsStep(served?: Wire['PlayerProfileOptionsResponse']) {
  stubGateWith(transport, { ratings: [RATING], hasPlayerProfile: false });
  stubOptionsWith(transport, served);

  await launchSignedIn();

  await waitFor(() => expect(screen).toHavePathname('/tags'));
  // The vocabulary and the bounds arrive together, and the continue control is what the
  // bounds produce — so waiting on it waits for a step that is fully drawn whatever
  // vocabulary this case served.
  await screen.findByLabelText('Pick 2 tags to continue');
}

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  useProfileDraft.getState().reset();
});

afterEach(() => {
  transport.restore();
  queryClient.clear();
});

// ---------------------------------------------------------------------------
// What the step offers
// ---------------------------------------------------------------------------

describe('the vocabulary the step offers', () => {
  it('renders every served tag under its heading, in the order it was served', async () => {
    await reachTheTagsStep();

    // Story 15: nineteen options must not read as an undifferentiated wall.
    expect(screen.getByText('After the match')).toBeTruthy();
    expect(screen.getByText('On the court')).toBeTruthy();
    expect(screen.getByText("Why you're here")).toBeTruthy();

    // Both orders are the contract's. The picker renders what it is given and sorts
    // nothing, so this list is the served one and not an alphabetised version of it.
    expect(chipLabels()).toEqual(EVERY_TAG_IN_ORDER);
  });

  it('offers a shorter vocabulary when a shorter one is served, rather than its own', async () => {
    // The one property that proves the vocabulary came from the server: serve two and the
    // screen shows two. A hardcoded picker passes every other test in this file.
    await reachTheTagsStep({
      ...PROFILE_OPTIONS_SERVED,
      social_tag_groups: [
        { group: 'ON_THE_COURT', tags: [{ id: 'PLAYS_TO_WIN' }, { id: 'QUIET_AND_FOCUSED' }] },
      ],
    });

    expect(chipLabels()).toEqual(['Plays to win', 'Quiet and focused']);
    expect(screen.queryByText('After the match')).toBeNull();
  });

  it('asks for nothing a player has to write', async () => {
    await reachTheTagsStep();

    // Story 22, and it is structural rather than stylistic: no free text is what keeps the
    // product's promise about what it asks. A field added here fails this.
    expect(screen.UNSAFE_queryAllByType(TextInput)).toEqual([]);
  });

  it('says nothing above the chips at all', async () => {
    // The line under the title and the note about what the tags are *for* are both gone:
    // the three group headings say what each set is about, and a screen of options reads
    // faster
    // with nothing stacked on top of them. Story 23's claim is kept by the vocabulary
    // itself — every one of them is about the game — rather than by a sentence
    // asserting it.
    await reachTheTagsStep();

    expect(screen.queryByText(/not how you look/)).toBeNull();
    expect(screen.queryByText(/another player would recognise you by/)).toBeNull();
  });

  it('draws each chip with an emoji and announces it without one', async () => {
    // The glyph is what lets a player find the chip they meant among nineteen. It is
    // decoration: a screen reader announcing its name would be reading the layout aloud
    // rather than the choice, so the accessible name is the words alone.
    await reachTheTagsStep();

    expect(await screen.findByText('🏆 Plays to win')).toBeTruthy();
    expect(screen.getByLabelText('Plays to win')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// The floor
// ---------------------------------------------------------------------------

describe('the floor', () => {
  it('is stated in the eyebrow, before anybody is blocked by it', async () => {
    // Story 18. A player should learn the rule from the screen rather than by being
    // stopped, so the numbers are in the chrome and not only inside a disabled label.
    await reachTheTagsStep();

    expect(screen.getByText('Setting up · Step 1 of 7 · Pick 2 to 6')).toBeTruthy();
  });

  it('blocks continuing with nothing picked, and says how many are missing', async () => {
    await reachTheTagsStep();

    const control = screen.getByLabelText('Pick 2 tags to continue');
    expect(control.props.accessibilityState?.disabled).toBe(true);
  });

  it('counts down as tags are picked, so a blocked control is never a mystery', async () => {
    // Story 17.
    await reachTheTagsStep();
    press('Plays to win');

    expect(await screen.findByLabelText('Pick 1 more tag to continue')).toBeTruthy();
  });

  it('lets the player continue once the floor is met', async () => {
    await reachTheTagsStep();
    press('Plays to win');
    press('Here to improve');

    const control = await screen.findByLabelText('Continue');
    expect(control.props.accessibilityState?.disabled).toBe(false);

    fireEvent.press(control);
    await waitFor(() => expect(screen).toHavePathname('/photos'));
  });

  it('stays met from the floor all the way to the ceiling', async () => {
    // Between the two numbers there is nothing to say: the control reads the same at three
    // as it does at six, and only the ceiling itself changes what a further press does.
    await reachTheTagsStep();
    for (const label of SIX.slice(0, 3)) press(label);
    expect(await screen.findByLabelText('Continue')).toBeTruthy();

    for (const label of SIX.slice(3)) press(label);

    const control = await screen.findByLabelText('Continue');
    expect(control.props.accessibilityState?.disabled).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// The ceiling
// ---------------------------------------------------------------------------

describe('the ceiling', () => {
  it('refuses a seventh tag, says so, and changes nothing', async () => {
    // Story 20. Silently dropping the oldest would remove a choice the player made without
    // telling them — so the refusal is out loud and the six they hold are untouched.
    await reachTheTagsStep();
    for (const label of SIX) press(label);
    expect(selectedLabels()).toEqual(SIX);

    press('Plays to win');

    expect(await screen.findByText(/6 tags is the most/)).toBeTruthy();
    expect(selectedLabels()).toEqual(SIX);
    expect(screen.getByLabelText('Plays to win').props.accessibilityState?.selected).toBe(false);
  });

  it('still lets a player at the ceiling remove one', async () => {
    // Story 21: the ceiling blocks adding and never blocks correcting.
    await reachTheTagsStep();
    for (const label of SIX) press(label);

    press('Shares a lift');

    await waitFor(() => expect(selectedLabels()).toEqual(SIX.slice(0, 5)));
  });

  it('takes the refusal back once there is room again', async () => {
    await reachTheTagsStep();
    for (const label of SIX) press(label);
    press('Plays to win');
    expect(await screen.findByText(/6 tags is the most/)).toBeTruthy();

    press('Shares a lift');

    await waitFor(() => expect(screen.queryByText(/6 tags is the most/)).toBeNull());
  });
});

// ---------------------------------------------------------------------------
// What a selection announces, and where it is kept
// ---------------------------------------------------------------------------

describe('a selected tag', () => {
  it('announces its selection rather than relying on being a different colour', async () => {
    // Story 24. The fill inverts *and* the state is announced; either alone excludes
    // somebody.
    await reachTheTagsStep();

    // `disabled: false` beside it since #365 gave 6.2 a disabled state: this step never draws
    // one — it refuses a seventh tag out loud rather than by greying twelve — and a chip that
    // announced nothing about it would leave *not refused* indistinguishable from *no answer*,
    // which is `selected`'s own argument one property over.
    expect(screen.getByLabelText('Plays to win').props.accessibilityState).toEqual({
      selected: false,
      disabled: false,
    });

    press('Plays to win');

    await waitFor(() =>
      expect(screen.getByLabelText('Plays to win').props.accessibilityState).toEqual({
        disabled: false,
        selected: true,
      }),
    );
  });
});

describe('the selection the part holds', () => {
  it('is still there when the player walks back to the step', async () => {
    await reachTheTagsStep();
    press('Plays to win');
    press('Here to improve');

    fireEvent.press(await screen.findByLabelText('Continue'));
    await waitFor(() => expect(screen).toHavePathname('/photos'));
    fireEvent.press(screen.getByLabelText('Back to What kind of player are you?'));
    await waitFor(() => expect(screen).toHavePathname('/tags'));

    await waitFor(() => expect(selectedLabels()).toEqual(['Plays to win', 'Here to improve']));
  });

  it('sends nothing to the server when a tag is picked', async () => {
    // The part is the checkpoint unit: the vocabulary is read once and nothing else leaves
    // the device until the commit at the end.
    await reachTheTagsStep();
    const onArrival = transport.requests.length;

    press('Plays to win');
    press('Here to improve');

    expect(transport.requests.slice(onArrival)).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// When the vocabulary cannot be read
// ---------------------------------------------------------------------------

describe('a vocabulary that will not load', () => {
  it('says so and offers to try again rather than showing an empty screen', async () => {
    stubGateWith(transport, { ratings: [RATING], hasPlayerProfile: false });
    // A 404: the route this build asks for is not one the server it is talking to serves.
    // Terminal, so nothing is retried behind the player's back and the failure is what they
    // are actually looking at.
    transport.on('GET', PROFILE_OPTIONS_PATH, () => errorResponse(404, 'not_found'));

    await launchSignedIn();
    await waitFor(() => expect(screen).toHavePathname('/tags'));

    expect(await screen.findByLabelText('Try again')).toBeTruthy();
    // Nothing to pick, so nothing to continue with — and the control says which of the two
    // it is waiting for.
    expect(screen.queryByLabelText('Continue')).toBeNull();
  });
});
