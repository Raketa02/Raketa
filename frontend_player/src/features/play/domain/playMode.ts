/**
 * Which mode Play opens in for a player who has declared one — and why the two values are
 * never allowed to become one value.
 *
 * `PlayIntent` has three values and `SearchMode` has two. That arity gap is
 * [ADR-0094](../../../../../docs/adr/0094-play-intent-declared-per-sport-in-its-own-aggregate.md)'s
 * central move: *"indifference about the kind of evening is not a third kind of evening"*, so
 * `NO_PREFERENCE` never selects a weight vector — it **inherits** one. On a search there is a
 * tab to inherit from; where there is nothing to inherit from, the mapping takes *for fun*,
 * which is the rule `mode_for_intent` applies on the backend and `the-two-contracts.md` §6
 * fixes.
 *
 * ## Why this is a seed and not a binding
 *
 * The obvious cheaper design is to have no client mode at all and read the declaration on
 * `GET /players/me/profile` every time. It loses on an argument
 * [#226](https://github.com/Raketa02/Raketa/issues/226) already made: ADR-0094's drift
 * backstop is written for *"the sticky-tab case — switch once, decline once, then search in
 * the new mode for a month with no further switch to hang an offer on."* A toggle re-seeded
 * from the declaration on every open **agrees with it on every first search**, and the
 * backstop catches nothing. The two values have to be able to disagree; that is what the
 * backstop is for.
 *
 * So the declaration seeds the toggle once per process and the toggle is **never written
 * back**. A relaunch landing on the declared default is correct behaviour, not a lost
 * preference.
 */

import type { PlayIntent, SearchMode } from './vocabulary';

/**
 * The mode a search opens in for a player who declared this intent.
 *
 * A table rather than a comparison of two enums' spellings, for the reason the backend's own
 * mapping gives: `PlayIntent` and `SearchMode` are deliberately different types and a shared
 * string is a coincidence the arithmetic must not lean on.
 */
const SEEDED_MODE: Readonly<Record<PlayIntent, SearchMode>> = {
  COMPETITIVE: 'COMPETITIVE',
  FOR_FUN: 'FOR_FUN',
  // Nothing to inherit from at a cold start — no tab has been chosen yet — so it is named
  // here rather than defaulted somewhere else.
  NO_PREFERENCE: 'FOR_FUN',
};

export function modeForIntent(intent: PlayIntent): SearchMode {
  return SEEDED_MODE[intent];
}

/**
 * What Play opens in when the player has declared nothing for this sport, or when the
 * declaration has not been read yet.
 *
 * **Derived from the mapping above rather than restated beside it.** It is the value
 * `NO_PREFERENCE` takes, and for the same reason — a first search should not assume somebody
 * wants a competitive evening — so writing `'FOR_FUN'` a second time would be one rule in two
 * places, and the second one is the one that gets missed.
 */
export const MODE_WITHOUT_A_DECLARATION: SearchMode = modeForIntent('NO_PREFERENCE');

/**
 * The declaration a player is agreeing to when they accept `UPDATE_PLAY_INTENT` — the
 * mapping above, read the other way, and **it is not its inverse.**
 *
 * `modeForIntent` is three values collapsing into two and cannot be run backwards: the
 * question this answers is *your last five searches were competitive — make that your
 * declaration?*, and the value being agreed to is the **searches' own mode**. So
 * `NO_PREFERENCE` is unreachable here, and correctly: a run of five searches in one mode is
 * evidence of a preference, and a prompt that offered indifference as the answer to it would
 * be proposing something the drift never observed.
 *
 * A table rather than a cast, for `SEEDED_MODE`'s reason: the two types are deliberately
 * different and a shared spelling is a coincidence nothing should lean on.
 */
const DECLARED_FROM_MODE: Readonly<Record<SearchMode, PlayIntent>> = {
  COMPETITIVE: 'COMPETITIVE',
  FOR_FUN: 'FOR_FUN',
};

export function intentForMode(mode: SearchMode): PlayIntent {
  return DECLARED_FROM_MODE[mode];
}

/**
 * Whether the mode on the segment and the declaration are **saying the same thing** — the
 * question the standing line under the segment is drawn from
 * ([#294](https://github.com/Raketa02/Raketa/issues/294)).
 *
 * **It is not an equality, and `NO_PREFERENCE` is why.** A player who declared that either
 * kind of evening suits them has said nothing a search can contradict, so no search of theirs
 * ever disagrees with their profile — which is the rule the backend's own drift loop applies
 * (`detect_intent_drift._AGREES_WITH`, *"``NO_PREFERENCE`` agrees with **both**"*), read here
 * rather than invented a second time. A line offering to *update* an indifferent declaration
 * to a mode would be proposing a narrowing off evidence of nothing.
 *
 * It is deliberately **not** `intentForMode(mode) === intent`, which says the same thing for
 * the two mode-shaped intents and the wrong thing for the third. A table over `SearchMode`,
 * for `SEEDED_MODE`'s reason: the two types are different by construction and a shared
 * spelling is a coincidence the arithmetic must not lean on.
 */
const AGREES_WITH: Readonly<Record<SearchMode, readonly PlayIntent[]>> = {
  COMPETITIVE: ['COMPETITIVE', 'NO_PREFERENCE'],
  FOR_FUN: ['FOR_FUN', 'NO_PREFERENCE'],
};

export function declarationAgreesWithMode(intent: PlayIntent, mode: SearchMode): boolean {
  return AGREES_WITH[mode].includes(intent);
}

/**
 * Whether a declaration **names a kind of evening** — the question the deck's standing line is
 * written against ([#295](https://github.com/Raketa02/Raketa/issues/295)).
 *
 * `POST /deck` carries no mode at all (`SearchEnvelope.mode` is null exactly there), so on that
 * surface the declaration genuinely *is* what the deal runs on, and the line says so: *dealing
 * competitive games at padel — your usual*. That sentence is only available for two of the three
 * answers. ADR-0094's *"indifference about the kind of evening is not a third kind of evening"*
 * is what makes the third one different in kind rather than merely different in wording: a
 * `NO_PREFERENCE` player is dealt on `modeForIntent`'s **inherited** for-fun vector, and telling
 * them the deck is dealing them for-fun games would report an inheritance as a choice they made.
 *
 * A table over the union rather than a comparison against one spelling, for `SEEDED_MODE`'s
 * reason — and so a fourth answer could not silently take the sentence written for the two.
 */
const NAMES_A_KIND: Readonly<Record<PlayIntent, boolean>> = {
  COMPETITIVE: true,
  FOR_FUN: true,
  NO_PREFERENCE: false,
};

export function declarationNamesAKind(intent: PlayIntent): boolean {
  return NAMES_A_KIND[intent];
}
