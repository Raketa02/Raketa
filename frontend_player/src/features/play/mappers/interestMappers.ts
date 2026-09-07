/**
 * Your own *Let's play* yeses, narrowed to the one number Play draws from them.
 *
 * `GET /interest` answers with three lists — outgoing, mutual, and where each sport stands
 * against its cap — and the Play tab reads **one** of them: `outstanding`, per sport.
 *
 * ## Why the count is the outstanding one and not a length
 *
 * *"Outstanding means sent, unexpired and not yet mutual"*, which is exactly the fact the
 * deck's empty state and the segment both state: yeses of yours that nobody has answered.
 * Counting `outgoing` instead would be this app re-deriving a number the contract already
 * publishes, off a list whose lapsing rule — *"on expiry the row is simply gone"* — is the
 * server's clock rather than the phone's.
 *
 * **The cap is not carried, and that is a deferral rather than a refusal.** It travels
 * *"before you are near either — a cap you cannot see is a refusal you cannot predict"*, and
 * the surface that owes a player that sentence is the one that refuses a yes for hitting it.
 * The deck does not draw it today; the day it does, the pair arrives together, because a count
 * shown against no cap is the half of it that cannot be acted on.
 *
 * **The rows themselves stop here.** A `player_id` and an `expires_at` are *You*'s screen, not
 * Play's, and a mapper that carried them would be a list nothing draws.
 */

import type { components } from '@/generated/schema';
import { toSport } from '@/features/onboarding/types';
import type { Sport } from '@/shared/vocabulary/sport';

type InterestListResponse = components['schemas']['InterestListResponse'];
type OutstandingSchema = components['schemas']['OutstandingSchema'];

/**
 * How many yeses of yours are still standing, per sport.
 *
 * **Partial by design.** An absent sport is *nothing outstanding there*, which is what the
 * route means by not sending a row — and a sport this build cannot name takes its own key out
 * with it, exactly as the declaration map does.
 */
export type OutstandingInterest = Readonly<Partial<Record<Sport, number>>>;

export function toOutstandingInterest(response: InterestListResponse): OutstandingInterest {
  return fromRows(response.outstanding);
}

/**
 * The same shape out of a single tap's answer — *"where this sport now stands, after this
 * tap"*.
 *
 * The response carries the new count, so saying yes updates the number without a second
 * round trip: Part 7's *"prefer response-driven updates; don't immediately refetch what you
 * were just handed"*, on the one number in this tab that moves while a player is looking at
 * it.
 */
export function toOutstandingAfterTap(outstanding: OutstandingSchema): OutstandingInterest {
  return fromRows([outstanding]);
}

function fromRows(rows: readonly OutstandingSchema[]): OutstandingInterest {
  const standing: Partial<Record<Sport, number>> = {};
  for (const row of rows) {
    const sport = toSport(row.sport);
    if (sport === undefined) continue;
    standing[sport] = row.outstanding;
  }
  return standing;
}
