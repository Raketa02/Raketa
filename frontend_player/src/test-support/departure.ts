/**
 * The departure route's wire fixtures, typed from the generated schema.
 *
 * The same rule as `now.ts`: a fake response is typed against the contract so a
 * backend shape change fails `pnpm typecheck` rather than a test run, and no test
 * can describe a screen the contract cannot produce.
 *
 * Not app code — nothing under `src/` imports this, so Metro never bundles it.
 */

import { matchCard } from './now';
import type { Transport, Wire } from './transport';
import { json } from './transport';

export function departurePath(matchId: string): string {
  return `/api/v1/matches/${matchId}/departure`;
}

/**
 * One row of the outcome table.
 *
 * `opensAt` is not defaulted from the standing, deliberately: the server sends a
 * moment on exactly one of the four and a builder that filled it in would make the
 * client's refusal to police the pairing untestable.
 */
export function outcomeRow(
  outcome: Wire['Outcome'],
  standing: Wire['OutcomeStanding'],
  opensAt: string | null = null,
): Wire['OutcomeRowResponse'] {
  return { outcome, standing, opens_at: opensAt };
}

/**
 * The four rows an open match past its commitment sends: the free reversal behind
 * her, the full-price search live, and the two tiers ahead of it.
 */
export function committedOutcomes(
  rescueAt: string,
  checkpointAt: string,
): Wire['OutcomeRowResponse'][] {
  return [
    outcomeRow('reversed', 'spent'),
    outcomeRow('refundedInFull', 'searching'),
    outcomeRow('refundedHalf', 'opens', rescueAt),
    outcomeRow('forfeited', 'opens', checkpointAt),
  ];
}

export interface DepartureScreenOptions {
  readonly matchId: string;
  readonly situation?: Wire['Situation'];
  readonly clubName?: string;
  /** Her seat's amount — the figure the outcomes are percentages of. */
  readonly amount?: number;
  readonly mayDepart?: boolean;
  readonly quote?: Wire['Outcome'];
  readonly outcomes?: Wire['OutcomeRowResponse'][];
  readonly counts?: Partial<Wire['SeatCountsResponse']>;
  /** `null` on a private court: there is no commitment for a deadline to be about. */
  readonly commitmentDeadline?: string | null;
  readonly facts?: Partial<Wire['SituationFactsResponse']>;
}

export function departureScreen({
  matchId,
  situation = 'confirmed',
  clubName = 'Sunset Padel',
  amount = 3800,
  mayDepart = true,
  quote = 'refundedInFull',
  outcomes = committedOutcomes('2026-08-23T18:00:00Z', '2026-08-23T20:00:00Z'),
  counts = {},
  commitmentDeadline = '2026-08-23T16:00:00Z',
  facts = {},
}: DepartureScreenOptions): Wire['DepartureScreenResponse'] {
  // The spine and the situation half are the *same* objects `GET /now` sends, so
  // the fixture composes them from the card builder rather than restating them —
  // two definitions of *where and when* in one test-support module is how two
  // fixtures come to describe two different matches under one name.
  const card = matchCard({ matchId, situation, clubName, amount, facts });

  return {
    match_id: matchId,
    clock: null,
    where: card.where,
    price: card.price,
    situation: card.situation,
    may_depart: mayDepart,
    quote,
    outcomes,
    counts: { seats: 4, paid: 2, held: 0, turned_up: null, ...counts },
    commitment_deadline: commitmentDeadline,
  };
}

/** A write's answer: its own screen, Now's update, and what the tap did. */
export function departureWrite(
  screen: Wire['DepartureScreenResponse'],
  card: Wire['MatchCardResponse'],
  applied: Wire['Outcome'] | null,
): Wire['DepartureWriteResponse'] {
  return { screen, update: { update_type: 'card', card }, applied };
}

/** What a leaver who paid carries beside the match's own situation. */
export function leftHavingPaid(
  amount: number,
  outcome: Wire['Outcome'] | null = null,
): Wire['SituationFactsResponse']['departure'] {
  return { form: 'recoverable', paid: { amount, currency: 'PLN' }, outcome };
}

/** A leaver whose money never left — a payload with no field that could hold one. */
export function leftHavingPaidNothing(): Wire['SituationFactsResponse']['departure'] {
  return { form: 'nothingTaken' };
}

export function stubDeparture(transport: Transport, screen: Wire['DepartureScreenResponse']): void {
  transport.on('GET', departurePath(screen.match_id), () => json(screen));
}
