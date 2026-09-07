/**
 * The availability step, driven through the real route tree with only the socket faked.
 *
 * The router, the http client, the domain rules, the draft and the screen all run for real.
 * Every assertion is about what a player can see, what they can operate, or what an
 * assistive technology is told — the grid renders its own answer, so nothing here reads the
 * store.
 *
 * **The absences are half the ticket.** No pre-seeded cell, no bulk selection, no clock
 * time, no hour and no date: each of those is a thing this step must not grow, and a suite
 * that only asserted what the screen does would notice none of them.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  launchSignedIn,
  stubGate as stubGateWith,
  stubProfileOptions,
} from '@/test-support/onboardingRouter';
import { installTransport, type Transport, type Wire } from '@/test-support/transport';

import { cellLabel, dayLabel, dayPartHead } from '@/shared/vocabulary/availabilityPresentation';
import { DAY_PARTS, WEEKDAYS } from '@/shared/vocabulary/week';

import { WEEK_CELLS, everyCell } from '../domain/availabilityWeek';
import { useProfileDraft } from '../store/profileDraft.store';

import { availabilityContinueLabel, availabilityEyebrow } from './availabilityPresentation';

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

/** What every cell is called, in the order it is drawn: Monday first, morning first. */
const EVERY_CELL = everyCell().map(cellLabel);

let transport: Transport;

/** A launch by a player the gate owes the second part to, walked as far as step three. */
async function reachTheAvailabilityStep() {
  stubGateWith(transport, { ratings: [RATING], hasPlayerProfile: false });
  stubProfileOptions(transport);

  await launchSignedIn();

  await waitFor(() => expect(screen).toHavePathname('/tags'));
  fireEvent.press(await screen.findByLabelText('Plays to win'));
  fireEvent.press(screen.getByLabelText('Here to improve'));
  fireEvent.press(await screen.findByLabelText('Continue'));

  await waitFor(() => expect(screen).toHavePathname('/photos'));
  fireEvent.press(screen.getByLabelText('Continue'));

  await waitFor(() => expect(screen).toHavePathname('/availability'));
  await screen.findByText('When do you usually play?');
}

const cells = () => screen.getAllByRole('checkbox');

const ticked = () =>
  cells()
    .filter((cell) => cell.props.accessibilityState?.checked === true)
    .map((cell) => String(cell.props.accessibilityLabel));

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
// The grid
// ---------------------------------------------------------------------------

describe('the grid', () => {
  it('is seven days by three parts of the day, Monday first', async () => {
    await reachTheAvailabilityStep();

    // Twenty-one cells in the order they are drawn. Monday first is the contract's order
    // as well as the design system's, and the parts of the day run in the order the domain
    // declares them, so nothing on this side sorts.
    expect(cells().map((cell) => String(cell.props.accessibilityLabel))).toEqual(EVERY_CELL);
    expect(cells()).toHaveLength(WEEK_CELLS);
  });

  it('labels every row with its day and every column with its part of the day', async () => {
    await reachTheAvailabilityStep();

    for (const day of WEEKDAYS) expect(screen.getByText(dayLabel(day))).toBeTruthy();
    for (const part of DAY_PARTS) {
      // Drawn, but decoration to assistive technology: a cell names its own column, so a
      // readable head would be announced once for every row it sits above.
      expect(screen.getByText(dayPartHead(part), { includeHiddenElements: true })).toBeTruthy();
      expect(screen.queryByLabelText(dayPartHead(part))).toBeNull();
    }
  });

  it('ships empty — nothing is ticked on the player’s behalf', async () => {
    // A pre-seeded slot is a claim the player never made that silently becomes a
    // matchmaking input. Blank means *no preference*, and never *leave me out*.
    await reachTheAvailabilityStep();

    expect(ticked()).toEqual([]);
    for (const cell of cells()) expect(cell.props.accessibilityState.checked).toBe(false);
  });

  it('announces each cell as a checkbox naming its day and its part of the day', async () => {
    // `checkbox` rather than `button`: twenty-one buttons announce twenty-one identical
    // actions, where twenty-one checkboxes announce twenty-one answers.
    await reachTheAvailabilityStep();

    expect(screen.getByRole('checkbox', { name: 'Monday morning' })).toBeTruthy();
    expect(screen.getByRole('checkbox', { name: 'Sunday evening' })).toBeTruthy();
  });
});

describe('pressing a cell', () => {
  it('toggles that one cell, on and then off again', async () => {
    await reachTheAvailabilityStep();

    fireEvent.press(screen.getByLabelText('Wednesday evening'));
    expect(ticked()).toEqual(['Wednesday evening']);

    // No floor: the last cell comes off like any other, and nothing refuses.
    fireEvent.press(screen.getByLabelText('Wednesday evening'));
    expect(ticked()).toEqual([]);
  });

  it('leaves the rest of its row, its column and the week alone', async () => {
    // Twenty-one independent answers. Describing an irregular week is the whole reason
    // there is no row, column or weekend behaviour anywhere in this grid.
    await reachTheAvailabilityStep();

    fireEvent.press(screen.getByLabelText('Monday morning'));

    expect(ticked()).toEqual(['Monday morning']);
    expect(screen.getByLabelText('Monday evening').props.accessibilityState.checked).toBe(false);
    expect(screen.getByLabelText('Tuesday morning').props.accessibilityState.checked).toBe(false);
  });

  it('is the only thing on the grid that is pressable', async () => {
    await reachTheAvailabilityStep();

    // No day control, no column control, no *weekends* shortcut: a shortcut is a claim
    // about what players want that this product has no evidence for.
    for (const day of WEEKDAYS) expect(screen.queryByLabelText(dayLabel(day))).toBeNull();
    expect(screen.queryByLabelText(/weekend/i)).toBeNull();
    expect(screen.queryByLabelText(/select all/i)).toBeNull();
  });

  it('takes the whole week, one cell at a time', async () => {
    // There is no ceiling either: twenty-one is a legal answer, and the twenty-first tick
    // is taken like the first.
    await reachTheAvailabilityStep();

    for (const name of EVERY_CELL) fireEvent.press(screen.getByLabelText(name));

    expect(ticked()).toEqual(EVERY_CELL);
  });
});

// ---------------------------------------------------------------------------
// Continuing, and what the step says about an empty week
// ---------------------------------------------------------------------------

describe('continuing', () => {
  it('is closed at zero slots, and names what is missing rather than going grey alone', async () => {
    // The floor ADR-0102 put on the week. A blank grid was being read as a *measured* zero
    // by a matcher nobody had told, so the question is asked rather than guessed at.
    await reachTheAvailabilityStep();

    const advance = screen.getByLabelText(availabilityContinueLabel({ kind: 'empty' }));
    expect(advance.props.accessibilityState?.disabled).toBe(true);

    fireEvent.press(advance);
    expect(screen).toHavePathname('/availability');
  });

  it('opens on the first tick — one of twenty-one is the whole floor', async () => {
    await reachTheAvailabilityStep();

    fireEvent.press(screen.getByLabelText('Saturday morning'));

    const advance = screen.getByLabelText('Continue');
    expect(advance.props.accessibilityState?.disabled).toBeFalsy();

    fireEvent.press(advance);
    await waitFor(() => expect(screen).toHavePathname('/location'));
  });

  it('closes again if the player unticks their last slot', async () => {
    // The floor blocks continuing, never correcting: the last cell comes off like any
    // other, and what changes is the control rather than the press.
    await reachTheAvailabilityStep();

    fireEvent.press(screen.getByLabelText('Saturday morning'));
    fireEvent.press(screen.getByLabelText('Saturday morning'));

    expect(ticked()).toEqual([]);
    expect(
      screen.getByLabelText(availabilityContinueLabel({ kind: 'empty' })).props.accessibilityState
        ?.disabled,
    ).toBe(true);
  });

  it('is offered at twenty-one slots too', async () => {
    await reachTheAvailabilityStep();
    for (const name of EVERY_CELL) fireEvent.press(screen.getByLabelText(name));

    const advance = screen.getByLabelText('Continue');
    expect(advance.props.accessibilityState?.disabled).toBeFalsy();

    fireEvent.press(advance);
    await waitFor(() => expect(screen).toHavePathname('/location'));
  });
});

describe('what the step says', () => {
  /**
   * **It is the grid and nothing else.** The line under the title, the note about what the
   * week is for, and the footnote under it were all cut: seven rows of three ticks are
   * self-evident, and three paragraphs of reassurance around them made the one thing to do
   * on the screen the smallest thing on it.
   *
   * The rules they stated are unchanged and are asserted where they can be: an empty week
   * continues, and nothing is ticked on anybody's behalf.
   */
  it('draws no prose around the grid at all', async () => {
    await reachTheAvailabilityStep();

    expect(screen.queryByText(/never that you are unavailable/i)).toBeNull();
    expect(screen.queryByText('A preference, not a promise')).toBeNull();
    expect(screen.queryByText(/nobody ever sees this as a calendar/i)).toBeNull();
    expect(screen.queryByText(/Your ordinary week/)).toBeNull();
  });

  it('states the floor in the chrome, where a player reads it before pressing anything', async () => {
    // A required answer is not a nudge, and a player facing a dead control deserves the
    // sentence that explains it — the tag step's argument, and the same one here. The rule
    // rides on the eyebrow rather than becoming a paragraph over the grid.
    await reachTheAvailabilityStep();

    expect(screen.getByText(availabilityEyebrow())).toBeTruthy();
  });

  it('counts nothing at a player either, ticked or not', async () => {
    await reachTheAvailabilityStep();

    fireEvent.press(screen.getByLabelText('Monday morning'));

    expect(screen.queryByText(/slot ticked/)).toBeNull();
  });

  it('offers no clock time, no hour and no date anywhere', async () => {
    // Three parts of the day are the finest precision this step may produce. A picker of
    // any of the three would be a precision the domain has nowhere to put.
    await reachTheAvailabilityStep();

    expect(screen.queryByText(/\d{1,2}[:.]\d{2}/)).toBeNull();
    expect(screen.queryByText(/\b(am|pm|o'clock)\b/i)).toBeNull();
    expect(screen.queryByLabelText(/\b(time|hour|date|calendar)\b/i)).toBeNull();
    expect(screen.queryByRole('adjustable')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// The draft
// ---------------------------------------------------------------------------

describe('the week the player ticked', () => {
  it('is still there after walking on and back', async () => {
    // The promise the part makes when it says checking one thing costs you nothing. The
    // grid is held in the draft, so the ticks survive the walk in both directions.
    await reachTheAvailabilityStep();

    fireEvent.press(screen.getByLabelText('Tuesday afternoon'));
    fireEvent.press(screen.getByLabelText('Saturday morning'));

    fireEvent.press(screen.getByLabelText('Continue'));
    await waitFor(() => expect(screen).toHavePathname('/location'));

    fireEvent.press(screen.getByLabelText('Back to When do you usually play?'));
    await waitFor(() => expect(screen).toHavePathname('/availability'));

    expect(ticked()).toEqual(['Tuesday afternoon', 'Saturday morning']);
  });

  it('leaves the device nowhere', async () => {
    await reachTheAvailabilityStep();
    const onArrival = transport.requests.length;

    fireEvent.press(screen.getByLabelText('Monday morning'));
    fireEvent.press(screen.getByLabelText('Continue'));

    await waitFor(() => expect(screen).toHavePathname('/location'));

    // Nothing is written until the one commit at the end of the part, which is what makes
    // moving between steps free in both directions.
    expect(
      transport.requests.slice(onArrival).filter((request) => request.method !== 'GET'),
    ).toEqual([]);
  });
});
