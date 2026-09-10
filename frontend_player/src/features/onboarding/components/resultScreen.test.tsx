/**
 * The result screen and the evidence trail, driven through the real route tree and the
 * network boundary.
 *
 * Only `fetch` is faked. The router, the http client, error mapping, the mappers, the
 * use-cases, the cache and the screens all run for real, and the player arrives here the
 * way a player does — by answering the last question, not by being rendered in place.
 *
 * Every assertion is about what a player can see, hear or do. The one exception is
 * declared where it is made: tabular figures are a style, and a style is the only way to
 * assert a requirement whose whole purpose is that two numbers line up.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';
import { AccessibilityInfo, StyleSheet, type StyleProp, type TextStyle } from 'react-native';

import { refreshTokens } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { theme } from '@/shared/ui';
import {
  pressHardwareBack,
  stopWatchingHardwareBack,
  watchHardwareBack,
} from '@/test-support/hardwareBack';
import {
  launchSignedIn,
  runInProgress,
  stubGate as stubGateWith,
} from '@/test-support/onboardingRouter';
import {
  installTransport,
  json,
  transcriptOf,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { useOnboardingPass } from '../store/onboardingPass.store';

const ASSESSMENT_ID = '1f0e5d1e-2b3c-4d5e-8f60-71829304a5b6';
const ANSWERS_PATH = `/api/v1/assessments/${ASSESSMENT_ID}/answers`;
const STEP_PATH = `/api/v1/assessments/${ASSESSMENT_ID}`;

/** The last question of the run, whatever it is. Answering it is what ends the run. */
const OUTSTANDING: Wire['AssessmentStepResponse'] = {
  assessment_id: ASSESSMENT_ID,
  status: 'in_progress',
  questions_asked: 1,
  transcript: transcriptOf(1),
  question: {
    id: 'q-overhead',
    category: 'Match execution',
    tier: 'discriminating',
    situation: 'A deep lob pushes you off the net',
    text: 'How often do you play a controlled overhead?',
    qualifier: 'A normal match against players at your level',
    options: [
      { id: 'rarely', text: 'Rarely' },
      { id: 'usually', text: 'Usually' },
    ],
  },
};

/**
 * An ordinary result: an Established player, two categories that moved the Level and one
 * thing that widened the range.
 *
 * The band's edges here are the model's — and are asserted as *printed*, which is what
 * makes a hard-coded table in the client fail this suite.
 */
const RESULT: Wire['ResultResponse'] = {
  mu: 2.71,
  sigma: 0.62,
  confidence: 28,
  // The engine's, not the app's. Every assertion about the ring's tick, its name and the
  // Confidence explainer reads this fixture — a client-side copy would keep them passing
  // while the served number moved underneath them.
  confidence_ceiling: 30,
  range: { low: 2.09, high: 3.33 },
  band: { name: 'Established', lower: 2.65, upper: 3.85 },
  status: 'initial_estimate',
  questions_asked: 6,
  engine_version: 'racketskill-v3',
  calibration_priority: 'standard',
  confidence_reason: {
    key: 'limited-match-evidence',
    sentence: 'We have not seen you play yet, so this is a starting estimate.',
  },
  factors: [
    { key: 'match-execution', label: 'Match execution', direction: 'up', level: 3.1 },
    { key: 'recent-activity', label: 'Recent activity', direction: 'down', level: 2.4 },
  ],
  uncertainty_factors: [
    {
      key: 'time-away',
      label: 'Time away from the game',
      detail: 'You have been away, so we widened your range rather than lowering your level.',
      sigma_added: 0.18,
    },
  ],
};

function finished(result: Wire['ResultResponse']): Wire['AssessmentStepResponse'] {
  return {
    assessment_id: ASSESSMENT_ID,
    status: 'completed',
    questions_asked: result.questions_asked,
    transcript: transcriptOf(result.questions_asked),
    question: null,
    result,
  };
}

let transport: Transport;

const stubGate = (options?: Parameters<typeof stubGateWith>[1]) => stubGateWith(transport, options);

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  useOnboardingPass.getState().reset();
});

afterEach(() => {
  transport.restore();
  queryClient.clear();
});

/**
 * Answer the outstanding question and land on the result, the way the flow does it.
 *
 * The re-stubbed `GET` is what the server would say afterwards: the run is over and the
 * rating is on it. Nothing here depends on the cache still holding the mutation's
 * response, which is the point — a player who relaunches onto this screen sees the same.
 */
async function arriveAtTheResult(result: Wire['ResultResponse'] = RESULT) {
  stubGate({ runs: [runInProgress('PADEL', ASSESSMENT_ID)] });
  transport.on('GET', STEP_PATH, () => json(OUTSTANDING));
  transport.on('POST', ANSWERS_PATH, () => {
    transport.on('GET', STEP_PATH, () => json(finished(result)));
    return json(finished(result));
  });

  await launchSignedIn();

  expect(await screen.findByLabelText('Usually')).toBeTruthy();
  fireEvent.press(screen.getByLabelText('Usually'));
  fireEvent.press(screen.getByLabelText('Confirm answer'));

  await waitFor(() => expect(screen).toHavePathname(`/result/${ASSESSMENT_ID}`));
}

// ---------------------------------------------------------------------------
// The verdict: four figures that have to be read together
// ---------------------------------------------------------------------------

describe('the verdict', () => {
  it('shows the Level inside its range, with its Confidence and its Band', async () => {
    await arriveAtTheResult();

    // A rating is never only a number: two players both showing 2,71 at very different
    // uncertainties are not the same player, so the number never appears on its own.
    expect(await screen.findByText('2,71')).toBeTruthy();
    expect(screen.getByText('2,09 – 3,33')).toBeTruthy();
    expect(screen.getByLabelText('Band: Established')).toBeTruthy();
    expect(screen.getByLabelText('Rating status: Initial estimate')).toBeTruthy();
    expect(screen.getByLabelText('Questions asked: 6')).toBeTruthy();
  });

  it('draws Confidence on the full scale, with the ceiling named beside it', async () => {
    await arriveAtTheResult();

    // Not rescaled so a questionnaire's maximum fills the ring: the same component has to
    // mean the same thing when matches later push Confidence to 75%. The tick is
    // invisible to a screen reader, so the name states both numbers.
    const ring = await screen.findByRole('progressbar', {
      name: 'Confidence 28%, out of the 30% a questionnaire can prove',
    });

    expect(ring.props.accessibilityValue).toEqual({ min: 0, max: 100, now: 28 });
  });

  it('names the ceiling the engine served, not one of its own', async () => {
    // The number is version-scoped and the app no longer holds a copy. A retune reaches the
    // ring on the next response rather than on the next release — so an engine whose
    // ceiling is 45 has to be read straight through, tick and name alike.
    await arriveAtTheResult({ ...RESULT, confidence: 41, confidence_ceiling: 45 });

    expect(
      await screen.findByRole('progressbar', {
        name: 'Confidence 41%, out of the 45% a questionnaire can prove',
      }),
    ).toBeTruthy();
    expect(screen.queryByLabelText(/30%/)).toBeNull();
  });

  it('says nothing about a ceiling for a rating whose engine has been retired', async () => {
    // The result was replayed from its stream because the engine that produced it is gone:
    // the numbers survive, the explanation does not, and what a retired engine could prove
    // is part of that explanation. So the ring's name carries the one number it has — and
    // a client falling back to a constant would state a limit that did not exist when this
    // rating was produced.
    await arriveAtTheResult({ ...RESULT, confidence_ceiling: null, confidence_reason: null });

    const ring = await screen.findByRole('progressbar', { name: 'Confidence 28%' });
    expect(ring.props.accessibilityValue).toEqual({ min: 0, max: 100, now: 28 });

    // The rating itself is still shown in full. Losing the explanation is not losing the
    // rating.
    expect(screen.getByText('2,71')).toBeTruthy();
    expect(screen.getByLabelText('Band: Established')).toBeTruthy();
  });

  it("says the rating is provisional, in the app's own words rather than the engine's", async () => {
    await arriveAtTheResult();

    // The note used to be the engine's `confidence_reason`, which explained *why this
    // Confidence and not another* — a true sentence answering a question a player meeting
    // their first rating is not asking. What they need said is that the number is a starting
    // point and that matches are what settle it, which is a claim about how Raketa works and
    // so is the client's to make — for every rating, not only the ones the engine sent a
    // reason with.
    expect(await screen.findByText('This is a starting point, not a verdict')).toBeTruthy();
    expect(screen.getByText(/best guess at where you sit/)).toBeTruthy();
    expect(screen.getByText(/played a few matches/)).toBeTruthy();
    expect(
      screen.queryByText('We have not seen you play yet, so this is a starting estimate.'),
    ).toBeNull();
  });

  it('prints the band edges it was sent, never a set of its own', async () => {
    // The edges are deliberately uneven and were wrong once already. A client holding a
    // second copy would print 2,65 – 3,85 here whatever the server said.
    await arriveAtTheResult({
      ...RESULT,
      band: { name: 'Established', lower: 2.5, upper: 3.4 },
    });

    expect(await screen.findByText('Levels 2,50 – 3,40')).toBeTruthy();
    expect(screen.queryByText(/2,65/)).toBeNull();
  });

  it("shows the band's plain-language meaning, because a name alone says nothing", async () => {
    await arriveAtTheResult();

    expect(await screen.findByText(/You play a full match/)).toBeTruthy();
  });

  it('writes every figure in tabular numerals', async () => {
    await arriveAtTheResult();

    // The one style assertion in this file, and it is here because the requirement *is*
    // the style: tabular figures are what stop a column of levels shifting as the digits
    // change, and #26 puts several of these cards side by side.
    const tabular = (element: { props: { style?: StyleProp<TextStyle> } }) =>
      StyleSheet.flatten(element.props.style).fontVariant;

    expect(tabular(await screen.findByText('2,71'))).toEqual(['tabular-nums']);
    expect(tabular(screen.getByText('2,09 – 3,33'))).toEqual(['tabular-nums']);
    expect(tabular(screen.getByText('28%'))).toEqual(['tabular-nums']);
  });
});

// ---------------------------------------------------------------------------
// The evidence trail
// ---------------------------------------------------------------------------

describe('the evidence trail', () => {
  it('says what the rows are, reads them against the Level, and itemises no widener', async () => {
    await arriveAtTheResult();

    // The heading names the *reading* rather than an arithmetic the response cannot
    // support: the figures are not weighted and no operation on them produces the Level, so
    // *what moved your level* invited a reconciliation the engine never performed.
    expect(await screen.findByText('How each part of your game reads')).toBeTruthy();
    // And the lede is what makes the scales legible — the rows are independent, and the
    // mark on each is the player's own Level, quoted.
    expect(
      screen.getByText('Each one read on its own. Your level, 2,71, is the mark on every scale.'),
    ).toBeTruthy();

    // The rows themselves are unchanged: one element each, named by the server's label and
    // the engine's own comparison.
    expect(screen.getByLabelText('Match execution: above your level, 3,10')).toBeTruthy();
    expect(screen.getByLabelText('Recent activity: below your level, 2,40')).toBeTruthy();

    // The wideners still arrive and the mapper still reads them — nothing about the contract
    // narrowed. They are not drawn: the range is on the verdict above, the note beside it
    // says the estimate is provisional, and that is the whole of what the widening means to
    // somebody who has not played a match yet.
    expect(screen.queryByText('What widened your range')).toBeNull();
    expect(screen.queryByText('Time away from the game')).toBeNull();
    expect(screen.queryByLabelText(/Widened your range by/)).toBeNull();
  });

  it('renders the words the server wrote, and takes the direction it was given', async () => {
    // Both halves of one rule. The labels are the server's, so they can be corrected
    // without an App Store release — and the direction is the engine's comparison, not a
    // comparison the client makes: this category's level is *below* the player's, and the
    // engine still says `up`. A client recomputing it would draw the arrow the other way.
    await arriveAtTheResult({
      ...RESULT,
      factors: [
        {
          key: 'match-execution',
          label: 'Copy the server can change',
          direction: 'up',
          level: 2.4,
        },
      ],
    });

    expect(
      await screen.findByLabelText('Copy the server can change: above your level, 2,40'),
    ).toBeTruthy();
    expect(screen.getByText('Above')).toBeTruthy();
  });

  it('never accuses the player when their answers disagreed, and never picks a side', async () => {
    await arriveAtTheResult({
      ...RESULT,
      calibration_priority: 'elevated',
      confidence_reason: {
        key: 'answers-disagreed',
        sentence: 'Some of your answers point to different ranges, so we kept your range wider.',
      },
      uncertainty_factors: [
        {
          key: 'answers-disagreed',
          label: 'Answers pointing to different ranges',
          detail:
            'Your answers point to more than one range, so we kept the range wider rather than picking one.',
          sigma_added: 0.24,
        },
      ],
    });

    // The contradiction is not itemised any more — no widener list is drawn at all — and
    // what remains is the part that was ever about the player: the estimate is queued for
    // real matches, stated as a property of the estimate rather than as a judgement.
    expect(
      await screen.findByText(/changes who you are matched with, never where you sit/),
    ).toBeTruthy();
    expect(screen.queryByText('Answers pointing to different ranges')).toBeNull();
    expect(screen.queryByText(/we kept the range wider rather than picking one/)).toBeNull();
  });

  it('renders a contribution whose direction it has never seen instead of dropping it', async () => {
    // A phone that has not updated in eight months still shows a category added last week.
    // This is the correctness requirement of the trail: a contribution missing from the
    // screen leaves a Level nothing on it accounts for.
    await arriveAtTheResult({
      ...RESULT,
      factors: [
        { key: 'moon-phase', label: 'Something added later', direction: 'sideways', level: 2.9 },
      ],
    });

    // The unreadable direction costs the row its mark and nothing else — no arrow is
    // guessed, and the category and its level still appear.
    expect(await screen.findByLabelText('Something added later: 2,90')).toBeTruthy();
    expect(screen.queryByText('Above')).toBeNull();
    expect(screen.queryByText('Below')).toBeNull();
  });

  it("shows a beginner the one thing they told us, and nothing about a range they didn't widen", async () => {
    // Answering "never played" completes the assessment immediately. There is one
    // contribution and no widener, and the second half of the trail simply is not there.
    await arriveAtTheResult({
      ...RESULT,
      mu: 1.2,
      sigma: 0.84,
      confidence: 30,
      range: { low: 1.0, high: 2.04 },
      band: { name: 'New', lower: 1.0, upper: 1.5 },
      questions_asked: 1,
      factors: [
        { key: 'recent-activity', label: 'Recent activity', direction: 'neutral', level: 1.3 },
      ],
      uncertainty_factors: [],
    });

    expect(await screen.findByText('1,20')).toBeTruthy();
    expect(screen.getByText('How each part of your game reads')).toBeTruthy();
    // One row, read against a Level of 1,20 — the lede quotes whatever the verdict says.
    expect(screen.getByText(/Your level, 1,20, is the mark on every scale/)).toBeTruthy();
    expect(screen.queryByText('What widened your range')).toBeNull();
    expect(screen.getByLabelText('Questions asked: 1')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// The three information marks
// ---------------------------------------------------------------------------

describe('the information marks', () => {
  it('explains each figure at the moment the player meets it', async () => {
    await arriveAtTheResult();

    expect(await screen.findByLabelText('What your Level means')).toBeTruthy();
    expect(screen.getByLabelText('What your likely range means')).toBeTruthy();
    expect(screen.getByLabelText('What Confidence means')).toBeTruthy();
  });

  it('opens a popover that hides the screen behind it, and gives it back on close', async () => {
    await arriveAtTheResult();

    fireEvent.press(await screen.findByLabelText('What Confidence means'));

    // A real overlay: while it is open nothing behind it answers a query, because the
    // screen root is hidden from assistive technology and the popover is its sibling.
    expect(
      await screen.findByText(
        /Shows how confident Raketa is about your level, not how good you are/,
      ),
    ).toBeTruthy();
    expect(screen.queryByText('2,71')).toBeNull();

    fireEvent.press(screen.getByLabelText('Close Confidence'));

    await waitFor(() => expect(screen.getByText('2,71')).toBeTruthy());
    expect(screen.queryByText(/Shows how confident Raketa is about your level/)).toBeNull();
  });

  it('moves accessibility focus into the popover, and back to the mark on close', async () => {
    // Part 13's third obligation, and the one a screen-reader user notices most: without
    // the return, closing leaves them at the top of the screen having to find their place
    // again. The trigger has to outlive the close for this to be possible at all.
    const focus = jest.spyOn(AccessibilityInfo, 'setAccessibilityFocus');
    await arriveAtTheResult();

    fireEvent.press(await screen.findByLabelText('What your Level means'));
    await screen.findByText(/Where you sit on the 1,00–5,00 scale/);
    const onOpen = focus.mock.calls.length;

    fireEvent.press(screen.getByLabelText('Close Your Level'));
    await waitFor(() => expect(screen.getByText('2,71')).toBeTruthy());

    expect(onOpen).toBeGreaterThan(0);
    expect(focus.mock.calls.length).toBeGreaterThan(onOpen);
    focus.mockRestore();
  });

  it('names the ceiling in the explanation, so a low number does not read as failure', async () => {
    // 28% out of a possible 100 reads as a failing grade. 28% out of the 30 a questionnaire
    // can prove reads as what it is, and the number in that sentence is the engine's.
    await arriveAtTheResult({ ...RESULT, confidence: 41, confidence_ceiling: 45 });

    fireEvent.press(await screen.findByLabelText('What Confidence means'));

    expect(await screen.findByText(/questionnaire can provide up to 45% confidence/)).toBeTruthy();
  });

  it('drops the sentence naming a ceiling when no ceiling was served', async () => {
    // The rest of the explanation still holds — what Confidence is, and that playing is
    // what raises it. Only the claim about a maximum goes, because there is no honest
    // number to put in it.
    await arriveAtTheResult({ ...RESULT, confidence_ceiling: null, confidence_reason: null });

    fireEvent.press(await screen.findByLabelText('What Confidence means'));

    expect(
      await screen.findByText(
        /Shows how confident Raketa is about your level, not how good you are/,
      ),
    ).toBeTruthy();
    expect(screen.queryByText(/can provide up to/)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Colour is never the only carrier
// ---------------------------------------------------------------------------

describe('nothing rests on colour', () => {
  it('says each direction in a word as well as a shape', async () => {
    await arriveAtTheResult();

    expect(await screen.findByText('Above')).toBeTruthy();
    expect(screen.getByText('Below')).toBeTruthy();
    // And the shapes are there too — a word alone is not readable to everyone either.
    expect(screen.getByText('▲')).toBeTruthy();
    expect(screen.getByText('▼')).toBeTruthy();
  });

  it('keeps the band bar legible on the dark card it lives on', async () => {
    await arriveAtTheResult();

    // The bar is one element to a screen reader, and it says the three numbers the
    // drawing carries. `muted` and the band inks are computed against paper; on `night`
    // they are unreadable, which is why the bar repaints rather than reusing them.
    expect(
      await screen.findByLabelText(
        'Level 2,71 of 5,00, likely range 2,09 – 3,33, band Established',
      ),
    ).toBeTruthy();
    expect(theme.color.onDarkTiny).not.toBe(theme.color.muted);
  });
});

/**
 * **The device's back button, on a rating a run has already produced.**
 *
 * Every screen in onboarding is reached by `replace`, so the group holds one history entry
 * and Android's back popped straight through it to the screen the part began on — welcome,
 * one push behind the sport picker, from which the only way forward is to rate a sport
 * again. [ADR-0090](../../../../../docs/adr/0090-onboarding-per-player-checkpoint.md): *"Back
 * and forward move freely inside each part and never cross between them."*
 *
 * Neither screen draws a back control, so the press is claimed and nothing happens — the same
 * answer the missing control already gives. `pressHardwareBack` replays the press through
 * what the app subscribed and reports whether anything claimed it; the pop that follows an
 * unclaimed press is the activity's, and no test here can perform it.
 */
describe("the device's own back button", () => {
  beforeEach(watchHardwareBack);
  afterEach(stopWatchingHardwareBack);

  it('is claimed and refused, leaving the result where the run put it', async () => {
    await arriveAtTheResult();

    expect(pressHardwareBack()).toBe(true);

    expect(screen).toHavePathname(`/result/${ASSESSMENT_ID}`);
  });
});
