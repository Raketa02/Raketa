/**
 * Your own *Let's play* yeses — where each sport stands against its cap, and who you said it to.
 *
 * `GET /interest` answers with three lists — outgoing, mutual, and where each sport stands
 * against its cap — and this reads **two** of them: `outstanding`, per sport, whole, and
 * `outgoing` narrowed to **ids per sport**.
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
 * ## The outgoing rows cross as ids, and so do the mutual rows — under their own name
 *
 * The rows themselves stopped at this boundary for as long as nothing drew them — *a
 * `player_id` and an `expires_at` are You's screen, not Play's*. ADR-0169 §8 gave the ids one
 * reader: **You said yes**, a tag on the builder's cards and a line on the challenge screen,
 * drawn wherever the person on the card is in the reader's own outgoing list for the sport on
 * screen. So the ids cross, per sport, and **nothing else about them does**: `at` and
 * `expires_at` are dates the server's clock owns, and *no list of your yeses* is one of §8's
 * refusals — what crosses is a lookup, never a screen (`domain/outgoingInterest`). The mutual
 * list was not read at all until the radar's sheet asked *am I matched with this person*
 * (ADR-0174 §4); it crosses the same way now, ids per sport, and stays the one list *You said
 * yes* must never be drawn from — a mutual has come back and is not *outgoing*.
 */

import type { components } from '@/generated/schema';
import { toSport } from '@/features/onboarding/types';
import type { Sport } from '@/shared/vocabulary/sport';

import type { MutualInterest, OutgoingInterest } from '../domain/outgoingInterest';
import type { InterestStanding } from '../domain/yesBudget';

type InterestListResponse = components['schemas']['InterestListResponse'];
type OutstandingSchema = components['schemas']['OutstandingSchema'];
type OutgoingInterestSchema = components['schemas']['OutgoingInterestSchema'];

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

/**
 * The read, whole: where every sport stands, who the reader has said yes to in each, and whose
 * yes came back.
 *
 * *My* because the glossary's **Interest** is one yes to one person; this is the reader's whole
 * ledger of them, as `GET /interest` answers it.
 */
export interface MyInterest {
  readonly standing: OutstandingInterest;
  readonly outgoing: OutgoingInterest;
  readonly mutual: MutualInterest;
}

export function toInterest(response: InterestListResponse): MyInterest {
  return {
    standing: fromRows(response.outstanding),
    outgoing: idsPerSport(response.outgoing),
    mutual: idsPerSport(response.mutual),
  };
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

/**
 * Ids per sport, in the order the wire sent them; a sport this build cannot name takes its rows
 * out. The outgoing rows and the mutual rows are one wire shape, so one narrowing serves both.
 */
function idsPerSport(rows: readonly OutgoingInterestSchema[]): OutgoingInterest {
  const ids: Partial<Record<Sport, string[]>> = {};
  for (const row of rows) {
    const sport = toSport(row.sport);
    if (sport === undefined) continue;
    (ids[sport] ??= []).push(row.player_id);
  }
  return ids;
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
