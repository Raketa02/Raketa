/**
 * The wire's composed screen, mapped into this feature's vocabulary.
 *
 * One of the two layers allowed to read generated types, and the layer that turns
 * a **code into a sentence**. That is the shape of the whole file: the copy tables
 * beside it are keyed on the generated unions (`ADR-0075`), so resolving a
 * situation, a shelf title or a caption here is what keeps `@/generated` out of
 * every component — and what makes the "unknown name" path a value (`undefined`)
 * rather than a branch a screen has to remember to write.
 *
 * **Nothing is computed.** No total, no count, no comparison against the clock, no
 * inference from an absent field. `ADR-0053` leaves the phone one derivation and
 * it lives in `domain/countdown.ts`; the only thing that happens below is
 * renaming, and formatting money, which is a rendering rather than a rule.
 *
 * **A widened wire union fails here first.** `Cover` and `Currency` are assigned
 * into narrower types this app owns, so a third cover or a second currency is a
 * `pnpm typecheck` failure in this file — the diff where somebody has to decide
 * what an outdoor-with-a-roof court looks like, rather than a card that renders
 * a blank.
 */

import type { components } from '@/generated/schema';
import type { Currency, Money } from '@/shared/lib/formatting';
import { formatMoney } from '@/shared/lib/formatting';

import type {
  ClubCard,
  Cover,
  DebtLine,
  MatchCard,
  NowCard,
  ComposedScreen,
  PersonCard,
  Place,
  Shelf,
} from '../domain/ComposedScreen';

import { actCopy } from './acts';
import { captionCopy } from './captions';
import { shelfTitle } from './shelves';
import { situationCopy } from './situations';

type NowResponse = components['schemas']['NowResponse'];
type MatchCardResponse = components['schemas']['MatchCardResponse'];
type PersonCardResponse = components['schemas']['PersonCardResponse'];
type ClubCardResponse = components['schemas']['ClubCardResponse'];
type ShelfResponse = components['schemas']['ShelfResponse'];
type ShelvesRegionResponse = components['schemas']['ShelvesRegionResponse'];
type PlaceResponse = components['schemas']['PlaceResponse'];
type MoneyResponse = components['schemas']['MoneyResponse'];
type DebtLineResponse = components['schemas']['DebtLineResponse'];

export function toComposedScreen(wire: NowResponse): ComposedScreen {
  return {
    offers: { cards: wire.offers.cards.map(toMatchCard) },
    yourMatches: { cards: wire.your_matches.cards.map(toMatchCard) },
    shelves: { shelves: wire.shelves.shelves.filter(isShelf).map(toShelf) },
    debt: wire.debt == null ? undefined : toDebtLine(wire.debt),
  };
}

/**
 * The shelves list also carries the **door** into an unrated sport's
 * questionnaire, and this build draws nothing for it (`Raketa02/Raketa#94`).
 *
 * Dropped rather than mapped to a blank row: `ADR-0084` puts the door in the
 * list precisely so that a build which has never heard of it loses one entry
 * from a list it already iterates. Until #94 lands, tapping a chip for a sport
 * this player holds no rating at renders the two light shelves and no ask —
 * which is the failure that ADR names as the cost of shipping the block first,
 * and it is bounded by one client release.
 */
function isShelf(block: ShelvesRegionResponse['shelves'][number]): block is ShelfResponse {
  return block.block_type === 'shelf';
}

/**
 * A shelf's words come from its code and never from the wire.
 *
 * An unrecognised code leaves `title` undefined, which is the same answer as *do
 * not draw this shelf's heading* — a shelf whose claim this build cannot state is
 * a row of cards under a blank line, and the blank line is the part that is wrong.
 */
function toShelf(wire: ShelfResponse): Shelf {
  return {
    code: wire.code,
    title: shelfTitle(wire.code),
    caption: wire.caption == null ? undefined : captionCopy(wire.caption),
    cards: wire.cards.map(toCard),
  };
}

function toCard(wire: ShelfResponse['cards'][number]): NowCard {
  switch (wire.card_type) {
    case 'match':
      return toMatchCard(wire);
    case 'person':
      return toPersonCard(wire);
    case 'club':
      return toClubCard(wire);
  }
}

function toMatchCard(wire: MatchCardResponse): MatchCard {
  const price = toMoney(wire.price);
  const where = toPlace(wire.where);
  const money = formatMoney(price);

  return {
    kind: 'match',
    matchId: wire.match_id,
    clock: wire.clock ?? undefined,
    claimExpiresAt: wire.seat_claim?.expires_at ?? undefined,
    where,
    price,
    situation: wire.situation.situation,
    // The act arrives as a code and leaves as a label and a destination. It is
    // read off the **spine** and never off the situation: the server decides
    // whether a control exists and this layer decides only what it says, which is
    // the line `ADR-0088` draws. A code this build cannot resolve is `undefined`
    // — the same answer as no act, and the same drawing.
    act: wire.act == null ? undefined : actCopy(wire.act, { price: money }),
    mayDepart: wire.may_depart,
    // The card's own facts, plus the two spine values a sentence may print. The
    // spine is drawn by every phone whether or not it can name the situation, so a
    // sentence built from it degrades to nothing worse than silence.
    status: situationCopy(wire.situation.situation, {
      facts: wire.situation.facts,
      clubName: where.clubName,
      price: money,
    }),
  };
}

function toPersonCard(wire: PersonCardResponse): PersonCard {
  return { kind: 'person', playerId: wire.player_id, nickname: wire.nickname };
}

function toClubCard(wire: ClubCardResponse): ClubCard {
  return {
    kind: 'club',
    clubId: wire.club_id,
    name: wire.name,
    distanceKm: wire.distance_km ?? undefined,
  };
}

function toPlace(wire: PlaceResponse): Place {
  const cover: Cover = wire.cover;

  return {
    clubId: wire.club_id,
    clubName: wire.club_name,
    zone: wire.zone,
    cover,
    distanceKm: wire.distance_km ?? undefined,
  };
}

function toMoney(wire: MoneyResponse): Money {
  const currency: Currency = wire.currency;
  return { amount: wire.amount, currency };
}

function toDebtLine(wire: DebtLineResponse): DebtLine {
  return { owed: toMoney(wire.owed), blocked: wire.blocked };
}
