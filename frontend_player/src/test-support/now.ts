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
    fit: null,
    emphasis: false,
    act,
    may_depart: mayDepart,
    seat_claim: seatClaimExpiresAt === undefined ? null : { expires_at: seatClaimExpiresAt },
    situation: { situation, facts: { hold: null, cause: null } },
  };
}

export function personCard(playerId: string, nickname: string): Wire['PersonCardResponse'] {
  return { card_type: 'person', player_id: playerId, stamp: 1, nickname };
}

export function clubCard(clubId: string, name: string): Wire['ClubCardResponse'] {
  return { card_type: 'club', club_id: clubId, stamp: 1, name, distance_km: 1.2 };
}

export function shelf(
  code: Wire['ShelfCode'],
  cards: Wire['ShelfResponse']['cards'],
  caption: Wire['CaptionCode'] | null = null,
): Wire['ShelfResponse'] {
  return { code, caption, cards };
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
