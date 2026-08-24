/**
 * Now's wire fixtures, typed from the generated schema.
 *
 * The same rule as `transport.ts`: a fake response is typed against the contract
 * so that a backend shape change fails `pnpm typecheck` rather than failing a test
 * run with a confusing assertion, and no test can describe a screen the contract
 * cannot produce.
 *
 * Not app code — nothing under `src/` imports this, so Metro never bundles it.
 */

import type { Transport, Wire } from './transport';
import { json } from './transport';

export const NOW_PATH = '/api/v1/now';

/** `GET /api/v1/now?sport=all`, the path the screen asks for on arrival. */
export function nowPathFor(sport: Wire['SportFilter']): string {
  return `${NOW_PATH}?sport=${sport}`;
}

/**
 * The three regions, present and empty — a player with nothing.
 *
 * The stamps are the region stamps `ADR-0070` requires; nothing in the client
 * reads one yet (the update race arrives with `Raketa02/Raketa#79`–`#81`), and
 * they are here because the contract carries them.
 */
export function emptyNow(): Wire['NowResponse'] {
  return {
    offers: { stamp: 1, cards: [] },
    your_matches: { stamp: 1, cards: [] },
    shelves: { stamp: 1, shelves: [] },
    debt: null,
  };
}

export interface MatchCardOptions {
  readonly matchId: string;
  readonly situation?: Wire['Situation'];
  readonly clock?: string | null;
  readonly clubName?: string;
  readonly amount?: number;
  readonly seatClaimExpiresAt?: string;
  /**
   * The one act the card names, from the **spine** — never derived from the
   * situation. A fixture that set it from `situation` would make the client's
   * refusal to derive it untestable.
   */
  readonly act?: Wire['ActCode'] | null;
  /** `ADR-0086`'s spine boolean: whether this viewer may leave. */
  readonly mayDepart?: boolean;
  /**
   * The situation half's facts, over the two every card carries.
   *
   * `counts` and `court_total` are **required on the wire** — counting is by
   * money and every card counts, and the court's total is the one money line
   * with no audience at all — so a builder that let them be left out would
   * build a card the server cannot compose.
   */
  readonly facts?: Partial<Wire['SituationFactsResponse']>;
  /**
   * The badge, or `null` for a card the server did not score — every card in the
   * strip, and every card on a screen that degraded.
   */
  readonly fit?: Wire['FitResponse'] | null;
  /**
   * `ADR-0037`'s one-card-per-screen flag, which is the **composed screen's** and
   * never a comparison against the score beside it. A fixture setting it from `fit`
   * would make the client's refusal to derive it untestable.
   */
  readonly emphasis?: boolean;
}

/** One reason behind the badge: a term code and the payload that term carries. */
export function fitReason(
  code: Wire['TermCode'],
  fact: Wire['FitReasonResponse']['fact'],
): Wire['FitReasonResponse'] {
  return { code, fact };
}

/** The badge as the ranked funnel composes one: a score, a warning and its reasons. */
export function fit({
  score,
  unsure = false,
  reasons = [fitReason('time_fit', { code: 'time_fit', weekday: 2, minute: 1140 })],
  target = null,
}: {
  readonly score: number;
  readonly unsure?: boolean;
  readonly reasons?: Wire['FitReasonResponse'][];
  readonly target?: number | null;
}): Wire['FitResponse'] {
  return { score, unsure, reasons, target };
}

export function matchCard({
  matchId,
  situation = 'forming',
  clock = null,
  clubName = 'Sunset Padel',
  amount = 3800,
  seatClaimExpiresAt,
  act = null,
  mayDepart = false,
  facts = {},
  fit = null,
  emphasis = false,
}: MatchCardOptions): Wire['MatchCardResponse'] {
  return {
    card_type: 'match',
    match_id: matchId,
    stamp: 1,
    clock,
    where: {
      club_id: '9f1b0000-0000-4000-8000-000000000001',
      club_name: clubName,
      zone: 'Europe/Warsaw',
      cover: 'indoor',
      distance_km: 2.4,
    },
    price: { amount, currency: 'PLN' },
    fit,
    emphasis,
    act,
    may_depart: mayDepart,
    seat_claim: seatClaimExpiresAt === undefined ? null : { expires_at: seatClaimExpiresAt },
    situation: {
      situation,
      facts: {
        counts: { seats: 4, paid: 2, held: 0, turned_up: null },
        court_total: { amount: amount * 4, currency: 'PLN' },
        hold: null,
        cause: null,
        ...facts,
      },
    },
  };
}

export function personCard(
  playerId: string,
  nickname: string,
  level: Wire['LevelResponse'] = { value: 2.7, provisional: true },
): Wire['PersonCardResponse'] {
  return { card_type: 'person', player_id: playerId, stamp: 1, nickname, level };
}

export function clubCard(clubId: string, name: string): Wire['ClubCardResponse'] {
  return { card_type: 'club', club_id: clubId, stamp: 1, name, distance_km: 1.2 };
}

/** The door into a sport this viewer holds no rating at (`ADR-0084`). */
export function door(code: Wire['DoorCode']): Wire['DoorResponse'] {
  return { block_type: 'door', code };
}

export function shelf(
  code: Wire['ShelfCode'],
  cards: Wire['ShelfResponse']['cards'],
  caption: Wire['CaptionCode'] | null = null,
): Wire['ShelfResponse'] {
  return { block_type: 'shelf', code, caption, cards };
}

/**
 * Answer `GET /api/v1/now` for one sport.
 *
 * Per sport, because the sport rides on the request and a switch is a **new
 * request** rather than a filter over a payload holding every sport — so a test
 * that asserts the filter reached the server does it by stubbing a second path
 * and reading what came back.
 */
export function stubNow(
  transport: Transport,
  body: Wire['NowResponse'] = emptyNow(),
  sport: Wire['SportFilter'] = 'all',
): void {
  transport.on('GET', nowPathFor(sport), () => json(body));
}

/** `POST /api/v1/matches/{id}/seat?sport=…`, the address the offer card's act writes to. */
export function seatPath(matchId: string, sport: Wire['SportFilter'] = 'all'): string {
  return `/api/v1/matches/${matchId}/seat?sport=${sport}`;
}

/**
 * What taking a seat answered.
 *
 * `claimed` and the two regions are **separate arguments**, although the server
 * sends the regions exactly when the tap applied: a fixture that derived one from
 * the other could not describe the answer the client is required to survive — a
 * claim whose regions did not arrive — and would make the client's refusal to
 * derive *was I refused* from them untestable.
 */
export function seatWrite({
  claimed,
  update,
  offers = null,
  yourMatches = null,
}: {
  readonly claimed: boolean;
  readonly update: Wire['MatchCardResponse'];
  readonly offers?: Wire['MatchCardResponse'][] | null;
  readonly yourMatches?: Wire['MatchCardResponse'][] | null;
}): Wire['SeatWriteResponse'] {
  return {
    claimed,
    update: { update_type: 'card', card: update },
    offers: offers === null ? null : { stamp: 2, cards: offers },
    your_matches: yourMatches === null ? null : { stamp: 2, cards: yourMatches },
  };
}

/** A screen holding one offer and nothing else — the shape a race starts from. */
export function nowOffering(...cards: Wire['MatchCardResponse'][]): Wire['NowResponse'] {
  return { ...emptyNow(), offers: { stamp: 1, cards } };
}

/** `DELETE /api/v1/matches/{id}/standby`, the address the queue card's act writes to. */
export function standbyPath(matchId: string): string {
  return `/api/v1/matches/${matchId}/standby`;
}

/**
 * What leaving standby answered: the update, and nothing beside it.
 *
 * The **gone** form by default, because that is what this act produces — a queue
 * place is the whole of what put the match on her strip, so the card goes with it.
 * The other form is reachable from here on purpose: an answer that came back
 * *changed* must not be read as *gone* by a client that assumed the act's usual
 * shape, and a fixture that could not describe it could not test that.
 */
export function standbyWrite(
  update: Wire['StandbyWriteResponse']['update'],
): Wire['StandbyWriteResponse'] {
  return { update };
}

/** The card is off her screen: the one form of the update that shortens a region. */
export function cardGone(matchId: string): Wire['NowUpdateResponse'] {
  return { update_type: 'gone', match_id: matchId };
}

/** The card is still on her screen, recomposed: the form every other act answers with. */
export function cardChanged(card: Wire['MatchCardResponse']): Wire['NowUpdateResponse'] {
  return { update_type: 'card', card };
}

/**
 * What she owes, and whether it costs her anything (`ADR-0070`).
 *
 * Present on the envelope exactly when something is owed — *"absent when there is
 * nothing owed, rather than present at zero"* — so a fixture that wanted *no debt*
 * leaves it `null` rather than passing zero here.
 */
export function debt(amount: number, blocked: boolean): Wire['DebtLineResponse'] {
  return { owed: { amount, currency: 'PLN' }, blocked };
}
