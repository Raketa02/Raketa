/**
 * Your own *Let's play* yeses, narrowed to the three numbers the deck draws from them.
 *
 * `GET /interest` answers with three lists — outgoing, mutual, and where each sport stands
 * against its cap — and the deck reads **one** of them: `outstanding`, per sport, whole.
 *
 * ## Why the count is the outstanding one and not a length
 *
 * *"Outstanding means sent, unexpired and not yet mutual"*, which is exactly the fact the
 * deck's counter subtracts from the cap: yeses of yours that nobody has answered. Counting
 * `outgoing` instead would be this app re-deriving a number the contract already publishes,
 * off a list whose lapsing rule — *"on expiry the row is simply gone"* — is the server's clock
 * rather than the phone's.
 *
 * ## The cap and the life of a yes cross beside it, and neither is held here
 *
 * The cap was deferred for as long as nothing drew it — *"the day it does, the pair arrives
 * together, because a count shown against no cap is the half of it that cannot be acted on"*.
 * That day is the counter's *N yeses to give*
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §5): `cap − outstanding`, both off this read, and the mapper stops dropping the cap. `ttl_days`
 * arrived on the same rows so the ending can say *your yeses stay live for 21 days* without the
 * client holding the number — ADR-0127 §6's rule kept by making the number cross rather than by
 * this app knowing it. **Read them from here, never hardcode them**: both are ruleset
 * configuration and may move between releases.
 *
 * **The rows themselves stop here.** A `player_id` and an `expires_at` are *You*'s screen, not
 * Play's, and a mapper that carried them would be a list nothing draws.
 */

import type { components } from '@/generated/schema';
import { toSport } from '@/features/onboarding/types';
import type { Sport } from '@/shared/vocabulary/sport';

import type { InterestStanding } from '../domain/yesBudget';

type InterestListResponse = components['schemas']['InterestListResponse'];
type OutstandingSchema = components['schemas']['OutstandingSchema'];

/**
 * Where one sport stands: the count, the cap in force, and how many days a yes there lives.
 *
 * `InterestStanding` is the pair the counter's arithmetic reads; `ttlDays` rides beside it for
 * the one sentence that prints it.
 */
export interface SportInterest extends InterestStanding {
  readonly ttlDays: number;
}

/**
 * Where every sport stands, per sport.
 *
 * **Partial by design.** An absent sport is *nothing outstanding there*, which is what the
 * route means by not sending a row — and a sport this build cannot name takes its own key out
 * with it, exactly as the declaration map does.
 */
export type OutstandingInterest = Readonly<Partial<Record<Sport, SportInterest>>>;

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
  const standing: Partial<Record<Sport, SportInterest>> = {};
  for (const row of rows) {
    const sport = toSport(row.sport);
    if (sport === undefined) continue;
    standing[sport] = { outstanding: row.outstanding, cap: row.cap, ttlDays: row.ttl_days };
  }
  return standing;
}
