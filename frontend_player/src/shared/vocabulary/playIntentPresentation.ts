/**
 * What the three declarations are **called**, what each one **means**, and how one is
 * **announced** — the words this app gives `playIntent.ts`'s closed three.
 *
 * They were `features/play/components/findAGamePresentation.ts`'s while Play was the only
 * feature that drew a declaration. `player_profile` is the second: the You tab lists what a
 * player has declared per sport and offers the same three answers on the same route
 * ([#296](https://github.com/Rakieta02/Rakieta/issues/296)), and the value in a row there has to
 * be the same word the search screen prints or the two screens are describing two facts.
 *
 * So they are promoted on `shared/README.md`'s own test — *"whether a second feature would
 * have written the identical table"* — rather than on a count of importers. It would have
 * written all three of these exactly, and `availabilityPresentation.ts` is the precedent in
 * this folder: the platform's names for a closed vocabulary, with each feature's own sentences
 * about its own rules left behind. `player_profile` **cannot** reach Play's copy in any case —
 * `PlayerProfileSurface` is the file that argues why that arrow does not exist, and
 * `playIntent.ts` records what happened the last time this vocabulary travelled through a
 * feature's front door.
 *
 * **What stayed behind is everything either feature says about the *control*.** Find a game's
 * card title, its eyebrow and the sentence naming who reads the answer are Play's, because they
 * are about the question that gates a search; the You tab's heading, its *Not set* and its row
 * hint are `player_profile`'s, because they are about a list of facts a stranger reads. Only
 * the three answers themselves are here.
 */

import type { PlayIntent } from './playIntent';

/**
 * The three declarations, as a player would say them.
 *
 * *Either suits me* is the whole of `NO_PREFERENCE` and states a preference rather than the
 * absence of one — *"indifference about the kind of evening is not a third kind of evening"*,
 * but it is still an answer somebody gave. A `Record` over the union, so a fourth value would
 * not compile without words.
 */
const INTENT_LABEL: Readonly<Record<PlayIntent, string>> = {
  COMPETITIVE: 'Competitive',
  FOR_FUN: 'For fun',
  NO_PREFERENCE: 'Either suits me',
};

export function intentLabel(intent: PlayIntent): string {
  return INTENT_LABEL[intent];
}

/**
 * One line under each answer, saying **what somebody reading it would take it to mean.**
 *
 * The three answers are a row of near-synonyms without them — *Competitive*, *For fun*,
 * *Either suits me* — and the surface they are on states a fact about the player, which is a
 * surface with room to say what the fact is ([#293](https://github.com/Rakieta02/Rakieta/issues/293)).
 *
 * They are written in the **second person about the player**, because that is who the answer
 * describes and who reads it: the intent alignment term takes *their* intent against *my* mode
 * (ADR-0094), so every one of these sentences is read by somebody else's search.
 * `NO_PREFERENCE` says that indifference is an answer somebody gave rather than a question they
 * skipped, which is the whole of why it has a label at all.
 */
const INTENT_GLOSS: Readonly<Record<PlayIntent, string>> = {
  COMPETITIVE: 'You are here for an even, serious game.',
  FOR_FUN: 'You are here for a hit, whoever wins.',
  NO_PREFERENCE: 'Either kind of evening suits you.',
};

export function intentGloss(intent: PlayIntent): string {
  return INTENT_GLOSS[intent];
}

/**
 * One answer's **spoken name**, and the phrase this app has always used for a declaration.
 *
 * *Your usual* is the app's own words for the durable value, and it has been saying it to
 * screen-reader users since the interstitial shipped — the visible copy on Find a game caught
 * up with it in [#293](https://github.com/Rakieta02/Rakieta/issues/293). It is here rather than
 * in Play for the reason the labels are: the You tab offers the identical three answers about
 * the identical fact, and *Competitive* announced two different ways on two screens is the same
 * value described as two.
 *
 * The lifetime is the whole of the name. *Competitive* is on Find a game **twice** — once as
 * the mode of one search, once as the declaration — and to a listener moving between them the
 * two are the same word; `modeControlLabel`'s *this search* is the other half of the pair, and
 * it stays in Play because a search's mode is Play's alone.
 */
export function declarationOptionLabel(intent: PlayIntent, sportName: string): string {
  return `${intentLabel(intent)}, your usual at ${sportName}`;
}
