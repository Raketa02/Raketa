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
 * `ChallengeSchema` carries the sport, the mode, the window and the deadlines, and nothing
 * draws any of them yet: the one reader today is the pair rule's naming
 * (`domain/challenge.ts`). Mapping the rest would be a DTO nobody is checking — the argument
 * `fillSeats` made about the prompts a line-up raises, right up until those prompts gained a
 * reader and stopped being a list nothing read
 * ([#287](https://github.com/Raketa02/Raketa/issues/287)). Which is the shape of the answer
 * here too: these fields are mapped by the ticket that draws them.
 */

import type { components } from '@/generated/schema';

import type { Challenge, ChallengeSeat } from '../domain/challenge';

type SendChallengeRequest = components['schemas']['SendChallengeRequest'];
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
  return {
    search_id: send.searchId,
    court: send.court.map((playerId, at) => ({
      side: sideAt(at, send.court.length),
      // Omitted rather than `null` on an empty seat: the field is optional, and the two mean
      // the same thing to the route.
      ...(playerId === undefined ? {} : { player_id: playerId }),
    })),
  };
}

/** Your challenges, newest first — the list a refused send re-reads to find a name. */
export function toChallenges(response: ChallengeListResponse): readonly Challenge[] {
  return response.challenges.map((one) => ({
    challengeId: one.challenge_id,
    organiserId: one.organiser_id,
    standing: one.standing,
    seats: one.seats.map(toSeat),
  }));
}

function toSeat(seat: components['schemas']['SeatSchema']): ChallengeSeat {
  return {
    ...(seat.player_id == null ? {} : { playerId: seat.player_id }),
    ...(seat.answer == null ? {} : { answer: seat.answer }),
  };
}
