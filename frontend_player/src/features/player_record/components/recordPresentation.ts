/**
 * **Every sentence the record sheet says**, and every name it gives a listener.
 *
 * One deck, on the rule the whole app is written to: a screen is assembled from words that
 * live in one place, never from templates inlined in six components. What is here is only what
 * this surface writes — the band's name, the Social tags' words and the sport names are all
 * somebody else's and are quoted through their own tables.
 *
 * ## Four regions, four elements
 *
 * The sheet has **no interactive element inside it** other than the pairing row, so every group
 * in it is actionless and merges into the nearest heading (§20.1). That is what the four
 * `…Label` functions below are: the header, the skill card, the record card and the tag row
 * each reach a listener as one clause list rather than as a table of figures read one stop at a
 * time.
 *
 * ## Two absences are deliberately unwritten
 *
 * There is no *no record yet* and no *not enough games*. **An absent panel is not drawn**,
 * which is the same spelling absence takes on the candidate card, in the record block and on
 * the meta line — a sheet that explained its own gaps would be teaching a stranger to read a
 * stranger's silence.
 */

import { counted } from '@/shared/formatting/counted';
import { formatLevel, formatPercent, formatRange } from '@/shared/formatting/ratingFormat';
import { NO_TAGS_IN_COMMON, socialTagName } from '@/shared/vocabulary/socialTagPresentation';
import type { SocialTagId } from '@/shared/vocabulary/socialTags';
import type { SocialTagOverlap } from '@/shared/vocabulary/socialTagOverlap';
import type { GameResult } from '@/shared/vocabulary/gameResult';
// `Photo checked: on court` is the mark's own clause, quoted rather than re-written.
import { ON_COURT_CLAUSE } from '@/shared/ui';

import type { OpponentVariety, ReliabilityStrand, StrandRow } from '../domain/playerRecord';
import { varietyShare } from '../domain/recordCard';

/** The sheet's title about somebody else, and **its accessible name** — the two are one string. */
export const RECORD_TITLE = 'Player record';

/**
 * The title about yourself.
 *
 * It is not *Your profile* and not a settings screen: what this sheet shows is the **outside
 * view**, exactly as everybody who is offered you sees it, and the title is what stops a reader
 * looking for controls that are not there.
 */
export const OWN_RECORD_TITLE = 'How others see you';

/** After your own handle, so the panel is not a stranger with your face on it. */
export const YOU_MARK = '(you)';

/**
 * Never just *Close* — 6.6's rule for every close control, which is that it says what it
 * closes.
 */
export function recordCloseLabel(isSelf: boolean): string {
  return isSelf ? `Close ${OWN_RECORD_TITLE.toLowerCase()}` : `Close ${RECORD_TITLE.toLowerCase()}`;
}

export function recordTitle(isSelf: boolean): string {
  return isSelf ? OWN_RECORD_TITLE : RECORD_TITLE;
}

/** The whole handle, with the one mark that says it is yours. */
export function recordHandle(name: string, isSelf: boolean): string {
  return isSelf ? `${name} ${YOU_MARK}` : name;
}

/**
 * **The one sentence a client may write from two area codes**, and the distance beside it.
 *
 * An `area_code` is a coordinate string and never a place name — nothing in this repository can
 * turn one into the word *Kazimierz*, and deriving one would be inventing a naming scheme
 * nobody has calibrated and printing it as fact beside a real person's face. What is licensed
 * is the **comparison**: two players in the same square share a code.
 *
 * **The absence of the reader's own code is not a difference.** A record opened where the
 * reader's area is unknown draws the kilometres alone, because *the comparison cannot be made*
 * and *they are not in your area* are two facts and only one of them is a claim.
 *
 * **On your own record the whole line goes, and not only the distance.** *Nought kilometres
 * from yourself* is the obvious half; the other is that the two codes are equal **by
 * construction** there, so a line built from the same comparison would tell somebody they are
 * in their own area. Both halves are one condition, which is why `isSelf` is read here rather
 * than at the two call sites that would each have to remember. What is left is an empty string,
 * so the sheet draws nothing rather than a stray separator.
 */
export const IN_YOUR_AREA = 'In your area';

export interface IdentityFacts {
  /** Whole kilometres, as the contract sends them. */
  readonly distanceKm?: number;
  /** Their coarse area, as a machine code. **Never printed.** */
  readonly areaCode: string;
  /** Yours, for the one comparison — absent where the surface that opened this knows none. */
  readonly viewerAreaCode?: string;
  /** Whether the record is the reader's own. The whole line is dropped when it is. */
  readonly isSelf: boolean;
}

export function identityLine(facts: IdentityFacts): string {
  if (facts.isSelf) return '';

  const near =
    facts.viewerAreaCode !== undefined && facts.viewerAreaCode === facts.areaCode
      ? [IN_YOUR_AREA]
      : [];
  const far = facts.distanceKm === undefined ? [] : [`${facts.distanceKm} km`];

  return [...near, ...far].join(' · ');
}

/** `Padel 2,75` — the pill's words, and the condition on drawing a sport's colour at all. */
export function sportPill(sportName: string, level: number): string {
  return `${sportName} ${formatLevel(level)}`;
}

/**
 * `Player Score 93` — the pill, and `Player Score 93 out of 100` for a listener.
 *
 * The scale is spelled in the spoken register because Fit is already the other hundred on the
 * screen this sheet opens over, and a bare figure in a run of clauses could be either.
 */
export const PLAYER_SCORE_NAME = 'Player Score';
const PLAYER_SCORE_DENOMINATOR = 100;

export function scorePill(score: number): string {
  return `${PLAYER_SCORE_NAME} ${score}`;
}

export function scorePillLabel(score: number): string {
  return `${scorePill(score)} out of ${PLAYER_SCORE_DENOMINATOR}`;
}

/**
 * `PADEL · 2,75 · 77 % sure · 21 counted` — **one text run and not three boxes.**
 *
 * The three figures are inseparable by design: a confident-looking number built on three games
 * must not read like one built on forty. Three boxes is how one of them ends up conditionally
 * hidden, and the one that would go is the one that makes the other two honest.
 */
export function skillHeadline(facts: {
  readonly sportName: string;
  readonly level: number;
  readonly confidence: number;
  readonly countedGames: number;
}): string {
  return [
    facts.sportName.toUpperCase(),
    formatLevel(facts.level),
    `${formatPercent(facts.confidence)} sure`,
    `${facts.countedGames} counted`,
  ].join(' · ');
}

/** `Likely 2,47–3,03` — the bracket in words, because the bracket itself is a drawing. */
export function likelyRangeLine(range: { readonly low: number; readonly high: number }): string {
  return `Likely ${formatRange(range)}`;
}

/**
 * `3 of the last 5 won` — the run as **one clause**, against its own length.
 *
 * Five squares carry no words, so a listener gets a count rather than five elements read like a
 * table. The denominator is the real one: a run of three says *of the last 3*, because a clause
 * saying *of the last 5* over three squares would pad in words what the drawing refuses to pad
 * in squares.
 */
export function lastFiveReading(results: readonly GameResult[]): string {
  const won = results.filter((result) => result === 'WIN').length;
  return `${won} of the last ${results.length} won`;
}

/** `21 counted games` — the figure with the noun, through the one pluralisation helper. */
export function countedGamesReading(count: number): string {
  return counted(count, 'counted game', 'counted games');
}

/**
 * **The header, as one element** — identifying facts first, and never a table.
 *
 * The order is the drawn one here: a header has no argument to make, so there is nothing to
 * re-order the way the candidate card's spoken body re-orders itself. Absent parts are dropped
 * rather than spoken as nothing.
 */
export interface HeaderFacts {
  readonly handle: string;
  readonly onCourt: boolean;
  readonly identity: string;
  /** One `sportPill` string per rated sport, in the registry's order. */
  readonly sports: readonly string[];
  readonly playerScore?: number;
}

export function recordHeaderLabel(facts: HeaderFacts): string {
  return sentences([
    facts.handle,
    ...(facts.onCourt ? [ON_COURT_CLAUSE] : []),
    ...(facts.identity === '' ? [] : [facts.identity]),
    ...(facts.sports.length === 0 ? [] : [facts.sports.join(', ')]),
    ...(facts.playerScore === undefined ? [] : [scorePillLabel(facts.playerScore)]),
  ]);
}

/**
 * **The skill card, as one element.**
 *
 * The band bar under the headline announces nothing of its own: it is a drawn scale and the
 * band's name is in the clause list already, so a bar naming itself would be the same fact read
 * twice. The bracket is the same — `likelyRangeLine` is what a listener gets instead of it.
 */
export interface SkillCardFacts {
  readonly sportName: string;
  readonly level: number;
  /** The band's published name, as the server spelled it. */
  readonly band: string;
  readonly confidence: number;
  readonly countedGames: number;
  readonly likelyRange: { readonly low: number; readonly high: number };
  readonly lastFive?: readonly GameResult[];
}

export function skillCardLabel(facts: SkillCardFacts): string {
  return sentences([
    facts.sportName,
    `Level ${formatLevel(facts.level)}, ${facts.band}`,
    `${formatPercent(facts.confidence)} sure`,
    countedGamesReading(facts.countedGames),
    likelyRangeLine(facts.likelyRange),
    ...(facts.lastFive === undefined || facts.lastFive.length === 0
      ? []
      : [lastFiveReading(facts.lastFive)]),
  ]);
}

/**
 * **The record card's heading, which is the rule it enforces rather than a label on it.**
 *
 * Every row beneath it is a ratio the platform observed. What other players *said* is not here
 * and will not be — an opinion under this title would make the title false — so sportsmanship
 * stands one block down under a heading naming its own author, and
 * [`countedRows`](../domain/recordCard.ts) is what keeps the promise rather than trusting a
 * remote service to keep it.
 *
 * Drawn in caps at the eyebrow's 9,5pt, which is *a label for a region you are reading*, and
 * **spoken in the sentence case below**: a listener meets a run of capitals as emphasis or, on
 * some engines, as letters. It is `skillHeadline`'s split, one card lower.
 */
export const RECORD_CARD_TITLE = 'The record — counted by the system, not written by people';

export const RECORD_CARD_TITLE_DRAWN = RECORD_CARD_TITLE.toUpperCase();

/**
 * **What each strand is called on screen**, keyed off the served code and never off the row's
 * position — a strand with nothing behind it is absent from the list entirely, so the rows a
 * card gets are the rows that person has.
 *
 * **`ANSWERS_RESULTS` is *Answers about results* and never *confirms* anything.** Countering a
 * score you believe is wrong is an answer and costs nothing
 * ([ADR-0156](../../../../../docs/adr/0156-a-results-strand-counts-answers-and-never-agreements.md));
 * a player who did exactly that and then watched a *confirms* figure rise is the one person
 * certain to notice the word was wrong.
 *
 * Three of the six have **no provider on this platform today** and never reach a screen. They
 * carry words anyway, because the table is keyed by the whole vocabulary and a code with no
 * words is a build failure — which is the point of keying it that way.
 */
export const STRAND_NAME: Readonly<Record<ReliabilityStrand, string>> = {
  SHOWS_UP: 'Shows up',
  ANSWERS_CHALLENGES: 'Answers challenges',
  ANSWERS_RESULTS: 'Answers about results',
  KEEPS_PLANS: 'Keeps plans',
  SETTLES_UP: 'Settles up',
  SPORTSMANSHIP: 'Sportsmanship',
};

/**
 * `9 of 9` — **the raw pair, in the one spelling every row on this card prints it in.**
 *
 * A perfect record over nine games and one over forty are different claims and a bar alone
 * hides which, which is the whole reason the card carries three numbers per row and draws two
 * of them. It is also what makes the bar decoration: the figure is text two words earlier, so
 * a meter announcing itself would be the same fact read twice.
 *
 * The variety row prints its pair through here too — the honesty rule is the card's rather
 * than the strand rows', and a second spelling of it is how the two rows drift apart.
 */
function rawPair(part: number, whole: number): string {
  return `${part} of ${whole}`;
}

export function strandFraction(row: Pick<StrandRow, 'good' | 'opportunities'>): string {
  return rawPair(row.good, row.opportunities);
}

/** One row as a listener meets it — the name and the pair, never the bar. */
function strandReading(row: StrandRow): string {
  return `${STRAND_NAME[row.strand]}, ${strandFraction(row)}`;
}

export const VARIETY_LABEL = 'Opponent variety';

/** The two halves, computed once so the drawn row and the spoken one cannot disagree. */
function varietyParts(variety: OpponentVariety): readonly [string, string] {
  return [
    formatPercent(varietyShare(variety)),
    rawPair(variety.distinctOpponents, variety.gamesPlayed),
  ];
}

/**
 * `70% · 14 of 20` — **the share and the pair, because the card just made that rule about
 * itself.**
 *
 * The percentage is the client's one division; the pair is the platform's and is what stops the
 * share being read as a settled habit over three games. The row draws **no bar**: the contract
 * attaches no banding, floor or tone to this figure, and an untoned meter in a column of toned
 * ones would be a tone claim made by adjacency.
 */
export function varietyValue(variety: OpponentVariety): string {
  return varietyParts(variety).join(' · ');
}

/** The same two halves as a listener meets them — clauses, where the row draws a separator. */
function varietyReading(variety: OpponentVariety): string {
  return `${VARIETY_LABEL}, ${varietyParts(variety).join(', ')}`;
}

/**
 * **The record card, as one element** — the heading first, then one clause per row.
 *
 * The bars are not in it and carry nothing of their own: each is a drawing of the fraction
 * spoken two words earlier, which is 6.8's argument about the availability grid's column heads
 * arriving on a third surface.
 */
export interface RecordCardFacts {
  /** The rows the card actually drew, in the order it drew them. */
  readonly rows: readonly StrandRow[];
  readonly variety?: OpponentVariety;
}

export function recordCardLabel(facts: RecordCardFacts): string {
  return sentences([
    RECORD_CARD_TITLE,
    ...facts.rows.map(strandReading),
    ...(facts.variety === undefined ? [] : [varietyReading(facts.variety)]),
  ]);
}

/**
 * **The tag row, as one element** — and the three silences kept apart.
 *
 * Worded so each clause says whose fact it is: *tags you share* is about the pair, *their tags*
 * is about them alone. That distinction is the whole of the row.
 *
 * A record opened with **no comparison behind it** reaches `unknown`, which says their tags and
 * claims nothing. The amber sentence is reserved for a comparison that was actually made and
 * found nothing, because *No tags in common* is a claim about everything.
 */
export function socialTagsLabel(row: SocialTagOverlap): string {
  switch (row.kind) {
    case 'shared': {
      const shared = row.tags.filter((tag) => tag.shared).map((tag) => tag.id);
      const rest = row.tags.filter((tag) => !tag.shared).map((tag) => tag.id);
      return sentences([
        ...(shared.length === 0 ? [] : [`Tags you share: ${tagNames(shared)}`]),
        ...(rest.length === 0 ? [] : [`Their other tags: ${tagNames(rest)}`]),
      ]);
    }
    case 'unknown':
      return `Their tags: ${tagNames(row.tags)}`;
    case 'none-in-common':
      return NO_TAGS_IN_COMMON;
    case 'hidden':
      return '';
  }
}

/**
 * **The one row on this sheet that is about the two of you rather than about them.**
 *
 * The Fit breakdown is not deleted — the number in the pill has no other account anywhere in
 * the app, and deleting its only explanation leaves a figure on screen that nothing answers
 * for. It moves behind a row that says what it is, so a pairing fact sits behind a label naming
 * a pairing rather than behind a photograph.
 *
 * The visible title carries the ✦ and the spoken one does not, which is §20.6's one exception
 * arriving here for the reason it exists: a glyph is doing work in the visible name.
 *
 * **The figure is rounded here, because this is where it is printed.** `whyFitColumn` writes the
 * whole breakdown against `Math.round(fit)` and the sheet's own title and accessible name are
 * that number, so a served `78,4` shown whole on this row would promise *why fit 78,4* and open
 * *Why fit 78*. Rounding at the call site instead would be a rule each of the three entry points
 * had to remember — `signedFigure`'s own rule that a figure is rounded where it is printed.
 */
export function fitRowTitle(fit: number): string {
  return `Why ✦ ${Math.round(fit)}`;
}

export const FIT_ROW_BODY = 'How you two were scored against each other — not a fact about them.';

export function fitRowLabel(fit: number): string {
  return `Why fit ${Math.round(fit)}. ${FIT_ROW_BODY}`;
}

/**
 * **The one line a record that cannot be opened draws, and there is nothing else on it.**
 *
 * Never disclosed, blocked in either direction, held, and no such player answer the same code
 * with the same body, byte for byte — the indistinguishability is the feature, because a
 * response that named which would deliver a block to the one person a block is meant to be
 * invisible to. So this client draws one line and offers no retry: re-asking a refusal returns
 * the refusal.
 */
export const RECORD_UNAVAILABLE = 'This record isn’t available.';

/** The backend's one code for all four causes. */
export const RECORD_UNAVAILABLE_CODE = 'record_unavailable';

/**
 * The control a failure to **reach** the platform gets, which the refusal above deliberately
 * does not: that one would answer identically, and this one genuinely can succeed.
 */
export const RETRY_RECORD_LABEL = 'Try again';

/**
 * What a listener is told while the sheet is filling.
 *
 * A spinner is a drawing and announces nothing, so the wait needs a name — and it is a name
 * rather than a sentence, because a listener meets it as one element in a sheet whose title has
 * already said whose record this is.
 */
export const READING_RECORD_LABEL = 'Reading their record';

/** The words alone. Prose does not carry glyphs — `socialTagPresentation`'s own split. */
function tagNames(tagIds: readonly SocialTagId[]): string {
  return tagIds.map(socialTagName).join(', ');
}

/** Clauses joined into one spoken run, with the empties dropped rather than spoken. */
function sentences(clauses: readonly string[]): string {
  return clauses.filter((clause) => clause !== '').join('. ');
}
