/**
 * **A list of names, given way at by dropping whole ones** — §15's rule, and the words it
 * draws.
 *
 * `playerName.ts` beside it turns *one* person into words; this turns several into a line. It is
 * here for that file's own stated reason — *"in `shared/` rather than in Play because the
 * challenge a send opens names the same people on screens Play does not own"* — and the Chats
 * tab is where that stops being hypothetical: a challenge row and a conversation row are two
 * different objects naming the same people under one heading each
 * ([`the-loop-screens.md`](../../../../docs/specs/the-loop/the-loop-screens.md) §1.2, §1.3).
 *
 * **Every *handle* in this file is a nickname** — what every screen says about a player since
 * [ADR-0199](../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md), whole and never
 * with an @. The word is right again: the nickname is a handle.
 *
 * **§15 is categorical: a name is not shortenable.** So a list of them gives way by dropping
 * **whole names**, the ellipsis falls at a separator, and whoever is dropped is whole on the
 * screen behind the row and whole in the row's spoken name — ADR-0107's rule is against
 * *inventing* a familiar form, and dropping a name invents nothing.
 *
 * **The budget is measured in characters at the widest character a name may contain**, because
 * *which* names fit is a question about width on a screen no module can measure, and React Native
 * will happily tail-truncate a `Text` in the middle of somebody's name. It is deliberately
 * conservative: dropping a name that would have fitted keeps the rule, and letting the ellipsis
 * land inside a name breaks it outright. The repertoire it is measured over is the one the
 * platform's players write in — printable ASCII and the Polish letters — and a name is free
 * text, so a glyph outside it is where the budget's margin is spent rather than a case it proves.
 *
 * What is **not** here is the furniture either row draws around the words — a face, an overlap, a
 * stripe. That is the Chats tab's, in `features/shell/components/chatsRowGeometry.ts`, for the
 * reason the tab's own sentences are the shell's: it is a fact about the *tab*, and the sections
 * under it own what a challenge and a conversation say.
 */

import { theme } from '@/shared/ui';

import { LIST_SEPARATOR, sentenceList } from './sentenceList';

/**
 * What separates two handles in a list of them — structure rather than voice, so the rule that
 * charges for it and the line that draws it cannot disagree about its width.
 *
 * **The platform's own list separator**, named again here because this file *charges* for it:
 * `charactersThatFit` spends its width out of a budget, which is a question nothing else asks.
 * Two spellings of `', '` would be two answers to what a line costs.
 */
export const HANDLE_SEPARATOR = LIST_SEPARATOR;

/**
 * The handles a row **speaks** — commas, and a final *and*.
 *
 * [`the-words.md`](../../../../docs/specs/matchmaking/the-words.md) §24.2 spells a Chats row's
 * spoken name as `Tomek W. and Ola K., padel, …`, and §22.6 gives the platform's own join for a
 * list in a sentence: *"joined with commas and a final and"*. A listener hears the handles, the
 * sport and the row's line one after another, so a flat comma list makes four facts one
 * undifferentiated run — the *and* is what says where the people stop.
 *
 * **It is not {@link handleLine}, and the difference is the point.** The visible line is a name
 * list inside a `cardTitle` where a conjunction would read as somebody's handle, and it drops
 * whole names with a `+2` counter. This one **never truncates**: §20.4 is *"the visible label
 * truncates, the spoken one never does"*, so every handle is here whether or not the row drew it.
 *
 * **The join is `sentenceList`'s and this is its name for handles**, which is the whole of what
 * this function is once the rule was promoted on its third caller: two accessibility decks read
 * *the handles, spoken* rather than *a list, joined*, and that name is what tells the reader at
 * either call site which of this file's two functions they are looking at.
 */
export function spokenHandles(names: readonly string[]): string {
  return sentenceList(names);
}

/**
 * The widest character a handle may contain, as a share of the type role's size.
 *
 * Archivo Bold's `@` is 1,0010 em and is the widest glyph in the repertoire a nickname can be
 * written in; this rounds up. Derived rather than chosen — `handleList.test.ts` reads the advance
 * widths out of the face that ships in the bundle, so an Archivo release that redraws the letters
 * goes red rather than truncating on somebody's phone.
 */
export const WIDEST_HANDLE_EM = 1.01;

/**
 * The two things about a type role that decide how wide its widest character is: the size, and
 * the tracking added after every glyph — `theme.type`'s roles carry both, and this is the shape
 * of what {@link charactersThatFit} reads off one.
 */
export interface HandleRole {
  readonly fontSize: number;
  /** Points added after each character. Absent is nought; `h1`'s is negative. */
  readonly letterSpacing?: number;
}

/**
 * How many characters of handle a column this wide can hold, **in the role the line is set in.**
 *
 * The role defaults to `cardTitle`, which is what both Chats rows set a handle line in; the
 * conversation header sets its line in `h1` and says so, because a budget counted at one size for
 * a line drawn at another promises room the line does not have — six points of size is nearly half
 * again as many characters — and what that draws is a one-line row cut mid-handle or a header
 * grown a second line, depending on which surface capped it
 * ([#401](https://github.com/Raketa02/Raketa/issues/401)). The role's tracking is spent too: it
 * is part of every character's advance, and ignoring `h1`'s negative tracking would drop a name
 * that fitted.
 *
 * It never answers nought: a row always names somebody, and a single handle longer than the row
 * has nothing to drop — §15 permits *that* one to truncate visually, *"a seat label may truncate
 * visually; a sentence may not, and a spoken name never does"*.
 */
export function charactersThatFit(
  columnWidth: number,
  role: HandleRole = theme.type.cardTitle,
): number {
  const advance = role.fontSize * WIDEST_HANDLE_EM + (role.letterSpacing ?? 0);

  return Math.max(Math.floor(columnWidth / advance), 1);
}

/**
 * **The handles a row draws, as one line** — whole names, and a count of the ones dropped.
 *
 * One function rather than *how many fit* and *what the line looks like* as two. They were split
 * across a rule and a copy deck while they lived in two layers of one feature; in one module the
 * split buys nothing and costs an ordering two call sites have to pair correctly.
 *
 * The counter that replaces the dropped names is charged for **before** the fact, or a line that
 * just fitted stops fitting the moment it says what it left out. It is a bare `+2` rather than a
 * sentence: it sits inside a name list at `cardTitle`, where a clause would read as somebody's
 * handle.
 *
 * **At least one name, always.** A single handle longer than the row has nothing to drop, and §15
 * permits *that* one to truncate visually — *"a seat label may truncate visually; a sentence may
 * not, and a spoken name never does"*. Every handle stays whole in {@link spokenHandles} and on
 * the screen behind the row either way.
 *
 * @param budget the line's width in characters, at its widest character — {@link charactersThatFit}.
 */
export function handleLine(names: readonly string[], budget: number): string {
  const shown = namesThatFit(names, budget);
  const drawn = names.slice(0, shown);
  const hidden = names.length - drawn.length;

  return hidden === 0 ? drawn.join(HANDLE_SEPARATOR) : `${drawn.join(HANDLE_SEPARATOR)} +${hidden}`;
}

/** How many of the names fit, counting the separators and the counter that replaces the rest. */
function namesThatFit(names: readonly string[], budget: number): number {
  let used = 0;
  let shown = 0;

  for (const [at, name] of names.entries()) {
    const cost = (at === 0 ? 0 : HANDLE_SEPARATOR.length) + [...name].length;
    const hidden = names.length - (at + 1);
    const counter = hidden === 0 ? 0 : ` +${hidden}`.length;

    if (at > 0 && used + cost + counter > budget) break;

    used += cost;
    shown += 1;
  }

  return Math.max(shown, 1);
}
