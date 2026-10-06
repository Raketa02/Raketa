/**
 * **The words on the one-tap declaration** — *Your usual game at Padel*, the lifetime above it,
 * and the line saying who reads the answer — for `DeclarationInterstitial` beside it.
 *
 * They were Find a game's while that screen was where the question was first asked, and came here
 * with the Games deck the interstitial stands in front of
 * ([#574](https://github.com/Raketa02/Raketa/issues/574)). Find a game's own line left with that
 * screen ([#576](https://github.com/Raketa02/Raketa/issues/576)).
 *
 * The three answers themselves — *Competitive*, *For fun*, *Either suits me* — are not here: they
 * are `shared/vocabulary/playIntentPresentation.ts`', because You lists the same three.
 */

/**
 * The one-tap declaration, on the screen ADR-0094 makes the edit surface.
 *
 * ***Your usual* is this app's own phrase for it**, and it has been saying it to screen-reader
 * users since the interstitial shipped — `declarationOptionLabel` announces *Competitive, your
 * usual at padel*. It was `What kind of game at ${sportName}?`, which differed from the mode
 * section's heading by two words and by a question mark
 * ([#293](https://github.com/Raketa02/Raketa/issues/293)); the visible words now say what the
 * spoken ones already did.
 */
export function declarationTitle(sportName: string): string {
  return `Your usual game at ${sportName}`;
}

/** The card's eyebrow: **the lifetime**, said before the question rather than after it. */
export const DECLARATION_EYEBROW = 'Kept on your profile';

/**
 * **The same question on a group's Games tab** ([#553](https://github.com/Raketa02/Raketa/issues/553),
 * the screens A2.1) — who reads the answer there is the group's deck: a group deals a player only
 * the kind of game they want, and nothing at all until they have said (the Games deck's intent
 * rule, #539). So the sentence names that reader, and keeps the lifetime.
 */
export const GROUP_DECK_DECLARATION_BODY =
  'Your groups deal you games of this kind — both, if either suits you. Asked once for this sport.';
