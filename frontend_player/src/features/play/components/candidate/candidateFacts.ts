/**
 * What a card reads off a candidate — the one join between the codes and the words.
 *
 * Three cards draw three shapes over one contract, and every one of them needs the same
 * answers: the person's name, the level row's facts, the meta line's, the reasons that
 * survived this surface's filter, the one concern it draws, and the spoken name composed from
 * all of them. Written per card that is the same lookup three times, and the third copy is
 * where one of them stops matching.
 *
 * **One call per render, and the spoken name is composed from the same values that are
 * drawn.** Read twice — once for the body and once for the label — the two could disagree
 * without anything failing: §20.3's whole claim is that the card is *spoken in a different
 * order than it is drawn*, which is only true if it is the same card.
 *
 * **It holds no words and no rules.** The words are `reasonPresentation`'s,
 * `livenessPresentation`'s, `concernPresentation`'s and `playerCardPresentation`'s; the rules
 * are `reasonSelection`'s. What is here is the wiring between them, including the one argument
 * `selectReasons` cannot make for itself — *can this evidence be written as a sentence at
 * all* — because that is a question about the copy and `domain/` holds none.
 */

import { playerName } from '@/shared/formatting/playerName';
import { ON_COURT_CLAUSE } from '@/shared/ui';

import type { AtStake, Candidate, SearchEnvelope } from '../../domain/candidate';
import { isTagEvidence, type Evidence, type ScoredTerm } from '../../domain/evidence';
import { wearsOnCourtMark, type MarkablePhoto } from '../../domain/onCourtMark';
import { selectConcern, selectReasons, type ReasonSelection } from '../../domain/reasonSelection';
import type { SocialTagOverlap } from '../../domain/socialTagOverlap';
import type { Term } from '../../domain/vocabulary';
import { candidateCardLabel } from '../accessibilityPresentation';
import { balanceReading } from '../balancePresentation';
import { concernLine } from '../concernPresentation';
import { livenessLine } from '../livenessPresentation';
import {
  recordClauses,
  socialTagClauses,
  stakeClauses,
  type LevelRowFacts,
  type MetaLineFacts,
  type RecordBlockFacts,
} from '../playerCardPresentation';
import { reasonLine } from '../reasonPresentation';

/**
 * Everything a card reads off one candidate, resolved once.
 *
 * The lines are already the sentences the card draws, and `label` is composed from those same
 * strings — see the module note.
 */
export interface CandidateFacts {
  /** §15's `playerName()` — the whole handle, and a type that will not take a shortened one. */
  readonly name: string;
  readonly level: LevelRowFacts;
  /**
   * Whether the photo panel wears the ON COURT mark — **one answer, drawn and spoken**.
   *
   * `wearsOnCourtMark`'s, taken here so the panel and the label cannot disagree about a
   * photograph: the mark is the one thing on this card whose absence has two causes, and two
   * reads of it are two chances to fold them differently.
   */
  readonly onCourt: boolean;
  /** The forecast reading, on the card that **draws** it rather than saying it. */
  readonly balance: string | undefined;
  /** Omitted where the card draws no meta line, or the distance term stood down. */
  readonly meta: MetaLineFacts | undefined;
  readonly reasons: readonly string[];
  /** At most one. The rest are the why-fit sheet's. */
  readonly concerns: readonly string[];
  /** The row's spoken clauses, on the card that draws it. Empty on the other two. */
  readonly socialTags: readonly string[];
  /** The card body's spoken name, in §20.3's order. */
  readonly label: string;
}

/**
 * What a card hands over — **an object, because three of the five are optional and each of
 * them means *this surface does not draw that part*.**
 *
 * Positionally, `(candidate, envelope, drawn, socialTags?, seats?)` is a call site whose
 * fourth and fifth arguments are two `undefined`s in a row on two cards of three, and the
 * reader has to count commas to find out which part is being declined. Named, each absence
 * says which.
 */
export interface CandidateFactsInput {
  readonly candidate: Candidate;
  readonly envelope: SearchEnvelope;
  /** The terms this surface renders a value for — the card's **own** exported set. */
  readonly drawn: readonly Term[];
  /**
   * Whether this surface draws the **argument** — the reason lines, and the concern under
   * them. Default `true`, which is the two cards that have always drawn one.
   *
   * **It is not a filter, and that is the whole of why it exists.** `drawn` takes a term off
   * the list *because the card states it somewhere else*, which is a claim about one fact;
   * this says the surface makes no case at all, and the lines are therefore not composed. The
   * difference shows up in the **label**: a card whose lines were filtered to nothing still
   * has reasons to speak, and one that argues nothing must not speak any — §20.3 lets the
   * spoken order differ from the drawn one, never the content.
   *
   * The competitive card sets it `false` (2026-09-09): its case is `SH.whyfit`'s, opened by a
   * named control on every row, and twenty rows each carrying three sentences is a list nobody
   * reads. Everything that card **measures** is untouched — the panel, the pill, the band, the
   * record blocks — so what it loses is prose and not a fact. The social and deck cards keep
   * theirs: neither has a sheet behind it, and on the deck the sentence **is** the card.
   */
  readonly argues?: boolean;
  /**
   * The **Social tag row**, passed in by the card that draws it — and omitted by the two that
   * do not ([#311](https://github.com/Raketa02/Raketa/issues/311)).
   *
   * It is the row itself rather than a flag saying *this card has one*, because both things
   * this function does with it need the **value**: the label's clauses are composed from it,
   * and the reason list is filtered against the tags it actually drew. Handed a boolean, the
   * second would have to re-derive what the first was given — which is the *read twice and they
   * could disagree* the module note opens with, in a smaller spelling — and it would re-derive
   * it from the wrong list, since the term's `matched` and the row's drawn chips are not
   * guaranteed to be the same set. It travels down to `reasonLinesOf` whole for that reason.
   *
   * **It is not in `drawn`.** That set is *terms the card draws as rows*, and the card draws
   * half of these two: `matched` becomes chips, while `complementary`, `clashing` and each
   * term's measured zero stay reason sentences and stay this card's. Adding them to `drawn`
   * would take all four registers away to stop one of them repeating.
   */
  readonly socialTags?: SocialTagOverlap;
  /**
   * The **three record blocks**, passed in by the card that draws them and omitted by the two
   * that do not ([#312](https://github.com/Raketa02/Raketa/issues/312)).
   *
   * `socialTags`' pattern one field down, and for its reason: the clauses are composed from
   * this value and the boxes are drawn from it, so there is one value and no second read. It is
   * the facts rather than a flag because `PlayerCard` already carries all three — the card hands
   * over its own subject, and a `drawsTheRecord: true` beside it would be a second thing to keep
   * true.
   *
   * **`undefined` and an object whose three fields are all absent are different answers.**
   * `undefined` is *this surface has no record block*; the empty object is *this surface has one
   * and the platform has watched nothing*. Only the second is a card for a brand-new player.
   */
  readonly record?: RecordBlockFacts;
  /**
   * What a counted game would move — **`stakeOnACard`'s answer**, taken by the card off the
   * sport's seat count before this is called.
   *
   * The decision is not here for the reason it is not in the component either: it is a rule
   * about doubles that somebody could be wrong about, so it lives in `domain/atStake`, and both
   * the drawing and the clauses read the one result.
   */
  readonly stake?: AtStake;
  /**
   * The **photo panel's** two fields, passed in by the one card that draws a panel and
   * omitted by the two that do not ([#313](https://github.com/Raketa02/Raketa/issues/313)).
   *
   * `record`'s shape and `record`'s argument: `undefined` is *this surface has no photo
   * panel*, and an object whose verdict is absent is *it has one, over a photograph nobody
   * looked at*. Two different answers, and only the second is a card that could have worn a
   * mark.
   *
   * **The panel is the competitive card's alone.** The social and deck cards draw the same
   * photograph full-bleed as media rather than as a panel with facts printed on it, and a
   * mark floated over media has nowhere it belongs: the panel's top was left clear for this
   * ([#309](https://github.com/Raketa02/Raketa/issues/309)) and no other card has a clear
   * top. So this is a fact about the **surface**, exactly as `drawn` is, and the two cards
   * without a panel decline it rather than being told not to draw one.
   */
  readonly photo?: MarkablePhoto;
}

export function candidateFacts(input: CandidateFactsInput): CandidateFacts {
  const { candidate, envelope, drawn, argues = true, socialTags, record, stake, photo } = input;
  const name = playerName({ kind: 'player', name: candidate.card.name });
  const level = levelFactsOf(candidate);
  // Read once for both registers, exactly as the tag row and the record block are: the panel
  // draws the mark from this answer and the label speaks it from the same one, so a
  // photograph cannot be marked to a reader and unmarked to a listener.
  const onCourt = photo !== undefined && wearsOnCourtMark(photo);
  // A clause per row the card DRAWS — which is the drawn set read the other way round. A
  // card that says a term as a reason line must not also state it as a fact, and a card that
  // draws it as a row must state it here, because the row itself announces nothing (§20.1).
  const balance = drawn.includes('PREDICTED_BALANCE') ? balanceOf(candidate) : undefined;
  const meta = drawn.includes('DISTANCE') ? metaFactsOf(candidate, envelope) : undefined;
  // Not composed rather than composed and dropped: what is not here cannot reach the label,
  // and the label is the one place a card can say something it does not draw.
  const reasons = argues ? reasonLinesOf(candidate, drawn, socialTags) : [];
  const concerns = argues ? concernLines(candidate) : [];
  const tagClauses = socialTags === undefined ? [] : socialTagClauses(socialTags);

  return {
    name,
    level,
    onCourt,
    balance,
    meta,
    reasons,
    concerns,
    socialTags: tagClauses,
    // §20.3 fixes ONE order for every card in the feature, and it is not the order they are
    // drawn in: identifying facts lead, the argument follows. A card composing its own could
    // drift from the other two, which is what §20.3 exists to stop.
    label: candidateCardLabel({
      name,
      fit: candidate.fit,
      level,
      ...(onCourt ? { onCourt: ON_COURT_CLAUSE } : {}),
      balance,
      meta,
      record: record === undefined ? undefined : recordClauses(record),
      stake: stake === undefined ? undefined : stakeClauses(stake),
      socialTags: tagClauses,
      reasons,
      concerns,
    }),
  };
}

/** The forecast as the card draws it, or nothing where the term stood down. */
function balanceOf(candidate: Candidate): string | undefined {
  const balance = evidenceOf(candidate, 'predicted_balance');
  return balance === undefined ? undefined : balanceReading(balance.pct);
}

/**
 * The evidence behind one of the terms a card draws **as a row**.
 *
 * Typed on the variant rather than on the term, so a card asking for the forecast gets
 * `PredictedBalanceEvidence` or nothing — never a `Evidence` it has to narrow again at the
 * call site, which is where a card would end up branching on a term after all.
 *
 * `undefined` means the term **stood down**: a degraded term is not on `terms[]` at all, and a
 * row with no evidence is a row the card does not draw. That is the same *hidden, never blank*
 * discipline the reason list takes.
 */
export function evidenceOf<K extends Evidence['kind']>(
  candidate: Candidate,
  kind: K,
): Extract<Evidence, { readonly kind: K }> | undefined {
  const row = candidate.terms.find((term) => term.evidence?.kind === kind);
  return row?.evidence as Extract<Evidence, { readonly kind: K }> | undefined;
}

/** The three facts the level row states, exactly as `player_card` published them. */
function levelFactsOf(candidate: Candidate): LevelRowFacts {
  const { level, band, range } = candidate.card;
  return { level, band, range };
}

/**
 * What the meta line states, or nothing at all.
 *
 * `distanceKm` is **omitted rather than zero** where the distance term stood down, and a meta
 * line with no distance in it would be an area comparison standing alone — which is the one
 * thing §6.3 licenses the client to compute and not a line the card was asked for. Hidden
 * rather than blank, once more.
 */
function metaFactsOf(candidate: Candidate, envelope: SearchEnvelope): MetaLineFacts | undefined {
  if (candidate.distanceKm === undefined) return undefined;
  return {
    km: candidate.distanceKm,
    theirAreaCode: candidate.card.areaCode,
    myAreaCode: envelope.myAreaCode,
  };
}

/**
 * The lines this surface says under the fit pill, in the order it draws them.
 *
 * `drawn` is the card's **own** exported set, passed in rather than looked up here: the set is
 * a statement about what that component draws, and this is not that component.
 *
 * **All three cards draw the whole selection, and the cap is `REASON_CAP`'s alone.** What the
 * social and deck cards *gain* is the reason line as a slot — without it `INTENT_ALIGNMENT`,
 * third-largest term in both modes, is invisible on two cards of three
 * ([`the-words.md`](../../../../../../docs/specs/matchmaking/the-words.md) §5) — not a second,
 * smaller cap of their own. A per-card count would be a fourth number nothing argues for, and
 * it would put the spoken name out of step with the drawing: §20.3 composes the card body's
 * label from these same lines, so a card drawing fewer than it announces is a card that says
 * one thing to a listener and another to a reader.
 */
function reasonLinesOf(
  candidate: Candidate,
  drawn: readonly Term[],
  socialTags: SocialTagOverlap | undefined,
): readonly string[] {
  return reasonLines(
    selectReasons({
      drawn,
      terms: candidate.terms,
      concerns: candidate.concerns,
      livenessReasons: candidate.livenessReasons,
      // A row this build cannot read says nothing on a **card**: §3 drops a code wherever the
      // screen states no total it belongs to, and a card shows three reasons out of eight and
      // always did. The named gap is the why-fit sheet's, which prints the column.
      saysSomething: (term) =>
        term.evidence !== null &&
        reasonLine(term.evidence) !== undefined &&
        !restatesTheTagRow(term.evidence, socialTags),
    }),
  );
}

/**
 * Whether this evidence's reason line would say what the tag row **has already drawn**.
 *
 * `tagTermReason`'s precedence is *matched, then complementary, then the measured zero*, so a
 * tag term with anything in `matched` writes **`Both of you: …`** — the same ids the row is
 * drawing as tinted chips two lines up. §10's *the fact is said once* is about the two
 * registers rather than the pixel count, so the sentence goes and the chips stay: the chips are
 * the richer form, and they are what the ticket asked for.
 *
 * **It asks about the tags the row drew, not about the term's own list**, and the difference is
 * the one edge where the two lists part company: the row is capped at `SOCIAL_TAG_ROW_CAP`, so
 * a match beyond the cap is a chip nobody drew — and a filter keyed on `matched.length > 0`
 * would delete the only sentence saying it, leaving the fact stated **nought** times. Asking the
 * row itself means the sentence goes exactly when something took its place.
 *
 * Nothing else about these terms changes. A term whose `matched` is empty still says its
 * complementary pair or its measured zero, which is exactly what the ticket protects when it
 * says complementary and clashing *"already reach this card as reason sentences"* — and a card
 * that draws no row (`undefined`) filters nothing at all, which is what keeps this a rule about
 * one surface rather than about the two terms.
 */
function restatesTheTagRow(evidence: Evidence, row: SocialTagOverlap | undefined): boolean {
  if (row?.kind !== 'shared' || !isTagEvidence(evidence)) return false;
  const drawn = new Set(row.tags.filter((tag) => tag.shared).map((tag) => tag.id));
  return evidence.matched.some((id) => drawn.has(id));
}

/**
 * The selection, as the sentences it names. `hidden` is no line rather than an empty one.
 *
 * **Exported**, because the challenge screen's card draws reason lines off the same selection
 * ([#361](https://github.com/Raketa02/Raketa02/issues/361)): a second copy of this `switch` is a
 * second place for a selection arm to be forgotten, and the arm that would be forgotten is
 * `hidden` — the one whose whole job is not printing a blank row.
 */
export function reasonLines(selection: ReasonSelection): readonly string[] {
  switch (selection.kind) {
    case 'terms':
      // `saysSomething` already dropped every row this can decline for, so nothing is lost
      // here — the filter is what keeps the promise of three from printing two.
      return selection.terms.flatMap((term) =>
        term.evidence === null ? [] : (reasonLine(term.evidence) ?? []),
      );
    case 'liveness':
      return [livenessLine(selection.reason)];
    case 'hidden':
      return [];
  }
}

/**
 * The one concern a card draws, as a sentence. All of them are the why-fit sheet's.
 *
 * Takes the two lists rather than a `Candidate`, so the challenge screen's card — which holds a
 * narrower pairing and no candidate at all — reads the same rule. `saysSomething` is here rather
 * than at the call sites because *can this evidence be written as a concern* is a fact about the
 * copy, and a caller passing its own answer is a caller that can disagree with the sentence that
 * gets drawn.
 */
export function concernLines(pairing: {
  readonly terms: readonly ScoredTerm[];
  readonly concerns: readonly Term[];
}): readonly string[] {
  return selectConcern({
    terms: pairing.terms,
    concerns: pairing.concerns,
    saysSomething: (term) => term.evidence !== null && concernLine(term.evidence) !== undefined,
  }).flatMap((term) => (term.evidence === null ? [] : (concernLine(term.evidence) ?? [])));
}
