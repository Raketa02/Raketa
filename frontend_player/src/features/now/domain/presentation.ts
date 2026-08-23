/**
 * The vocabulary Now renders with: a tone, a tag, an alert, and the shapes a copy
 * table hands back.
 *
 * **None of this crosses the wire, and that is the decision rather than an
 * omission.** The tag, the tone and the alert are total functions of the
 * situation, so `ADR-0041` and `ADR-0072` put all three in this client's own
 * table: a flag would let the server and the phone disagree about whether a card
 * is urgent, which is exactly the two-derivations failure `ADR-0040` exists to
 * make unreachable.
 *
 * Pure types and nothing else. `domain/` may not read `@/generated`, so the
 * tables themselves live one layer out in `mappers/` — the app's declared wire
 * boundary and the only layer allowed to name a generated union. What lives here
 * is the half of each entry the wire has no opinion about.
 */

/**
 * How loudly to say it. Five values, resolved to a colour by whatever draws the
 * card, against the surface it lands on (`ADR-0041`).
 *
 * `bad` is deliberately absent. The prototype declared it on `inventoryLost`
 * alone and its own `ST_TONE` had no such key, so the dot rendered colourless;
 * `UI` §G decides the fix is to map that situation to `ended`, which is what the
 * table does. A sixth value would restore the defect by giving it somewhere to
 * live.
 */
export type Tone = 'good' | 'watch' | 'time' | 'ended' | 'idle';

/**
 * The tag on a card, in the words a player reads.
 *
 * Nineteen, where the state-table research counted seventeen. The two additions
 * are the offer situations `ADR-0072` created — an offered seat is a fact about
 * *this viewer*, not about what the match is doing, and neither of the
 * seventeen says it. Recorded here rather than absorbed into a near-miss,
 * because a tag that means two things is the failure the table exists to refuse.
 */
export type Tag =
  | 'Forming'
  | 'Court held'
  | 'Court released'
  | 'Court committed'
  | 'Court protected'
  | 'Full'
  | 'Confirmed'
  | 'Replacement pending'
  | 'Rescue active'
  | 'Ready to play'
  | 'Needs result'
  | 'Confirm the result'
  | 'Completed'
  | 'Played'
  | 'On standby'
  | 'Reserved'
  | 'Cancelled'
  | 'Seat offered'
  | 'Seat open';

/**
 * What one situation says, once its facts are known.
 *
 * `alert` is the strip above the card and is `null` for thirty-three of the
 * thirty-six. It fires on exactly the three that leave a player short of a
 * player inside the rescue window — `replacement`, `rescue` and `rescueLate` —
 * and stops when a seat is actually being taken, which is why
 * `replacementTransfer` carries none.
 */
export interface SituationCopy {
  readonly line: string;
  readonly tag: Tag;
  readonly tone: Tone;
  readonly alert: string | null;
}

/**
 * Which of the three audiences a card is drawn for (`ADR-0072`).
 *
 * **Nothing on the wire distinguishes them today**, so no row reads this yet and
 * `SituationContext` does not carry it. The type exists because the audience is
 * settled vocabulary and the leaver is a named audience rather than a special
 * case applied by hand at render time; the field arrives with the departure
 * payload that makes it answerable.
 */
export type Audience = 'inTheMatch' | 'lookingIn' | 'leaver';

/** Where a tap on a card's one act goes. A code determines its own destination. */
export type ActSurface =
  /** A seat claim: five exclusive minutes to buy one seat (`ADR-0081`). */
  | 'seatClaim'
  /** The payment behind a claim already running. */
  | 'claimPayment'
  /** The result route, which both entering and answering a score leave for. */
  | 'result'
  /** Find, pre-filtered — the door out of a match that is not happening. */
  | 'find'
  /** The Getting-in sheet: the door code and the QR. */
  | 'gettingIn'
  /**
   * Not a route. Leaving standby is a bare write with no confirmation
   * (`ADR-0087`), so the act resolves to the write and never to a screen.
   */
  | 'standbyWrite';

/** What a card's one act says, and where it goes. */
export interface ActCopy {
  readonly label: string;
  readonly surface: ActSurface;
}

/**
 * What a shelf code *claims*, in the terms Find will one day filter on.
 *
 * A shelf running out is a door and not a wall, so every shelf ends in a card
 * into Find carrying the shelf's own claim plus the sport the client is already
 * filtered to. The sport is **not** here: it is the sport bar's selection rather
 * than a property of the shelf, and `findPreFilter` in `mappers/` is what puts
 * the two together. Held as a value object rather than as a query string —
 * Find does not exist yet, and a URL shape decided here would be decided in the
 * wrong place.
 */
export interface FindClaim {
  readonly seats: 'open' | 'full' | 'any';
  readonly order: 'fit' | 'level' | 'newest';
  readonly kind: 'matches' | 'players' | 'clubs';
}

/** A shelf's title, and what the door at the end of it claims. */
export interface ShelfCopy {
  readonly title: string;
  readonly claim: FindClaim;
}

/**
 * The sport bar's swatch key.
 *
 * The same four names `theme.sport` is keyed on, restated here because
 * `domain/` may not read the design system and a chip's swatch is a fact about
 * the *sport*, not about the theme. `SportBar` indexes the theme with it, so the
 * two disagreeing is a compile error rather than a missing dot.
 *
 * `All` has none — `ADR-0084`: a swatch on the four sports and none on `All`,
 * because `All` is not a sport, which is the distinction the whole bar carries.
 */
export type SportSwatch = 'padel' | 'tennis' | 'squash' | 'badminton';

/** One chip on the sport bar: what it filters to, what it says, and its dot. */
export interface SportChipCopy {
  readonly label: string;
  readonly swatch: SportSwatch | undefined;
}
