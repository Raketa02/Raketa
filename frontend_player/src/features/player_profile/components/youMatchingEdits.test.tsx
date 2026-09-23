/**
 * **Who you play with and Game suggestions, walked the way a player walks them** — the real
 * route tree, the real bar, and only `fetch` faked
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2, §4, §8; [#472](https://github.com/Raketa02/Raketa/issues/472)).
 *
 * Each screen is an onboarding step's controls under the tab's chrome, and the steps' own
 * suites already prove the controls — the three answers, the reach sentence, the promises.
 * What is proved here is what the tab added: each group **pre-selects from the read** and
 * **saves alone** through its own route; the reach sentence is said at the press and never for
 * *Anyone*; the row says the preference and **never the gender**; and the opt-in **sends on
 * every press** with the version on screen, the card following the reply rather than the press.
 * And, since 2026-09-18, that each group's *Save* is green and saying *Saved* while its draft
 * is the profile's own — so the group just saved turns green and the other stays as it was.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { clearStoredTokens, resetSessionStatus } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { doorRowLabel, theme } from '@/shared/ui';
import { fillOf } from '@/test-support/drawn';
import {
  PROFILE_SURFACE_SERVED,
  launchSignedIn,
  profileSurface,
  stubGate,
  stubInterest,
  stubOwnRecord,
  stubProfileOptions,
  stubProfileSurface,
} from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  noContent,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { reachOf } from '../domain/gender';
import { toRecordedProposalsOptIn } from '../mappers/playerProfileMappers';

import {
  GENDER_HEADING,
  GENDER_SCOPE,
  PREFERENCE_HEADING,
  PREFERENCE_IS_DURABLE,
  PREFER_NOT_TO_SAY_COST,
  reachNote,
} from './genderPresentation';
import {
  OPT_IN_EYEBROW,
  OPT_IN_NEVER_PRE_TICKED,
  OPT_IN_PROMISES,
  OPT_IN_PROMISES_ON_PROFILE,
  OPT_IN_PROMISE_HEADING,
  OPT_IN_SCOPE,
  PROPOSALS_OPT_IN_COPY_VERSION,
  optInAnswerLabel,
} from './optInPresentation';
import {
  GAME_SUGGESTIONS_TITLE,
  SAVE,
  SAVED,
  WHO_YOU_PLAY_WITH_TITLE,
  YOUR_ANSWER,
  YOUR_WEEK_TITLE,
  answerGivenLine,
  gameSuggestionsLine,
  groupSaveLabel,
  weekLine,
  whoYouPlayWithLine,
} from './youProfilePresentation';

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

/** The answer the served profile holds: a yes from setting up, on the twelfth of August. */
const HELD_ANSWER = toRecordedProposalsOptIn(PROFILE_SURFACE_SERVED.proposals_opt_in);

let transport: Transport;

beforeEach(() => {
  transport = installTransport();
  stubGate(transport, { ratings: [RATING], hasPlayerProfile: true });
  stubProfileSurface(transport);
  stubProfileOptions(transport);
  stubInterest(transport);
  stubOwnRecord(transport);
});

afterEach(async () => {
  transport.restore();
  queryClient.clear();
  resetSessionStatus();
  await clearStoredTokens();
});

const TWO_SLOTS = weekLine([
  { day: 2, part: 'evening' },
  { day: 6, part: 'morning' },
]);

/** A signed-in player standing on the You tab, with the profile read in. */
async function onYou() {
  await launchSignedIn();
  fireEvent.press(await screen.findByLabelText('You'));
  await screen.findByLabelText(doorRowLabel(YOUR_WEEK_TITLE, TWO_SLOTS));
}

const row = (title: string, line: string) => screen.getByLabelText(doorRowLabel(title, line));

const control = (label: string) => screen.getByLabelText(label);
const isSelected = (label: string) => control(label).props.accessibilityState?.selected;
const isDisabled = (label: string) => control(label).props.accessibilityState?.disabled;
const isGreen = (label: string) => fillOf(control(label)) === theme.color.mintInk;

const GENDER_PATH = '/api/v1/players/me/gender';
const PREFERENCE_PATH = '/api/v1/players/me/gender-preference';
const OPT_IN_PATH = '/api/v1/players/me/proposals-opt-in';

const puts = (path: string) => transport.requestsTo('PUT', path);

// ---------------------------------------------------------------------------
// The two rows
// ---------------------------------------------------------------------------

describe('the two rows under Finding players', () => {
  it('draw the preference and the standing answer from the read', async () => {
    await onYou();

    expect(row(WHO_YOU_PLAY_WITH_TITLE, whoYouPlayWithLine('any'))).toBeTruthy();
    expect(row(GAME_SUGGESTIONS_TITLE, gameSuggestionsLine(HELD_ANSWER))).toBeTruthy();
    expect(gameSuggestionsLine(HELD_ANSWER)).toBe('Yes — since 12 Aug');
  });

  it('never carry the gender — the row says who the player is matched with, and nothing about them', async () => {
    stubProfileSurface(
      transport,
      profileSurface({ gender: 'WOMAN', gender_preference: 'MEN_ONLY' }),
    );
    await onYou();

    expect(row(WHO_YOU_PLAY_WITH_TITLE, 'Matched with men only')).toBeTruthy();
    // Nowhere on the tab — not the row, not the header card, not a line under any row.
    expect(screen.queryByText('Woman')).toBeNull();
    expect(screen.queryByLabelText(/\bwoman\b/i)).toBeNull();
    expect(screen.queryByText(/\bwoman\b/i)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Who you play with
// ---------------------------------------------------------------------------

describe('Who you play with', () => {
  /** The two *Save*s, as a listener hears them: the visible word and the group it belongs to. */
  const SAVE_ABOUT_YOU = groupSaveLabel(SAVE, GENDER_HEADING);
  const SAVED_ABOUT_YOU = groupSaveLabel(SAVED, GENDER_HEADING);
  const SAVE_PREFERENCE = groupSaveLabel(SAVE, PREFERENCE_HEADING);
  const SAVED_PREFERENCE = groupSaveLabel(SAVED, PREFERENCE_HEADING);

  async function openWhoYouPlayWith(line = whoYouPlayWithLine('any')) {
    await onYou();
    fireEvent.press(row(WHO_YOU_PLAY_WITH_TITLE, line));
    await screen.findByRole('header', { name: WHO_YOU_PLAY_WITH_TITLE });
    await screen.findByLabelText('Anyone');
  }

  it('opens on both answers the profile holds, each group with Saved shut, and none of the step’s scope sentences', async () => {
    await openWhoYouPlayWith();

    expect(screen.getByText(GENDER_HEADING)).toBeTruthy();
    expect(screen.getByText(PREFERENCE_HEADING)).toBeTruthy();
    expect(isSelected('Man')).toBe(true);
    expect(isSelected('Woman')).toBe(false);
    expect(isSelected('Prefer not to say')).toBe(false);
    expect(isSelected('Anyone')).toBe(true);
    expect(isSelected('Women only')).toBe(false);

    expect(SAVED_ABOUT_YOU).toBe('Saved — About you');
    expect(isDisabled(SAVED_ABOUT_YOU)).toBe(true);
    expect(isDisabled(SAVED_PREFERENCE)).toBe(true);
    expect(isGreen(SAVED_ABOUT_YOU)).toBe(true);
    expect(isGreen(SAVED_PREFERENCE)).toBe(true);
    expect(screen.queryByLabelText(SAVE_ABOUT_YOU)).toBeNull();
    expect(screen.queryByLabelText(SAVE_PREFERENCE)).toBeNull();
    expect(screen.queryByLabelText('Continue')).toBeNull();

    // What the step said once, on the way in, is not said again on the way back (ADR-0179 §2).
    expect(screen.queryByText(GENDER_SCOPE)).toBeNull();
    expect(screen.queryByText(PREFERENCE_IS_DURABLE)).toBeNull();
  });

  it('says what narrowing costs at the press, saves that group alone, and the row follows', async () => {
    transport.on('PUT', PREFERENCE_PATH, () => noContent());
    await openWhoYouPlayWith();
    const womenOnly = reachNote(reachOf('women-only')) ?? '';

    expect(screen.queryByText(womenOnly)).toBeNull();
    fireEvent.press(control('Women only'));

    // **The sentence ADR-0096 requires**, on the second surface that takes the value — before
    // the save, not after it.
    expect(screen.getByText(womenOnly)).toBeTruthy();
    expect(isSelected('Women only')).toBe(true);
    expect(isSelected('Anyone')).toBe(false);
    // One Save opened and one still shut: the group about the player has not changed.
    expect(isDisabled(SAVE_PREFERENCE)).toBe(false);
    expect(fillOf(control(SAVE_PREFERENCE))).toBe(theme.color.coralInk);
    expect(isDisabled(SAVED_ABOUT_YOU)).toBe(true);
    expect(isGreen(SAVED_ABOUT_YOU)).toBe(true);
    expect(puts(PREFERENCE_PATH)).toHaveLength(0);

    fireEvent.press(control(SAVE_PREFERENCE));

    await waitFor(() => expect(puts(PREFERENCE_PATH)).toHaveLength(1));
    expect(puts(PREFERENCE_PATH)[0]?.body).toEqual({ gender_preference: 'WOMEN_ONLY' });
    expect(puts(GENDER_PATH)).toHaveLength(0);
    expect(await screen.findByLabelText(SAVED_PREFERENCE)).toBeTruthy();
    expect(isGreen(SAVED_PREFERENCE)).toBe(true);
    expect(screen.getByText(womenOnly)).toBeTruthy();

    fireEvent.press(control('Back'));
    expect(
      await screen.findByLabelText(
        doorRowLabel(WHO_YOU_PLAY_WITH_TITLE, 'Matched with women only'),
      ),
    ).toBeTruthy();
  });

  it('takes the reach sentence away again on Anyone, and never says it for Anyone', async () => {
    stubProfileSurface(transport, profileSurface({ gender_preference: 'MEN_ONLY' }));
    await openWhoYouPlayWith(whoYouPlayWithLine('men-only'));
    const menOnly = reachNote(reachOf('men-only')) ?? '';

    // Opened on a narrowed preference, the cost is said before anything is pressed.
    expect(screen.getByText(menOnly)).toBeTruthy();

    fireEvent.press(control('Anyone'));

    expect(screen.queryByText(menOnly)).toBeNull();
    expect(screen.queryByText(reachNote(reachOf('women-only')) ?? '')).toBeNull();
    expect(isDisabled(SAVE_PREFERENCE)).toBe(false);
  });

  it('saves the answer about the player alone, with the cost line where that answer is not free', async () => {
    transport.on('PUT', GENDER_PATH, () => noContent());
    await openWhoYouPlayWith();

    expect(screen.queryByText(PREFER_NOT_TO_SAY_COST)).toBeNull();
    fireEvent.press(control('Prefer not to say'));
    expect(screen.getByText(PREFER_NOT_TO_SAY_COST)).toBeTruthy();

    fireEvent.press(control(SAVE_ABOUT_YOU));

    await waitFor(() => expect(puts(GENDER_PATH)).toHaveLength(1));
    expect(puts(GENDER_PATH)[0]?.body).toEqual({ gender: 'PREFER_NOT_TO_SAY' });
    expect(puts(PREFERENCE_PATH)).toHaveLength(0);
    expect(await screen.findByLabelText(SAVED_ABOUT_YOU)).toBeTruthy();
    expect(isGreen(SAVED_ABOUT_YOU)).toBe(true);
    expect(isDisabled(SAVED_PREFERENCE)).toBe(true);
    expect(isSelected('Prefer not to say')).toBe(true);

    // The row still says who the player is matched with, and nothing about them.
    fireEvent.press(control('Back'));
    expect(
      await screen.findByLabelText(
        doorRowLabel(WHO_YOU_PLAY_WITH_TITLE, whoYouPlayWithLine('any')),
      ),
    ).toBeTruthy();
    expect(screen.queryByText(/prefer not to say/i)).toBeNull();
  });

  it('pre-selects nothing about a player the question was never put to', async () => {
    // A profile committed before the question existed holds no gender, and the absence is
    // never read as *Prefer not to say* — that is an answer somebody gives.
    const { gender: _neverAsked, ...neverAsked } = PROFILE_SURFACE_SERVED;
    stubProfileSurface(transport, neverAsked);
    await openWhoYouPlayWith();

    for (const label of ['Woman', 'Man', 'Prefer not to say']) {
      expect(isSelected(label)).toBe(false);
    }
    expect(isSelected('Anyone')).toBe(true);
    expect(isDisabled(SAVED_ABOUT_YOU)).toBe(true);
    expect(isDisabled(SAVED_PREFERENCE)).toBe(true);

    fireEvent.press(control('Woman'));
    expect(isDisabled(SAVE_ABOUT_YOU)).toBe(false);
  });

  it('keeps the draft and says why under the group when a save is refused', async () => {
    transport.on('PUT', PREFERENCE_PATH, () => errorResponse(403, 'forbidden'));
    await openWhoYouPlayWith();

    fireEvent.press(control('Men only'));
    fireEvent.press(control(SAVE_PREFERENCE));

    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(isSelected('Men only')).toBe(true);
    expect(isDisabled(SAVE_PREFERENCE)).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Game suggestions
// ---------------------------------------------------------------------------

describe('Game suggestions', () => {
  const YES = optInAnswerLabel(true);
  const NO = optInAnswerLabel(false);

  async function openGameSuggestions(answer = HELD_ANSWER) {
    await onYou();
    fireEvent.press(row(GAME_SUGGESTIONS_TITLE, gameSuggestionsLine(answer)));
    await screen.findByRole('header', { name: GAME_SUGGESTIONS_TITLE });
    await screen.findByLabelText(YES);
  }

  it('draws the promises with the third said from here, the scope line, and the standing answer with its evidence', async () => {
    await openGameSuggestions();

    expect(screen.getByText(OPT_IN_PROMISE_HEADING)).toBeTruthy();
    for (const promise of OPT_IN_PROMISES_ON_PROFILE) {
      expect(screen.getByLabelText(`${promise.term} ${promise.detail}`)).toBeTruthy();
    }
    expect(screen.getByText('any time, from here')).toBeTruthy();
    // The step's third reads *from your profile*; on the profile it says *here*, and nothing else
    // about the three changed.
    expect(screen.queryByText(OPT_IN_PROMISES[2]?.detail ?? '')).toBeNull();
    expect(screen.getByText(OPT_IN_SCOPE)).toBeTruthy();

    expect(screen.getByText(YOUR_ANSWER)).toBeTruthy();
    expect(screen.getByText('Yes')).toBeTruthy();
    expect(
      screen.getByText('Given 12 Aug, against these words (proposals-opt-in.v3), from setting up.'),
    ).toBeTruthy();
    expect(isSelected(YES)).toBe(true);
    expect(isSelected(NO)).toBe(false);

    // The step's chrome and its claim about its own controls are not drawn: here the answer
    // **is** pre-selected, because it was given.
    expect(screen.queryByText(OPT_IN_EYEBROW)).toBeNull();
    expect(screen.queryByText(OPT_IN_NEVER_PRE_TICKED)).toBeNull();
    expect(screen.queryByLabelText(/finish/i)).toBeNull();
  });

  /** What the route answers with: the record it made, stamped by the server, from this screen. */
  function stubRecorded() {
    transport.on('PUT', OPT_IN_PATH, (request) =>
      json<Wire['ProposalsOptInResponse']>({
        accepted: (request.body as Wire['AnswerProposalsOptInRequest']).accepted,
        copy_version: (request.body as Wire['AnswerProposalsOptInRequest']).copy_version,
        surface: 'PROFILE',
        answered_at: '2026-09-18T08:30:00Z',
      }),
    );
  }

  it('records the same answer again on a press, with the version on screen, and the card follows the reply', async () => {
    stubRecorded();
    await openGameSuggestions();

    fireEvent.press(control(YES));

    // The press is the answer — no Save, no draft — and a re-affirmation is a record.
    await waitFor(() => expect(puts(OPT_IN_PATH)).toHaveLength(1));
    expect(puts(OPT_IN_PATH)[0]?.body).toEqual({
      accepted: true,
      copy_version: PROPOSALS_OPT_IN_COPY_VERSION,
    });
    // The card draws the record the route made — its clock, its surface — never the press.
    expect(
      await screen.findByText(
        'Given 18 Sep, against these words (proposals-opt-in.v3), from this screen.',
      ),
    ).toBeTruthy();
    expect(isSelected(YES)).toBe(true);

    fireEvent.press(control('Back'));
    expect(
      await screen.findByLabelText(doorRowLabel(GAME_SUGGESTIONS_TITLE, 'Yes — since 18 Sep')),
    ).toBeTruthy();
  });

  it('records a no, and the answer card and the row say so', async () => {
    stubRecorded();
    await openGameSuggestions();

    fireEvent.press(control(NO));

    await waitFor(() => expect(puts(OPT_IN_PATH)).toHaveLength(1));
    expect(puts(OPT_IN_PATH)[0]?.body).toEqual({
      accepted: false,
      copy_version: PROPOSALS_OPT_IN_COPY_VERSION,
    });
    expect(await screen.findByText('No')).toBeTruthy();
    expect(screen.queryByText('Yes')).toBeNull();
    expect(isSelected(NO)).toBe(true);
    expect(isSelected(YES)).toBe(false);

    // And once more: two presses are two records, not one.
    fireEvent.press(control(NO));
    await waitFor(() => expect(puts(OPT_IN_PATH)).toHaveLength(2));
  });

  it('keeps the standing answer and says why when the record is refused', async () => {
    transport.on('PUT', OPT_IN_PATH, () => errorResponse(403, 'forbidden'));
    await openGameSuggestions();

    fireEvent.press(control(NO));

    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.getByText('Yes')).toBeTruthy();
    expect(isSelected(YES)).toBe(true);
    expect(isSelected(NO)).toBe(false);
    expect(screen.getByText(answerGivenLine(HELD_ANSWER))).toBeTruthy();
  });

  it('opens on a standing no, given from this screen', async () => {
    const no: Wire['ProposalsOptInResponse'] = {
      accepted: false,
      copy_version: 'proposals-opt-in.v2',
      surface: 'PROFILE',
      answered_at: '2026-09-01T12:00:00Z',
    };
    stubProfileSurface(transport, profileSurface({ proposals_opt_in: no }));
    await openGameSuggestions(toRecordedProposalsOptIn(no));

    expect(screen.getByText('No')).toBeTruthy();
    expect(
      screen.getByText('Given 1 Sep, against these words (proposals-opt-in.v2), from this screen.'),
    ).toBeTruthy();
    expect(isSelected(NO)).toBe(true);
    expect(isSelected(YES)).toBe(false);
  });
});
