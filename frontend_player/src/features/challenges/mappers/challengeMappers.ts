/**
 * The two shapes that cross on `challenges`' own routes: **a court going out, and a list of
 * challenges coming back.**
 *
 * One of the two layers allowed to read generated types, and the only place either shape is
 * turned into words this app owns.
 *
 * ## A court is a list of sides, and the sides are the sport's
 *
 * `SendChallengeRequest.court` is *"the sides as you arranged them, in the court's own order:
 * every **A** seat, then every **B**"*, and the backend checks that list against
 * `court_sides(sport)` rather than counting it — *"a court whose sides arrive in some caller's
 * order could not answer* which side is short *the same way twice"*. So the side is **derived
 * from the position** and never carried on the seating: the builder's court already draws its
 * seats in that order, `theme.size.court.seats` lists them *your side first*, and
 * `seatPlaces` reads a half off exactly this arithmetic.
 *
 * **The organiser is in the list like anybody else**, and on either side. `Side`'s docstring
 * says the organiser is always on `A`, but the aggregate checks only the sequence — and swap
 * mode is *change sides, never seats*, so a player who moved themselves across the net sends a
 * court with their own id in the `B` half. Refusing that here would be this client inventing a
 * rule the route does not have.
 *
 * **An empty seat is a seat.** It keeps its place with nobody in it, because *which side is
 * short* is part of what a court is — and dropping it would renumber every seat behind it.
 *
 * ## Coming back, only what has a reader
 *
 * `ChallengeSchema` carried fields nothing drew, and *"these fields are mapped by the ticket
 * that draws them"* was the rule. The Chats inbox is that ticket
 * ([#360](https://github.com/Raketa02/Raketa/issues/360)): the row prints a sport, sorts on
 * `opened_at`, names a person from a seat's `name` and folds a duration from that seat's
 * `answer_by` — so those four arrive, and `mode` and `window` stay unmapped, because still
 * nothing draws them.
 *
 * **`read_at` is copied onto each challenge**, exactly as `gameMappers` copies
 * `GameListResponse`'s: it is one instant for the whole list, and carrying it per row is what
 * makes it impossible for a component to render a countdown against a clock the standing beside
 * it never saw (ADR-0143 §7).
 *
 * ## `null` is *this response said nothing*, and it collapses to absent
 *
 * Every optional on this wire arrives as `T | null | undefined` and every one becomes
 * `undefined` here, so no screen has two spellings of one absence to branch on.
 *
 * ## Two codes are narrowed, and they are narrowed differently
 *
 * A **standing** this build cannot read becomes `undefined` and the challenge stays: the code
 * *is* the whole line, so `the-words.md` §3 owes it a named gap rather than a drop. A **sport**
 * it cannot read takes the whole challenge with it, which is `gameMappers`' own rule for the
 * same field: the sport is what the row calls the game, and a challenge this app cannot name
 * the sport of is a row with a hole where the identifying fact goes.
 */

import type { components } from '@/generated/schema';
import { toSport } from '@/features/onboarding/types';

import type { Challenge, ChallengeSeat } from '../domain/challenge';
import { STANDINGS, type Standing } from '../domain/standing';

type SendChallengeRequest = components['schemas']['SendChallengeRequest'];
type FillSeatsRequest = components['schemas']['FillSeatsRequest'];
type SeatChoiceSchema = components['schemas']['SeatChoiceSchema'];
type ChallengeListResponse = components['schemas']['ChallengeListResponse'];

/**
 * The court a send carries: **one entry per seat, in the court's own order**, holding the
 * player in it or nobody.
 *
 * Your own seat is in it. A court that left the organiser out is refused with
 * `organiser_holds_a_seat`, and it would be a different arrangement from the one on screen.
 */
export type ProposedCourt = readonly (string | undefined)[];

/**
 * Which half of the court a seat is in — every **A**, then every **B**.
 *
 * `Math.ceil` rather than a sport lookup: the shape is checked server-side against the sport
 * the *search* names, and a second table of *how many play this* on this side is a second
 * place for it to be true. An odd length cannot be a court and is refused there, by the one
 * check that knows which sport it was.
 */
function sideAt(seat: number, seats: number): SeatChoiceSchema['side'] {
  return seat < Math.ceil(seats / 2) ? 'A' : 'B';
}

export function toSendChallengeRequest(send: {
  readonly searchId: string;
  readonly court: ProposedCourt;
}): SendChallengeRequest {
  return { search_id: send.searchId, court: toSeatChoices(send.court) };
}

/**
 * **The send's shape minus the mint** — the fill, on `POST /challenges/{id}/seats`.
 *
 * The challenge is in the path, so the body is the two things a fill has to say and the two the
 * send says: the court as it will stand, and the search behind it. The seats are the send's own
 * — the same list, the same order, the same side arithmetic — because *"an acceptance is to the
 * game and not to the side"* and what crosses is the **whole** arrangement rather than the seats
 * being filled ([ADR-0150](../../../../../docs/adr/0150-the-fill-names-the-challenge-it-completes-and-the-gate-steps-aside.md) §6).
 *
 * A second body shape with one field fewer, sharing `toSeatChoices`, rather than one function
 * with an optional challenge: the two go to different routes and a caller that could send either
 * would be one edit away from minting a second challenge where it meant to grow one.
 */
export function toFillSeatsRequest(fill: {
  readonly searchId: string;
  readonly court: ProposedCourt;
}): FillSeatsRequest {
  return { search_id: fill.searchId, court: toSeatChoices(fill.court) };
}

/** One entry per seat, the side derived from the position — see the module note. */
function toSeatChoices(court: ProposedCourt): SeatChoiceSchema[] {
  return court.map((playerId, at) => ({
    side: sideAt(at, court.length),
    // Omitted rather than `null` on an empty seat: the field is optional, and the two mean
    // the same thing to the route.
    ...(playerId === undefined ? {} : { player_id: playerId }),
  }));
}

/**
 * The standing, or nothing where the server sent a code this build has no words for.
 *
 * A membership test against `domain/standing.ts`'s own list rather than a third table beside
 * `ENDED` and `STILL_BEING_ARRANGED`: those two are **rules** keyed by the union, and this is
 * only asking whether the union contains a value. The `Exact` assertion in `wireVocabulary.ts`
 * holds the two unions equal at **build** time; a phone running last month's binary against
 * this month's server is the case it cannot cover, and `the-words.md` §3 is written for exactly
 * that phone.
 */
function toStanding(wire: Standing): Standing | undefined {
  return STANDINGS.some((known) => known === wire) ? wire : undefined;
}

/** Your challenges, newest first — the inbox's list, and the one a refused send re-reads. */
export function toChallenges(response: ChallengeListResponse): readonly Challenge[] {
  return response.challenges.flatMap((one) => {
    const sport = toSport(one.sport);
    if (sport === undefined) return [];

    const standing = toStanding(one.standing);

    return [
      {
        challengeId: one.challenge_id,
        organiserId: one.organiser_id,
        ...(standing === undefined ? {} : { standing }),
        sport,
        openedAt: one.opened_at,
        ...(one.ended_at == null ? {} : { endedAt: one.ended_at }),
        ...(one.ended_by == null ? {} : { endedBy: one.ended_by }),
        ...(one.game_id == null ? {} : { gameId: one.game_id }),
        readAt: response.read_at,
        seats: one.seats.map(toSeat),
      },
    ];
  });
}

function toSeat(seat: components['schemas']['SeatSchema']): ChallengeSeat {
  return {
    ...(seat.player_id == null ? {} : { playerId: seat.player_id }),
    ...(seat.answer == null ? {} : { answer: seat.answer }),
    ...(seat.name == null ? {} : { name: seat.name }),
    ...(seat.answer_by == null ? {} : { answerBy: seat.answer_by }),
  };
}
