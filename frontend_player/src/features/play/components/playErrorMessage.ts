/**
 * Backend `code` → the sentence a Play surface writes, over `recoveryMessage`'s fallback.
 *
 * The shape is `authErrorMessage.ts`'s and the reason is the same: localization goes **code →
 * message, never message → message**, and the fallback under the table is by *recovery
 * category* rather than one generic apology, so a code this build has never seen still says
 * something true about what to do next.
 *
 * ## Why Play needs a table at all
 *
 * Six of its refusals have a **remedy the category cannot name**. The sharpest is
 * `search_not_found`: it is a `404`, `404` maps to `terminal`, and `terminal` renders
 * *"Something went wrong at our end. Try again later"* — for a state whose actual remedy is
 * to run the search again, and whose cause is very often the player's own act
 * ([#239](https://github.com/Raketa02/Raketa/issues/239) §3: re-running a search mints a new
 * id and orphans the line-up bound to the old one).
 *
 * ## One code carries four cases, and the sentence carries none of them
 *
 * `POST /forecasts` answers `search_not_found` when the search does not exist, when it is
 * somebody else's, when it was for another sport, and when it never showed one of these
 * people — *"telling them apart would answer questions about strangers one probe at a time."*
 * The sentence therefore states what the player can act on and **guesses at no cause**, which
 * is the same ceiling the court's withheld mark is held to
 * ([`courtPresentation.ts`](./courtPresentation.ts)).
 *
 * ## Four 503s, one sentence
 *
 * The matchmaking context gives its four outages **four codes on purpose** — the engine
 * raised, a fail-closed gate could not be read, the index is too far behind, the search could
 * not be recorded — *"so a client can tell a transient outage from a refusal about you."* That
 * distinction is between 503 and everything else, and it is drawn: the five codes above say
 * something about **you**, and these four say something about **us**. Among themselves they
 * are one fact to somebody holding a phone, and four sentences would publish an operational
 * distinction the player cannot act on. They are distinguished in the log, which is where the
 * difference is useful.
 *
 * The fallback is wrong for them in a second way, too: `mapError` classifies every 5xx as
 * `retryable-automatically`, whose sentence is *"We couldn't reach Raketa. Check your
 * connection and try again"* — and a 503 is Raketa **reached**, answering, and declining.
 *
 * > The ticket that ordered this table said *both* 503s, counting the two on `POST /forecasts`
 * > and the read-back. The search, the line-up and the deck each answer **four**, and the
 * > argument does not change with the count — so all four share the sentence rather than two
 * > of them sharing it and two falling through to *"try again later"*.
 */

import { codeMessage, type AppError } from '@/shared/errors';

/**
 * The 503s' one sentence.
 *
 * It says the platform could not do it and that trying again is worth it, and it names no
 * mechanism: *the engine*, *the index* and *a gate* are our words for our problem, and a
 * player reading them learns only that something they cannot see is broken.
 */
const PLATFORM_CANNOT_ANSWER = "We couldn't put a game together just now. Try again in a moment.";

const BY_CODE: Readonly<Record<string, string>> = {
  /**
   * The origin search cannot be used. The remedy is a **new search**, which is also what
   * usually caused it — so the sentence names the act rather than the loss.
   */
  search_not_found: 'That search is no longer available. Run a new one to keep going.',
  /**
   * The deck's own pair of refusals, and both are about *this* answer rather than about the
   * player ([#270](https://github.com/Raketa02/Raketa/issues/270)).
   *
   * `origin_search_not_found` is `search_not_found` one layer down: the yes or the pass cited
   * a deal that is not this player's or never showed that person, and the remedy is the same —
   * a new deal, which the deck's own control asks for. It says *deck* rather than *search*
   * because that is the act the player is standing in front of.
   */
  origin_search_not_found: 'That deal is no longer available. Deal again to keep going.',
  /**
   * The cap, and the one sentence that must not promise a way round it. **Nothing of yours is
   * shortened to make room** — the contract says so — so the honest remedy is waiting, and
   * the count and the cap are both on the read the segment already holds.
   */
  outstanding_interest_cap_reached:
    "You have as many yeses out as this sport allows. One comes back, or one lapses, and there's room again.",
  /**
   * Unreachable while the sport chips are drawn from the rated sports, and the backstop for a
   * stale profile on a second device. It sends the player where the rating is made.
   */
  sport_not_rated: "You're not rated in this sport yet. Rate it, then search again.",
  /**
   * The client opens the one-tap declaration **before** the refusal rather than after it, so
   * this is what a player sees when that interstitial was not reached.
   */
  play_intent_not_declared: "Say what kind of game you're after in this sport, then try again.",
  /** Unreachable by design — the Play tab is behind a committed profile. */
  player_profile_not_committed: 'Finish setting up your profile before you search for a game.',
  /**
   * A `403` about the account, and the reason there is **no client hold state anywhere**: the
   * gate fires at the request, and this sentence is the whole of what the client knows.
   */
  account_held: 'Your account is on hold. Get in touch with us.',
  matchmaking_unavailable: PLATFORM_CANNOT_ANSWER,
  gate_data_unavailable: PLATFORM_CANNOT_ANSWER,
  index_too_stale: PLATFORM_CANNOT_ANSWER,
  search_not_recorded: PLATFORM_CANNOT_ANSWER,
};

export function playErrorMessage(error: AppError): string {
  return codeMessage(BY_CODE, error);
}
