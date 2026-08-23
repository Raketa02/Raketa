/**
 * The screen's own sentences — the ones that are about *the screen* rather than
 * about a match.
 *
 * A match's sentence comes off the situation table in `mappers/`; these are the
 * greeting, the region headings, the empty states and the one failure line.
 *
 * **Nothing here admits staleness.** `ADR-0038` Rule IV, kept by `ADR-0054`: no
 * card carries a stale marker, no banner appears, and there is no *"can't reach
 * Raketa"*. The screen either shows what is true or shows that it is fetching, and
 * the residual is bounded by the player's own behaviour rather than by us. The one
 * failure line below fires only when there is **nothing on screen to be stale
 * about** — a cold open that did not land — which is a different sentence from a
 * refresh that quietly did not.
 */

import type { AppError } from '@/shared/errors';

import type { SportFilter } from '../mappers/codes';
import { SPORT_CHIP_COPY } from '../mappers/sportBar';

/** `Hi, ada` — the header's title, from the *who am I* answer the app holds. */
export function greeting(nickname: string | undefined): string {
  return nickname === undefined ? 'Hi' : `Hi, ${nickname}`;
}

export const REGION_HEADING = {
  offers: 'A seat just opened',
  yourMatches: 'Your matches',
} as const;

/** What the strip says when a player is in nothing. The prototype's own line. */
export const NO_MATCHES_BOOKED = 'No matches booked';

/**
 * The honest empty city.
 *
 * `ADR-0084` fixes the `All` reading: *"Nothing open in **your sports** right
 * now"* is true only because `all` resolves to the sports she holds a rating at,
 * never to every sport on the platform. A named sport says its own name.
 *
 * The screen does not invent players to make a city look busy, and it does not
 * conclude anything from the emptiness either — an unrated sport is answered by a
 * door the **server** sends (`Raketa02/Raketa#78`), never by the phone noticing
 * that the shelves are missing.
 */
export function nothingOpen(sport: SportFilter): string {
  const where = sport === 'all' ? 'your sports' : SPORT_CHIP_COPY[sport].label;
  return `Nothing open in ${where} right now`;
}

/**
 * A cold open that did not land.
 *
 * By recovery category rather than by the backend's `message`, which is a
 * diagnostic written for a log. This is the third copy of that table in the app
 * and the rule stands: a feature never deep-imports another, and moving a file to
 * `shared/` because two features use it is how `shared/` becomes a junk drawer.
 * **A fourth is the signal to move it** — the sentences have already diverged here,
 * because this screen's failure is *the whole screen is missing* rather than *that
 * form did not submit*.
 */
const BY_RECOVERY: Readonly<Record<AppError['recovery'], string>> = {
  'retryable-automatically': 'Pull down to load your screen.',
  'retryable-by-user': 'Pull down to load your screen.',
  'requires-reauthentication': 'Your session has ended. Sign in again.',
  'requires-user-correction': 'Pull down to load your screen.',
  'business-conflict': 'Pull down to load your screen.',
  terminal: 'Something went wrong at our end. Pull down to try again.',
};

export function nowErrorMessage(error: AppError): string {
  return BY_RECOVERY[error.recovery];
}

/**
 * What the exit control announces.
 *
 * `ADR-0086` records that the prototype's two icons had **nothing** for a label
 * (`UI` §1087) and that the control replacing them carries a real one. It names
 * the club because a screen holds a dozen cards and *Leave this match* said twelve
 * times is not a label, it is a shrug.
 *
 * It does not name a price, and that is the point of `ADR-0086`'s own ruling: what
 * leaving is worth is the route's to state, and a control that quoted it here
 * would be quoting a number the card never checked.
 */
export function exitLabel(clubName: string): string {
  return `Leave this match at ${clubName}`;
}

/** What the exit opens: a screen that states the price before anything happens. */
export const EXIT_HINT = 'Shows what leaving is worth before anything happens.';

/**
 * How a countdown reads aloud.
 *
 * The figure alone — `4:37` — is a number with no noun. What the slot means is
 * *this is how long is left*, and a screen reader is the one place that has to be
 * said rather than shown by position.
 */
export function clockAccessibilityLabel(countdown: string): string {
  return `${countdown} left`;
}
