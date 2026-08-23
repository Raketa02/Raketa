/**
 * Leaving a match, driven through the real route tree and the network boundary.
 *
 * The same shape as the Now suite, and deliberately so: only `fetch` is faked. The
 * router, the http client, error mapping, the mappers, the use-cases, the hooks
 * and both screens run for real — so a pass here means the act works end to end
 * minus the socket, including the part nobody can see from one screen, which is
 * that **Now corrects itself off the player's own tap**.
 *
 * **Assertions are about what a player can see, or what left the device.** The
 * request key is the second kind: it is invisible in the render tree and it is the
 * whole of what makes a second press safe.
 */

import { focusManager, onlineManager } from '@tanstack/react-query';
import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  departurePath,
  departureScreen,
  departureWrite,
  leftHavingPaid,
  leftHavingPaidNothing,
  outcomeRow,
  stubDeparture,
} from '@/test-support/departure';
import { emptyNow, matchCard, nowPathFor, stubNow } from '@/test-support/now';
import { launchSignedIn, stubGate } from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  networkFailure,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { OUTCOME_ROW_ID } from './OutcomeTable';
import {
  CLOSE_LABEL,
  DEPARTURE_TITLE,
  DONE_LABEL,
  LOAD_FAILED,
  REFUSED_LINE,
  WRITE_FAILED,
} from './departureCopy';

const MATCH = '5b0c0000-0000-4000-8000-000000000001';
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

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  focusManager.setFocused(true);
});

afterEach(() => {
  transport.restore();
  queryClient.clear();
  onlineManager.setOnline(true);
  focusManager.setFocused(undefined);
});

/**
 * A line only Now draws.
 *
 * The suite needs to know it is standing on Now, and it asks with **its own
 * fixture** rather than by reaching into that feature for a test id: a card's
 * metadata line is Now's and this screen deliberately has none, so the two are
 * never both on display. Cross-feature deep imports are blocked by ESLint for the
 * same reason they are a bad idea here — a test that knew Now's internals would
 * break when Now rearranged them.
 */
const ON_NOW = /Sunset Padel · indoor/;

/** Her matches, with one card she may leave. */
function nowHolding(card: Wire['MatchCardResponse']): Wire['NowResponse'] {
  return { ...emptyNow(), your_matches: { stamp: 1, cards: [card] } };
}

/** A signed-in player standing on Now, holding one seat she may leave. */
async function launchOnNow(body: Wire['NowResponse']) {
  stubGate(transport, { ratings: [RATING] });
  stubNow(transport, body);

  await launchSignedIn();
  await screen.findByText(ON_NOW);
}

/** Straight to the screen, for the cases that are about the screen itself. */
async function launchOnDeparture(wire = departureScreen({ matchId: MATCH })) {
  stubGate(transport, { ratings: [RATING] });
  stubDeparture(transport, wire);

  await launchSignedIn(`/matches/${MATCH}/departure`);
  await drawn();
}

/**
 * Wait for an answer rather than for the screen.
 *
 * The header draws while the quote is still in flight, so waiting on the title
 * would let an assertion run against a screen that has no answer yet. Every loaded
 * screen has at least one outcome row — a private court's two are the fewest the
 * contract can send — and no unloaded one has any.
 */
async function drawn() {
  await screen.findAllByTestId(OUTCOME_ROW_ID);
}

/** From Now: press the exit on her card and wait for the quote to arrive. */
async function openDeparture() {
  fireEvent.press(screen.getByLabelText('Leave this match at Sunset Padel'));
  await drawn();
}

/**
 * Wait until the departure route has actually been popped.
 *
 * Now stays mounted underneath a pushed screen, so *is Now's card on screen* is
 * true throughout and says nothing. The address does.
 */
async function backOnNow() {
  await waitFor(() => expect(screen).toHavePathname('/'));
  await waitFor(() => expect(screen.queryAllByTestId(OUTCOME_ROW_ID)).toHaveLength(0));
}

/** What the write was asked to do, as it left the device. */
function writes(): readonly Record<string, unknown>[] {
  return transport
    .requestsTo('POST', departurePath(MATCH))
    .map((request) => request.body as Record<string, unknown>);
}

// ---------------------------------------------------------------------------
// Getting there
// ---------------------------------------------------------------------------

describe('the exit on a card', () => {
  it('opens the screen that states the price before anything happens', async () => {
    await launchOnNow(nowHolding(matchCard({ matchId: MATCH, mayDepart: true })));
    stubDeparture(transport, departureScreen({ matchId: MATCH }));

    await openDeparture();

    expect(screen.getByText(DEPARTURE_TITLE)).toBeTruthy();
    // It asked about the match, and about nothing else. The card's own already
    // composed facts are not carried across: what leaving is worth is asked for
    // at the instant the screen opens, never quoted from a card that never
    // checked it.
    expect(transport.requestsTo('GET', departurePath(MATCH))).toHaveLength(1);
  });

  it('asks again every time it is opened', async () => {
    // The quote is the basis of an irreversible decision and turns on clocks the
    // phone does not hold, so a screen opened twice inside the app's 30-second
    // default must ask twice. A cached quote is the one thing it must not show.
    await launchOnNow(nowHolding(matchCard({ matchId: MATCH, mayDepart: true })));
    stubDeparture(transport, departureScreen({ matchId: MATCH }));

    await openDeparture();
    expect(transport.requestsTo('GET', departurePath(MATCH))).toHaveLength(1);

    fireEvent.press(screen.getByLabelText(CLOSE_LABEL));
    await backOnNow();

    await openDeparture();

    expect(transport.requestsTo('GET', departurePath(MATCH))).toHaveLength(2);
  });

  it('asks again when the app comes back to the foreground', async () => {
    // The case a fresh visit does not cover, and the one the stale time is
    // actually about: she is **still standing on the screen** — she read the
    // quote, put the phone down, and picked it up ten minutes later. The app's
    // thirty-second default would serve her what she was quoted before lunch, so
    // this screen holds none at all.
    await launchOnDeparture();
    expect(transport.requestsTo('GET', departurePath(MATCH))).toHaveLength(1);

    await act(async () => {
      focusManager.setFocused(false);
      focusManager.setFocused(true);
      await Promise.resolve();
    });

    await waitFor(() => expect(transport.requestsTo('GET', departurePath(MATCH))).toHaveLength(2));
  });
});

// ---------------------------------------------------------------------------
// What the screen states
// ---------------------------------------------------------------------------

describe('the outcome table', () => {
  it('prints all four with a marker on each, in the quote’s own order', async () => {
    // Not only the reachable ones: *a table that quietly drops forfeited once it is
    // unreachable is also a table that never showed it while it was*.
    await launchOnDeparture();

    expect(screen.getAllByTestId(OUTCOME_ROW_ID)).toHaveLength(4);
    expect(screen.getByLabelText('Payment reversed. Behind you.')).toBeTruthy();
    expect(screen.getByLabelText('Refunded in full. What leaving is worth now.')).toBeTruthy();
  });

  it('names a moment on the row that opens, and never on one that is behind her', async () => {
    await launchOnDeparture();

    // `2026-08-23T18:00` and `20:00` against the suite's own clock — the figures
    // move with it, so the assertion is about *which rows carry one*.
    expect(screen.getByLabelText(/^Half refunded\. In /)).toBeTruthy();
    expect(screen.getByLabelText(/^Nothing comes back\. In /)).toBeTruthy();
    expect(screen.queryByLabelText(/^Payment reversed\. In /)).toBeNull();
  });

  it('says *once it fills* where there is no moment to name', async () => {
    // An open match that has not committed reaches none of the money outcomes
    // until it fills, and nothing can say when that will be.
    await launchOnDeparture(
      departureScreen({
        matchId: MATCH,
        quote: 'reversed',
        outcomes: [
          outcomeRow('reversed', 'searching'),
          outcomeRow('refundedInFull', 'stillPossible'),
          outcomeRow('refundedHalf', 'stillPossible'),
          outcomeRow('forfeited', 'stillPossible'),
        ],
      }),
    );

    expect(screen.getByLabelText('Refunded in full. Once the match fills.')).toBeTruthy();
  });

  it('drops a row this build cannot name rather than drawing a blank one', async () => {
    // The same answer an unknown situation gets. A row with no name over a
    // standing is a defect where a missing row is a loss — and the row it would
    // describe is one whose consequence this build cannot state, which is exactly
    // the thing not to guess at on a screen about an irreversible act.
    const wire = departureScreen({ matchId: MATCH });
    await launchOnDeparture({
      ...wire,
      outcomes: [
        ...wire.outcomes,
        outcomeRow('transferred' as Wire['Outcome'], 'stillPossible'),
        // And a standing it cannot name either, which is the other half of the
        // same rule: a row whose *marker* this build cannot read cannot say where
        // it stands, and an outcome with nowhere to stand is not a row.
        outcomeRow('refundedInFull', 'reopened' as Wire['OutcomeStanding']),
      ],
    });

    expect(screen.getAllByTestId(OUTCOME_ROW_ID)).toHaveLength(4);
  });

  it('draws the two rows a private court sends, and no commitment deadline', async () => {
    // Only two outcomes are reachable on a converted court, and the court was
    // bought at booking — so there is no commitment for a deadline to be about.
    await launchOnDeparture(
      departureScreen({
        matchId: MATCH,
        situation: 'privateFull',
        quote: 'refundedInFull',
        outcomes: [
          outcomeRow('refundedInFull', 'searching'),
          outcomeRow('forfeited', 'opens', '2026-08-24T19:00:00Z'),
        ],
        commitmentDeadline: null,
      }),
    );

    expect(screen.getAllByTestId(OUTCOME_ROW_ID)).toHaveLength(2);
    expect(screen.queryByText('Commitment deadline')).toBeNull();
  });
});

describe('the reasons beside the quote', () => {
  it('names the commitment deadline, her seat and how full the match is', async () => {
    await launchOnDeparture(
      departureScreen({ matchId: MATCH, amount: 3800, counts: { seats: 4, paid: 3, held: 0 } }),
    );

    expect(screen.getByText('Commitment deadline')).toBeTruthy();
    expect(screen.getByLabelText('Your seat, 38,00 zł')).toBeTruthy();
    expect(screen.getByLabelText('Seats paid, 3 of 4')).toBeTruthy();
    // Drawn, and not only announced: a row's label is composed separately from its
    // value, so asserting the label alone leaves a blank row green.
    expect(screen.getByText('38,00 zł')).toBeTruthy();
    expect(screen.getByText('3 of 4')).toBeTruthy();
  });

  it('counts down to the commitment deadline rather than printing the moment', async () => {
    // The other two reasons are facts and this one is a clock, so it is the one
    // reason whose *value* the assertion above cannot pin: a row drawing
    // `2026-08-23T16:00:00Z` where it means `2 h 14 min` satisfies every claim
    // made about the label, about the row, and about the countdown's absence on a
    // private court. It is also the only countdown on a screen whose whole job is
    // to state a deadline before she decides irreversibly.
    //
    // Thirty seconds past the figure, so the minute cannot turn between the
    // fixture being built and the assertion running.
    const deadline = new Date(Date.now() + (2 * 60 + 14) * 60 * 1000 + 30 * 1000).toISOString();

    await launchOnDeparture(departureScreen({ matchId: MATCH, commitmentDeadline: deadline }));

    expect(screen.getByText('2 h 14 min')).toBeTruthy();
    expect(screen.getByLabelText('Commitment deadline, 2 h 14 min left')).toBeTruthy();
    // And never the moment it was handed. The two assertions above both pass on a
    // row holding the countdown *and* the raw moment, and a raw ISO string is
    // exactly what the slot renders if somebody drops the countdown on the way.
    expect(screen.queryByText(deadline)).toBeNull();
  });

  it('counts a held seat separately, and only when there is one', async () => {
    // A held seat is a name with no money behind it and can lapse. Folded into
    // the paid count it would tell her the match is complete while a seat may
    // still go; drawn as a zero it would invite the reading that somebody is
    // holding nothing.
    await launchOnNow(nowHolding(matchCard({ matchId: MATCH, mayDepart: true })));

    stubDeparture(
      transport,
      departureScreen({ matchId: MATCH, counts: { seats: 4, paid: 2, held: 0 } }),
    );
    await openDeparture();
    expect(screen.queryByText('Seats held')).toBeNull();

    fireEvent.press(screen.getByLabelText(CLOSE_LABEL));
    await backOnNow();

    stubDeparture(
      transport,
      departureScreen({ matchId: MATCH, counts: { seats: 4, paid: 2, held: 1 } }),
    );
    await openDeparture();

    expect(screen.getByLabelText('Seats held, 1')).toBeTruthy();
    // And the paid count is unmoved by it, drawn as well as announced. Folded in,
    // this would read *3 of 4* and tell her the match is complete while a seat may
    // still lapse.
    expect(screen.getByLabelText('Seats paid, 2 of 4')).toBeTruthy();
    expect(screen.getByText('2 of 4')).toBeTruthy();
    expect(screen.queryByText('3 of 4')).toBeNull();
  });

  it('shows the match’s own situation, in the words the card used', async () => {
    await launchOnDeparture(departureScreen({ matchId: MATCH, situation: 'confirmed' }));

    expect(screen.getByText('38,00 zł settled to the club.')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// The one button
// ---------------------------------------------------------------------------

describe('the control that takes the quote', () => {
  it('carries the quote, and is the only step', async () => {
    // The route *is* the confirmation. A dialog over a screen whose entire job is
    // to state the consequence asks the same question twice.
    await launchOnDeparture();

    const button = screen.getByLabelText('Leave — refunded in full');
    transport.on('POST', departurePath(MATCH), () =>
      json(
        departureWrite(
          departureScreen({ matchId: MATCH, mayDepart: false }),
          matchCard({ matchId: MATCH }),
          'refundedInFull',
        ),
      ),
    );

    fireEvent.press(button);

    await waitFor(() => expect(writes()).toHaveLength(1));
    // One press, one request. No confirm step in between.
    expect(writes()[0]?.quote).toBe('refundedInFull');
  });

  it('is absent, never refusing, past the point of departure', async () => {
    // `mayDepart` is the server's boolean and no door is offered that will not
    // open. The situation line above is what says why.
    await launchOnDeparture(
      departureScreen({ matchId: MATCH, situation: 'ready', mayDepart: false }),
    );

    expect(screen.queryByLabelText(/^Leave — /)).toBeNull();
    expect(screen.getByText('Everything is paid and the court is yours.')).toBeTruthy();
  });

  it('is absent for a quote this build has never heard of', async () => {
    // A control whose consequence the app cannot state is the one outcome worse
    // than silence — on a screen about an irreversible act, most of all.
    const wire = departureScreen({ matchId: MATCH });
    await launchOnDeparture({ ...wire, quote: 'transferred' as Wire['Outcome'] });

    expect(screen.queryByLabelText(/^Leave — /)).toBeNull();
  });

  it('sends the same key however many times she presses', async () => {
    // The key is one intent, not one press: a press that timed out and a press she
    // was not sure registered are the same intent, and the server answers a repeat
    // with what the first one did.
    await launchOnDeparture();
    transport.on('POST', departurePath(MATCH), networkFailure());

    const button = screen.getByLabelText('Leave — refunded in full');
    fireEvent.press(button);
    await screen.findByText(WRITE_FAILED);
    fireEvent.press(button);

    await waitFor(() => expect(writes()).toHaveLength(2));
    expect(writes()[0]?.idempotency_key).toBe(writes()[1]?.idempotency_key);
    expect(writes()[0]?.idempotency_key).toEqual(expect.stringContaining(MATCH));
  });
});

// ---------------------------------------------------------------------------
// What comes back
// ---------------------------------------------------------------------------

describe('a departure that applied', () => {
  const applied = () =>
    departureWrite(
      departureScreen({ matchId: MATCH, situation: 'rescue', mayDepart: false }),
      matchCard({
        matchId: MATCH,
        situation: 'rescue',
        mayDepart: false,
        facts: { departure: leftHavingPaid(3800) },
      }),
      'refundedInFull',
    );

  it('says what she got, and offers the way back', async () => {
    await launchOnDeparture();
    transport.on('POST', departurePath(MATCH), () => json(applied()));

    fireEvent.press(screen.getByLabelText('Leave — refunded in full'));

    expect(await screen.findByText('You have left. You are refunded in full.')).toBeTruthy();
    // And the control that would do it again is gone, because the server says so.
    expect(screen.queryByLabelText(/^Leave — /)).toBeNull();
    expect(screen.getByLabelText(DONE_LABEL)).toBeTruthy();
  });

  it('brings her card back in place on Now, rendered for a leaver', async () => {
    // The card is returned **changed, in place** — same match, same region, new
    // rendering. Nothing vanishes, and it keeps showing the match's progress so
    // she can watch for a refill: a refill is the only thing that decides her
    // outcome.
    await launchOnNow(nowHolding(matchCard({ matchId: MATCH, mayDepart: true })));
    stubDeparture(transport, departureScreen({ matchId: MATCH }));

    await openDeparture();

    transport.on('POST', departurePath(MATCH), () => json(applied()));
    fireEvent.press(screen.getByLabelText('Leave — refunded in full'));
    await screen.findByText('You have left. You are refunded in full.');

    fireEvent.press(screen.getByLabelText(DONE_LABEL));
    await backOnNow();

    // Her own money, beside the match's own progress.
    expect(
      screen.getByText('You left — 38,00 zł comes back if somebody takes your seat.'),
    ).toBeTruthy();
    expect(screen.getByText('38,00 zł settled to the club — the seat stays funded.')).toBeTruthy();
    // And the exit is gone from the card, because the update said so.
    expect(screen.queryByLabelText('Leave this match at Sunset Padel')).toBeNull();
  });

  it('corrects Now without asking Now for anything', async () => {
    // `ADR-0074`: the update rides in the write's own answer. Popping back off a
    // route is deliberately none of the four occasions Now refetches on, so a
    // second compose here would be a cost bought for tidiness — and the player
    // would watch the screen she just came back to rebuild itself.
    await launchOnNow(nowHolding(matchCard({ matchId: MATCH, mayDepart: true })));
    stubDeparture(transport, departureScreen({ matchId: MATCH }));

    await openDeparture();
    const composesBefore = transport.requestsTo('GET', nowPathFor('all')).length;

    transport.on('POST', departurePath(MATCH), () => json(applied()));
    fireEvent.press(screen.getByLabelText('Leave — refunded in full'));
    await screen.findByText('You have left. You are refunded in full.');
    fireEvent.press(screen.getByLabelText(DONE_LABEL));
    await backOnNow();

    expect(transport.requestsTo('GET', nowPathFor('all')).length).toBe(composesBefore);
  });

  it('leaves an ordinary card saying nothing about a departure', async () => {
    // The negative half, and the one that matters most: a card telling a player
    // who holds a seat that she left is worse than any missing sentence. The line
    // is present exactly when the payload is, which is only for a leaver.
    await launchOnNow(nowHolding(matchCard({ matchId: MATCH, mayDepart: true })));

    expect(screen.queryByText(/You left/)).toBeNull();
  });

  it('names no amount to a leaver whose money never left', async () => {
    // *Nothing was taken* and *nothing has come back yet* are opposite sentences,
    // and she is not invited to interpret a blank.
    await launchOnNow(
      nowHolding(
        matchCard({
          matchId: MATCH,
          situation: 'forming',
          facts: { departure: leftHavingPaidNothing() },
        }),
      ),
    );

    const line = screen.getByText('You left — nothing had been taken.');

    expect(line).toBeTruthy();
    expect(screen.queryByText(/You left — .*zł/)).toBeNull();
  });
});

describe('a departure that was refused', () => {
  it('renders the refusal and the new outcome, in place', async () => {
    // She never gets less than quoted, silently. The refusal comes back as what a
    // success returns — the same screen, recomposed — so she *sees* the new quote
    // rather than being told about it by a dialog.
    await launchOnDeparture();
    transport.on('POST', departurePath(MATCH), () =>
      json(
        departureWrite(
          departureScreen({
            matchId: MATCH,
            quote: 'refundedHalf',
            outcomes: [
              outcomeRow('reversed', 'spent'),
              outcomeRow('refundedInFull', 'spent'),
              outcomeRow('refundedHalf', 'searching'),
              outcomeRow('forfeited', 'opens', '2026-08-23T20:00:00Z'),
            ],
          }),
          matchCard({ matchId: MATCH }),
          null,
        ),
      ),
    );

    fireEvent.press(screen.getByLabelText('Leave — refunded in full'));

    expect(await screen.findByText(REFUSED_LINE)).toBeTruthy();
    // The button now carries the new quote, and the old one is gone.
    expect(screen.getByLabelText('Leave — half refunded')).toBeTruthy();
    expect(screen.queryByLabelText('Leave — refunded in full')).toBeNull();
    expect(screen.getByLabelText('Refunded in full. Behind you.')).toBeTruthy();
  });

  it('offers no way back, because nothing has happened', async () => {
    // The *done* control belongs to a departure that was made. A refusal leaves
    // her exactly where she was, with a decision still to take.
    await launchOnDeparture();
    transport.on('POST', departurePath(MATCH), () =>
      json(
        departureWrite(
          departureScreen({ matchId: MATCH, situation: 'ready', mayDepart: false }),
          matchCard({ matchId: MATCH }),
          null,
        ),
      ),
    );

    fireEvent.press(screen.getByLabelText('Leave — refunded in full'));

    await screen.findByText(REFUSED_LINE);
    expect(screen.queryByLabelText(DONE_LABEL)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// When the screen cannot be drawn at all
// ---------------------------------------------------------------------------

describe('the screen that did not load', () => {
  it('says so, and can be asked again', async () => {
    stubGate(transport, { ratings: [RATING] });
    // A 404 is the stranger's own answer, and it is not a category the client
    // retries on its own — so the failure surfaces rather than being backed off.
    transport.on('GET', departurePath(MATCH), () => errorResponse(404, 'match_not_found'));

    await launchSignedIn(`/matches/${MATCH}/departure`);

    expect(await screen.findByText(LOAD_FAILED)).toBeTruthy();
    expect(screen.queryByLabelText(/^Leave — /)).toBeNull();

    transport.on('GET', departurePath(MATCH), () => json(departureScreen({ matchId: MATCH })));
    fireEvent.press(screen.getByLabelText('Try again'));

    expect(await screen.findByLabelText('Leave — refunded in full')).toBeTruthy();
  });

  it('goes home rather than asking about a link it cannot trust', async () => {
    // The param becomes a request path, so it is validated before anything reads
    // it. This is not the authorisation boundary — the server answers a stranger
    // with a 404 whatever the phone believes.
    stubGate(transport, { ratings: [RATING] });

    await launchSignedIn('/matches/not-a-match/departure');

    await waitFor(() => expect(screen).toHavePathname('/'));
    expect(transport.requestsTo('GET', '/api/v1/matches/not-a-match/departure')).toHaveLength(0);
  });
});

describe('the write that never reached the server', () => {
  it('says nothing has changed, and leaves the quote where it was', async () => {
    await launchOnDeparture();
    transport.on('POST', departurePath(MATCH), networkFailure());

    fireEvent.press(screen.getByLabelText('Leave — refunded in full'));

    expect(await screen.findByText(WRITE_FAILED)).toBeTruthy();
    expect(screen.getByLabelText('Leave — refunded in full')).toBeTruthy();
  });

  it('is never retried on the app’s own initiative', async () => {
    // A retry the client makes on its own is a request the player did not
    // authorise, on an act that ends her participation in a match.
    await launchOnDeparture();
    transport.on('POST', departurePath(MATCH), networkFailure());

    fireEvent.press(screen.getByLabelText('Leave — refunded in full'));
    await screen.findByText(WRITE_FAILED);

    await act(async () => {
      await Promise.resolve();
    });

    expect(writes()).toHaveLength(1);
  });
});

describe('what the screen never says', () => {
  it('offers nothing about handing a seat to somebody', async () => {
    // `ADR-0086`: transferring a seat is the leaver's best outcome and it belongs
    // to the invite flow, which this map rules out — *advertising a door that is
    // not there is worse than the gap*.
    await launchOnDeparture();

    expect(screen.queryByText(/transfer/i)).toBeNull();
    expect(screen.queryByText(/pass (it|your seat) on/i)).toBeNull();
  });
});
