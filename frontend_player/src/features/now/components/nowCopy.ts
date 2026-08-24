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
import type { ScoreBoardRow } from '@/shared/ui';

import type { ScoreLine, ScoreSide } from '../domain/ComposedScreen';
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
 * What the fit badge says aloud, since `✦ 93` is two symbols and no sentence.
 *
 * **The emphatic band is a colour and nothing else** — `ADR-0037` gates it on three
 * facts and caps it at one card per screen, and `UI` §B9 is final on *"two bands
 * only"*. That leaves the loudest claim on the screen with no non-visual half at
 * all, which is a cue nobody using a screen reader can have. The word is added
 * **here**, where it costs no pixel and creates no third band: the drawing is
 * untouched and the announcement carries the state, which is the split
 * `ADR-0082` priced for the tab bar and could not make there.
 */
export function fitBadgeLabel(score: number, emphatic: boolean): string {
  return emphatic ? `Fit ${score}, the pick of this screen` : `Fit ${score}`;
}

/**
 * The card at the end of every shelf.
 *
 * A shelf running out is a **door and not a wall** — the row stops because the cap
 * did, never because the city did. It is not in the contract: the client appends it
 * from the shelf's own code plus the sport it is already filtered to, which is the
 * same composition the door's sentence makes.
 */
export const FIND_TAIL_LABEL = 'See more in Find';

/** A screen holds up to five of these, all reading the same. The shelf names itself. */
export function findTailLabel(shelfTitle: string | undefined): string {
  return shelfTitle === undefined ? FIND_TAIL_LABEL : `${FIND_TAIL_LABEL}: ${shelfTitle}`;
}

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

/**
 * What a side is called when the wire named nobody on it.
 *
 * A side comes back with a name missing, or with none at all, whenever a seat has
 * been vacated — a leaver's own side is the ordinary case, and she is exactly the
 * player who most needs the score to read the right way round. So a nameless side
 * is named by **position**, which is the one thing that is always true of it and is
 * the server's own composition: index 0 is the viewer's.
 *
 * Two positional names and no more. A third side is not a thing a net has, and a
 * score that arrived with one would draw its rows with no name rather than with an
 * invented one.
 */
export const SIDE_FALLBACK: readonly [string, string] = ['Your side', 'The other side'];

/**
 * A score as two named rows of games — the one place either half is decided.
 *
 * `ADR-0060` requires **every** surface showing a score to name both sides with the
 * viewer's first, and there are two such surfaces: the settled card on Now and the
 * result route's screen. This is the function both call, so a side cannot be named
 * one way on the card and another on the screen she reaches by tapping it.
 *
 * **The transpose is a projection and not arithmetic.** `first` is `sides[0]`'s
 * games — the wire says so — so row 0 reads every set's `first` and row 1 every
 * set's `second`. Nothing is summed, nothing is compared, and who won is never
 * worked out: it is not a fact the phone was sent, and computing it would be the
 * level movement `ADR-0049` refuses, arriving through a formatter.
 */
export function scoreBoardRows(score: ScoreLine): readonly ScoreBoardRow[] {
  return score.sides.map((side, index) => ({
    name: sideName(side, index),
    games: score.sets.map((set) => (index === 0 ? set.first : set.second)),
  }));
}

/** The players on a side, or where it sat when the wire named none of them. */
export function sideName(side: ScoreSide, index: number): string {
  if (side.players.length > 0) return side.players.join(' and ');
  return SIDE_FALLBACK[index] ?? '';
}

/**
 * What a seat she was not fastest to says, once.
 *
 * `ADR-0062`, in its own words: *"one plain line at the top of Now — that seat has
 * gone. Not a card, no action, no tap target; it fades."* A card is what a
 * **takeable** seat wears, and a gone seat in card shape is exactly what the
 * product owner's hard constraint forbids.
 *
 * It is written by the client rather than sent, and that is the one sentence on
 * this screen that is. The server answers a refusal with the **corrected card**
 * (`ADR-0070`) — which is what she sees, and which no longer offers her anything —
 * and the line is the acknowledgement that she tapped and did not get it. Without
 * it a card would silently stop offering a seat under her thumb and she would be
 * left wondering whether the tap landed at all.
 */
export const SEAT_GONE = 'That seat has gone.';

/**
 * The two refusals that are about **her** rather than about the seat.
 *
 * Six of the eight ways taking a seat can stop applying come back as what a
 * success returns, and she reads them off the card. These two cannot be said by
 * recomposing a card about *this* match — one is a sentence about a different
 * match and the other is about a moment — so the server answers them as conflicts,
 * each carrying the one thing to do about it (`ADR-0081`'s two structural limits
 * on a serial claimant).
 *
 * Keyed on the backend's stable `code` and never on its `message`, which is a
 * diagnostic written for a log.
 */
const SEAT_FAILURE_BY_CODE: Readonly<Record<string, string>> = {
  match_player_already_claiming: 'You are already buying a seat. Finish that one first.',
  match_claim_cooling_down: 'Give that seat a moment before trying again.',
};

/** A tap that never reached the server, or one it could not answer at all. */
export const SEAT_WRITE_FAILED = 'That did not go through, and nothing has changed. Try again.';

/**
 * What a failed tap says — the same one plain line, never a dialog.
 *
 * **Own properties only.** Indexing a `Record` with an arbitrary string reaches
 * `Object.prototype`, and a code spelled `toString` would otherwise resolve to a
 * function and put whatever that stringifies to on the screen
 * (`Raketa02/Raketa#118`).
 */
export function seatFailureLine(error: AppError): string {
  const code = error.code;
  if (code !== undefined && Object.prototype.hasOwnProperty.call(SEAT_FAILURE_BY_CODE, code)) {
    return SEAT_FAILURE_BY_CODE[code] ?? SEAT_WRITE_FAILED;
  }
  return SEAT_WRITE_FAILED;
}
