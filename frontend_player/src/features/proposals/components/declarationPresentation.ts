/**
 * **The words on the one-tap declaration** — *Your usual game at Padel*, the lifetime above it,
 * and the line saying who reads the answer — for `DeclarationInterstitial` beside it.
 *
 * They were Find a game's (`features/play/components/findAGamePresentation.ts`) while that screen
 * was where the question was first asked. A group's Games tab asks it too, and the interstitial
 * came here with the Games deck it stands in front of
 * ([#574](https://github.com/Raketa02/Raketa/issues/574)); its words came with it, so a sentence
 * keeps one home. **`DECLARATION_BODY` is Find a game's line** and goes with that screen in
 * [#576](https://github.com/Raketa02/Raketa/issues/576), leaving the Games tab's.
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
 * **Who reads the answer** — which is the one thing about a declaration a player cannot guess.
 *
 * It used to disambiguate the control above it — *the switch above still moves for a single
 * search* — and there is no longer a control above it: the declaration is a precondition for
 * the form existing and is now the only thing on screen while it is unanswered
 * ([#293](https://github.com/Raketa02/Raketa/issues/293)). A sentence pointing at a control
 * that is not drawn is worse than no sentence.
 *
 * So it says the two readers instead. **Somebody else's search** reads it — the intent
 * alignment term's signature is `(my_mode, their_intent)`, so this is the half of a pairing the
 * player contributes when a stranger finds them. And **a yes on Players that becomes a game**:
 * the deck itself reads no declaration any more — every deal runs under one ruler
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §2), which retired *and by Match me* from this sentence — but the court a mutual opens is a
 * friendly when either of the two declared *for fun* (§8), and that is the declaration read.
 * The player's own search reads neither, which is §6.4's rule and is why the mode segment on
 * the other side of the answer is not mentioned here.
 */
export const DECLARATION_BODY =
  'Read when somebody else’s search finds you, and when a yes on Players becomes a game. ' +
  'Asked once for this sport.';

/**
 * **The same question on a group's Games tab** ([#553](https://github.com/Raketa02/Raketa/issues/553),
 * the screens A2.1) — who reads the answer there is the group's deck: a group deals a player only
 * the kind of game they want, and nothing at all until they have said (the Games deck's intent
 * rule, #539). So the sentence names that reader, and keeps the lifetime.
 */
export const GROUP_DECK_DECLARATION_BODY =
  'Your groups deal you games of this kind — both, if either suits you. Asked once for this sport.';
