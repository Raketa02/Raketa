/**
 * Racing for a seat, driven through the real route tree and the network boundary.
 *
 * The same shape as the rest of this app's flow suites: only `fetch` is faked, so
 * the http client, error mapping, the mapper, the use-case, the hook, the cache
 * write and the screen all run for real. A pass here means the tap works end to
 * end minus the socket — including the half nobody can see from one card, which is
 * that **Now corrects itself off the same tap** (`ADR-0074`).
 *
 * Its own file rather than a section of `nowFlow.test.tsx`, because the two suites
 * are about two different things: that one is about composing a screen from an
 * answer, and this one is about a **write** and the four ways it can come back.
 *
 * **The assertions are what a player can see, what left the device, and what did
 * not happen.** The last is the point of the ticket: no dialog, no toast, no
 * second compose — she finds out from the screen.
 */

import { Alert } from 'react-native';
import { focusManager, onlineManager } from '@tanstack/react-query';
import { act, fireEvent, screen, waitFor } from 'expo-router/testing-library';

import { refreshTokens } from '@/features/auth/types';
import { clearStoredTokens, resetSessionStatus, wireHttpCredentials } from '@/shared/lib/auth';
import { queryClient } from '@/shared/lib/query-client';
import {
  emptyNow,
  matchCard,
  nowOffering,
  nowPathFor,
  seatPath,
  seatWrite,
  stubNow,
} from '@/test-support/now';
import { launchSignedIn, stubGate } from '@/test-support/onboardingRouter';
import {
  errorResponse,
  installTransport,
  json,
  networkFailure,
  type Transport,
  type Wire,
} from '@/test-support/transport';

import { useSportFilterStore } from '../store/sportFilter.store';

import { CLOCK_ID } from './CardClock';
import { REGION_ID } from './NowRegions';
import { TRANSIENT_LINE_ID } from './TransientLine';
import { SEAT_GONE, SEAT_WRITE_FAILED } from './nowCopy';

const MATCH = '5b0c0000-0000-4000-8000-000000000001';
const OTHER = '5b0c0000-0000-4000-8000-000000000002';

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

const TAKE_IT = 'Take the seat · 38,00 zł, Sunset Padel';

let transport: Transport;
let dialogs: jest.SpyInstance;

beforeEach(async () => {
  transport = installTransport();
  resetSessionStatus();
  wireHttpCredentials(refreshTokens);
  await clearStoredTokens();
  queryClient.clear();
  useSportFilterStore.getState().reset();
  focusManager.setFocused(true);
  // The one assertion the render tree cannot make: a dialog is not in it.
  dialogs = jest.spyOn(Alert, 'alert').mockImplementation(() => undefined);
});

afterEach(() => {
  dialogs.mockRestore();
  transport.restore();
  queryClient.clear();
  onlineManager.setOnline(true);
  focusManager.setFocused(undefined);
});

/** An offer card: the situation the cascade composes, and the act it arrives with. */
function offer(matchId = MATCH, clubName = 'Sunset Padel'): Wire['MatchCardResponse'] {
  return matchCard({
    matchId,
    situation: 'seatOpened',
    clubName,
    clock: '2099-01-01T18:00:00Z',
    act: 'takeSeat',
  });
}

/** The card a claim-holder gets back: the claim's five minutes, and one thing to do. */
function claimed(matchId = MATCH): Wire['MatchCardResponse'] {
  return matchCard({
    matchId,
    situation: 'confirmed',
    seatClaimExpiresAt: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
    act: 'finishPaying',
    mayDepart: false,
  });
}

/** The card somebody else's tap left behind: no offer, no act, no way in. */
function full(matchId = MATCH): Wire['MatchCardResponse'] {
  return matchCard({ matchId, situation: 'full', act: null });
}

async function launchOnNow(body: Wire['NowResponse'] = nowOffering(offer())) {
  stubGate(transport, { ratings: [RATING] });
  stubNow(transport, body);

  await launchSignedIn();
  await screen.findByTestId(REGION_ID.offers);
}

/** Answer the tap with one body, and hand back how many taps reached the socket. */
function seatAnswers(body: Wire['SeatWriteResponse'], matchId = MATCH): () => number {
  transport.on('POST', seatPath(matchId), () => json(body));
  return () => transport.requestsTo('POST', seatPath(matchId)).length;
}

const composes = () => transport.requestsTo('GET', nowPathFor('all')).length;

// ---------------------------------------------------------------------------
// What leaves the device
// ---------------------------------------------------------------------------

describe('the tap', () => {
  it('goes to the seat route with nothing but the chip she is holding', async () => {
    // Which *seat* is the match's answer and not the caller's, and a price is not
    // something a caller quotes — so there is no body. The sport is a fact about
    // the **screen**: the two regions come back composed under it.
    await launchOnNow();
    const taps = seatAnswers(seatWrite({ claimed: false, update: full() }));

    fireEvent.press(screen.getByLabelText(TAKE_IT));
    await waitFor(() => expect(taps()).toBe(1));

    const sent = transport.requestsTo('POST', seatPath(MATCH))[0];

    expect(sent?.body).toBeUndefined();
    expect(sent?.headers.Authorization).toMatch(/^Bearer /);
  });

  it('carries the sport chip the screen is filtered to', async () => {
    await launchOnNow(emptyNow());
    stubNow(transport, nowOffering(offer()), 'SQUASH');
    fireEvent.press(screen.getByRole('radio', { name: 'Squash' }));
    await screen.findByLabelText(TAKE_IT);

    transport.on('POST', seatPath(MATCH, 'SQUASH'), () =>
      json(seatWrite({ claimed: false, update: full() })),
    );

    fireEvent.press(screen.getByLabelText(TAKE_IT));

    await waitFor(() =>
      expect(transport.requestsTo('POST', seatPath(MATCH, 'SQUASH'))).toHaveLength(1),
    );
    // And never under the chip that is not on screen: a region composed under one
    // filter would replace her filtered screen with somebody else's.
    expect(transport.requestsTo('POST', seatPath(MATCH, 'all'))).toHaveLength(0);
  });

  it('corrects the filtered screen she is standing on, and not the one she is not', async () => {
    // The other half of the chip, and the half no request transcript can show: the
    // two regions come back **composed under it**, so they belong to that chip's
    // cached screen. Written to `all` instead, the squash screen would keep its own
    // offers region and the match would stay on the wrong one — with the corrected
    // card in it, saying something true in a place that is not.
    await launchOnNow(emptyNow());
    stubNow(transport, nowOffering(offer()), 'SQUASH');
    fireEvent.press(screen.getByRole('radio', { name: 'Squash' }));
    await screen.findByLabelText(TAKE_IT);

    transport.on('POST', seatPath(MATCH, 'SQUASH'), () =>
      json(seatWrite({ claimed: true, update: claimed(), offers: [], yourMatches: [claimed()] })),
    );

    fireEvent.press(screen.getByLabelText(TAKE_IT));
    await screen.findByText(/^Finish paying/);

    expect(screen.getByTestId(REGION_ID.offers).children).toHaveLength(0);
    expect(screen.queryByText('No matches booked')).toBeNull();
  });

  it('is not sent twice while the first one is in flight', async () => {
    // The write has no idempotency key, deliberately: what one would buy is
    // answered by the card that comes back carrying the claim. What must not
    // happen is the app sending a second command for one press of a thumb.
    await launchOnNow();

    let answer: (() => void) | undefined;
    const held = new Promise<void>((resolve) => {
      answer = resolve;
    });
    transport.on('POST', seatPath(MATCH), async () => {
      await held;
      return json(seatWrite({ claimed: true, update: claimed(), offers: [], yourMatches: [] }));
    });

    fireEvent.press(screen.getByLabelText(TAKE_IT));
    // The button is blocked while it works, and says so rather than looking idle.
    await waitFor(() =>
      expect(screen.getByLabelText(TAKE_IT).props.accessibilityState.busy).toBe(true),
    );

    fireEvent.press(screen.getByLabelText(TAKE_IT));
    fireEvent.press(screen.getByLabelText(TAKE_IT));

    await act(async () => {
      answer?.();
      await held;
    });

    expect(transport.requestsTo('POST', seatPath(MATCH))).toHaveLength(1);
  });

  it('is never retried on the app’s own initiative', async () => {
    // `retry: false`, and this is the case that default was written for: a retry
    // the client makes for her is a command she did not give, against five minutes
    // her money is behind.
    await launchOnNow();
    transport.on('POST', seatPath(MATCH), () => errorResponse(500, 'internal_error'));

    fireEvent.press(screen.getByLabelText(TAKE_IT));
    await screen.findByTestId(TRANSIENT_LINE_ID);

    await act(async () => {
      jest.advanceTimersByTime(30_000);
    });

    expect(transport.requestsTo('POST', seatPath(MATCH))).toHaveLength(1);
  });
});

// ---------------------------------------------------------------------------
// A tap that got there first
// ---------------------------------------------------------------------------

describe('a seat she was fastest to', () => {
  /** The answer the server composes: the offer is gone, the match is hers to pay for. */
  const applied = () =>
    seatWrite({ claimed: true, update: claimed(), offers: [], yourMatches: [claimed()] });

  it('switches the card’s clock to the claim’s five minutes and its act to finish paying', async () => {
    await launchOnNow();
    seatAnswers(applied());

    fireEvent.press(screen.getByLabelText(TAKE_IT));

    expect(await screen.findByText(/^Finish paying/)).toBeTruthy();
    expect(screen.queryByText(/^Take the seat/)).toBeNull();
    // Five minutes, not the match's own moment two thousand days out.
    expect(screen.getByTestId(CLOCK_ID).props.children).toMatch(/^[0-5]:\d\d$/);
  });

  it('moves the card out of the offers region and into the strip', async () => {
    // `ADR-0070`'s reason for the two region slots existing at all: *"an accepted
    // offer changes three things at once — the offer is gone, the match belongs in
    // the strip"*. Both regions arrive whole and composed by the server.
    await launchOnNow();
    seatAnswers(applied());

    fireEvent.press(screen.getByLabelText(TAKE_IT));
    await screen.findByText(/^Finish paying/);

    expect(screen.getByTestId(REGION_ID.offers).children).toHaveLength(0);
    expect(screen.getByTestId(REGION_ID.yourMatches)).toBeTruthy();
    // The strip's own empty state is gone, because the strip is not empty.
    expect(screen.queryByText('No matches booked')).toBeNull();
  });

  it('keeps the offers that survived the tap, from the region the server sent', async () => {
    // The region comes back **whole**, not emptied: a player told about two seats
    // who takes one still has the other, and a client that rebuilt the region from
    // the one card it was handed would drop it. The composed answer is the only
    // thing that knows which offers are still live.
    await launchOnNow(nowOffering(offer(), offer(OTHER, 'Hala Wisła')));
    seatAnswers(
      seatWrite({
        claimed: true,
        update: claimed(),
        offers: [offer(OTHER, 'Hala Wisła')],
        yourMatches: [claimed()],
      }),
    );

    fireEvent.press(screen.getByLabelText(TAKE_IT));
    await screen.findByText(/^Finish paying/);

    expect(screen.getByLabelText('Take the seat · 38,00 zł, Hala Wisła')).toBeTruthy();
    expect(screen.queryByLabelText(TAKE_IT)).toBeNull();
  });

  it('shows no exit control while the payment is running', async () => {
    // Abandoning a payment must not be dressed as leaving (`ADR-0081`). The server
    // says so — `may_depart` is false under a live claim — and the card obeys.
    await launchOnNow();
    seatAnswers(applied());

    fireEvent.press(screen.getByLabelText(TAKE_IT));
    await screen.findByText(/^Finish paying/);

    expect(screen.queryByLabelText(/^Leave this match/)).toBeNull();
  });

  it('says nothing about a seat having gone', async () => {
    // The negative control for the line below, and the one that matters most: a
    // player who got the seat must not be told she did not.
    await launchOnNow();
    seatAnswers(applied());

    fireEvent.press(screen.getByLabelText(TAKE_IT));
    await screen.findByText(/^Finish paying/);

    expect(screen.queryByTestId(TRANSIENT_LINE_ID)).toBeNull();
    expect(screen.queryByText(SEAT_GONE)).toBeNull();
  });

  it('corrects Now without asking Now for anything', async () => {
    // `ADR-0074`: the answer was composed at the instant of the write. A second
    // compose here would pay the whole funnel for something already in hand, and
    // she would watch the screen under her thumb rebuild itself.
    await launchOnNow();
    const before = composes();
    seatAnswers(applied());

    fireEvent.press(screen.getByLabelText(TAKE_IT));
    await screen.findByText(/^Finish paying/);

    expect(composes()).toBe(before);
  });
});

// ---------------------------------------------------------------------------
// A tap that was not fastest
// ---------------------------------------------------------------------------

describe('a seat somebody else took', () => {
  /** Six of the eight refusals answer with what a success answers (`ADR-0070`). */
  const refused = () => seatWrite({ claimed: false, update: full() });

  it('renders the corrected card in place, and no dialog appears', async () => {
    await launchOnNow();
    seatAnswers(refused());

    fireEvent.press(screen.getByLabelText(TAKE_IT));

    // She *sees* it: the card that offered her a seat now says the match is full,
    // where it already was, and offers nothing.
    expect(
      await screen.findByText(
        'Every seat is paid — it settles to the club at the commitment deadline.',
      ),
    ).toBeTruthy();
    expect(screen.queryByText(/^Take the seat/)).toBeNull();
    expect(dialogs).not.toHaveBeenCalled();
  });

  it('says the seat has gone, in one plain line that is not a control', async () => {
    // `ADR-0062`: *"one plain line at the top of Now — that seat has gone. Not a
    // card, no action, no tap target; it fades."*
    await launchOnNow();
    seatAnswers(refused());

    fireEvent.press(screen.getByLabelText(TAKE_IT));

    const line = await screen.findByTestId(TRANSIENT_LINE_ID);

    expect(screen.getByText(SEAT_GONE)).toBeTruthy();
    expect(line.props.pointerEvents).toBe('none');
    expect(screen.queryByRole('button', { name: SEAT_GONE })).toBeNull();
  });

  it('says it once, and then stops saying it', async () => {
    await launchOnNow();
    seatAnswers(refused());

    fireEvent.press(screen.getByLabelText(TAKE_IT));
    await screen.findByTestId(TRANSIENT_LINE_ID);

    await act(async () => {
      jest.advanceTimersByTime(10_000);
    });

    expect(screen.queryByTestId(TRANSIENT_LINE_ID)).toBeNull();
    expect(screen.queryByText(SEAT_GONE)).toBeNull();
    // And the card is still exactly where it was, still saying what is true.
    expect(
      screen.getByText('Every seat is paid — it settles to the club at the commitment deadline.'),
    ).toBeTruthy();
  });

  it('leaves the corrected card where it was rather than removing it', async () => {
    // A refusal moved nothing, so no region comes back — which is what leaves the
    // card on screen long enough for the line to be about something.
    await launchOnNow();
    seatAnswers(refused());

    fireEvent.press(screen.getByLabelText(TAKE_IT));
    await screen.findByText(
      'Every seat is paid — it settles to the club at the commitment deadline.',
    );

    expect(screen.getByTestId(REGION_ID.offers).children.length).toBeGreaterThan(0);
  });

  it('keeps the offers she can still take', async () => {
    // Only the card the tap was about changes. The second offer is untouched, and
    // in the order it arrived in (`ADR-0032`).
    await launchOnNow(nowOffering(offer(), offer(OTHER, 'Hala Wisła')));
    seatAnswers(refused());

    fireEvent.press(screen.getByLabelText(TAKE_IT));
    await screen.findByText(
      'Every seat is paid — it settles to the club at the commitment deadline.',
    );

    expect(screen.getByLabelText('Take the seat · 38,00 zł, Hala Wisła')).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// The two refusals that are about her
// ---------------------------------------------------------------------------

describe('a refusal that no card about this match could state', () => {
  it('says she is already buying a seat, in the same one line', async () => {
    // `ADR-0081`'s first structural limit on a serial claimant. It is a sentence
    // about a **different match**, so no recomposed card here could carry it.
    await launchOnNow();
    transport.on('POST', seatPath(MATCH), () =>
      errorResponse(409, 'match_player_already_claiming'),
    );

    fireEvent.press(screen.getByLabelText(TAKE_IT));

    expect(
      await screen.findByText('You are already buying a seat. Finish that one first.'),
    ).toBeTruthy();
    expect(dialogs).not.toHaveBeenCalled();
    // The card still offers the seat, because nothing about this match changed.
    expect(screen.getByLabelText(TAKE_IT)).toBeTruthy();
  });

  it('says to give the seat a moment when she has just let it go', async () => {
    // The second limit: thirty seconds, per seat. *"Enough to break a tap-loop,
    // not enough to cost a mistyped PIN a Saturday game."*
    await launchOnNow();
    transport.on('POST', seatPath(MATCH), () => errorResponse(409, 'match_claim_cooling_down'));

    fireEvent.press(screen.getByLabelText(TAKE_IT));

    expect(await screen.findByText('Give that seat a moment before trying again.')).toBeTruthy();
  });

  it('says the plain thing for a tap that never landed', async () => {
    // A failure with no code of its own is not a sentence about a seat, and the
    // line does not invent one.
    await launchOnNow();
    transport.on('POST', seatPath(MATCH), networkFailure());

    fireEvent.press(screen.getByLabelText(TAKE_IT));

    expect(await screen.findByText(SEAT_WRITE_FAILED)).toBeTruthy();
    expect(dialogs).not.toHaveBeenCalled();
  });

  it('replaces one line rather than stacking two, and holds the second in full', async () => {
    // *Once* is one line at a time: two disappointments stacked would be a list.
    // And the second showing gets the whole hold rather than whatever was left of
    // the first — a sentence that appears and leaves inside a second is a flicker,
    // which is what a line drawn without restarting its own clock would be.
    await launchOnNow(nowOffering(offer(), offer(OTHER, 'Hala Wisła')));
    seatAnswers(seatWrite({ claimed: false, update: full() }));
    transport.on('POST', seatPath(OTHER), () => errorResponse(409, 'match_claim_cooling_down'));

    fireEvent.press(screen.getByLabelText(TAKE_IT));
    await screen.findByText(SEAT_GONE);

    await act(async () => {
      jest.advanceTimersByTime(2_500);
    });

    fireEvent.press(screen.getByLabelText('Take the seat · 38,00 zł, Hala Wisła'));
    const second = await screen.findByText('Give that seat a moment before trying again.');

    expect(second).toBeTruthy();
    expect(screen.queryAllByTestId(TRANSIENT_LINE_ID)).toHaveLength(1);
    expect(screen.queryByText(SEAT_GONE)).toBeNull();

    // Past the moment the *first* line would have ended, and still readable.
    await act(async () => {
      jest.advanceTimersByTime(1_000);
    });
    expect(screen.getByText('Give that seat a moment before trying again.')).toBeTruthy();
  });
});
