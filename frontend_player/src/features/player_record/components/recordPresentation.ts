/**
 * **Every sentence the record sheet says**, and every name it gives a listener.
 *
 * One deck, on the rule the whole app is written to: a screen is assembled from words that
 * live in one place, never from templates inlined in six components. What is here is only what
 * this surface writes — the band's name, the Social tags' words and the sport names are all
 * somebody else's and are quoted through their own tables.
 *
 * ## Five regions, five elements
 *
 * The sheet has **no interactive element inside it** other than the pairing row, so every group
 * in it is actionless and merges into the nearest heading (§20.1). That is what the five
 * `…Label` functions below are: the header, the skill card, the record card, *What opponents
 * said* and the tag row each reach a listener as one clause list rather than as a table of
 * figures read one stop at a time.
 *
 * ## Two absences are deliberately unwritten
 *
 * There is no *no record yet* and no *not enough games*. **An absent panel is not drawn**,
 * which is the same spelling absence takes on the candidate card, in the record block and on
 * the meta line — a sheet that explained its own gaps would be teaching a stranger to read a
 * stranger's silence.
 */

import { counted } from '@/shared/formatting/counted';
import {
  formatLevel,
  formatPercent,
  formatRange,
  formatStars,
} from '@/shared/formatting/ratingFormat';
import { NO_TAGS_IN_COMMON, socialTagName } from '@/shared/vocabulary/socialTagPresentation';
import type { SocialTagId } from '@/shared/vocabulary/socialTags';
import type { SocialTagOverlap } from '@/shared/vocabulary/socialTagOverlap';
import type { GameResult } from '@/shared/vocabulary/gameResult';
// `Photo checked: on court` is the mark's own clause, quoted rather than re-written.
import { ON_COURT_CLAUSE } from '@/shared/ui';

import type {
  Opinion,
  OpinionBand,
  OpinionFigure,
  OpponentVariety,
  ReliabilityStrand,
  StrandRow,
} from '../domain/playerRecord';
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

/**
 * **Their intro, inside the drawing's own quotation marks.**
 *
 * The marks are the sheet's and never the player's: they say *this is them speaking*, which
 * is the whole of what tells a line under a name apart from a second name. Never truncated —
 * the cap at the write is what makes an ellipsis unnecessary
 * ([ADR-0170](../../../../../docs/adr/0170-a-player-may-write-one-line-and-it-is-read-as-their-own.md)
 * §4) — and drawn on the record sheet and the deck card only; the same marks, spelled here
 * rather than imported, because a feature may not deep-import another's copy and a second
 * caller is not the third.
 */
export function introLine(intro: string): string {
  return `“${intro}”`;
}

/** `Padel 2,75` — the pill's words, and the condition on drawing a sport's colour at all. */
export function sportPill(sportName: string, level: number): string {
  return `${sportName} ${formatLevel(level)}`;
}

/**
 * **The three record blocks' names**, and the one of them a listener needs a scale with.
 *
 * They are 7.13's own words, spelled here rather than imported from `features/play/`: the
 * competitive card draws the same three blocks about the same three facts, and a feature may
 * not deep-import another's copy. What is shared between the two surfaces is the **box** and
 * never the words in it — `shared/ui`'s `StatBox` — which is the same split `RunOfForm` takes
 * with `lastFiveReading`.
 *
 * The scale is spelled in the spoken register because Fit is already the other hundred on the
 * screen this sheet opens over, and a bare figure in a run of clauses could be either. Drawn,
 * it needs none: the figure sits under a box named *Player Score*, where nothing else could be
 * out of a hundred.
 */
export const PLAYER_SCORE_BLOCK = 'Player reliability';
export const LAST_FIVE_BLOCK = 'Last 5';
export const COUNTED_BLOCK = 'Counted';
const PLAYER_SCORE_DENOMINATOR = 100;

/**
 * **The block says *Player reliability* and the glossary still says *Player Score*.**
 *
 * That is a divergence on purpose and it is worth knowing which way round it runs. The domain
 * term is the platform's — the ruleset prices it, the matcher acts on it, `CONTEXT.md` owns the
 * word — and nothing here renames any of that. What changed is the **label over the figure**,
 * because *Score* beside a Level, a band and a run of form is the fourth number on one card a
 * reader could take for a rating, and *reliability* is the one word that says what it is not.
 *
 * It is spelled once, here, so the drawn label and the spoken one cannot come apart.
 */
export function scorePillLabel(score: number): string {
  return `${PLAYER_SCORE_BLOCK} ${score} out of ${PLAYER_SCORE_DENOMINATOR}`;
}

/**
 * `PADEL · 2,75 · 77 % sure` — **one text run, and the count is no longer in it.**
 *
 * It read `· 21 counted` as a fourth clause, on the argument that the three figures are
 * inseparable — *a confident-looking number built on three games must not read like one built
 * on forty* — and that three boxes is how one of them ends up conditionally hidden.
 *
 * **The count keeps that job and gets a better place for it.** It is now `COUNTED_BLOCK`, one
 * of 7.13's three, drawn a few points below this line and **never conditional**: `counted_games`
 * is a measured figure the wire always sends beside a Level, so the block that would have gone
 * missing cannot. What the argument was actually protecting is *the count is drawn wherever the
 * Level is*, and that is now structural rather than a rule this string obeys.
 *
 * Printing it in both places was weighed and refused. The two are inches apart in one card, so
 * a reader meets `21 counted` twice in two registers — which is the double announcement §20.1
 * spends the whole sheet avoiding in the spoken half, made visible.
 */
export function skillHeadline(facts: {
  readonly sportName: string;
  readonly level: number;
  readonly confidence: number;
}): string {
  return [
    facts.sportName.toUpperCase(),
    formatLevel(facts.level),
    `${formatPercent(facts.confidence)} sure`,
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
  /** Their intro, already inside its marks (`introLine`), or nothing where they wrote none. */
  readonly intro?: string;
  readonly identity: string;
  /** One `sportPill` string per rated sport, in the registry's order. */
  readonly sports: readonly string[];
}

export function recordHeaderLabel(facts: HeaderFacts): string {
  return sentences([
    facts.handle,
    ...(facts.onCourt ? [ON_COURT_CLAUSE] : []),
    // Inside its marks, so a listener hears it as the person's own words and never as a
    // second name — the deck card speaks it the same way.
    ...(facts.intro === undefined ? [] : [facts.intro]),
    ...(facts.identity === '' ? [] : [facts.identity]),
    ...(facts.sports.length === 0 ? [] : [facts.sports.join(', ')]),
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
  readonly likelyRange: { readonly low: number; readonly high: number };
}

export function skillCardLabel(facts: SkillCardFacts): string {
  return sentences([
    facts.sportName,
    `Level ${formatLevel(facts.level)}, ${facts.band}`,
    `${formatPercent(facts.confidence)} sure`,
    likelyRangeLine(facts.likelyRange),
  ]);
}

/**
 * **The block row, as one element** — nought to three clauses, in the order they are drawn.
 *
 * There is no argument for a different order here, unlike the candidate card's spoken body: the
 * three are the same register and the row reads left to right. A block that is hidden says
 * nothing, which is *hidden, never blank* read in the register a reader cannot see.
 *
 * **It is its own element rather than a clause of the card above it**, because the card above
 * it is about **one sport** and the Player Score is about the whole person. Folding the row into
 * `skillCardLabel` would announce a reliability figure inside a sentence that opened with
 * *Tennis*.
 */
export interface RecordBlockFacts {
  readonly playerScore?: number;
  readonly lastFive?: readonly GameResult[];
  readonly countedGames?: number;
}

export function recordBlocksLabel(facts: RecordBlockFacts): string {
  return sentences([
    ...(facts.playerScore === undefined ? [] : [scorePillLabel(facts.playerScore)]),
    ...(facts.lastFive === undefined || facts.lastFive.length === 0
      ? []
      : [lastFiveReading(facts.lastFive)]),
    ...(facts.countedGames === undefined ? [] : [countedGamesReading(facts.countedGames)]),
  ]);
}

// **The card carries no heading, and losing it was the point.** It read *The record — counted
// by the system, not written by people*, and that sentence was a promise about **authorship**:
// it is why `countedRows` drops the sportsmanship strand, and why what other players said stood
// outside the card in a block of its own. The rating belongs on the record, so the heading went
// rather than the row — a title claiming nobody wrote any of this, over a star average people
// wrote, is worse than no title. What it was carrying is now on {@link SPORTSMANSHIP_LABEL},
// the one row that has an author.

/**
 * **What each strand is called on screen**, keyed off the served code and never off the row's
 * position — a strand with nothing behind it is absent from the list entirely, so the rows a
 * card gets are the rows that person has.
 *
 * **`ANSWERS_RESULTS` is *Answers about results* and never *confirms* anything.** Countering a
 * score you believe is wrong is an answer and costs nothing
 * ([ADR-0160](../../../../../docs/adr/0160-a-results-strand-counts-answers-and-never-agreements.md));
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

/**
 * **The one row on this card people wrote, and the label says so.**
 *
 * *by players* is what survives of the card's own heading. Every row above it is counted by
 * the platform and none of them needs an author; this one does, and naming it here costs three
 * words where a heading over the whole card cost the truth of every row under it.
 *
 * **Not *by opponents***, which `the-decisions.md` struck by name: *"which stopped being true
 * when partners started rating"*. The card asks about everybody who was on the court, partner
 * included — the person who saw you play closest was on your own side of the net — so a label
 * naming opponents would describe the one seat the figure does **not** rest on alone.
 */
export const SPORTSMANSHIP_LABEL = 'Sportsmanship, by players';

/**
 * What the row prints on the right — `4,7 / 5 · 17 players` for a reader, one word for the
 * subject.
 *
 * The two arms are the wire's, folded at the boundary from `is_self`, so this switches on what
 * it was handed and compares nothing. The band takes **no tone**: `scoreTone` is this sheet's
 * one ladder and it belongs to the Player Score, so a coarse three-step painted in the same
 * three colours would offer itself as a second score on the screen a held player opens to find
 * out what is holding them back.
 */
export function opinionValue(opinion: Opinion): string {
  return opinion.kind === 'band' ? OPINION_BAND_NAME[opinion.band] : opinionFigure(opinion);
}

/** The two halves, computed once so the drawn row and the spoken one cannot disagree. */
function varietyParts(variety: OpponentVariety): readonly [string, string] {
  return [
    formatPercent(varietyShare(variety)),
    rawPair(variety.distinctOpponents, variety.timesOnCourt),
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
  readonly opinion?: Opinion;
}

/**
 * **The card, as one element** — every row it drew, and nothing about a heading it no longer
 * has.
 *
 * The sportsmanship clause carries `WRITTEN_BY_PLAYERS` behind it, which is the contract's own
 * instruction and the half a listener cannot get from the row's label: *by players* says who
 * wrote it, and the sentence says that a low one acts on nobody. It is spoken only where the row
 * is drawn, because a promise about a figure nobody was shown is a sentence about nothing.
 */
export function recordCardLabel(facts: RecordCardFacts): string {
  return sentences([
    ...facts.rows.map(strandReading),
    ...(facts.variety === undefined ? [] : [varietyReading(facts.variety)]),
    ...(facts.opinion === undefined ? [] : [opinionReading(facts.opinion)]),
  ]);
}

/**
 * The scale, printed beside the figure: `4,7` alone says nothing about what five would be.
 *
 * It is **copy** rather than a formatting constant, which is why it is here and the decimal
 * place is in `ratingFormat`: the drawn register writes it as `/ 5` and the spoken one as *out
 * of 5*, so the two are one word apart and neither is a number's shape.
 */
const STAR_SCALE = 5;

/**
 * `4,7 / 5 · 17 players` — **the average and the count, and never one without the other.**
 *
 * A figure drawn without its count is this field's one way of lying: `4,7 / 5 · 17 players` and
 * `3,0 / 5 · 1 player` are the same field, and the second has to visibly read as one person's
 * opinion. There is no minimum before it publishes because the count does a minimum's work
 * honestly — which is the discipline the metered rows already take by printing their raw pair.
 *
 * The mean is **served, not derived**: there is one rounding of this record on the platform.
 */
export function opinionFigure(figure: OpinionFigure): string {
  return `${formatStars(figure.average)} / ${STAR_SCALE} · ${ratersReading(figure.raters)}`;
}

/** **People, not ratings** — a weekly partner is one rater however many evenings they play. */
function ratersReading(raters: number): string {
  return counted(raters, 'player', 'players');
}

/**
 * **The three steps a subject may be told**, and there is nothing finer anywhere on their own
 * record.
 *
 * One word each, drawn in the type register a sentence takes rather than in a figure's mono, and
 * **carrying no tone**: `scoreTone` is the sheet's one ladder and it belongs to the number the
 * matcher acts on, so tinting a coarse band in the same three colours would offer this one to be
 * read as a second Player Score. The word is the whole answer, which is what makes the band safe.
 */
export const OPINION_BAND_NAME: Readonly<Record<OpinionBand, string>> = {
  GOOD: 'Good',
  MIXED: 'Mixed',
  POOR: 'Poor',
};

/**
 * **The two sentences under the card are gone, and this is what they said** (#384).
 *
 * `BAND_HAS_NO_COUNT` — *A band and no count, so no single answer can be worked out of it* —
 * explained to the subject why their own record is coarser than the ones they read all day.
 * `WRITTEN_BY_PLAYERS` — *Written by other players. It is not in the Player Score, and it hides
 * nobody and holds nobody back* — is asked for **by name** by `the-words.md` wherever the star
 * figure is drawn beside the reliability figure, and both of its halves were load-bearing:
 * naming the score says where the average is *not* counted, and the second half says a low one
 * acts on nobody.
 *
 * **They are removed by decision and the cost is real.** The row's label still names its author
 * — *Sportsmanship, by players* — which is the half a reader can infer; what is no longer said
 * anywhere on this sheet is that a low average **costs nothing**. A reader may now take a
 * `2,0 / 5` for a penalty the platform issued, and the subject is left to notice on their own
 * that their own record is coarser than everybody else's. If either reading turns out to
 * matter, the sentences are here and go back on the block rather than being rewritten.
 */

/**
 * **The answer as a listener meets it** — clauses, where the block draws a separator and a
 * slash, and the band's own sentence with it.
 *
 * One switch on the arm and not two: what a listener is told and how much of it there is are
 * the same fact about which arm this is, and splitting them is how a block ends up speaking one
 * arm's sentence over the other's figure.
 */
function opinionClauses(opinion: Opinion): readonly string[] {
  return opinion.kind === 'band'
    ? [`${OPINION_BAND_NAME[opinion.band]}.`]
    : [`${formatStars(opinion.average)} out of ${STAR_SCALE}, ${ratersReading(opinion.raters)}.`];
}

/**
 * **The row as a listener meets it** — its label, then its answer.
 *
 * It reads as a clause in the card's own sentence rather than as a block of its own, which is
 * what moving the figure onto the card made it. `WRITTEN_BY_PLAYERS` follows it in
 * {@link recordCardLabel} rather than being folded in here, because it is one promise about the
 * row and not part of the answer.
 */
function opinionReading(opinion: Opinion): string {
  // The clause carries its own full stop — it was a block's prose before it was a row's —
  // and `sentences` punctuates what it is handed, so it is dropped here rather than leaving
  // the reading with two.
  const said = opinionClauses(opinion).join(' ').replace(/\.$/, '');

  return `${SPORTSMANSHIP_LABEL}, ${said}`;
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
 * **The one control on this sheet, and the one thing on it about the two of you.**
 *
 * The Fit breakdown is not deleted — the number in the pill has no other account anywhere in
 * the app, and deleting its only explanation leaves a figure on screen that nothing answers
 * for. It sits under the sport pills now rather than in a card at the foot of the sheet: it is
 * the sheet's only action, and an action a reader has to scroll past four zones to find is one
 * most readers never find.
 *
 * **It is named for what it opens, and it carries the figure it opens an account of.** *Why ✦
 * 78* put a glyph in the control's own name and made that name a question; *Player fit 78* is
 * the fact and the number, which is what a reader is deciding whether to ask about.
 *
 * **The figure is rounded here, because this is where it is printed.** `whyFitColumn` writes
 * the whole breakdown against `Math.round(fit)`, so a served `78,4` shown whole on this control
 * would promise *Player fit 78,4* and open a sheet titled 78. Rounding at the call site instead
 * would be a rule each entry point had to remember — `signedFigure`'s own rule that a figure is
 * rounded where it is printed.
 *
 * The visible name and the spoken one are the same string, which is §20.6's flat rule: there is
 * no glyph doing work in it any more, so the one exception no longer applies.
 */
export const FIT_ROW_NAME = 'Player fit';

export function fitRowLabel(fit: number): string {
  return `${FIT_ROW_NAME} ${Math.round(fit)}`;
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
