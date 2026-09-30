/**
 * The availability step, driven through the real route tree with only the socket faked.
 *
 * The router, the http client, the domain rules, the draft and the screen all run for real.
 * Every assertion is about what a player can see, what they can operate, or what an
 * assistive technology is told — the grid renders its own answer, so nothing here reads the
 * store.
 *
 * **The absences are half the ticket.** No pre-seeded cell, no bulk selection, no date and
 * nothing finer than an hour: each of those is a thing this step must not grow, and a suite
 * that only asserted what the screen does would notice none of them.
 *
 * A tap is a press on an hour's checkbox; a drag is the grid's pan, fired by
 * `test-support/weekGridTouch` with the finger sampled hours apart, so every hour between two
 * samples is one the grid had to find itself.
 */

import { fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import { cellLabel, dayLabel, hourLabel } from '@/shared/vocabulary/availabilityPresentation';
import { HOURS, WEEKDAYS } from '@/shared/vocabulary/week';
import {
  launchSignedIn,
  stubGate as stubGateWith,
  stubProfileOptions,
} from '@/test-support/onboardingRouter';
import { installTransport, type Transport, type Wire } from '@/test-support/transport';
import { paint } from '@/test-support/weekGridTouch';

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

/** What every cell is called, in the order it is drawn: 07:00 first, Monday to Sunday along it. */
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
  await waitFor(() => expect(screen).toHavePathname('/intro'));

  // Nothing written: the intro is optional, and *Next* on an empty box carries none.
  fireEvent.press(screen.getByLabelText('Next'));
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
  it('is seven days across by sixteen hours down, 07:00 first and Monday first', async () => {
    await reachTheAvailabilityStep();

    // A hundred and twelve cells in the order they are drawn. Monday first and the hours in
    // the order a day runs are the contract's order as well as the design system's, so nothing
    // on this side sorts.
    expect(cells().map((cell) => String(cell.props.accessibilityLabel))).toEqual(EVERY_CELL);
    expect(cells()).toHaveLength(WEEK_CELLS);
    expect(cells()[0]?.props.accessibilityLabel).toBe('Monday 07:00');
    expect(cells()[1]?.props.accessibilityLabel).toBe('Tuesday 07:00');
    expect(cells().at(-1)?.props.accessibilityLabel).toBe('Sunday 22:00');
  });

  it('heads every column with its day and labels every row with its hour', async () => {
    await reachTheAvailabilityStep();

    for (const hour of HOURS) expect(screen.getByText(hourLabel(hour))).toBeTruthy();
    for (const day of WEEKDAYS) {
      // Drawn, but decoration to assistive technology: a cell names its own day, so a
      // readable head would be announced once for every hour it sits above.
      expect(screen.getByText(dayLabel(day), { includeHiddenElements: true })).toBeTruthy();
      expect(screen.queryByLabelText(dayLabel(day))).toBeNull();
    }
  });

  it('ships empty — nothing is ticked on the player’s behalf', async () => {
    // A pre-seeded hour is a claim the player never made that silently becomes a
    // matchmaking input. Blank means *no preference*, and never *leave me out*.
    await reachTheAvailabilityStep();

    expect(ticked()).toEqual([]);
    for (const cell of cells()) expect(cell.props.accessibilityState.checked).toBe(false);
  });

  it('announces each cell as a checkbox naming its day and its hour', async () => {
    await reachTheAvailabilityStep();

    expect(screen.getByRole('checkbox', { name: 'Monday 07:00' })).toBeTruthy();
    expect(screen.getByRole('checkbox', { name: 'Sunday 22:00' })).toBeTruthy();
  });
});

describe('tapping an hour', () => {
  it('toggles that one hour, on and then off again', async () => {
    await reachTheAvailabilityStep();

    fireEvent.press(screen.getByLabelText('Wednesday 19:00'));
    expect(ticked()).toEqual(['Wednesday 19:00']);

    // No floor on the grid: the last hour comes off like any other, and nothing refuses.
    fireEvent.press(screen.getByLabelText('Wednesday 19:00'));
    expect(ticked()).toEqual([]);
  });

  it('leaves the rest of its day, its hour and the week alone', async () => {
    // Independent answers. Describing an irregular week is the whole reason there is no row,
    // column or weekend behaviour anywhere in this grid.
    await reachTheAvailabilityStep();

    fireEvent.press(screen.getByLabelText('Monday 09:00'));

    expect(ticked()).toEqual(['Monday 09:00']);
    expect(screen.getByLabelText('Monday 10:00').props.accessibilityState.checked).toBe(false);
    expect(screen.getByLabelText('Tuesday 09:00').props.accessibilityState.checked).toBe(false);
  });

  it('is the only press on the grid — no day, no hour, no shortcut', async () => {
    await reachTheAvailabilityStep();

    // No day control, no hour control, no *weekends* shortcut: a shortcut is a claim about
    // what players want that this product has no evidence for.
    for (const day of WEEKDAYS) expect(screen.queryByLabelText(dayLabel(day))).toBeNull();
    for (const hour of HOURS) expect(screen.queryByLabelText(hourLabel(hour))).toBeNull();
    expect(screen.queryByLabelText(/weekend/i)).toBeNull();
    expect(screen.queryByLabelText(/select all/i)).toBeNull();
  });
});

describe('dragging across the grid', () => {
  it('paints every hour the finger crosses down a day, the ones between samples included', async () => {
    await reachTheAvailabilityStep();

    // Sampled at 18:00 and then at 21:00 — a fast finger — and 19:00 and 20:00 are painted
    // all the same.
    paint({ day: 2, hour: 18 }, { day: 2, hour: 21 });

    expect(ticked()).toEqual(['Tuesday 18:00', 'Tuesday 19:00', 'Tuesday 20:00', 'Tuesday 21:00']);
  });

  it('paints across the days along an hour', async () => {
    await reachTheAvailabilityStep();

    paint({ day: 1, hour: 12 }, { day: 5, hour: 12 });

    expect(ticked()).toEqual([
      'Monday 12:00',
      'Tuesday 12:00',
      'Wednesday 12:00',
      'Thursday 12:00',
      'Friday 12:00',
    ]);
  });

  it('leaves an hour already ticked as it was, rather than toggling it off', async () => {
    // Painting is not toggling a run: a drag that began on an empty hour ticks what it
    // crosses, and an hour already ticked in its way stays ticked.
    await reachTheAvailabilityStep();
    fireEvent.press(screen.getByLabelText('Friday 20:00'));

    paint({ day: 5, hour: 18 }, { day: 5, hour: 21 });

    expect(ticked()).toEqual(['Friday 18:00', 'Friday 19:00', 'Friday 20:00', 'Friday 21:00']);
  });

  it('clears the hours it crosses when it began on a ticked one', async () => {
    await reachTheAvailabilityStep();
    paint({ day: 6, hour: 8 }, { day: 6, hour: 16 });

    // Begun on 10:00, which is ticked: this drag clears, 10:00 to 13:00, and nothing else.
    paint({ day: 6, hour: 10 }, { day: 6, hour: 13 });

    expect(ticked()).toEqual([
      'Saturday 08:00',
      'Saturday 09:00',
      'Saturday 14:00',
      'Saturday 15:00',
      'Saturday 16:00',
    ]);
  });

  it('keeps what it painted when it turns back over its own hours', async () => {
    // Down to 21:00 and back up to 19:00 before lifting: the hours it crossed twice were
    // painted once, and turning back does not clear them.
    await reachTheAvailabilityStep();

    paint({ day: 3, hour: 17 }, { day: 3, hour: 21 }, { day: 3, hour: 19 });

    expect(ticked()).toEqual([
      'Wednesday 17:00',
      'Wednesday 18:00',
      'Wednesday 19:00',
      'Wednesday 20:00',
      'Wednesday 21:00',
    ]);
  });

  it('paints the one hour it began on when the finger never leaves it', async () => {
    // A tap that drifted far enough to be claimed as a drag paints only its own hour —
    // which is what the tap would have done.
    await reachTheAvailabilityStep();

    paint({ day: 7, hour: 22 });

    expect(ticked()).toEqual(['Sunday 22:00']);
  });
});

// ---------------------------------------------------------------------------
// Continuing, and what the step says about an empty week
// ---------------------------------------------------------------------------

describe('continuing', () => {
  it('is closed at no hours, and names what is missing rather than going grey alone', async () => {
    // The floor ADR-0102 put on the week. A blank week was being read as a *measured* zero
    // by a matcher nobody had told, so the question is asked rather than guessed at.
    await reachTheAvailabilityStep();

    const advance = screen.getByLabelText(availabilityContinueLabel({ kind: 'empty' }));
    expect(advance.props.accessibilityState?.disabled).toBe(true);

    fireEvent.press(advance);
    expect(screen).toHavePathname('/availability');
  });

  it('opens on the first hour — one is the whole floor', async () => {
    await reachTheAvailabilityStep();

    fireEvent.press(screen.getByLabelText('Saturday 09:00'));

    const advance = screen.getByLabelText('Continue');
    expect(advance.props.accessibilityState?.disabled).toBeFalsy();

    fireEvent.press(advance);
    await waitFor(() => expect(screen).toHavePathname('/location'));
  });

  it('opens on a painted run, the way it opens on a tap', async () => {
    await reachTheAvailabilityStep();

    paint({ day: 4, hour: 18 }, { day: 4, hour: 20 });

    fireEvent.press(screen.getByLabelText('Continue'));
    await waitFor(() => expect(screen).toHavePathname('/location'));
  });

  it('closes again if the player clears their last hour', async () => {
    // The floor blocks continuing, never correcting: the last hour comes off like any
    // other, by a tap or by a drag, and what changes is the control rather than the press.
    await reachTheAvailabilityStep();

    paint({ day: 6, hour: 9 }, { day: 6, hour: 11 });
    paint({ day: 6, hour: 11 }, { day: 6, hour: 9 });

    expect(ticked()).toEqual([]);
    expect(
      screen.getByLabelText(availabilityContinueLabel({ kind: 'empty' })).props.accessibilityState
        ?.disabled,
    ).toBe(true);
  });

  it('is offered with the whole week ticked too — there is no ceiling', async () => {
    await reachTheAvailabilityStep();
    for (const day of WEEKDAYS) paint({ day, hour: 7 }, { day, hour: 22 });

    expect(ticked()).toEqual(EVERY_CELL);
    const advance = screen.getByLabelText('Continue');
    expect(advance.props.accessibilityState?.disabled).toBeFalsy();

    fireEvent.press(advance);
    await waitFor(() => expect(screen).toHavePathname('/location'));
  });
});

describe('what the step says', () => {
  /**
   * **It is the grid and nothing else.** The line under the title, the note about what the
   * week is for, and the footnote under it were all cut: a week of hours is self-evident, and
   * paragraphs of reassurance around it made the one thing to do on the screen the smallest
   * thing on it.
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
    // sentence that explains it — the tag step's argument, and the same one here.
    await reachTheAvailabilityStep();

    expect(screen.getByText(availabilityEyebrow())).toBeTruthy();
  });

  it('counts nothing at a player either, ticked or not', async () => {
    await reachTheAvailabilityStep();

    fireEvent.press(screen.getByLabelText('Monday 09:00'));

    expect(screen.queryByText(/hours? ticked/)).toBeNull();
  });

  it('offers no date and nothing finer than an hour', async () => {
    // A whole hour is the finest precision this step may produce: a date or a minute would be
    // a precision the domain has nowhere to put. The only times on screen are the sixteen
    // rows, each on the hour.
    await reachTheAvailabilityStep();

    expect(screen.getAllByText(/\d{1,2}[:.]\d{2}/).map((node) => node.props.children)).toEqual(
      HOURS.map(hourLabel),
    );
    expect(screen.queryByLabelText(/\b(date|calendar)\b/i)).toBeNull();
    expect(screen.queryByRole('adjustable')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// The draft
// ---------------------------------------------------------------------------

describe('the week the player ticked', () => {
  it('is still there after walking on and back', async () => {
    // The promise the part makes when it says checking one thing costs you nothing. The
    // week is held in the draft, so the hours survive the walk in both directions.
    await reachTheAvailabilityStep();

    fireEvent.press(screen.getByLabelText('Tuesday 14:00'));
    paint({ day: 6, hour: 9 }, { day: 6, hour: 10 });

    fireEvent.press(screen.getByLabelText('Continue'));
    await waitFor(() => expect(screen).toHavePathname('/location'));

    fireEvent.press(screen.getByLabelText('Back to When do you usually play?'));
    await waitFor(() => expect(screen).toHavePathname('/availability'));

    expect(ticked()).toEqual(['Saturday 09:00', 'Saturday 10:00', 'Tuesday 14:00']);
  });

  it('leaves the device nowhere', async () => {
    await reachTheAvailabilityStep();
    const onArrival = transport.requests.length;

    paint({ day: 1, hour: 7 }, { day: 1, hour: 9 });
    fireEvent.press(screen.getByLabelText('Continue'));

    await waitFor(() => expect(screen).toHavePathname('/location'));

    // Nothing is written until the one commit at the end of the part, which is what makes
    // moving between steps free in both directions.
    expect(
      transport.requests.slice(onArrival).filter((request) => request.method !== 'GET'),
    ).toEqual([]);
  });
});
