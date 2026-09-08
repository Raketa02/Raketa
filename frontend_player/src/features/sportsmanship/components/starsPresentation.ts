/**
 * **Every sentence the card says.** Nothing the sportsmanship contract sends is prose — the
 * route answers ids and refusal codes, and the words for all of them are the client's
 * ([ADR-0022](../../../../../docs/adr/0022-wire-codes-never-sentences.md)) — so this file is
 * the feature's copy deck and the card is assembled from it, the same shape
 * `features/games/components/gamePresentation.ts` and `features/play/components/*Presentation.ts`
 * take: *code → message, never message → message*, and **a sentence is never a template
 * inlined in a component**.
 *
 * ## The word *rating* is Skill rating's, and this context arrived second
 *
 * Everything here is spelled **stars** or **the card** ([`CONTEXT.md`](../../../../../CONTEXT.md)
 * · Sportsmanship). A bare *rating* on this platform still means the μ/σ a player holds in a
 * sport, and a card in the same tab as a Level would be the one surface where it meant two
 * things.
 *
 * ## Three sentences carry the weight, and the ticket names two of them
 *
 * - **A low answer feeds the average and nothing else.** {@link matchingLine} is the ticket's
 *   own acceptance criterion and it is drawn **before the stars rather than beside the
 *   button**: a player deciding what a star *means* is deciding it while they tap, and *Pass*
 *   and *Block* already exist and both mean something specific. A control that silently does
 *   two things is one nobody can reason about, and the sentence is what keeps this one doing
 *   one.
 * - **Ignoring the card costs nothing**, so nothing here nags, counts down or thanks anybody.
 *   The nearest this deck comes to asking is naming the act on the button.
 * - **Submitting closes it for ever, and there is no correction path.** The contract's own
 *   instruction is *"ask before you send"*, and {@link LEAVE_ANYBODY_BLANK} is how it is asked:
 *   the finality is **stated before the press** rather than confirmed after it. A pre-send
 *   sheet was weighed and refused — `ProposeSheet` exists because a challenge reaches four
 *   other people and starts a window nobody can stop, where this reaches nobody and tells
 *   nobody. What it costs is one opinion the player cannot revise, and the answer to that is
 *   a sentence and a control that can be pressed a second time to clear a slip.
 *
 * ## Two registers, and the spoken one names the evening
 *
 * Several cards can stand in the list at once. *Send stars* three times over is three
 * identical buttons to a listener, so the **visible** label is the act and the **spoken** one
 * is the act and the evening — which is `gameRowLabel`'s own answer to the same problem, one
 * section further down the same tab. The star names do **not** take the evening: a person's
 * handle is who they are, the same person on two cards takes the same words, and a name
 * repeating the sport five times a row is the double announcement §20.8 refuses elsewhere.
 */

import { counted } from '@/shared/formatting/counted';
import { playerName } from '@/shared/formatting/playerName';
import { codeMessage, offlineMessage, type AppError } from '@/shared/errors';
import type { StarNames } from '@/shared/ui';

import type { StarSubject } from '../domain/card';

// ---------------------------------------------------------------------------
// The section
// ---------------------------------------------------------------------------

/**
 * The heading over the cards, above *Your games* on the Now tab.
 *
 * A question rather than a chore's name: *Rate your opponents* is an instruction to somebody
 * under no obligation, and the whole design rests on this staying a favour.
 */
export const STARS_HEADING = 'How were they?';

// ---------------------------------------------------------------------------
// The card
// ---------------------------------------------------------------------------

/**
 * The one line the ticket requires — **a low answer will not stop you being matched.**
 *
 * It names the person where there is one to name, which is the singles case and the form the
 * decision was written in. In doubles it does not: three people are on the card and naming one
 * of them makes a promise about the wrong person. And it never names an **unknown** seat —
 * `?` is what this app draws for an account `users` can no longer answer for, and a sentence
 * reading *matched with ?* is the one place that mark would be read as a word.
 */
export function matchingLine(subjects: readonly StarSubject[]): string {
  const only = subjects.length === 1 ? subjects[0] : undefined;
  const who = only?.name.kind === 'player' ? playerName(only.name) : 'any of them';

  return `This helps other players. It won't stop you being matched with ${who}.`;
}

/**
 * The two things a press cannot be taken back from, said before it — see the module note.
 *
 * One line rather than two: they are one fact about the same press, and a card that spent
 * three paragraphs explaining itself would be arguing with the reader about a favour.
 */
export const LEAVE_ANYBODY_BLANK = 'Leave anybody blank. Once you send, this card closes for good.';

/**
 * The control, named for the answer it is about to make.
 *
 * **Sending with everybody blank closes the card too** — *an explicit "I am not rating anyone"
 * is an answer* — so the button says that rather than saying *Send* over a body with nothing
 * in it. A player who means to close the card unanswered should be able to read that they are
 * doing it, and a player who meant to give somebody stars should be able to notice they have
 * not.
 */
export function submitLabel(given: number): string {
  return given === 0 ? 'Send no stars' : 'Send stars';
}

/** Swapped in while the card is going. A busy button is not a disabled button. */
export const SENDING_LABEL = 'Sending…';

/** The act **and the evening**, because a list can hold several cards. See the module note. */
export function submitName(
  label: string,
  sportName: string,
  subjects: readonly StarSubject[],
): string {
  return `${label} — ${sportName} with ${namesOn(subjects)}`;
}

/**
 * *kasia_w, tomek.p and marekb* — the court's own order, and the whole of every handle.
 *
 * The last comma is an *and* because this is prose and not a legend, and `counted()` is not
 * reached for: nothing here is counted. It is four lines rather than an import of
 * `gamePresentation`'s private one because the two sentences it lands in are different
 * sentences, and a shared join would be a formatter deciding a layout for both.
 */
function namesOn(subjects: readonly StarSubject[]): string {
  const names = subjects.map((subject) => playerName(subject.name));
  const last = names[names.length - 1] ?? '';
  const rest = names.slice(0, -1);

  return rest.length === 0 ? last : `${rest.join(', ')} and ${last}`;
}

// ---------------------------------------------------------------------------
// What each star announces
// ---------------------------------------------------------------------------

/**
 * `4 stars for kasia_w` — one name per star, because a listener has no row to count along.
 *
 * `the-words.md` §20.1: one accessibility element per action, and there are five actions in a
 * row. Through {@link counted} like every counted phrase in the app, so the day plural forms
 * arrive they arrive in one place.
 */
export function starName(stars: number, subject: StarSubject): string {
  return `${counted(stars, 'star', 'stars')} for ${playerName(subject.name)}`;
}

/**
 * The five names for one person's row, ascending.
 *
 * Spelled out rather than mapped, because {@link StarNames} is a **tuple**: the scale is five
 * and a row handed four names would draw four stars and call it an answer. The one place in
 * this feature where the length of the scale is written down twice, and the second one is a
 * type.
 */
export function starNames(subject: StarSubject): StarNames {
  return [
    starName(1, subject),
    starName(2, subject),
    starName(3, subject),
    starName(4, subject),
    starName(5, subject),
  ];
}

/**
 * Announced on the star that already stands, and on that one alone.
 *
 * The gesture that makes a mis-tap survivable, and the only part of the card a sighted player
 * discovers by trying it — so a listener is told outright.
 */
export const CLEAR_HINT = 'Clears these stars and leaves them blank.';

// ---------------------------------------------------------------------------
// A refused card
// ---------------------------------------------------------------------------

/**
 * Backend `code` → the sentence the card writes, over `recoveryMessage`'s fallback.
 *
 * **Three of these a current build cannot earn.** The scale is a type, the court is what the
 * answer is read against rather than checked against afterwards, and a `Record` keyed by a
 * player id cannot hold two answers about one person — so `stars_are_one_to_five`,
 * `they_were_not_on_this_court` and `you_rated_the_same_person_twice` are all unrepresentable
 * here. They keep their sentences for the adult attestation's reason: an older build or a
 * replayed request can carry a body this card would not have sent, and *try again* would then
 * be the one thing that is not true.
 *
 * **There is no `account_held` here, and the absence is checked rather than assumed.** Play's
 * six routes and the challenge send all document that `403`; neither of these two does, and a
 * sentence for a refusal a route cannot make is one nothing can ever be wrong about. The
 * recovery fallback under the table is what answers a code this build has never seen.
 *
 * **`this_game_is_not_yours_to_rate` is one code for three cases and it stays one** — it does
 * not exist, you did not play in it, or its result has not settled. The server refuses to
 * separate them because separating them would answer *is this id real* about four strangers'
 * evening, and this sentence keeps the refusal rather than undoing it.
 */
const BY_CODE: Readonly<Record<string, string>> = {
  /** A `409`. The list is what is stale, and the read behind it is refreshed on the way out. */
  you_have_already_rated_this_game:
    'This card is already answered. It closed when you answered it, and there is no way to reopen it.',
  this_game_is_not_yours_to_rate: 'No settled game of yours has this address.',
  stars_are_one_to_five: 'Stars are one to five, whole — there is no zero and there are no halves.',
  they_were_not_on_this_court: 'One of those players was not on that court, so nothing was sent.',
  you_rated_the_same_person_twice:
    'That card said two things about one player, and it carries one.',
};

export function starsErrorMessage(error: AppError): string {
  // Before the table, because it is about the transport rather than about a refusal: nothing
  // reached the server, so there is no `code` for the table to read. Nothing about a card
  // carries a deadline the player chose — the seven days are the game's and started without
  // them — so this write pauses like everything else in the app, and the sentence promises it.
  if (error.kind === 'network-unavailable') return offlineMessage('resumes');
  return codeMessage(BY_CODE, error);
}
