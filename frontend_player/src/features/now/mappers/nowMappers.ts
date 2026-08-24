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
 * it lives in `domain/countdown.ts`; the only things that happen below are
 * renaming, formatting money, and clamping the fit badge to 20–99 — the last two
 * being renderings rather than rules, and the clamp being `ADR-0037`'s own display
 * bound, applied here so that the true score never enters the app at all.
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
  Block,
  ClubCard,
  ComposedScreen,
  Cover,
  DebtLine,
  Door,
  EnrolledRegion,
  MatchCard,
  NowCard,
  NowUpdate,
  OffersRegion,
  PersonCard,
  Place,
  ScoreLine,
  SeatAnswer,
  Shelf,
} from '../domain/ComposedScreen';
import type { FitBadge } from '../domain/fitBadge';
import { MAX_REASONS, clampBadgeScore } from '../domain/fitBadge';

import { actCopy } from './acts';
import { captionCopy } from './captions';
import type { AssertTrue, SportFilter } from './codes';
import { leaverLine } from './departures';
import { doorCopy } from './doors';
import { fitReasonSentence } from './fitReasons';
import { shelfTitle } from './shelves';
import { situationCopy } from './situations';

type NowResponse = components['schemas']['NowResponse'];
type MatchCardResponse = components['schemas']['MatchCardResponse'];
type PersonCardResponse = components['schemas']['PersonCardResponse'];
type ClubCardResponse = components['schemas']['ClubCardResponse'];
type ShelfResponse = components['schemas']['ShelfResponse'];
type ShelvesRegionResponse = components['schemas']['ShelvesRegionResponse'];
type DoorResponse = components['schemas']['DoorResponse'];
type PlaceResponse = components['schemas']['PlaceResponse'];
type MoneyResponse = components['schemas']['MoneyResponse'];
type DebtLineResponse = components['schemas']['DebtLineResponse'];
type FitResponse = components['schemas']['FitResponse'];
type NowUpdateResponse = components['schemas']['NowUpdateResponse'];
type OffersRegionResponse = components['schemas']['OffersRegionResponse'];
type EnrolledRegionResponse = components['schemas']['EnrolledRegionResponse'];
type SeatWriteResponse = components['schemas']['SeatWriteResponse'];
type ScoreLineResponse = components['schemas']['ScoreLineResponse'];

/**
 * Coverage is never a number the player sees, and this is where that stops being a
 * promise (`ADR-0037`).
 *
 * The share of the weight that actually ran ranks the list and gates emphasis, both
 * on the server. If it ever crossed, the field would be one `toFitBadge` line away
 * from a second gauge on the card — so its **absence from the contract** is asserted
 * rather than its absence from this file, and the day it arrives `pnpm typecheck`
 * fails here and somebody has to decide, in a diff, what a player is told with it.
 */
export type CoverageNeverCrosses = AssertTrue<'coverage' extends keyof FitResponse ? false : true>;

/**
 * A shelf's words are the client's, so the wire has no room for them.
 *
 * `ADR-0070` keeps shelf presence and shelf order on the server and leaves the
 * title here. A `title` arriving on `ShelfResponse` would make `SHELF_COPY` the
 * second opinion rather than the only one, and the two would disagree in whichever
 * language shipped last.
 */
export type NoTitleCrosses = AssertTrue<'title' extends keyof ShelfResponse ? false : true>;

/**
 * @param sport the chip the request carried, which is the one thing the door's
 * block does not repeat. Passing it here rather than resolving the door's words
 * in a component is this app's rule that **a component never holds a table**: the
 * sport is an input to the copy, not a second place the copy is decided.
 */
export function toComposedScreen(wire: NowResponse, sport: SportFilter): ComposedScreen {
  return {
    offers: toOffersRegion(wire.offers),
    yourMatches: toEnrolledRegion(wire.your_matches),
    shelves: { blocks: wire.shelves.shelves.map((block) => toBlock(block, sport)) },
    debt: wire.debt == null ? undefined : toDebtLine(wire.debt),
  };
}

/**
 * Both viewer-owned regions are cards and an order, and nothing else.
 *
 * Two one-line functions rather than two inline `map`s because a **second**
 * producer of a whole region landed with the seat write: a compose and an
 * accepted offer both build these, and two transcriptions of *a region is its
 * cards* is how the two come to disagree about what one is. The `stamp` beside
 * them on the wire is not read here — nothing in the client reads a stamp yet,
 * and mapping one would be a field kept warm for a race nobody has written.
 */
function toOffersRegion(wire: OffersRegionResponse): OffersRegion {
  return { cards: wire.cards.map(toMatchCard) };
}

function toEnrolledRegion(wire: EnrolledRegionResponse): EnrolledRegion {
  return { cards: wire.cards.map(toMatchCard) };
}

/**
 * What taking a seat answered (`ADR-0070`, `ADR-0074`).
 *
 * **`claimed` is read and never derived.** It is the server's statement about the
 * command, and the client's one self-written sentence — *that seat has gone* —
 * hangs off it. Deriving it from a seat claim appearing on the card, or from the
 * regions arriving, would be a rule the phone holds (`ADR-0053`) and would put
 * the wrong sentence on the screen the first time the two disagreed.
 *
 * **The two regions are one field, and it is `undefined` unless both arrived.**
 * The server sends both or neither — *a tap that applied moved a card from one
 * region to the other, and a tap that did not moved nothing* — so half an answer
 * is treated as none: keeping the regions the screen already holds and correcting
 * the one card in place is the direction this can fail in without a region going
 * blank under her thumb.
 */
export function toSeatAnswer(wire: SeatWriteResponse): SeatAnswer {
  const offers = wire.offers;
  const yourMatches = wire.your_matches;

  return {
    claimed: wire.claimed,
    update: toNowUpdate(wire.update),
    regions:
      offers == null || yourMatches == null
        ? undefined
        : { offers: toOffersRegion(offers), yourMatches: toEnrolledRegion(yourMatches) },
  };
}

/**
 * What an action off Now hands back so the screen corrects itself (`ADR-0074`).
 *
 * **One card in one of two forms, and the same `toMatchCard` a compose runs
 * through**, so a card arriving from an action and the same card arriving from a
 * compose cannot be rendered by two different expressions. There is no shelf
 * here and no region, and the type is what says so: an update carrying a `Shelf`
 * would be a match moving under her thumb, and `Shelf` can only be constructed
 * in this module.
 *
 * **The two forms are narrowed on the wire's own discriminator** and never on
 * the presence of a card. `ADR-0087`'s *gone* has no card at all, so a phone
 * testing for one would be reading the absence of a field as a meaning — which
 * is the blank `ADR-0072` refuses one shape over.
 */
export function toNowUpdate(wire: NowUpdateResponse): NowUpdate {
  switch (wire.update_type) {
    case 'card':
      return { kind: 'card', card: toMatchCard(wire.card) };
    case 'gone':
      return { kind: 'gone', matchId: wire.match_id };
  }
}

/**
 * A shelf or a door, discriminated by the wire's own `block_type`.
 *
 * **This is the only place a door is ever made**, which is the whole of
 * `ADR-0084`'s negative rule: the phone never concludes *the ranked shelves are
 * missing, therefore she is unrated*. That inference is wrong on any day the city
 * genuinely has nothing in a sport she is rated at, and there is nowhere else in
 * this feature it could be written, because nothing else constructs the type.
 */
function toBlock(block: ShelvesRegionResponse['shelves'][number], sport: SportFilter): Block {
  switch (block.block_type) {
    case 'shelf':
      return toShelf(block);
    case 'door':
      return toDoor(block, sport);
  }
}

function toDoor(wire: DoorResponse, sport: SportFilter): Door {
  return { kind: 'door', code: wire.code, copy: doorCopy(wire.code, { sport }) };
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
    kind: 'shelf',
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
    fit: wire.fit == null ? undefined : toFitBadge(wire.fit),
    // The composed screen's flag, carried across untouched. Nothing here reads the
    // score beside it: a client that recomputed emphasis would light up every 90 on
    // the board, which is the measured 4,3 % of scores `ADR-0037` was written about.
    emphasis: wire.emphasis,
    // The card's own facts, plus the two spine values a sentence may print. The
    // spine is drawn by every phone whether or not it can name the situation, so a
    // sentence built from it degrades to nothing worse than silence.
    status: situationCopy(wire.situation.situation, {
      facts: wire.situation.facts,
      clubName: where.clubName,
      price: money,
    }),
    // Present exactly for a viewer who has left, which is what makes this card
    // *rendered for a leaver* rather than the same card with a flag on it. The
    // situation above is untouched: an audience changes a card's words and never
    // its situation (`ADR-0072`).
    departure: leaverLine(wire.situation.facts.departure),
    // The score exactly as it was sent, sides and sets in the order they arrived.
    // Whose 6 it is has already been decided by the server putting the viewer's
    // side first, and re-deciding it here would be the second answer to that
    // question `ADR-0060` names the sides to prevent.
    score: wire.situation.facts.score == null ? undefined : toScoreLine(wire.situation.facts.score),
  };
}

/**
 * The score, carried across and never rearranged.
 *
 * The two `map`s are renamings and nothing else — `first` is `sides[0]`'s games,
 * which is the wire's own statement about the pair. Nothing sums a set, compares
 * two, or works out who won: who won is not a fact the phone was sent, and a
 * client that computed it would be the level movement `ADR-0049` refuses arriving
 * through the back door.
 */
function toScoreLine(wire: ScoreLineResponse): ScoreLine {
  return {
    sides: wire.sides.map((side) => ({ players: side.players })),
    sets: wire.sets.map((set) => ({ first: set.first, second: set.second })),
  };
}

/**
 * The badge: one clamped number, one boolean, and at most three sentences.
 *
 * **The clamp is here and not in the component**, so the true score never enters
 * this app and no later reader can print an unclamped one by reaching past
 * whatever clamped. `ADR-0037` calls it a display rule, and a display rule applied
 * once at the boundary is the version that cannot be applied twice or not at all.
 *
 * **A term this build has never heard of is dropped rather than drawn blank**, the
 * same answer an unknown situation gets. A card with two reasons instead of three
 * has lost the thing that is actually missing; a card with an empty bullet has
 * gained a defect. The badge itself is unaffected, because the number is the claim
 * and the reasons are the support.
 *
 * **`target` is not read.** It is the Level the match is aimed at and crosses only
 * when precise, and no card draws it — mapping it here with nothing to render it
 * would be a field kept warm for a screen that does not exist.
 */
function toFitBadge(wire: FitResponse): FitBadge {
  return {
    score: clampBadgeScore(wire.score),
    unsure: wire.unsure,
    reasons: wire.reasons
      .slice(0, MAX_REASONS)
      .map(fitReasonSentence)
      .filter((sentence): sentence is string => sentence !== undefined),
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
