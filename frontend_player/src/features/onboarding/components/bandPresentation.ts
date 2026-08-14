/**
 * A Band and a Rating status, as this app draws and says them.
 *
 * **The boundaries are not here and must never be.** They are deliberately uneven, they
 * were wrong once already, and they travel on the response — a screen that prints a band's
 * edges prints the ones it was sent. What lives here is presentation the wire does not
 * carry: which of the four bands a name refers to, so the level bar can highlight it and a
 * card can take its ink, and the plain-language meaning the glossary says every band has.
 *
 * **The name is matched, not parsed.** `Developing` is the engine's word; this is the same
 * lookup `toSport` performs for a sport, with the same fallback: a band this build has
 * never heard of gets no colour and no meaning rather than a guessed one, and the screen
 * still shows the name, the numbers and the trail. A band added after this build shipped
 * must not be able to blank the result screen.
 */

import type { BandKey } from '@/shared/ui';

/**
 * The four band names, for the level bar's own labels.
 *
 * The bar draws all four; only one of them arrives in a response. These are the shared
 * glossary's names (`CONTEXT.md`), which is where the vocabulary is defined — the *edges*
 * beside them there are the model's and are not restated anywhere in this client.
 */
export const BAND_NAMES: Readonly<Record<BandKey, string>> = {
  new: 'New',
  developing: 'Developing',
  established: 'Established',
  advanced: 'Advanced',
};

/**
 * What each band means in words, because "Developing" on its own tells a player nothing.
 *
 * Client copy, deliberately: the wire carries a band's name and its edges and no sentence,
 * and unlike the evidence trail — which is computed and must be able to change with a
 * retune — a band's meaning is fixed vocabulary that changes when the glossary does.
 */
const MEANINGS: Readonly<Record<BandKey, string>> = {
  new: 'You are starting out. The basics are still coming together, and everything from here is progress.',
  developing:
    'You keep a rally going and you are building consistency. Points are won and lost on whether the ball comes back.',
  established:
    'You play a full match with shots you can rely on, and you have a plan for the point rather than just a return.',
  advanced:
    'You compete near the top of the amateur game, with few weaknesses for an opponent to work on.',
};

const KEY_BY_NAME: Readonly<Record<string, BandKey>> = {
  new: 'new',
  developing: 'developing',
  established: 'established',
  advanced: 'advanced',
};

export interface BandPresentation {
  readonly key: BandKey;
  readonly meaning: string;
}

/** `undefined` for a band this build has no identity for — see the note above. */
export function bandPresentation(name: string): BandPresentation | undefined {
  const key = KEY_BY_NAME[name.trim().toLowerCase()];
  return key === undefined ? undefined : { key, meaning: MEANINGS[key] };
}

/**
 * The Rating status, in words.
 *
 * Everyone leaves onboarding as an **Initial Estimate** — the questionnaire counts no
 * matches — and the two states after it exist so the label means the same thing wherever a
 * rating is read back. An unrecognised status shows the server's own word rather than
 * disappearing: the same rule the difficulty tag follows, for the same reason.
 */
const STATUS_LABELS: Readonly<Record<string, string>> = {
  initial_estimate: 'Initial estimate',
  calibrating: 'Calibrating',
  stable: 'Stable',
};

export function ratingStatusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status;
}
